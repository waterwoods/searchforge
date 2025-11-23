#!/usr/bin/env python3
"""
应用 doc_id 映射到当前 Qdrant collection

Usage:
    python3 scripts/docid_apply_map.py --base http://localhost:6333 --collection fiqa_para_50k --map .runs/docid_map/fiqa_para_50k.sha1_to_docid.json
"""

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, Optional

from qdrant_client import QdrantClient
from tqdm import tqdm


def normalize_text(text: str) -> str:
    """Normalize text: remove CRLF, strip whitespace, preserve case."""
    if not text:
        return ""
    # Replace CRLF and LF with single space
    normalized = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    # Strip leading/trailing whitespace
    normalized = normalized.strip()
    return normalized


def compute_sha1(text: str) -> str:
    """Compute SHA1 hash of normalized text."""
    normalized = normalize_text(text)
    return hashlib.sha1(normalized.encode('utf-8')).hexdigest()


def iter_points(client: QdrantClient, collection: str, limit: int = 512):
    """Iterate over all points in collection using scroll."""
    offset = None
    while True:
        points, offset = client.scroll(
            collection,
            with_payload=True,
            with_vectors=False,
            limit=limit,
            offset=offset,
        )
        if not points:
            break
        yield points
        if offset is None:
            break


def load_mapping(map_path: Path) -> Dict[str, str]:
    """Load SHA1 to doc_id mapping from JSON file."""
    if not map_path.exists():
        print(f"[ERROR] Mapping file not found: {map_path}")
        sys.exit(1)
    
    with open(map_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    print(f"[INFO] Loaded {len(mapping)} mappings from {map_path}")
    return mapping


def apply_mapping(
    client: QdrantClient,
    collection: str,
    mapping: Dict[str, str],
    verify_only: bool = False,
    sample_size: Optional[int] = None
) -> Dict[str, int]:
    """Apply doc_id mapping to collection."""
    stats = {
        "total": 0,
        "matched": 0,
        "updated": 0,
        "missing_text": 0,
        "missing_doc_id_in_map": 0,
        "mismatches": 0,
    }
    
    all_points = []
    
    # First pass: collect all points
    print(f"[INFO] Collecting points from {collection}...")
    for chunk in iter_points(client, collection, limit=512):
        all_points.extend(chunk)
    
    stats["total"] = len(all_points)
    
    # Sample if verify-only mode
    if verify_only and sample_size:
        if len(all_points) > sample_size:
            all_points = random.sample(all_points, sample_size)
            print(f"[INFO] Sampling {sample_size} points for verification")
    
    # Second pass: apply mapping
    if verify_only:
        print(f"[INFO] Verifying doc_id mapping ({'sampled' if sample_size else 'all'} points)...")
    else:
        print(f"[INFO] Applying doc_id mapping to {len(all_points)} points...")
    
    batch_payloads = []
    batch_ids = []
    
    for point in tqdm(all_points, desc="Processing"):
        payload = point.payload or {}
        
        # Get text
        text = payload.get('text', '') or payload.get('abstract', '') or ''
        if not text:
            stats["missing_text"] += 1
            continue
        
        # Compute SHA1 and lookup old doc_id
        sha1_hash = compute_sha1(text)
        old_doc_id = mapping.get(sha1_hash)
        
        if old_doc_id is None:
            stats["missing_doc_id_in_map"] += 1
            continue
        
        stats["matched"] += 1
        
        current_doc_id = payload.get('doc_id')
        
        if verify_only:
            # Only verify, don't update
            if str(current_doc_id) != str(old_doc_id):
                stats["mismatches"] += 1
        else:
            # Check if update needed
            if str(current_doc_id) != str(old_doc_id):
                batch_payloads.append({"doc_id": old_doc_id})
                batch_ids.append(point.id)
                stats["updated"] += 1
                
                # Batch update every 1000 points
                if len(batch_ids) >= 1000:
                    for i, pid in enumerate(batch_ids):
                        client.set_payload(collection, payload=batch_payloads[i], points=[pid])
                    batch_payloads = []
                    batch_ids = []
    
    # Final batch update
    if not verify_only and batch_ids:
        for i, pid in enumerate(batch_ids):
            client.set_payload(collection, payload=batch_payloads[i], points=[pid])
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Apply doc_id mapping to Qdrant collection"
    )
    parser.add_argument(
        "--base",
        type=str,
        default=os.getenv("QDRANT_URL", os.getenv("RAG_API_BASE", "http://localhost:6333")),
        help="Qdrant base URL (default: from env or http://localhost:6333)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        required=True,
        help="Collection name (e.g., fiqa_para_50k)"
    )
    parser.add_argument(
        "--map",
        type=str,
        required=True,
        help="Mapping JSON file path"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify mapping without applying"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Sample size for verification (default: all)"
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=50000,
        help="Expected number of documents (default: 50000)"
    )
    
    args = parser.parse_args()
    
    # Normalize base URL (remove /api if present)
    base_url = args.base.replace('/api', '').rstrip('/')
    
    # Initialize client
    client = QdrantClient(url=base_url, prefer_grpc=False)
    
    # Check collection exists
    try:
        collection_info = client.get_collection(args.collection)
        print(f"[INFO] Collection {args.collection} found: {collection_info.points_count} points")
    except Exception as e:
        print(f"[ERROR] Collection {args.collection} not found: {e}")
        sys.exit(1)
    
    # Load mapping
    map_path = Path(args.map)
    mapping = load_mapping(map_path)
    
    # Apply mapping
    stats = apply_mapping(
        client=client,
        collection=args.collection,
        mapping=mapping,
        verify_only=args.verify_only,
        sample_size=args.sample
    )
    
    # Print summary
    print(f"\n[INFO] {'Verification' if args.verify_only else 'Update'} summary:")
    print(f"  Total points: {stats['total']}")
    print(f"  Matched in mapping: {stats['matched']}")
    if not args.verify_only:
        print(f"  Updated: {stats['updated']}")
    print(f"  Missing text: {stats['missing_text']}")
    print(f"  Missing in mapping: {stats['missing_doc_id_in_map']}")
    print(f"  Mismatches: {stats['mismatches']}")
    
    # Verify expected count
    if args.verify_only:
        if stats['mismatches'] > 0:
            print(f"\n[ERROR] Found {stats['mismatches']} mismatches")
            sys.exit(1)
        else:
            print(f"\n[SUCCESS] All sampled points match mapping (mismatches: 0)")
    else:
        expected_updated = args.expected_count - stats['matched']
        if stats['matched'] < args.expected_count:
            print(f"\n[ERROR] Expected {args.expected_count} matches, got {stats['matched']}")
            sys.exit(1)
        
        if stats['mismatches'] > 0:
            print(f"\n[WARN] Found {stats['mismatches']} mismatches after update")
        else:
            print(f"\n[SUCCESS] Updated {stats['updated']}/{stats['matched']} points (mismatches: 0)")
    
    # Output JSON summary
    output = {
        "collection": args.collection,
        "verify_only": args.verify_only,
        **stats,
        "ok": stats['mismatches'] == 0 and stats['matched'] >= args.expected_count
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

