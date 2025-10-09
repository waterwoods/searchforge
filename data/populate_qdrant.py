#!/usr/bin/env python3
"""
Script to populate Qdrant with 5000 synthetic AI documents.
Creates a collection named 'demo_5k' with 384-dimensional vectors.
"""

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import time

def main():
    print("🚀 Starting Qdrant population script...")
    
    # 1. Connect to local Qdrant
    print("🔗 Connecting to Qdrant at localhost:6333...")
    client = QdrantClient(host="localhost", port=6333)
    
    collection_name = "demo_5k"
    vector_size = 384
    total_points = 5000
    batch_size = 200
    
    # 2. Check if collection exists, create if not
    try:
        collections = client.get_collections()
        existing_collections = [c.name for c in collections.collections]
        
        if collection_name not in existing_collections:
            print(f"📋 Creating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{collection_name}' created successfully!")
        else:
            print(f"📋 Collection '{collection_name}' already exists.")
            
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return
    
    # 3. Generate and insert 5000 records
    print(f"📊 Generating {total_points} synthetic records...")
    
    points = []
    for i in range(total_points):
        # Generate random 384-dimensional vector (normal distribution)
        vector = np.random.normal(0, 1, vector_size).astype(np.float32)
        
        # Create point structure
        point = PointStruct(
            id=i,
            vector=vector.tolist(),
            payload={
                "text": f"Synthetic AI text sample #{i}",
                "category": "AI",
                "doc_id": f"doc_{i}"
            }
        )
        points.append(point)
    
    # 4. Batch insert (200 points per batch)
    print(f"📤 Inserting {total_points} points in batches of {batch_size}...")
    
    start_time = time.time()
    for i in range(0, total_points, batch_size):
        batch = points[i:i + batch_size]
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch
            )
            batch_num = (i // batch_size) + 1
            total_batches = (total_points + batch_size - 1) // batch_size
            print(f"  ✅ Batch {batch_num}/{total_batches} inserted ({len(batch)} points)")
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            return
    
    end_time = time.time()
    
    # 5. Verify insertion
    try:
        collection_info = client.get_collection(collection_name)
        actual_points = collection_info.points_count
        print(f"\n🎉 Successfully inserted {actual_points} points into '{collection_name}'!")
        print(f"⏱️  Total time: {end_time - start_time:.2f} seconds")
        print(f"📊 Average speed: {actual_points / (end_time - start_time):.0f} points/second")
        
    except Exception as e:
        print(f"❌ Error verifying insertion: {e}")

if __name__ == "__main__":
    main()












