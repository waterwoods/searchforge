#!/usr/bin/env python3
"""
Fix missing doc_id and text fields in Qdrant collection.

This script scans all points in the demo_5k collection and fixes:
- Missing "doc_id" in payload -> fill with point.id
- Missing "text" in payload -> fill with empty string ""
"""

import argparse
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

def fix_collection(collection_name="demo_5k", batch_size=500):
    """Fix missing doc_id and text fields in the collection."""
    client = QdrantClient(url="http://localhost:6333")
    
    try:
        # Get collection info
        info = client.get_collection(collection_name)
        total_points = info.points_count or 0
        print(f"Collection '{collection_name}' has {total_points} points")
        
        if total_points == 0:
            print("Collection is empty, nothing to fix")
            return
            
    except Exception as e:
        print(f"Error accessing collection '{collection_name}': {e}")
        return
    
    fixed_count = 0
    examples_shown = 0
    points_to_update = []
    fix_examples = []
    
    # Scroll through all points
    next_page = None
    while True:
        try:
            # Get batch of points
            res = client.scroll(
                collection_name=collection_name,
                with_payload=True,
                limit=batch_size,
                offset=next_page
            )
            batch, next_page = res
            
            if not batch:
                break
                
            # Process each point
            for point in batch:
                point_id = point.id
                payload = point.payload or {}
                original_payload = payload.copy()
                needs_fix = False
                
                # Fix missing doc_id
                if "doc_id" not in payload:
                    payload["doc_id"] = str(point_id)
                    needs_fix = True
                
                # Fix missing text
                if "text" not in payload:
                    payload["text"] = ""
                    needs_fix = True
                
                # If payload was modified, collect for batch update
                if needs_fix:
                    # Store example for later display
                    if examples_shown < 3:
                        fix_examples.append({
                            'id': point_id,
                            'before': original_payload,
                            'after': payload.copy()
                        })
                        examples_shown += 1
                    
                    # Add to batch update list
                    points_to_update.append(PointStruct(
                        id=point_id,
                        payload=payload
                    ))
                    fixed_count += 1
                    
                    # Batch update when we reach batch_size
                    if len(points_to_update) >= batch_size:
                        try:
                            client.upsert(
                                collection_name=collection_name,
                                points=points_to_update
                            )
                            print(f"Updated batch of {len(points_to_update)} points")
                            points_to_update = []
                        except Exception as e:
                            print(f"Error updating batch: {e}")
                            # Try individual updates as fallback
                            for point in points_to_update:
                                try:
                                    client.set_payload(
                                        collection_name=collection_name,
                                        payload=point.payload,
                                        points=[point.id]
                                    )
                                except Exception as e2:
                                    print(f"Error updating point {point.id}: {e2}")
                            points_to_update = []
                        
        except Exception as e:
            print(f"Error processing batch: {e}")
            break
    
    # Update remaining points
    if points_to_update:
        try:
            client.upsert(
                collection_name=collection_name,
                points=points_to_update
            )
            print(f"Updated final batch of {len(points_to_update)} points")
        except Exception as e:
            print(f"Error updating final batch: {e}")
            # Try individual updates as fallback
            for point in points_to_update:
                try:
                    client.set_payload(
                        collection_name=collection_name,
                        payload=point.payload,
                        points=[point.id]
                    )
                except Exception as e2:
                    print(f"Error updating point {point.id}: {e2}")
    
    print(f"Fixed {fixed_count} documents in total.")
    
    # Show examples
    if fix_examples:
        print("Example fixes:")
        for example in fix_examples:
            print(f"Before: id={example['id']}, payload={example['before']}")
            print(f"After:  id={example['id']}, payload={example['after']}")

def main():
    parser = argparse.ArgumentParser(description="Fix missing doc_id and text fields in Qdrant collection")
    parser.add_argument("--collection", default="demo_5k", help="Collection name to fix")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for updates")
    args = parser.parse_args()
    
    fix_collection(args.collection, args.batch_size)

if __name__ == "__main__":
    main()
