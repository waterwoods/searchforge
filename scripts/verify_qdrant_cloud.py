#!/usr/bin/env python3
"""
Quick verification script for Qdrant Cloud connection and collection health.

Usage:
    python scripts/verify_qdrant_cloud.py
    
    Or with env vars:
    export QDRANT_URL=https://your-cluster.qdrant.io
    export QDRANT_API_KEY=your-api-key
    export QDRANT_COLLECTION=fiqa_10k_v1
    python scripts/verify_qdrant_cloud.py
"""

import os
import sys
from typing import Optional

try:
    from qdrant_client import QdrantClient
except ImportError:
    print("ERROR: qdrant-client not installed. Install with: pip install qdrant-client")
    sys.exit(1)


def verify_cloud_connection(
    url: str,
    api_key: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> bool:
    """Verify Qdrant Cloud connection and optionally check collection."""
    print("=" * 70)
    print("Qdrant Cloud Verification")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"API Key: {'***' + api_key[-4:] if api_key else 'Not set'}")
    print()
    
    # Connect
    print("[1] Connecting to Qdrant Cloud...")
    try:
        client_kwargs = {"url": url}
        if api_key:
            client_kwargs["api_key"] = api_key
        
        client = QdrantClient(**client_kwargs)
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected successfully")
        print(f"   Found {len(collections.collections)} collection(s)")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # List collections
    if collections.collections:
        print("[2] Available collections:")
        for coll in collections.collections:
            print(f"   - {coll.name}")
        print()
    
    # Check specific collection if provided
    if collection_name:
        print(f"[3] Checking collection '{collection_name}'...")
        try:
            info = client.get_collection(collection_name)
            print(f"✅ Collection found")
            print(f"   Vector size: {info.config.params.vectors.size}")
            print(f"   Distance: {info.config.params.vectors.distance}")
            print(f"   Points: {info.points_count:,}")
            
            # Sample a few points
            if info.points_count > 0:
                print()
                print("[4] Sampling points...")
                points, _ = client.scroll(
                    collection_name=collection_name,
                    limit=3,
                    with_payload=True,
                    with_vectors=False,
                )
                for i, point in enumerate(points, 1):
                    doc_id = point.payload.get("doc_id", "N/A")
                    title = point.payload.get("title", "N/A")[:50]
                    print(f"   Point {i}: id={point.id}, doc_id={doc_id}, title={title}...")
            
            print()
            print("=" * 70)
            print("✅ All checks passed!")
            print("=" * 70)
            return True
            
        except Exception as e:
            if "not found" in str(e).lower():
                print(f"❌ Collection '{collection_name}' not found")
            else:
                print(f"❌ Error checking collection: {e}")
            return False
    else:
        print("=" * 70)
        print("✅ Connection verified (no collection specified)")
        print("=" * 70)
        return True


def main():
    # Get from env vars or command line
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION")
    
    if not url:
        print("ERROR: QDRANT_URL environment variable not set")
        print()
        print("Usage:")
        print("  export QDRANT_URL=https://your-cluster.qdrant.io")
        print("  export QDRANT_API_KEY=your-api-key")
        print("  export QDRANT_COLLECTION=fiqa_10k_v1  # optional")
        print("  python scripts/verify_qdrant_cloud.py")
        sys.exit(1)
    
    success = verify_cloud_connection(url, api_key, collection)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
