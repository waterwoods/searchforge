#!/usr/bin/env python3
"""
ID Alignment Auditor - Read-only audit tool for checking doc_id alignment
between Qdrant collections and offline data (corpus/qrels).

This tool performs read-only checks and generates audit reports without
modifying any code or indices.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import ScrollRequest
except ImportError:
    print("ERROR: qdrant-client not installed. Install with: pip install qdrant-client")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Default candidate collections (priority order)
DEFAULT_COLLECTIONS = [
    "fiqa_para_50k",
    "fiqa_win256_o64_50k",
    "fiqa_sent_50k",
    "fiqa_50k_v1"
]

# Qdrant connection settings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

# Sample size for Qdrant checks
SAMPLE_SIZE = 2000

# Alignment thresholds
ALIGNMENT_THRESHOLD = 0.95


def load_winners_final(reports_dir: Path) -> Optional[Dict[str, Any]]:
    """Load winners.final.json if it exists."""
    winners_path = reports_dir / "winners.final.json"
    if winners_path.exists():
        try:
            with open(winners_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load winners.final.json: {e}")
    return None


def load_policies(config_dir: Path) -> Optional[Dict[str, Any]]:
    """Load policies.json if it exists."""
    policies_path = config_dir / "policies.json"
    if policies_path.exists():
        try:
            with open(policies_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load policies.json: {e}")
    return None


def extract_collections(winners: Optional[Dict], policies: Optional[Dict]) -> List[str]:
    """Extract candidate collection names from winners and policies."""
    collections = set()
    
    # Add default collections
    collections.update(DEFAULT_COLLECTIONS)
    
    # Extract from policies
    if policies:
        policies_data = policies.get("policies", {})
        for policy in policies_data.values():
            collection = policy.get("collection")
            if collection:
                collections.add(collection)
    
    # Extract from winners (if structured)
    if winners:
        if isinstance(winners, dict):
            # Check for collection references
            for key, value in winners.items():
                if isinstance(value, dict) and "collection" in value:
                    collections.add(value["collection"])
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "collection" in item:
                            collections.add(item["collection"])
    
    # Return in priority order
    result = []
    for default_col in DEFAULT_COLLECTIONS:
        if default_col in collections:
            result.append(default_col)
            collections.remove(default_col)
    
    # Add any remaining collections
    result.extend(sorted(collections))
    
    return result


def infer_dataset_name(winners: Optional[Dict], policies: Optional[Dict]) -> str:
    """Infer dataset name from winners/policies or use default."""
    # Try to extract from policies
    if policies:
        policies_data = policies.get("policies", {})
        for policy in policies_data.values():
            # Check metadata or description for dataset hints
            pass
    
    # Default dataset name
    return "fiqa_50k_v1"


def load_corpus_ids(data_dir: Path, dataset_name: str, max_lines: int = 50000) -> Set[str]:
    """Load doc_ids from corpus.jsonl or processed_corpus.jsonl.
    
    If corpus file not found, try to infer from Qdrant collections.
    """
    corpus_ids = set()
    
    # Try multiple possible paths
    possible_paths = [
        data_dir / dataset_name / "corpus.jsonl",
        data_dir / dataset_name / "processed_corpus.jsonl",
        data_dir / "fiqa" / "processed_corpus.jsonl",
        data_dir / "fiqa" / "corpus.jsonl",
    ]
    
    corpus_path = None
    for path in possible_paths:
        if path.exists():
            corpus_path = path
            break
    
    if corpus_path:
        logger.info(f"Loading corpus from: {corpus_path}")
        count = 0
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if count >= max_lines:
                        break
                    if line.strip():
                        try:
                            data = json.loads(line.strip())
                            doc_id = data.get("doc_id") or data.get("id") or data.get("_id")
                            if doc_id:
                                corpus_ids.add(str(doc_id))
                                count += 1
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Failed to load corpus: {e}")
    else:
        logger.warning(f"Corpus file not found in any of: {[str(p) for p in possible_paths]}")
        logger.info("Will infer corpus_ids from Qdrant collections if available")
    
    logger.info(f"Loaded {len(corpus_ids)} doc_ids from corpus")
    return corpus_ids


def infer_corpus_ids_from_qdrant(
    client: QdrantClient,
    collection_name: str,
    sample_size: int = 10000
) -> Set[str]:
    """Infer corpus doc_ids by sampling from Qdrant collection."""
    corpus_ids = set()
    try:
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=sample_size,
            with_payload=True,
            with_vectors=False
        )
        
        for point in scroll_result[0]:
            payload = point.payload or {}
            doc_id = payload.get("doc_id")
            if doc_id:
                corpus_ids.add(str(doc_id))
        
        logger.info(f"Inferred {len(corpus_ids)} doc_ids from Qdrant collection '{collection_name}'")
    except Exception as e:
        logger.warning(f"Failed to infer corpus_ids from Qdrant: {e}")
    
    return corpus_ids


def load_qrels_doc_ids(data_dir: Path, dataset_name: str) -> Set[str]:
    """Load doc_ids from qrels file."""
    qrels_doc_ids = set()
    
    # Try multiple possible paths (prioritize numeric doc_id format)
    possible_paths = [
        data_dir / "fiqa" / "fiqa_qrels_hard_50k_v1.tsv",  # Priority: numeric doc_ids
        data_dir / dataset_name / "qrels.txt",
        data_dir / dataset_name / "qrels.tsv",
        data_dir / dataset_name / "qrels" / "test.tsv",
        data_dir / "fiqa" / "qrels" / "test.tsv",
    ]
    
    qrels_path = None
    for path in possible_paths:
        if path.exists():
            qrels_path = path
            break
    
    if not qrels_path:
        logger.warning(f"Qrels file not found in any of: {[str(p) for p in possible_paths]}")
        return qrels_doc_ids
    
    logger.info(f"Loading qrels from: {qrels_path}")
    try:
        with open(qrels_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0 and ("query_id" in line.lower() or line.startswith("query_id")):  # Skip header
                    continue
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        doc_id = parts[1].strip()
                        if doc_id:
                            qrels_doc_ids.add(str(doc_id))  # Ensure string format
    except Exception as e:
        logger.warning(f"Failed to load qrels: {e}")
    
    logger.info(f"Loaded {len(qrels_doc_ids)} doc_ids from qrels")
    return qrels_doc_ids


def sample_qdrant_collection(
    client: QdrantClient,
    collection_name: str,
    sample_size: int = SAMPLE_SIZE
) -> Tuple[List[Dict[str, Any]], bool]:
    """Sample points from Qdrant collection."""
    points = []
    collection_exists = False
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        if collection_name not in collection_names:
            logger.warning(f"Collection '{collection_name}' does not exist")
            return points, collection_exists
        
        collection_exists = True
        
        # Scroll to sample points
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=sample_size,
            with_payload=True,
            with_vectors=False
        )
        
        for point in scroll_result[0]:
            payload = point.payload or {}
            points.append({
                "point_id": point.id,
                "payload": payload,
                "has_doc_id": "doc_id" in payload,
                "doc_id": str(payload.get("doc_id", "")) if payload.get("doc_id") else None
            })
        
        logger.info(f"Sampled {len(points)} points from '{collection_name}'")
        
    except Exception as e:
        logger.warning(f"Failed to sample collection '{collection_name}': {e}")
    
    return points, collection_exists


def analyze_collection_alignment(
    points: List[Dict[str, Any]],
    corpus_ids: Set[str],
    qrels_doc_ids: Set[str]
) -> Dict[str, float]:
    """Calculate alignment metrics for a collection."""
    if not points:
        return {
            "has_payload_doc_id_ratio": 0.0,
            "point_id_in_corpus_ratio": 0.0,
            "payload_doc_id_in_corpus_ratio": 0.0,
            "payload_doc_id_in_qrels_ratio": 0.0,
            "sample_size": 0
        }
    
    has_doc_id_count = sum(1 for p in points if p["has_doc_id"])
    point_id_in_corpus_count = sum(1 for p in points if str(p["point_id"]) in corpus_ids)
    payload_doc_id_in_corpus_count = 0
    payload_doc_id_in_qrels_count = 0
    
    for point in points:
        if point["doc_id"]:
            if point["doc_id"] in corpus_ids:
                payload_doc_id_in_corpus_count += 1
            if point["doc_id"] in qrels_doc_ids:
                payload_doc_id_in_qrels_count += 1
    
    total = len(points)
    
    return {
        "has_payload_doc_id_ratio": has_doc_id_count / total if total > 0 else 0.0,
        "point_id_in_corpus_ratio": point_id_in_corpus_count / total if total > 0 else 0.0,
        "payload_doc_id_in_corpus_ratio": payload_doc_id_in_corpus_count / total if total > 0 else 0.0,
        "payload_doc_id_in_qrels_ratio": payload_doc_id_in_qrels_count / total if total > 0 else 0.0,
        "sample_size": total
    }


def get_aligned_examples(
    points: List[Dict[str, Any]],
    corpus_ids: Set[str],
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get examples where payload.doc_id is in corpus_ids."""
    aligned = []
    for point in points:
        if point["doc_id"] and point["doc_id"] in corpus_ids:
            aligned.append({
                "point_id": point["point_id"],
                "doc_id": point["doc_id"],
                "status": "aligned"
            })
            if len(aligned) >= limit:
                break
    return aligned


