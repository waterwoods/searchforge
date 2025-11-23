#!/usr/bin/env python3
"""
从旧 Qdrant 卷导出 doc_id 映射（基于文本的 SHA1）

Usage:
    python3 scripts/docid_export_from_qdrant.py --base http://localhost:6335 --collection fiqa_para_50k --out .runs/docid_map/fiqa_para_50k.sha1_to_docid.json
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict

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


def main():
    parser = argparse.ArgumentParser(
        description="Export doc_id mapping from old Qdrant collection"
    )
    parser.add_argument(
        "--base",
        type=str,
        required=True,
        help="Qdrant base URL (e.g., http://localhost:6335)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        required=True,
        help="Collection name (e.g., fiqa_para_50k)"
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=50000,
        help="Expected number of documents (default: 50000)"
    )
    
    args = parser.parse_args()
    
    # Initialize client
    client = QdrantClient(url=args.base, prefer_grpc=False)
    
    # Check collection exists
    try:
        collection_info = client.get_collection(args.collection)
        print(f"[INFO] Collection {args.collection} found: {collection_info.points_count} points")
    except Exception as e:
        print(f"[ERROR] Collection {args.collection} not found: {e}")
        sys.exit(1)
    
    # Build mapping: sha1(text) -> doc_id
    mapping: Dict[str, str] = {}
    seen = 0
    missing_text = 0
    missing_doc_id = 0
    
    print(f"[INFO] Exporting doc_id mapping from {args.collection}...")
    
    for chunk in tqdm(iter_points(client, args.collection, limit=512), desc="Exporting"):
        for point in chunk:
            seen += 1
            payload = point.payload or {}
            
            # Get text
            text = payload.get('text', '') or payload.get('abstract', '') or ''
            if not text:
                missing_text += 1
                continue
            
            # Get doc_id
            doc_id = payload.get('doc_id')
            if doc_id is None:
                missing_doc_id += 1
                continue
            
            # Normalize and hash text
            sha1_hash = compute_sha1(text)
            
            # Store mapping
            if sha1_hash in mapping:
                # Warn if duplicate (shouldn't happen)
                print(f"[WARN] Duplicate SHA1 for doc_id {doc_id} (existing: {mapping[sha1_hash]})")
            else:
                mapping[sha1_hash] = str(doc_id)
    
    print(f"\n[INFO] Export summary:")
    print(f"  Total points: {seen}")
    print(f"  Mapped: {len(mapping)}")
    print(f"  Missing text: {missing_text}")
    print(f"  Missing doc_id: {missing_doc_id}")
    
    # Verify expected count
    if seen < args.expected_count:
        print(f"[ERROR] Expected at least {args.expected_count} points, got {seen}")
        sys.exit(1)
    
    if len(mapping) < args.expected_count:
        print(f"[ERROR] Expected at least {args.expected_count} mappings, got {len(mapping)}")
        sys.exit(1)
    
    # Write mapping to file
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] Mapping saved to: {out_path}")
    print(f"  Total mappings: {len(mapping)}")
    
    # Output summary for make target
    print(json.dumps({
        "collection": args.collection,
        "total_points": seen,
        "mappings": len(mapping),
        "missing_text": missing_text,
        "missing_doc_id": missing_doc_id,
        "output_file": str(out_path),
        "ok": len(mapping) >= args.expected_count
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()



