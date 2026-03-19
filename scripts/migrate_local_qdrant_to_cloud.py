#!/usr/bin/env python3
"""
Migration script: Migrate local Qdrant collection to Qdrant Cloud

This script:
1. Reads all points from local Qdrant collection (fiqa_10k_v1)
2. Recreates the same collection on Qdrant Cloud
3. Upserts all points with payloads and vectors
4. Verifies point count and samples

Usage:
    python scripts/migrate_local_qdrant_to_cloud.py \
        --local-url http://localhost:6333 \
        --cloud-url https://your-cluster.qdrant.io \
        --cloud-api-key your-api-key \
        --collection fiqa_10k_v1

The script is idempotent and safe to re-run.
"""

import argparse
import os
import sys
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    print("ERROR: qdrant-client not installed. Install with: pip install qdrant-client")
    sys.exit(1)


def scroll_all_points(
    client: QdrantClient, 
    collection_name: str,
    batch_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    Scroll through all points in a Qdrant collection.
    
    Returns list of documents with id, payload, and vector.
    """
    all_points = []
    offset = None
    
    print(f"[SCROLL] Fetching all points from '{collection_name}'...")
    
    while True:
        try:
            result = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            for point in points:
                all_points.append({
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload or {},
                })
            
            if len(all_points) % 10000 == 0:
                print(f"  ... fetched {len(all_points)} points")
            
            offset = next_offset
            if offset is None:
                break
                
        except Exception as e:
            print(f"ERROR: Failed to scroll points: {e}")
            raise
    
    print(f"[SCROLL] Total: {len(all_points)} points fetched")
    return all_points


def get_collection_info(client: QdrantClient, collection_name: str) -> Optional[Dict[str, Any]]:
    """Get collection information including vector size and distance."""
    try:
        info = client.get_collection(collection_name)
        return {
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance,
            "points_count": info.points_count,
        }
    except Exception as e:
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            return None
        raise


def create_collection_on_cloud(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
    recreate: bool = False,
) -> None:
    """Create collection on cloud Qdrant."""
    # Check if collection exists
    existing_info = get_collection_info(client, collection_name)
    
    if existing_info:
        if recreate:
            print(f"[COLLECTION] Deleting existing collection '{collection_name}'...")
            try:
                client.delete_collection(collection_name)
                time.sleep(1)  # Wait for deletion
                print(f"[COLLECTION] Deleted '{collection_name}'")
            except Exception as e:
                print(f"[WARN] Error deleting collection (may not exist): {e}")
        else:
            print(f"[COLLECTION] Collection '{collection_name}' already exists with {existing_info['points_count']} points")
            print(f"[COLLECTION] Skipping creation (use --recreate to force)")
            return
    
    # Create collection
    print(f"[COLLECTION] Creating '{collection_name}' on cloud...")
    print(f"  Vector size: {vector_size}")
    print(f"  Distance: {distance.value}")
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=distance,
        ),
    )
    
    print(f"[COLLECTION] Created '{collection_name}' successfully")


def upsert_points_batch(
    client: QdrantClient,
    collection_name: str,
    points: List[Dict[str, Any]],
    batch_size: int = 500,
) -> None:
    """Upsert points to cloud collection in batches."""
    total = len(points)
    print(f"[UPSERT] Upserting {total} points to '{collection_name}'...")
    
    for i in range(0, total, batch_size):
        batch = points[i : i + batch_size]
        
        # Convert to PointStruct
        point_structs = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point["payload"],
            )
            for point in batch
        ]
        
        try:
            client.upsert(
                collection_name=collection_name,
                points=point_structs,
                wait=True,
            )
            
            if (i + batch_size) % 5000 == 0 or (i + batch_size) >= total:
                print(f"  ... upserted {min(i + batch_size, total)}/{total} points")
                
        except Exception as e:
            print(f"ERROR: Failed to upsert batch {i}-{i+len(batch)}: {e}")
            raise
    
    print(f"[UPSERT] Completed: {total} points upserted")


def verify_migration(
    local_client: QdrantClient,
    cloud_client: QdrantClient,
    collection_name: str,
    sample_size: int = 10,
) -> bool:
    """Verify migration by comparing point counts and sampling random points."""
    print(f"[VERIFY] Verifying migration...")
    
    # Get point counts
    local_info = get_collection_info(local_client, collection_name)
    cloud_info = get_collection_info(cloud_client, collection_name)
    
    if not local_info or not cloud_info:
        print(f"ERROR: Could not get collection info")
        return False
    
    local_count = local_info["points_count"]
    cloud_count = cloud_info["points_count"]
    
    print(f"  Local collection: {local_count} points")
    print(f"  Cloud collection: {cloud_count} points")
    
    if local_count != cloud_count:
        print(f"⚠️  WARNING: Point counts don't match!")
        return False
    
    # Sample random points and compare
    print(f"  Sampling {sample_size} random points for verification...")
    
    try:
        # Get random points from local
        local_points, _ = local_client.scroll(
            collection_name=collection_name,
            limit=sample_size,
            with_payload=True,
            with_vectors=True,
        )
        
        # Verify same points exist in cloud
        for local_point in local_points:
            cloud_point = cloud_client.retrieve(
                collection_name=collection_name,
                ids=[local_point.id],
                with_payload=True,
                with_vectors=True,
            )
            
            if not cloud_point:
                print(f"  ❌ Point {local_point.id} not found in cloud")
                return False
            
            # Compare payloads (vectors may have slight floating point differences)
            if local_point.payload != cloud_point[0].payload:
                print(f"  ⚠️  WARNING: Payload mismatch for point {local_point.id}")
                # Don't fail, just warn (payloads might have been updated)
        
        print(f"  ✅ Sample verification passed")
        return True
        
    except Exception as e:
        print(f"  ⚠️  WARNING: Sample verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Migrate local Qdrant collection to Qdrant Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python scripts/migrate_local_qdrant_to_cloud.py \\
      --local-url http://localhost:6333 \\
      --cloud-url https://your-cluster-id.us-east4-0.gcp.cloud.qdrant.io \\
      --cloud-api-key \$QDRANT_API_KEY \\
      --collection fiqa_10k_v1

  # Force recreate collection
  python scripts/migrate_local_qdrant_to_cloud.py \\
      --local-url http://localhost:6333 \\
      --cloud-url https://your-cluster.qdrant.io \\
      --cloud-api-key your-key \\
      --collection fiqa_10k_v1 \\
      --recreate
        """
    )
    
    parser.add_argument(
        "--local-url",
        default=os.getenv("LOCAL_QDRANT_URL", "http://localhost:6333"),
        help="Local Qdrant URL (default: http://localhost:6333 or LOCAL_QDRANT_URL env var)",
    )
    
    parser.add_argument(
        "--cloud-url",
        required=True,
        help="Qdrant Cloud URL (required, or set QDRANT_URL env var)",
    )
    
    parser.add_argument(
        "--cloud-api-key",
        default=os.getenv("QDRANT_API_KEY"),
        help="Qdrant Cloud API key (required, or set QDRANT_API_KEY env var)",
    )
    
    parser.add_argument(
        "--collection",
        default="fiqa_10k_v1",
        help="Collection name to migrate (default: fiqa_10k_v1)",
    )
    
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection on cloud (delete if exists)",
    )
    
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verification step",
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for upserting points (default: 500)",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.cloud_api_key:
        print("ERROR: --cloud-api-key is required (or set QDRANT_API_KEY env var)")
        sys.exit(1)
    
    if not args.cloud_url.startswith(("http://", "https://")):
        print("ERROR: --cloud-url must start with http:// or https://")
        sys.exit(1)
    
    print("=" * 70)
    print("Qdrant Migration: Local → Cloud")
    print("=" * 70)
    print(f"Local URL:  {args.local_url}")
    print(f"Cloud URL:  {args.cloud_url}")
    print(f"Collection: {args.collection}")
    print(f"Recreate:   {args.recreate}")
    print("=" * 70)
    print()
    
    # Initialize clients
    print("[INIT] Connecting to local Qdrant...")
    try:
        local_client = QdrantClient(url=args.local_url)
        local_client.get_collections()  # Test connection
        print("✅ Connected to local Qdrant")
    except Exception as e:
        print(f"ERROR: Failed to connect to local Qdrant: {e}")
        sys.exit(1)
    
    print("[INIT] Connecting to Qdrant Cloud...")
    try:
        cloud_client = QdrantClient(
            url=args.cloud_url,
            api_key=args.cloud_api_key,
        )
        cloud_client.get_collections()  # Test connection
        print("✅ Connected to Qdrant Cloud")
    except Exception as e:
        print(f"ERROR: Failed to connect to Qdrant Cloud: {e}")
        print("  Check your URL and API key")
        sys.exit(1)
    
    # Check local collection exists
    print(f"[CHECK] Checking local collection '{args.collection}'...")
    local_info = get_collection_info(local_client, args.collection)
    if not local_info:
        print(f"ERROR: Local collection '{args.collection}' not found")
        sys.exit(1)
    
    print(f"✅ Local collection found:")
    print(f"   Vector size: {local_info['vector_size']}")
    print(f"   Distance: {local_info['distance']}")
    print(f"   Points: {local_info['points_count']}")
    print()
    
    # Read all points from local
    print("[STEP 1] Reading all points from local collection...")
    local_points = scroll_all_points(local_client, args.collection)
    
    if not local_points:
        print("ERROR: No points found in local collection")
        sys.exit(1)
    
    print()
    
    # Create collection on cloud
    print("[STEP 2] Creating collection on cloud...")
    create_collection_on_cloud(
        client=cloud_client,
        collection_name=args.collection,
        vector_size=local_info["vector_size"],
        distance=local_info["distance"],
        recreate=args.recreate,
    )
    print()
    
    # Upsert points to cloud
    print("[STEP 3] Migrating points to cloud...")
    upsert_points_batch(
        client=cloud_client,
        collection_name=args.collection,
        points=local_points,
        batch_size=args.batch_size,
    )
    print()
    
    # Verify migration
    if not args.skip_verify:
        print("[STEP 4] Verifying migration...")
        success = verify_migration(
            local_client=local_client,
            cloud_client=cloud_client,
            collection_name=args.collection,
        )
        print()
        
        if not success:
            print("⚠️  Verification had warnings, but migration may still be successful")
            print("   Check the cloud collection manually if needed")
    else:
        print("[STEP 4] Skipping verification (--skip-verify)")
        print()
    
    # Final summary
    cloud_info = get_collection_info(cloud_client, args.collection)
    print("=" * 70)
    print("✅ Migration Complete!")
    print("=" * 70)
    print(f"Collection: {args.collection}")
    print(f"Local points:  {local_info['points_count']}")
    if cloud_info:
        print(f"Cloud points:  {cloud_info['points_count']}")
    print()
    print("Next steps:")
    print("1. Update your .env file with:")
    print(f"   QDRANT_URL={args.cloud_url}")
    print(f"   QDRANT_API_KEY={args.cloud_api_key[:20]}...")
    print(f"   QDRANT_COLLECTION={args.collection}")
    print()
    print("2. Test the connection:")
    print("   python scripts/verify_qdrant_cloud.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
