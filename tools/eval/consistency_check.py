#!/usr/bin/env python3
"""
consistency_check.py - Dataset/Collection/Field Consistency Checker
==================================================================
Validates dataset↔qrels↔collection mapping and field consistency.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


# Dataset mapping (can be overridden by config file)
DEFAULT_DATASET_MAP = {
    "fiqa_10k_v1": {
        "qrels": "fiqa_qrels_10k_v1",
        "collection": "fiqa_10k_v1",
        "queries": "fiqa_queries_10k_v1"
    },
    "fiqa_50k_v1": {
        "qrels": "fiqa_qrels_50k_v1",
        "collection": "fiqa_50k_v1",
        "queries": "fiqa_queries_50k_v1"
    }
}


def load_dataset_map(config_path: Optional[str]) -> Dict:
    """Load dataset mapping from config file."""
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Look for dataset_map or presets
                if "dataset_map" in config:
                    return config["dataset_map"]
                elif "presets" in config:
                    # Extract from presets
                    dataset_map = {}
                    for preset in config.get("presets", []):
                        dataset_name = preset.get("dataset_name")
                        if dataset_name:
                            dataset_map[dataset_name] = {
                                "qrels": preset.get("qrels_name"),
                                "collection": preset.get("collection"),
                                "queries": None  # Not in preset
                            }
                    return dataset_map
        except Exception as e:
            print(f"WARNING: Failed to load config: {e}", file=sys.stderr)
    
    return DEFAULT_DATASET_MAP


def check_collection_fields(
    qdrant_host: str,
    qdrant_port: int,
    collection: str,
    expected_fields: List[str],
    sample_size: int = 10
) -> Dict:
    """Check if collection contains expected fields in payload."""
    base_url = f"http://{qdrant_host}:{qdrant_port}"
    scroll_url = f"{base_url}/collections/{collection}/points/scroll"
    
    scroll_request = {
        "limit": sample_size,
        "with_payload": True,
        "with_vector": False
    }
    
    try:
        response = requests.post(scroll_url, json=scroll_request, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        points = data.get("result", {}).get("points", [])
        if not points:
            return {
                "status": "ERROR",
                "message": "No points found in collection"
            }
        
        field_stats = {field: {"present": 0, "non_empty": 0} for field in expected_fields}
        
        for point in points:
            payload = point.get("payload", {})
            for field in expected_fields:
                if field in payload:
                    field_stats[field]["present"] += 1
                    value = payload[field]
                    if value and (isinstance(value, str) and value.strip() or not isinstance(value, str)):
                        field_stats[field]["non_empty"] += 1
        
        # Check coverage
        total = len(points)
        coverage = {
            field: {
                "present_percent": stats["present"] / total * 100 if total > 0 else 0,
                "non_empty_percent": stats["non_empty"] / total * 100 if total > 0 else 0
            }
            for field, stats in field_stats.items()
        }
        
        all_present = all(cov["present_percent"] == 100.0 for cov in coverage.values())
        all_non_empty = all(cov["non_empty_percent"] == 100.0 for cov in coverage.values())
        
        return {
            "status": "PASS" if (all_present and all_non_empty) else "FAIL",
            "sample_size": total,
            "field_coverage": coverage,
            "all_fields_present": all_present,
            "all_fields_non_empty": all_non_empty
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Check dataset/collection/field consistency")
    parser.add_argument("--dataset-name", required=True, help="Dataset name (e.g., fiqa_50k_v1)")
    parser.add_argument("--qrels-name", help="Qrels name (optional, will use mapping if not provided)")
    parser.add_argument("--collection", help="Collection name (optional, will use mapping if not provided)")
    parser.add_argument("--fields", default="title,text", help="Comma-separated list of expected fields")
    parser.add_argument("--config", default="configs/presets_v10.json", help="Config file path")
    parser.add_argument("--qdrant-host", default="qdrant", help="Qdrant host")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--sample-size", type=int, default=10, help="Sample size for field check")
    parser.add_argument("--out", default="reports/consistency.json", help="Output JSON report path")
    
    args = parser.parse_args()
    
    # Load dataset mapping
    dataset_map = load_dataset_map(args.config)
    
    # Resolve names
    dataset_info = dataset_map.get(args.dataset_name, {})
    qrels_name = args.qrels_name or dataset_info.get("qrels")
    collection = args.collection or dataset_info.get("collection")
    
    if not qrels_name:
        print(f"ERROR: Could not resolve qrels_name for dataset {args.dataset_name}", file=sys.stderr)
        sys.exit(1)
    
    if not collection:
        print(f"ERROR: Could not resolve collection for dataset {args.dataset_name}", file=sys.stderr)
        sys.exit(1)
    
    expected_fields = [f.strip() for f in args.fields.split(',')]
    
    print(f"Checking consistency for:")
    print(f"  Dataset: {args.dataset_name}")
    print(f"  Qrels: {qrels_name}")
    print(f"  Collection: {collection}")
    print(f"  Expected fields: {expected_fields}")
    
    # Check mapping consistency
    mapping_check = {
        "status": "PASS",
        "dataset_name": args.dataset_name,
        "qrels_name": qrels_name,
        "collection": collection,
        "mapping_found": args.dataset_name in dataset_map
    }
    
    # Check field consistency
    field_check = check_collection_fields(
        args.qdrant_host,
        args.qdrant_port,
        collection,
        expected_fields,
        sample_size=args.sample_size
    )
    
    # Build report
    report = {
        "mapping": mapping_check,
        "fields": field_check,
        "overall_status": "PASS" if (
            mapping_check["status"] == "PASS" and field_check.get("status") == "PASS"
        ) else "FAIL"
    }
    
    # Write report
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Mapping check: {mapping_check['status']}")
    print(f"Field check: {field_check.get('status', 'UNKNOWN')}")
    if "field_coverage" in field_check:
        for field, coverage in field_check["field_coverage"].items():
            print(f"  {field}: {coverage['present_percent']:.1f}% present, {coverage['non_empty_percent']:.1f}% non-empty")
    print(f"Overall status: {report['overall_status']}")
    print(f"Report written to: {out_path}")
    print(f"{'='*60}")
    
    if report["overall_status"] != "PASS":
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

