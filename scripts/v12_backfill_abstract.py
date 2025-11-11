#!/usr/bin/env python3
"""
v12_backfill_abstract.py - Backfill abstract field in Qdrant collection

Updates points in a Qdrant collection to add abstract field where missing.
Sets abstract = text for points that don't have abstract in their payload.

Usage:
    docker compose exec rag-api python scripts/v12_backfill_abstract.py --collection fiqa_10k_v1
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from tqdm import tqdm


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_qdrant_client(url: str) -> QdrantClient:
    """Create Qdrant client."""
    if url.startswith("http://") or url.startswith("https://"):
        url_parts = url.replace("http://", "").replace("https://", "").split(":")
        host = url_parts[0] if url_parts else "localhost"
        port = int(url_parts[1]) if len(url_parts) > 1 else 6333
        return QdrantClient(host=host, port=port)
    else:
        return QdrantClient(url=url)


def backfill_abstract(
    client: QdrantClient,
    collection_name: str,
    batch_size: int = 1000,
    qdrant_url: str = "http://localhost:6333",
) -> Dict[str, int]:
    """
    Backfill abstract field for points missing it.
    
    Returns:
        Dict with counts: scanned, updated
    """
    print(f"[BACKFILL] Starting backfill for collection '{collection_name}'...")
    
    scanned = 0
    updated = 0
    offset = None
    
    # Scroll through all points
    while True:
        result = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,  # Need vectors to preserve them during update
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        # Collect points that need updating
        points_to_update = []
        
        for point in points:
            scanned += 1
            payload = point.payload or {}
            
            # Check if abstract is missing
            if "abstract" not in payload:
                # Set abstract = text
                text = payload.get("text", "")
                new_payload = payload.copy()
                new_payload["abstract"] = text
                
                points_to_update.append(
                    PointStruct(
                        id=point.id,
                        vector=point.vector,  # Preserve original vector
                        payload=new_payload,
                    )
                )
        
        # Batch update
        if points_to_update:
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=points_to_update,
                    wait=True,
                )
                updated += len(points_to_update)
                if scanned % 5000 == 0 or updated > 0:
                    print(f"  ... scanned: {scanned}, updated: {updated}")
            except Exception as e:
                print(f"[WARN] Failed to update batch: {e}")
                # Continue with next batch
        
        offset = next_offset
        if offset is None:
            break
    
    return {
        "scanned": scanned,
        "updated": updated,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Backfill abstract field in Qdrant collection"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="fiqa_10k_v1",
        help="Qdrant collection name (default: fiqa_10k_v1)",
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for updates (default: 1000)",
    )
    
    args = parser.parse_args()
    
    print(f"=" * 60)
    print(f"V12 Backfill Abstract")
    print(f"  Collection: {args.collection}")
    print(f"  Qdrant URL: {args.qdrant_url}")
    print(f"  Batch size: {args.batch_size}")
    print(f"=" * 60)
    
    # Connect to Qdrant
    client = get_qdrant_client(args.qdrant_url)
    
    # Check if collection exists (with API version compatibility)
    try:
        try:
            info = client.get_collection(args.collection)
            points_count = getattr(info, 'points_count', 0)
            print(f"[INFO] Collection '{args.collection}' has {points_count} points")
        except Exception as api_error:
            # API version differences - check if it's a validation error
            if "validation" in str(api_error).lower() or "strict_mode" in str(api_error).lower():
                print(f"[WARN] API compatibility issue (continuing anyway): {api_error}")
                print(f"[INFO] Proceeding with backfill for '{args.collection}'")
            else:
                raise
    except Exception as e:
        print(f"[ERROR] Failed to access collection '{args.collection}': {e}")
        sys.exit(1)
    
    # Perform backfill
    results = backfill_abstract(
        client,
        args.collection,
        args.batch_size,
        args.qdrant_url,
    )
    
    print(f"=" * 60)
    print(f"✅ Backfill complete!")
    print(f"  Scanned: {results['scanned']} points")
    print(f"  Updated: {results['updated']} points")
    if results['scanned'] > 0:
        update_rate = results['updated'] / results['scanned'] * 100
        print(f"  Update rate: {update_rate:.1f}%")
    print(f"=" * 60)


if __name__ == "__main__":
    main()