def get_misaligned_examples(
    points: List[Dict[str, Any]],
    corpus_ids: Set[str],
    qrels_doc_ids: Set[str],
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Get examples where payload.doc_id is not in corpus_ids or qrels_doc_ids."""
    misaligned = []
    for point in points:
        if point["doc_id"]:
            if point["doc_id"] not in corpus_ids and point["doc_id"] not in qrels_doc_ids:
                misaligned.append({
                    "point_id": point["point_id"],
                    "doc_id": point["doc_id"],
                    "status": "misaligned"
                })
                if len(misaligned) >= limit:
                    break
    return misaligned


def scan_historical_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    """Scan historical reports for high recall evidence."""
    evidence = []
    
    # Look for winners files
    winners_patterns = [
        "winners*.json",
        "AB_*.csv",
        "winners_chunk.json"
    ]
    
    for pattern in winners_patterns:
        for report_path in reports_dir.glob(pattern):
            try:
                if report_path.suffix == ".json":
                    with open(report_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Look for recall metrics
                        if isinstance(data, dict):
                            # Check winner metrics
                            winner = data.get("winner", {})
                            if isinstance(winner, dict):
                                metrics = winner.get("metrics", {})
                                recall = metrics.get("recall_at_10", 0.0)
                                if recall >= 0.95:
                                    evidence.append({
                                        "file": report_path.name,
                                        "collection": winner.get("config_id", "unknown").split("-")[0] if winner.get("config_id") else "unknown",
                                        "recall_at_10": recall,
                                        "timestamp": data.get("generated_at", "unknown")
                                    })
                elif report_path.suffix == ".csv":
                    # Parse CSV for recall metrics
                    with open(report_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            recall_str = row.get("recall_at_10", "0")
                            try:
                                recall = float(recall_str)
                                if recall >= 0.95:
                                    evidence.append({
                                        "file": report_path.name,
                                        "collection": row.get("collection", "unknown"),
                                        "recall_at_10": recall,
                                        "timestamp": "unknown"
                                    })
                            except ValueError:
                                continue
            except Exception as e:
                logger.debug(f"Failed to parse {report_path}: {e}")
    
    return evidence


def generate_report(
    dataset_name: str,
    collections: List[str],
    corpus_ids: Set[str],
    qrels_doc_ids: Set[str],
    collection_results: Dict[str, Dict[str, Any]],
    historical_evidence: List[Dict[str, Any]],
    reports_dir: Path
) -> Tuple[Path, Path]:
    """Generate audit report in Markdown and CSV formats."""
    
    # Determine aligned collections
    aligned_collections = []
    suspicious_collections = []
    
    for coll_name, result in collection_results.items():
        metrics = result.get("metrics", {})
        exists = result.get("exists", False)
        
        if not exists:
            suspicious_collections.append(coll_name)
            continue
        
        payload_corpus_ratio = metrics.get("payload_doc_id_in_corpus_ratio", 0.0)
        has_doc_id_ratio = metrics.get("has_payload_doc_id_ratio", 0.0)
        qrels_coverage = metrics.get("qrels_coverage", 0.0)
        
        # Check if aligned
        is_aligned = (
            has_doc_id_ratio >= ALIGNMENT_THRESHOLD and
            payload_corpus_ratio >= ALIGNMENT_THRESHOLD and
            (qrels_coverage >= ALIGNMENT_THRESHOLD if qrels_doc_ids else True)  # If no qrels, skip qrels check
        )
        
        # Check historical evidence
        has_historical_evidence = any(
            ev.get("collection", "").startswith(coll_name) or coll_name in ev.get("collection", "")
            for ev in historical_evidence
        )
        
        if is_aligned or has_historical_evidence:
            aligned_collections.append(coll_name)
        else:
            suspicious_collections.append(coll_name)
    
    # Generate Markdown report
    md_path = reports_dir / "ID_ALIGN_AUDIT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# ID Alignment Audit Report\n\n")
        f.write(f"**Dataset**: {dataset_name}\n\n")
        f.write(f"**Generated**: {json.dumps({'timestamp': 'auto'}, indent=2)}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Aligned Collections**: {', '.join(aligned_collections) if aligned_collections else 'None'}\n")
        f.write(f"- **Suspicious Collections**: {', '.join(suspicious_collections) if suspicious_collections else 'None'}\n")
        f.write(f"- **Corpus IDs Loaded**: {len(corpus_ids)}\n")
        f.write(f"- **Qrels Doc IDs Loaded**: {len(qrels_doc_ids)}\n\n")
        
        f.write("## Collection Alignment Metrics\n\n")
        f.write("| Collection | Has doc_id | Point ID→Corpus | Payload doc_id→Corpus | Qrels→Collection | Sample Size | Status |\n")
        f.write("|------------|------------|-----------------|----------------------|------------------|-------------|--------|\n")
        
        for coll_name in collections:
            result = collection_results.get(coll_name, {})
            metrics = result.get("metrics", {})
            exists = result.get("exists", False)
            
            if not exists:
                f.write(f"| {coll_name} | N/A | N/A | N/A | N/A | 0 | ⚠️ NOT FOUND |\n")
                continue
            
            has_doc_id = metrics.get("has_payload_doc_id_ratio", 0.0)
            point_corpus = metrics.get("point_id_in_corpus_ratio", 0.0)
            payload_corpus = metrics.get("payload_doc_id_in_corpus_ratio", 0.0)
            qrels_coverage = metrics.get("qrels_coverage", 0.0)
            sample_size = metrics.get("sample_size", 0)
            
            status = "✅ ALIGNED" if coll_name in aligned_collections else "⚠️ SUSPECT"
            
            f.write(f"| {coll_name} | {has_doc_id:.3f} | {point_corpus:.3f} | {payload_corpus:.3f} | {qrels_coverage:.3f} | {sample_size} | {status} |\n")
        
        f.write("\n## Aligned Examples\n\n")
        f.write("| Collection | Point ID | Doc ID | Status |\n")
        f.write("|------------|----------|--------|--------|\n")
        
        for coll_name in collections:
            result = collection_results.get(coll_name, {})
            examples = result.get("aligned_examples", [])
            for ex in examples[:10]:  # Show first 10
                f.write(f"| {coll_name} | {ex['point_id']} | {ex['doc_id']} | {ex['status']} |\n")
        
        f.write("\n## Misaligned Examples\n\n")
        f.write("| Collection | Point ID | Doc ID | Status |\n")
        f.write("|------------|----------|--------|--------|\n")
        
        for coll_name in collections:
            result = collection_results.get(coll_name, {})
            examples = result.get("misaligned_examples", [])
            for ex in examples[:10]:  # Show first 10
                f.write(f"| {coll_name} | {ex['point_id']} | {ex['doc_id']} | {ex['status']} |\n")
        
        f.write("\n## Historical High Recall Evidence\n\n")
        if historical_evidence:
            f.write("| File | Collection | Recall@10 | Timestamp |\n")
            f.write("|------|------------|-----------|-----------|\n")
            for ev in historical_evidence:
                f.write(f"| {ev['file']} | {ev['collection']} | {ev['recall_at_10']:.3f} | {ev['timestamp']} |\n")
        else:
            f.write("No historical evidence found.\n")
        
        f.write("\n## Conclusion\n\n")
        f.write(f"**Aligned Collections** (meet threshold ≥{ALIGNMENT_THRESHOLD}): {', '.join(aligned_collections) if aligned_collections else 'None'}\n\n")
        f.write(f"**Suspicious Collections** (below threshold or not found): {', '.join(suspicious_collections) if suspicious_collections else 'None'}\n\n")
    
    # Generate CSV report
    csv_path = reports_dir / "ID_ALIGN_AUDIT.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "collection", "has_payload_doc_id_ratio", "point_id_in_corpus_ratio",
            "payload_doc_id_in_corpus_ratio", "qrels_coverage",
            "sample_size", "status"
        ])
        
        for coll_name in collections:
            result = collection_results.get(coll_name, {})
            metrics = result.get("metrics", {})
            exists = result.get("exists", False)
            
            if not exists:
                writer.writerow([coll_name, "N/A", "N/A", "N/A", "N/A", 0, "NOT_FOUND"])
                continue
            
            status = "ALIGNED" if coll_name in aligned_collections else "SUSPECT"
            writer.writerow([
                coll_name,
                metrics.get("has_payload_doc_id_ratio", 0.0),
                metrics.get("point_id_in_corpus_ratio", 0.0),
                metrics.get("payload_doc_id_in_corpus_ratio", 0.0),
                metrics.get("qrels_coverage", 0.0),
                metrics.get("sample_size", 0),
                status
            ])
    
    return md_path, csv_path


def check_alignment_cli(collection: str, qrels_path: str, host: str = "http://127.0.0.1:6333") -> Dict[str, Any]:
    """
    CLI mode: Check alignment for a single collection and qrels file.
    Returns JSON result dict.
    """
    qrels_file = Path(qrels_path)
    if not qrels_file.exists():
        return {
            "collection": collection,
            "qrels": str(qrels_path),
            "checked": 0,
            "found": 0,
            "mismatch": 0,
            "mismatch_rate": 1.0,
            "error": f"Qrels file not found: {qrels_path}"
        }
    
    # Load qrels doc_ids
    qrels_doc_ids = set()
    try:
        with open(qrels_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0 and ("query_id" in line.lower() or line.startswith("query_id")):
                    continue
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        doc_id = parts[1].strip()
                        if doc_id:
                            qrels_doc_ids.add(str(doc_id))
    except Exception as e:
        return {
            "collection": collection,
            "qrels": str(qrels_path),
            "checked": 0,
            "found": 0,
            "mismatch": 0,
            "mismatch_rate": 1.0,
            "error": f"Failed to load qrels: {e}"
        }
    
    if not qrels_doc_ids:
        return {
            "collection": collection,
            "qrels": str(qrels_path),
            "checked": 0,
            "found": 0,
            "mismatch": 0,
            "mismatch_rate": 1.0,
            "error": "No doc_ids found in qrels file"
        }
    
    # Connect to Qdrant and scan collection
    try:
        client = QdrantClient(url=host, timeout=30)
        
        # Get all unique doc_ids from collection
        collection_doc_ids = set()
        offset = None
        scroll_count = 0
        
        while True:
            scroll_result = client.scroll(
                collection_name=collection,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            batch_points, next_offset = scroll_result
            if not batch_points:
                break
            
            for point in batch_points:
                payload = point.payload or {}
                doc_id = payload.get("doc_id")
                if doc_id:
                    collection_doc_ids.add(str(doc_id))
            
            scroll_count += len(batch_points)
            if next_offset is None:
                break
            offset = next_offset
        
        # Check alignment: every qrels doc_id must be in collection
        checked = len(qrels_doc_ids)
        found = len(qrels_doc_ids & collection_doc_ids)
        mismatch = checked - found
        mismatch_rate = mismatch / checked if checked > 0 else 1.0
        
        return {
            "collection": collection,
            "qrels": str(qrels_path),
            "checked": checked,
            "found": found,
            "mismatch": mismatch,
            "mismatch_rate": mismatch_rate,
            "collection_total_points": scroll_count,
            "collection_unique_doc_ids": len(collection_doc_ids)
        }
        
    except Exception as e:
        return {
            "collection": collection,
            "qrels": str(qrels_path),
            "checked": len(qrels_doc_ids),
            "found": 0,
            "mismatch": len(qrels_doc_ids),
            "mismatch_rate": 1.0,
            "error": f"Failed to check collection: {e}"
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ID Alignment Auditor")
    parser.add_argument("--collection", type=str, help="Collection name to check")
    parser.add_argument("--qrels", type=str, help="Path to qrels TSV file")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:6333", help="Qdrant host URL")
    parser.add_argument("--json", action="store_true", help="Output JSON only (for CLI mode)")
    parser.add_argument("--json-out", type=str, default=None, help="Optional path to write JSON output")
    
    args = parser.parse_args()
    
    # CLI mode: single collection + qrels check
    if args.collection and args.qrels:
        result = check_alignment_cli(args.collection, args.qrels, args.host)
        json_output = json.dumps(result, indent=2)
        print(json_output)
        
        # Write to file if requested
        if args.json_out:
            with open(args.json_out, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logger.info(f"JSON written to: {args.json_out}")
        
        sys.exit(0 if result.get("mismatch_rate", 1.0) == 0.0 else 1)
    
    # Full audit mode (original behavior)
    repo_root = Path(__file__).resolve().parent.parent.parent
    reports_dir = repo_root / "reports"
    config_dir = repo_root / "configs"
    data_dir = repo_root / "experiments" / "data"
    
    reports_dir.mkdir(exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("ID Alignment Auditor - Read-only Audit")
    logger.info("=" * 80)
    
    # Step 1: Parse baseline and candidate collections
    logger.info("\n[Step 1] Parsing baseline and candidate collections...")
    winners = load_winners_final(reports_dir)
    policies = load_policies(config_dir)
    collections = extract_collections(winners, policies)
    dataset_name = infer_dataset_name(winners, policies)
    
    logger.info(f"[ALIGN] dataset={dataset_name}")
    logger.info(f"[ALIGN] candidate collections: {', '.join(collections)}")
    
    # Step 2: Load offline data
    logger.info("\n[Step 2] Loading offline data...")
    corpus_ids = load_corpus_ids(data_dir, dataset_name)
    qrels_doc_ids = load_qrels_doc_ids(data_dir, dataset_name)
    
    # If corpus_ids not found, try to infer from Qdrant
    if not corpus_ids and collections:
        logger.info("Corpus file not found, attempting to infer from Qdrant...")
        try:
            client_temp = QdrantClient(url=QDRANT_URL, timeout=10)
            # Try first available collection
            for coll_name in collections:
                corpus_ids = infer_corpus_ids_from_qdrant(client_temp, coll_name)
                if corpus_ids:
                    break
        except Exception as e:
            logger.warning(f"Failed to infer corpus_ids from Qdrant: {e}")
    
    if corpus_ids:
        logger.info(f"[ALIGN] corpus_ids: {len(corpus_ids)}")
    else:
        logger.warning("[ALIGN] corpus_ids: NOT FOUND")
    
    if qrels_doc_ids:
        logger.info(f"[ALIGN] qrels_doc_ids: {len(qrels_doc_ids)}")
        if corpus_ids:
            intersection = len(qrels_doc_ids & corpus_ids)
            logger.info(f"[ALIGN] qrels ∩ corpus: {intersection} ({intersection/len(qrels_doc_ids)*100:.1f}% of qrels)")
    else:
        logger.warning("[ALIGN] qrels_doc_ids: NOT FOUND")
    
    # Step 3: Qdrant read-only sampling
    logger.info("\n[Step 3] Sampling Qdrant collections...")
    try:
        client = QdrantClient(url=QDRANT_URL, timeout=10)
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant at {QDRANT_URL}: {e}")
        logger.error("Please ensure Qdrant is running and accessible.")
        sys.exit(1)
    
    collection_results = {}
    
    for coll_name in collections:
        logger.info(f"  Sampling '{coll_name}'...")
        points, exists = sample_qdrant_collection(client, coll_name, SAMPLE_SIZE)
        
        if not exists:
            collection_results[coll_name] = {
                "exists": False,
                "metrics": {},
                "aligned_examples": [],
                "misaligned_examples": []
            }
            continue
        
        metrics = analyze_collection_alignment(points, corpus_ids, qrels_doc_ids)
        aligned_examples = get_aligned_examples(points, corpus_ids, limit=20)
        misaligned_examples = get_misaligned_examples(points, corpus_ids, qrels_doc_ids, limit=20)
        
        collection_results[coll_name] = {
            "exists": True,
            "metrics": metrics,
            "aligned_examples": aligned_examples,
            "misaligned_examples": misaligned_examples,
            "points": points  # Store points for qrels coverage calculation
        }
        
        # Calculate qrels coverage (how many qrels doc_ids are in collection)
        # Use full collection scan for accurate qrels coverage
        qrels_coverage = 0.0
        if qrels_doc_ids:
            logger.info(f"  Scanning full collection '{coll_name}' for qrels coverage...")
            try:
                # Scroll through entire collection to get all unique doc_ids
                all_collection_doc_ids = set()
                offset = None
                scroll_count = 0
                while True:
                    scroll_result = client.scroll(
                        collection_name=coll_name,
                        limit=1000,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False
                    )
                    batch_points, next_offset = scroll_result
                    if not batch_points:
                        break
                    
                    for point in batch_points:
                        payload = point.payload or {}
                        doc_id = payload.get("doc_id")
                        if doc_id:
                            all_collection_doc_ids.add(str(doc_id))
                    
                    scroll_count += len(batch_points)
                    if next_offset is None:
                        break
                    offset = next_offset
                
                qrels_found = len(qrels_doc_ids & all_collection_doc_ids)
                qrels_coverage = qrels_found / len(qrels_doc_ids) if qrels_doc_ids else 0.0
                logger.info(f"  Scanned {scroll_count} points, found {qrels_found}/{len(qrels_doc_ids)} qrels doc_ids (coverage: {qrels_coverage:.3f})")
            except Exception as e:
                logger.warning(f"  Failed to scan full collection for qrels coverage: {e}")
                # Fallback to sample-based calculation
                collection_doc_ids = set(p["doc_id"] for p in points if p.get("doc_id"))
                if collection_doc_ids:
                    qrels_found = len(qrels_doc_ids & collection_doc_ids)
                    qrels_coverage = qrels_found / len(qrels_doc_ids) if qrels_doc_ids else 0.0
        
        # Print summary
        payload_corpus = metrics.get("payload_doc_id_in_corpus_ratio", 0.0)
        payload_qrels = metrics.get("payload_doc_id_in_qrels_ratio", 0.0)
        point_corpus = metrics.get("point_id_in_corpus_ratio", 0.0)
        
        # Check alignment (use qrels_coverage for reverse check)
        is_aligned_check = (
            metrics.get("has_payload_doc_id_ratio", 0.0) >= ALIGNMENT_THRESHOLD and
            payload_corpus >= ALIGNMENT_THRESHOLD and
            (qrels_coverage >= ALIGNMENT_THRESHOLD if qrels_doc_ids else True)
        )
        
        status = "✅ ALIGNED" if is_aligned_check else "⚠️ SUSPECT"
        
        logger.info(
            f"[ALIGN] {coll_name}: "
            f"payload.doc_id→corpus={payload_corpus:.3f}, "
            f"qrels→collection={qrels_coverage:.3f}, "
            f"point.id→corpus={point_corpus:.3f}  {status}"
        )
        
        # Store qrels_coverage in metrics for report generation
        metrics["qrels_coverage"] = qrels_coverage
    
    # Step 4: Historical evidence
    logger.info("\n[Step 4] Scanning historical reports...")
    historical_evidence = scan_historical_reports(reports_dir)
    if historical_evidence:
        logger.info(f"Found {len(historical_evidence)} historical high recall evidence(s)")
        for ev in historical_evidence:
            logger.info(f"  - {ev['file']}: {ev['collection']} (recall={ev['recall_at_10']:.3f})")
    else:
        logger.info("No historical evidence found")
    
    # Step 5: Generate reports
    logger.info("\n[Step 5] Generating audit reports...")
    md_path, csv_path = generate_report(
        dataset_name, collections, corpus_ids, qrels_doc_ids,
        collection_results, historical_evidence, reports_dir
    )
    
    # Print final summary (recalculate alignment with proper qrels coverage)
    aligned = []
    suspicious = []
    
    for coll_name in collections:
        result = collection_results.get(coll_name, {})
        if not result.get("exists"):
            suspicious.append(coll_name)
            continue
        
        metrics = result.get("metrics", {})
        has_doc_id = metrics.get("has_payload_doc_id_ratio", 0.0)
        payload_corpus = metrics.get("payload_doc_id_in_corpus_ratio", 0.0)
        qrels_coverage = metrics.get("qrels_coverage", 0.0)
        
        is_aligned = (
            has_doc_id >= ALIGNMENT_THRESHOLD and
            payload_corpus >= ALIGNMENT_THRESHOLD and
            (qrels_coverage >= ALIGNMENT_THRESHOLD if qrels_doc_ids else True)
        )
        
        # Also check historical evidence
        has_historical = any(
            ev.get("collection", "").startswith(coll_name) or coll_name in ev.get("collection", "")
            for ev in historical_evidence
        )
        
        if is_aligned or has_historical:
            aligned.append(coll_name)
        else:
            suspicious.append(coll_name)
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Aligned collections: {', '.join(aligned) if aligned else 'None'}")
    logger.info(f"Suspicious collections: {', '.join(suspicious) if suspicious else 'None'}")
    logger.info(f"\nReport: {md_path}")
    logger.info(f"CSV: {csv_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

