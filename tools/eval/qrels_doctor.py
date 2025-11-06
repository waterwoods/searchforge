#!/usr/bin/env python3
"""
qrels_doctor.py - Qrels Coverage and Type Checker
=================================================
Validates qrels against Qdrant collection to check coverage and type consistency.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


def load_qrels(qrels_path: str) -> Dict[str, List[str]]:
    """Load qrels from TSV file (qid, 0, doc_id, relevance)."""
    qrels = defaultdict(list)
    with open(qrels_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                qid = parts[0].strip()
                doc_id = parts[2].strip()
                qrels[qid].append(doc_id)
    return dict(qrels)


def fetch_collection_doc_ids(qdrant_host: str, qdrant_port: int, collection: str, limit: int = None) -> Set[str]:
    """Fetch all doc_id values from Qdrant collection."""
    base_url = f"http://{qdrant_host}:{qdrant_port}"
    
    # Use scroll API to get all points
    all_doc_ids = set()
    scroll_url = f"{base_url}/collections/{collection}/points/scroll"
    
    scroll_request = {
        "limit": 10000,
        "with_payload": False,
        "with_vector": False
    }
    
    offset = None
    count = 0
    
    while True:
        if offset:
            scroll_request["offset"] = offset
        
        try:
            response = requests.post(scroll_url, json=scroll_request, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            points = data.get("result", {}).get("points", [])
            if not points:
                break
            
            # Extract doc_id from each point
            for point in points:
                payload = point.get("payload", {})
                doc_id = payload.get("doc_id") or str(point.get("id", ""))
                if doc_id:
                    all_doc_ids.add(str(doc_id))
                    count += 1
                    if limit and count >= limit:
                        return all_doc_ids
            
            # Check if there's more
            next_offset = data.get("result", {}).get("next_page_offset")
            if not next_offset:
                break
            offset = next_offset
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch collection: {e}", file=sys.stderr)
            break
    
    return all_doc_ids


def check_type_consistency(qrels: Dict[str, List[str]], collection_doc_ids: Set[str]) -> Dict[str, Any]:
    """Check if doc_id types are consistent between qrels and collection."""
    qrels_ids = set()
    for doc_ids in qrels.values():
        qrels_ids.update(doc_ids)
    
    # Check type patterns
    qrels_int_count = sum(1 for d in qrels_ids if str(d).isdigit())
    qrels_str_count = len(qrels_ids) - qrels_int_count
    
    coll_int_count = sum(1 for d in collection_doc_ids if str(d).isdigit())
    coll_str_count = len(collection_doc_ids) - coll_int_count
    
    # Check overlap
    qrels_str_set = {str(d) for d in qrels_ids}
    coll_str_set = {str(d) for d in collection_doc_ids}
    overlap = qrels_str_set & coll_str_set
    
    return {
        "qrels_total": len(qrels_ids),
        "qrels_int_like": qrels_int_count,
        "qrels_str_like": qrels_str_count,
        "collection_total": len(collection_doc_ids),
        "collection_int_like": coll_int_count,
        "collection_str_like": coll_str_count,
        "overlap_count": len(overlap),
        "overlap_percent": len(overlap) / len(qrels_ids) * 100 if qrels_ids else 0.0,
        "type_mismatch": qrels_int_count > 0 and coll_int_count == 0 or qrels_int_count == 0 and coll_int_count > 0
    }


def main():
    parser = argparse.ArgumentParser(description="Check qrels coverage against Qdrant collection")
    parser.add_argument("--qrels", help="Path to qrels TSV file")
    parser.add_argument("--dataset", help="Dataset name (e.g., fiqa_50k_v1) - will resolve qrels path")
    parser.add_argument("--collection", help="Collection name (required if --dataset not provided)")
    parser.add_argument("--api", help="API base URL (for resolving collection name from dataset)")
    parser.add_argument("--qdrant-host", default="qdrant", help="Qdrant host (default: qdrant)")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port (default: 6333)")
    parser.add_argument("--id-field", default="doc_id", help="Document ID field name (default: doc_id)")
    parser.add_argument("--limit", type=int, help="Limit number of points to check (for dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--out", default="reports/qrels_coverage.json", help="Output JSON report path")
    
    args = parser.parse_args()
    
    # Resolve qrels path from dataset if provided
    qrels_path = args.qrels
    if args.dataset:
        # First try to resolve from presets
        qrels_name_from_preset = None
        try:
            presets_path = Path("configs/presets_v10.json")
            if presets_path.exists():
                with open(presets_path, 'r') as f:
                    presets = json.load(f)
                    for preset in presets.get("presets", []):
                        if preset.get("dataset_name") == args.dataset:
                            qrels_name_from_preset = preset.get("qrels_name")
                            break
        except Exception:
            pass
        
        # Try common paths
        dataset_short = args.dataset.replace("_v1", "").replace("fiqa_", "")
        tried_paths = []
        
        # If we have qrels_name from preset, try that first
        if qrels_name_from_preset:
            for base_dir in ["experiments/data/fiqa", "data/fiqa"]:
                for subdir in ["", "qrels"]:
                    path = Path(base_dir) / subdir / f"{qrels_name_from_preset}.tsv"
                    tried_paths.append(str(path))
                    if path.exists():
                        qrels_path = str(path)
                        break
                if qrels_path and Path(qrels_path).exists():
                    break
        
        # If still not found, try standard patterns
        if not qrels_path or not Path(qrels_path).exists():
            for path_template in [
                f"experiments/data/fiqa/fiqa_qrels_{dataset_short}_v1.tsv",
                f"experiments/data/fiqa/{args.dataset}_qrels.tsv",
                f"experiments/data/fiqa/qrels/fiqa_qrels_{dataset_short}_v1.tsv",
                f"experiments/data/fiqa/qrels/{args.dataset}_qrels.tsv",
                f"experiments/data/fiqa/qrels/test.tsv",  # BEIR standard
                f"experiments/data/fiqa/qrels/dev.tsv",   # BEIR standard
                f"data/fiqa/fiqa_qrels_{dataset_short}_v1.tsv",
                f"data/fiqa/qrels/fiqa_qrels_{dataset_short}_v1.tsv"
            ]:
                if path_template not in tried_paths:
                    tried_paths.append(path_template)
                if Path(path_template).exists():
                    qrels_path = path_template
                    break
        
        if not qrels_path or not Path(qrels_path).exists():
            print(f"ERROR: Could not resolve qrels path for dataset {args.dataset}", file=sys.stderr)
            if qrels_name_from_preset:
                print(f"  Expected qrels_name from preset: {qrels_name_from_preset}", file=sys.stderr)
            print(f"Tried paths:", file=sys.stderr)
            for p in tried_paths:
                print(f"  - {p}", file=sys.stderr)
            print(f"\nPlease provide --qrels explicitly or ensure qrels file exists", file=sys.stderr)
            sys.exit(1)
    
    # Resolve collection from dataset if provided
    collection = args.collection
    if args.dataset and not collection:
        # Default: dataset name usually matches collection name
        collection = args.dataset
        # Or try to resolve from presets
        try:
            presets_path = Path("configs/presets_v10.json")
            if presets_path.exists():
                with open(presets_path, 'r') as f:
                    presets = json.load(f)
                    for preset in presets.get("presets", []):
                        if preset.get("dataset_name") == args.dataset:
                            collection = preset.get("collection") or args.dataset
                            break
        except Exception:
            pass
    
    if not qrels_path:
        print("ERROR: Must provide --qrels or --dataset", file=sys.stderr)
        print("  Example: --qrels experiments/data/fiqa/fiqa_qrels_50k_v1.tsv", file=sys.stderr)
        print("  Or: --dataset fiqa_50k_v1", file=sys.stderr)
        sys.exit(1)
    
    if not collection:
        print("ERROR: Must provide --collection or --dataset", file=sys.stderr)
        print("  Example: --collection fiqa_50k_v1", file=sys.stderr)
        print("  Or: --dataset fiqa_50k_v1 (will use dataset name as collection)", file=sys.stderr)
        sys.exit(1)
    
    # Load qrels
    if not Path(qrels_path).exists():
        print(f"ERROR: Qrels file not found: {qrels_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading qrels from {qrels_path}...")
    qrels = load_qrels(qrels_path)
    print(f"Loaded {len(qrels)} queries with {sum(len(docs) for docs in qrels.values())} total judgments")
    
    # Fetch collection doc_ids
    if args.dry_run:
        print(f"[DRY-RUN] Would fetch collection {collection} from {args.qdrant_host}:{args.qdrant_port}")
        print(f"[DRY-RUN] Limit: {args.limit or 'none'}")
        sys.exit(0)
    
    print(f"Fetching doc_ids from collection {collection}...")
    collection_doc_ids = fetch_collection_doc_ids(
        args.qdrant_host, args.qdrant_port, collection, limit=args.limit
    )
    print(f"Found {len(collection_doc_ids)} documents in collection")
    
    # Check coverage
    all_qrels_doc_ids = set()
    for doc_ids in qrels.values():
        all_qrels_doc_ids.update(doc_ids)
    
    # Normalize to strings for comparison
    qrels_str_set = {str(d) for d in all_qrels_doc_ids}
    coll_str_set = {str(d) for d in collection_doc_ids}
    
    missing = qrels_str_set - coll_str_set
    extra = coll_str_set - qrels_str_set
    
    coverage = len(qrels_str_set & coll_str_set) / len(qrels_str_set) * 100 if qrels_str_set else 0.0
    
    # Type consistency check
    type_info = check_type_consistency(qrels, collection_doc_ids)
    
    # Build report
    report = {
        "qrels_path": qrels_path,
        "collection": collection,
        "qrels_stats": {
            "num_queries": len(qrels),
            "num_doc_ids": len(all_qrels_doc_ids),
            "total_judgments": sum(len(docs) for docs in qrels.values())
        },
        "collection_stats": {
            "num_doc_ids": len(collection_doc_ids)
        },
        "coverage": {
            "percent": round(coverage, 2),
            "matched": len(qrels_str_set & coll_str_set),
            "missing_count": len(missing),
            "missing_sample": list(sorted(missing))[:20] if missing else [],
            "extra_count": len(extra)
        },
        "type_consistency": type_info,
        "status": "PASS" if coverage >= 99.0 and not type_info.get("type_mismatch") else "FAIL"
    }
    
    # Write report
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Coverage: {coverage:.2f}%")
    print(f"Missing doc_ids: {len(missing)}")
    if missing:
        print(f"Sample missing: {list(missing)[:10]}")
    print(f"Type consistency: {'PASS' if not type_info.get('type_mismatch') else 'FAIL'}")
    print(f"Status: {report['status']}")
    print(f"Report written to: {out_path}")
    print(f"{'='*60}")
    
    # Exit with error if coverage < 99%
    if coverage < 99.0:
        print(f"ERROR: Coverage {coverage:.2f}% below 99% threshold", file=sys.stderr)
        sys.exit(1)
    
    if type_info.get("type_mismatch"):
        print("ERROR: Type mismatch detected between qrels and collection", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

