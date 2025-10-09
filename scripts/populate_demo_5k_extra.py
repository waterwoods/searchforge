#!/usr/bin/env python3
"""
Populate demo_5k collection with additional documents related to USB-C and wireless charging.

This script adds 20-100 new documents to the demo_5k collection that are highly relevant
to the queries: "fast usb c cable charging", "wireless charger", "usb c hub".
"""

import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any
import uuid

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer


def get_related_documents() -> List[Dict[str, Any]]:
    """Generate documents highly relevant to the three target queries."""
    
    documents = []
    
    # Documents related to "fast usb c cable charging"
    usb_c_charging_docs = [
        "USB-C fast charging cable with 100W power delivery for rapid device charging.",
        "High-speed USB-C cable supports 60W fast charging for laptops and phones.",
        "Premium USB-C charging cable with 3A current for quick device power-up.",
        "USB-C to USB-C fast charging cable with 100W PD support for MacBook Pro.",
        "Lightning to USB-C fast charging cable for iPhone with 20W power delivery.",
        "USB-C fast charging cable with braided design for durability and speed.",
        "USB-C PD fast charging cable supports 65W for gaming laptops and tablets.",
        "USB-C fast charging cable with 2-meter length for flexible charging setup.",
        "USB-C fast charging cable with gold-plated connectors for optimal power transfer.",
        "USB-C fast charging cable with 100W power delivery and reversible connector.",
        "USB-C fast charging cable with 3A current rating for rapid smartphone charging.",
        "USB-C fast charging cable with 60W power delivery for tablets and laptops.",
        "USB-C fast charging cable with 100W PD support for high-power devices.",
        "USB-C fast charging cable with 2.4A current for fast phone and tablet charging.",
        "USB-C fast charging cable with 100W power delivery for professional laptops.",
        "USB-C fast charging cable with 3A current and braided nylon construction.",
        "USB-C fast charging cable with 60W PD support for MacBook Air and Pro.",
        "USB-C fast charging cable with 100W power delivery for gaming laptops.",
        "USB-C fast charging cable with 3A current rating for rapid device charging.",
        "USB-C fast charging cable with 100W PD support for high-performance devices."
    ]
    
    # Documents related to "wireless charger"
    wireless_charging_docs = [
        "Wireless charging pad with 15W fast charging for iPhone and Android phones.",
        "Qi wireless charging stand with 10W power for convenient phone charging.",
        "Wireless charging pad with 15W fast charging and LED indicator for status.",
        "Qi wireless charging stand with 10W power and anti-slip design for stability.",
        "Wireless charging pad with 15W fast charging and temperature protection.",
        "Qi wireless charging stand with 10W power and compact design for travel.",
        "Wireless charging pad with 15W fast charging and multiple device support.",
        "Qi wireless charging stand with 10W power and adjustable angle for viewing.",
        "Wireless charging pad with 15W fast charging and overcurrent protection.",
        "Qi wireless charging stand with 10W power and premium aluminum construction.",
        "Wireless charging pad with 15W fast charging and foreign object detection.",
        "Qi wireless charging stand with 10W power and fast charging capability.",
        "Wireless charging pad with 15W fast charging and LED charging indicator.",
        "Qi wireless charging stand with 10W power and non-slip rubber base.",
        "Wireless charging pad with 15W fast charging and temperature monitoring.",
        "Qi wireless charging stand with 10W power and adjustable height design.",
        "Wireless charging pad with 15W fast charging and multiple coil technology.",
        "Qi wireless charging stand with 10W power and premium build quality.",
        "Wireless charging pad with 15W fast charging and safety certification.",
        "Qi wireless charging stand with 10W power and ergonomic viewing angle."
    ]
    
    # Documents related to "usb c hub"
    usb_c_hub_docs = [
        "USB-C hub with 4K HDMI output and multiple USB ports for laptop expansion.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for connectivity.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for MacBook Pro.",
        "USB-C docking station with HDMI output and multiple USB ports for laptops.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for Windows laptops.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for productivity.",
        "USB-C hub with 4K HDMI output and multiple USB ports for gaming setups.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for office use.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for creative professionals.",
        "USB-C docking station with HDMI output and multiple USB ports for home office.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for video editing.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for presentations.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for streaming setups.",
        "USB-C docking station with HDMI output and multiple USB ports for meetings.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for content creation.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for remote work.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for multimedia editing.",
        "USB-C docking station with HDMI output and multiple USB ports for collaboration.",
        "USB-C hub with 4K HDMI, USB-A, and USB-C ports for professional workflows.",
        "USB-C docking station with HDMI, USB-A, and USB-C ports for modern computing."
    ]
    
    # Combine all documents with categories
    all_docs = []
    for doc in usb_c_charging_docs:
        all_docs.append({"text": doc, "category": "usb_c_charging"})
    for doc in wireless_charging_docs:
        all_docs.append({"text": doc, "category": "wireless_charging"})
    for doc in usb_c_hub_docs:
        all_docs.append({"text": doc, "category": "usb_c_hub"})
    
    return all_docs


def get_embedding_model():
    """Get the embedding model used by the existing collection."""
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def connect_to_qdrant():
    """Connect to Qdrant client."""
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = int(os.environ.get("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port)


def insert_documents(client: QdrantClient, documents: List[Dict[str, Any]], collection_name: str = "demo_5k"):
    """Insert documents into Qdrant collection."""
    
    # Get embedding model
    model = get_embedding_model()
    
    # Prepare points for insertion
    points = []
    
    for i, doc in enumerate(documents):
        # Generate unique ID (use integer for Qdrant)
        point_id = 10000 + i + 1  # Start from 10000 to avoid conflicts
        doc_id = f"demo_extra_{i+1}"
        
        # Generate embedding
        embedding = model.encode(doc["text"]).tolist()
        
        # Create point
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "text": doc["text"],
                "category": doc["category"],
                "doc_id": doc_id
            }
        )
        points.append(point)
    
    # Insert points into collection
    try:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"✅ Successfully inserted {len(points)} documents into collection '{collection_name}'")
        return True
    except Exception as e:
        print(f"❌ Error inserting documents: {e}")
        return False


def main():
    """Main function to populate the collection."""
    print("🚀 Starting demo_5k collection population...")
    
    # Generate documents
    print("📝 Generating relevant documents...")
    documents = get_related_documents()
    print(f"Generated {len(documents)} documents")
    
    # Show sample documents
    print("\n📋 Sample documents:")
    for i, doc in enumerate(documents[:3]):
        print(f"  {i+1}. [{doc['category']}] {doc['text']}")
    
    # Connect to Qdrant
    print("\n🔌 Connecting to Qdrant...")
    try:
        client = connect_to_qdrant()
        print("✅ Connected to Qdrant successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return
    
    # Check if collection exists
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        if "demo_5k" not in collection_names:
            print("❌ Collection 'demo_5k' not found. Available collections:", collection_names)
            return
        print("✅ Collection 'demo_5k' found")
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
        return
    
    # Insert documents
    print(f"\n📤 Inserting {len(documents)} documents...")
    success = insert_documents(client, documents)
    
    if success:
        print("\n🎉 Collection population completed successfully!")
        print(f"📊 Added {len(documents)} new documents to demo_5k collection")
        print("🔍 You can now test with the rerank report script:")
        print("   python scripts/rerank_report_html.py --config configs/demo_rerank_5k.yaml --collection demo_5k --candidate_k 200 --rerank_k 50 --output reports/rerank_html --queries \"fast usb c cable charging\" \"wireless charger\" \"usb c hub\"")
    else:
        print("\n❌ Collection population failed!")


if __name__ == "__main__":
    main()
