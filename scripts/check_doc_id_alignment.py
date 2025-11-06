#!/usr/bin/env python3
"""
Doc ID Alignment Health Check
Verifies that Qdrant vector DB IDs/payload can be aligned with evaluation IDs used for Recall@10.
"""

import requests
import json
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime


class DocIdAlignmentChecker:
    def __init__(self, collection: str, host: str = "localhost", port: int = 6333):
        self.collection = collection
        self.base_url = f"http://{host}:{port}"
        self.log_file = "fix.log"
        self.report_file = "HEALTH_REPORT.md"
        
        self.doc_id_field = None
        self.normalizer_fn = None
        self.results = {}
        
        # Clear log file
        with open(self.log_file, "w") as f:
            f.write(f"=== Doc ID Alignment Check - {datetime.now()} ===\n\n")
    
    @staticmethod
    def normalize_doc_id(doc_id) -> str:
        """Normalize document ID for robust matching (handles numeric, whitespace, case)."""
        if doc_id is None:
            return ""
        return str(doc_id).strip().lower()
    
    def log(self, message: str, to_console: bool = True):
        """Write to both log file and optionally console"""
        with open(self.log_file, "a") as f:
            f.write(message + "\n")
        if to_console:
            print(message)
    
    def discover_id_field(self) -> str:
        """Step 1: Discover which field to use as document ID"""
        self.log("\n=== STEP 1: Discover ID Field ===")
        
        # Scroll first 5 points
        try:
            response = requests.post(
                f"{self.base_url}/collections/{self.collection}/points/scroll",
                json={"limit": 5, "with_payload": True, "with_vector": False},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok" or not data.get("result", {}).get("points"):
                self.log("❌ Failed to fetch points from Qdrant")
                return None
            
            points = data["result"]["points"]
            self.log(f"✓ Fetched {len(points)} sample points")
            
            # Check candidate fields in order
            candidates = ["doc_id", "docId", "uuid", "id"]
            payload_keys = set()
            
            for point in points:
                if "payload" in point and point["payload"]:
                    payload_keys.update(point["payload"].keys())
            
            self.log(f"  Payload keys found: {sorted(payload_keys)}")
            
            # Find first matching candidate
            for candidate in candidates:
                if candidate in payload_keys:
                    self.doc_id_field = candidate
                    self.log(f"✓ Found candidate field: '{candidate}' in payload")
                    self.log(f"  Decision: Use payload['{candidate}'] as DOC_ID_FIELD")
                    
                    # Sample values
                    sample_values = []
                    for point in points:
                        val = point.get("payload", {}).get(candidate)
                        if val is not None:
                            sample_values.append(val)
                    
                    self.log(f"  Sample values: {sample_values[:5]}")
                    self.results["doc_id_field"] = candidate
                    self.results["doc_id_source"] = "payload"
                    return candidate
            
            # Fallback to Qdrant point ID
            self.log(f"  No candidate field found in payload")
            self.log(f"  Decision: Fall back to using Qdrant point 'id' as document ID")
            self.doc_id_field = "_point_id"
            
            sample_ids = [point["id"] for point in points]
            self.log(f"  Sample point IDs: {sample_ids[:5]}")
            
            self.results["doc_id_field"] = "_point_id"
            self.results["doc_id_source"] = "point_id"
            return "_point_id"
            
        except Exception as e:
            self.log(f"❌ Error discovering ID field: {e}")
            return None
    
    def check_uniqueness(self, sample_size: int = 10000) -> Dict[str, Any]:
        """Step 2: Check uniqueness of IDs"""
        self.log("\n=== STEP 2: Uniqueness Check ===")
        
        if not self.doc_id_field:
            self.log("❌ Skipping: doc_id_field not determined")
            return {"status": "skipped"}
        
        try:
            # Get collection info first
            response = requests.get(f"{self.base_url}/collections/{self.collection}")
            response.raise_for_status()
            collection_info = response.json()
            total_points = collection_info.get("result", {}).get("points_count", 0)
            
            self.log(f"  Total points in collection: {total_points}")
            
            # Determine sample size
            actual_sample = min(sample_size, total_points)
            self.log(f"  Sampling {actual_sample} points for uniqueness check")
            
            # Scroll through points
            seen_ids = []
            offset = None
            
            while len(seen_ids) < actual_sample:
                batch_size = min(100, actual_sample - len(seen_ids))
                
                payload = {"limit": batch_size, "with_payload": True, "with_vector": False}
                if offset is not None:
                    payload["offset"] = offset
                
                response = requests.post(
                    f"{self.base_url}/collections/{self.collection}/points/scroll",
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                points = data.get("result", {}).get("points", [])
                if not points:
                    break
                
                for point in points:
                    if self.doc_id_field == "_point_id":
                        doc_id = str(point["id"])
                    else:
                        doc_id = point.get("payload", {}).get(self.doc_id_field)
                        if doc_id is not None:
                            doc_id = str(doc_id)
                    
                    if doc_id is not None:
                        seen_ids.append(doc_id)
                
                offset = data.get("result", {}).get("next_page_offset")
                if offset is None:
                    break
            
            # Calculate uniqueness
            total_sampled = len(seen_ids)
            unique_ids = len(set(seen_ids))
            duplicates_count = total_sampled - unique_ids
            
            self.log(f"  Total sampled: {total_sampled}")
            self.log(f"  Unique IDs: {unique_ids}")
            self.log(f"  Duplicates: {duplicates_count}")
            
            result = {
                "status": "pass" if duplicates_count == 0 else "fail",
                "total_points": total_points,
                "sampled_points": total_sampled,
                "unique_ids": unique_ids,
                "duplicates_count": duplicates_count
            }
            
            if duplicates_count > 0:
                # Find top duplicates
                counter = Counter(seen_ids)
                top_dupes = counter.most_common(10)
                self.log(f"❌ FAIL: Found {duplicates_count} duplicates")
                self.log(f"  Top 10 duplicates:")
                for doc_id, count in top_dupes:
                    if count > 1:
                        self.log(f"    {doc_id}: appears {count} times")
                result["top_duplicates"] = top_dupes
            else:
                self.log(f"✓ PASS: All IDs are unique")
            
            self.results["uniqueness"] = result
            return result
            
        except Exception as e:
            self.log(f"❌ Error checking uniqueness: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_type_consistency(self, qrels_file: str) -> Dict[str, Any]:
        """Step 3: Check type consistency between Qdrant and evaluation IDs"""
        self.log("\n=== STEP 3: Type Consistency Check ===")
        
        if not self.doc_id_field:
            self.log("❌ Skipping: doc_id_field not determined")
            return {"status": "skipped"}
        
        try:
            # Get sample from Qdrant
            response = requests.post(
                f"{self.base_url}/collections/{self.collection}/points/scroll",
                json={"limit": 10, "with_payload": True, "with_vector": False},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            points = data.get("result", {}).get("points", [])
            
            qdrant_ids = []
            for point in points:
                if self.doc_id_field == "_point_id":
                    qdrant_ids.append(point["id"])
                else:
                    doc_id = point.get("payload", {}).get(self.doc_id_field)
                    if doc_id is not None:
                        qdrant_ids.append(doc_id)
            
            # Get sample from qrels
            eval_ids = []
            try:
                with open(qrels_file, 'r') as f:
                    for i, line in enumerate(f):
                        if i == 0:  # Skip header
                            continue
                        if i > 100:  # Sample first 100
                            break
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            eval_ids.append(parts[1])  # corpus-id
            except Exception as e:
                self.log(f"⚠️  Could not load qrels: {e}")
                return {"status": "error", "error": str(e)}
            
            # Detect types
            qdrant_types = set(type(x).__name__ for x in qdrant_ids)
            eval_types = set(type(x).__name__ for x in eval_ids)
            
            self.log(f"  Qdrant ID types: {qdrant_types}")
            self.log(f"  Qdrant ID samples: {qdrant_ids[:5]}")
            self.log(f"  Eval ID types: {eval_types}")
            self.log(f"  Eval ID samples: {eval_ids[:5]}")
            
            # Check if normalization needed
            needs_normalization = False
            normalizer_rule = "none"
            
            # Both should be strings for comparison
            # Check if they look similar
            qdrant_sample_str = [str(x) for x in qdrant_ids[:5]]
            eval_sample_str = [str(x) for x in eval_ids[:5]]
            
            # Detect if there's a pattern mismatch
            if qdrant_types != eval_types:
                self.log(f"  Type mismatch detected")
                needs_normalization = True
                normalizer_rule = "str().strip()"
            
            # Check for prefix patterns (e.g., "FIQA_")
            if any(str(x).startswith("FIQA_") for x in eval_ids[:10]):
                self.log(f"  Detected 'FIQA_' prefix in eval IDs")
                needs_normalization = True
                normalizer_rule = "strip('FIQA_').strip()"
            
            # Always use robust normalization (handles numeric, whitespace, case)
            self.log(f"  Using robust normalization: str().strip().lower()")
            self.normalizer_fn = self.normalize_doc_id
            
            result = {
                "status": "pass",
                "qdrant_types": list(qdrant_types),
                "eval_types": list(eval_types),
                "needs_normalization": needs_normalization,
                "normalizer_rule": normalizer_rule
            }
            
            self.results["type_consistency"] = result
            return result
            
        except Exception as e:
            self.log(f"❌ Error checking type consistency: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_alignment_rate(self, qrels_file: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Step 4: Check alignment rate between Qdrant and evaluation IDs"""
        self.log("\n=== STEP 4: Alignment Rate Check ===")
        
        if not self.doc_id_field:
            self.log("❌ Skipping: doc_id_field not determined")
            return {"status": "skipped"}
        
        try:
            # Load evaluation IDs from qrels
            eval_doc_ids = set()
            with open(qrels_file, 'r') as f:
                for i, line in enumerate(f):
                    if i == 0:  # Skip header
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        eval_doc_ids.add(parts[1])  # corpus-id
            
            self.log(f"  Loaded {len(eval_doc_ids)} unique document IDs from qrels")
            
            # Sample N IDs
            sample_eval_ids = list(eval_doc_ids)[:sample_size]
            self.log(f"  Sampling {len(sample_eval_ids)} IDs for alignment check")
            
            # Try to find each in Qdrant
            found_count = 0
            missing_ids = []
            
            # Build a lookup of Qdrant IDs
            self.log(f"  Building Qdrant ID lookup...")
            qdrant_id_map = {}  # normalized_id -> point_info
            
            # Get collection size
            response = requests.get(f"{self.base_url}/collections/{self.collection}")
            response.raise_for_status()
            collection_info = response.json()
            total_points = collection_info.get("result", {}).get("points_count", 0)
            
            # Scan all points (or up to 100k for very large collections)
            max_scan = min(total_points, 100000)
            
            offset = None
            total_scanned = 0
            
            while total_scanned < max_scan:
                payload = {"limit": 100, "with_payload": True, "with_vector": False}
                if offset is not None:
                    payload["offset"] = offset
                
                response = requests.post(
                    f"{self.base_url}/collections/{self.collection}/points/scroll",
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                points = data.get("result", {}).get("points", [])
                if not points:
                    break
                
                for point in points:
                    if self.doc_id_field == "_point_id":
                        doc_id = point["id"]
                    else:
                        doc_id = point.get("payload", {}).get(self.doc_id_field)
                    
                    if doc_id is not None:
                        normalized_id = self.normalizer_fn(doc_id)
                        qdrant_id_map[normalized_id] = {
                            "original": doc_id,
                            "point_id": point["id"]
                        }
                
                total_scanned += len(points)
                
                # Progress indicator
                if total_scanned % 10000 == 0:
                    self.log(f"  ... scanned {total_scanned}/{max_scan} points", to_console=False)
                
                offset = data.get("result", {}).get("next_page_offset")
                if offset is None:
                    break
            
            self.log(f"  Scanned {total_scanned} Qdrant points, built lookup with {len(qdrant_id_map)} IDs")
            
            # Check alignment
            for eval_id in sample_eval_ids:
                normalized_eval_id = self.normalizer_fn(eval_id)
                
                if normalized_eval_id in qdrant_id_map:
                    found_count += 1
                else:
                    if len(missing_ids) < 20:
                        missing_ids.append(eval_id)
            
            alignment_rate = found_count / len(sample_eval_ids) if sample_eval_ids else 0
            
            self.log(f"  Alignment rate: {found_count}/{len(sample_eval_ids)} = {alignment_rate:.4f}")
            
            result = {
                "status": "pass" if alignment_rate >= 0.99 else "fail",
                "found": found_count,
                "total_sampled": len(sample_eval_ids),
                "alignment_rate": alignment_rate,
                "qdrant_points_scanned": total_scanned,
                "qdrant_unique_ids": len(qdrant_id_map)
            }
            
            if alignment_rate < 0.99:
                self.log(f"❌ FAIL: Alignment rate {alignment_rate:.4f} < 0.99")
                self.log(f"  Missing IDs (first 20):")
                for missing_id in missing_ids[:20]:
                    self.log(f"    {missing_id}")
                result["missing_ids"] = missing_ids[:20]
            else:
                self.log(f"✓ PASS: Alignment rate {alignment_rate:.4f} >= 0.99")
            
            self.results["alignment"] = result
            return result
            
        except Exception as e:
            self.log(f"❌ Error checking alignment rate: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_api_wiring(self) -> Dict[str, Any]:
        """Step 5: Check API wiring in search code"""
        self.log("\n=== STEP 5: API Wiring Check ===")
        
        api_file = "services/fiqa_api/app.py"
        
        try:
            with open(api_file, 'r') as f:
                content = f.read()
            
            # Look for doc_id extraction patterns
            patterns_to_check = [
                "payload.get('doc_id')",
                "payload.doc_id",
                "document.id",
                "result.id",
                "metadata.get('doc_id')",
            ]
            
            found_patterns = []
            for pattern in patterns_to_check:
                if pattern in content:
                    found_patterns.append(pattern)
            
            self.log(f"  Checked {api_file}")
            self.log(f"  Found doc_id extraction patterns: {found_patterns}")
            
            # Check if DOC_ID_FIELD constant exists
            has_constant = "DOC_ID_FIELD" in content
            self.log(f"  Has DOC_ID_FIELD constant: {has_constant}")
            
            result = {
                "status": "info",
                "file_checked": api_file,
                "patterns_found": found_patterns,
                "has_constant": has_constant
            }
            
            self.results["api_wiring"] = result
            return result
            
        except Exception as e:
            self.log(f"⚠️  Could not check API wiring: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_report(self):
        """Generate final health report"""
        self.log("\n=== Generating Health Report ===")
        
        report_lines = []
        report_lines.append("# Doc ID Alignment Health Report")
        report_lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Collection**: `{self.collection}`")
        report_lines.append("")
        
        # Summary
        report_lines.append("## Summary")
        report_lines.append("")
        
        doc_id_field = self.results.get("doc_id_field", "unknown")
        doc_id_source = self.results.get("doc_id_source", "unknown")
        report_lines.append(f"- **Chosen DOC_ID_FIELD**: `{doc_id_field}` (source: {doc_id_source})")
        
        uniqueness = self.results.get("uniqueness", {})
        duplicates = uniqueness.get("duplicates_count", "N/A")
        report_lines.append(f"- **Duplicates Count**: {duplicates}")
        
        alignment = self.results.get("alignment", {})
        alignment_rate = alignment.get("alignment_rate", 0)
        report_lines.append(f"- **Alignment Rate**: {alignment_rate:.4f} ({alignment.get('found', 0)}/{alignment.get('total_sampled', 0)})")
        
        type_consistency = self.results.get("type_consistency", {})
        needs_norm = type_consistency.get("needs_normalization", False)
        normalizer_rule = type_consistency.get("normalizer_rule", "none")
        report_lines.append(f"- **Normalization Applied**: {normalizer_rule if needs_norm else 'none'}")
        
        report_lines.append("")
        
        # Overall status
        all_pass = (
            uniqueness.get("status") == "pass" and
            alignment.get("status") == "pass"
        )
        
        if all_pass:
            report_lines.append("## ✅ Overall Status: PASS")
        else:
            report_lines.append("## ❌ Overall Status: FAIL")
        
        report_lines.append("")
        
        # Detailed results
        report_lines.append("## Detailed Results")
        report_lines.append("")
        
        report_lines.append("### 1. ID Field Discovery")
        report_lines.append(f"- Field: `{doc_id_field}`")
        report_lines.append(f"- Source: {doc_id_source}")
        report_lines.append("")
        
        report_lines.append("### 2. Uniqueness Check")
        if uniqueness:
            report_lines.append(f"- Status: {uniqueness.get('status', 'unknown').upper()}")
            report_lines.append(f"- Total points: {uniqueness.get('total_points', 'N/A')}")
            report_lines.append(f"- Sampled: {uniqueness.get('sampled_points', 'N/A')}")
            report_lines.append(f"- Unique IDs: {uniqueness.get('unique_ids', 'N/A')}")
            report_lines.append(f"- Duplicates: {uniqueness.get('duplicates_count', 'N/A')}")
        report_lines.append("")
        
        report_lines.append("### 3. Type Consistency")
        if type_consistency:
            report_lines.append(f"- Qdrant types: {type_consistency.get('qdrant_types', [])}")
            report_lines.append(f"- Eval types: {type_consistency.get('eval_types', [])}")
            report_lines.append(f"- Needs normalization: {needs_norm}")
            report_lines.append(f"- Normalizer rule: `{normalizer_rule}`")
        report_lines.append("")
        
        report_lines.append("### 4. Alignment Rate")
        if alignment:
            report_lines.append(f"- Status: {alignment.get('status', 'unknown').upper()}")
            report_lines.append(f"- Found: {alignment.get('found', 0)}/{alignment.get('total_sampled', 0)}")
            report_lines.append(f"- Rate: {alignment_rate:.4f}")
            report_lines.append(f"- Threshold: 0.99")
            
            if alignment.get("status") == "fail" and "missing_ids" in alignment:
                report_lines.append(f"- Missing IDs (sample): {', '.join(alignment['missing_ids'][:10])}")
        report_lines.append("")
        
        report_lines.append("### 5. API Wiring")
        api_wiring = self.results.get("api_wiring", {})
        if api_wiring:
            report_lines.append(f"- File checked: `{api_wiring.get('file_checked', 'N/A')}`")
            report_lines.append(f"- Patterns found: {', '.join(f'`{p}`' for p in api_wiring.get('patterns_found', []))}")
            report_lines.append(f"- Has DOC_ID_FIELD constant: {api_wiring.get('has_constant', False)}")
        report_lines.append("")
        
        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")
        
        if not all_pass:
            if alignment.get("status") == "fail":
                report_lines.append("- ❌ **Alignment rate is below threshold**: Review ID mapping between Qdrant and evaluation data")
                report_lines.append("- Suggest: Check if documents were ingested with correct IDs")
                report_lines.append(f"- Check missing IDs in `{self.log_file}`")
            
            if uniqueness.get("status") == "fail":
                report_lines.append("- ❌ **Duplicate IDs found**: Review ingestion process")
                report_lines.append(f"- Check top duplicates in `{self.log_file}`")
        else:
            report_lines.append("- ✅ All checks passed")
            report_lines.append("- System is ready for Recall@10 evaluation")
        
        report_lines.append("")
        report_lines.append(f"See detailed logs in `{self.log_file}`")
        
        # Write report
        report_content = "\n".join(report_lines)
        
        # Check if HEALTH_REPORT.md exists
        try:
            with open(self.report_file, 'r') as f:
                existing_content = f.read()
        except FileNotFoundError:
            existing_content = ""
        
        # Append to existing report
        if existing_content:
            separator = "\n\n---\n\n"
            report_content = existing_content + separator + report_content
        
        with open(self.report_file, 'w') as f:
            f.write(report_content)
        
        self.log(f"\n✓ Report written to {self.report_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check doc_id alignment between Qdrant and evaluation data")
    parser.add_argument("--collection", default="beir_fiqa_full_ta", help="Qdrant collection name")
    parser.add_argument("--qrels", default="data/fiqa/qrels/test.tsv", help="Path to qrels file")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--sample-uniqueness", type=int, default=10000, help="Sample size for uniqueness check")
    parser.add_argument("--sample-alignment", type=int, default=1000, help="Sample size for alignment check")
    
    args = parser.parse_args()
    
    checker = DocIdAlignmentChecker(args.collection, args.host, args.port)
    
    print("="*60)
    print("DOC ID ALIGNMENT HEALTH CHECK")
    print("="*60)
    
    # Run all checks
    checker.discover_id_field()
    checker.check_uniqueness(args.sample_uniqueness)
    checker.check_type_consistency(args.qrels)
    checker.check_alignment_rate(args.qrels, args.sample_alignment)
    checker.check_api_wiring()
    
    # Generate report
    checker.generate_report()
    
    print("\n" + "="*60)
    print("CHECK COMPLETE")
    print("="*60)
    print(f"Log: {checker.log_file}")
    print(f"Report: {checker.report_file}")
    
    # Return exit code based on results
    alignment = checker.results.get("alignment", {})
    uniqueness = checker.results.get("uniqueness", {})
    
    if alignment.get("status") == "pass" and uniqueness.get("status") == "pass":
        print("\n✅ All checks PASSED")
        return 0
    else:
        print("\n❌ Some checks FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

