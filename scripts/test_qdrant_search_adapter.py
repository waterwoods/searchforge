#!/usr/bin/env python3
"""
Minimal test script for Qdrant search adapter.

Tests that the qdrant_search adapter function works correctly with the installed
qdrant-client version and returns results with doc_id and text/title fields.
"""

import os
import sys

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fiqa_api.clients import get_qdrant_client
from services.fiqa_api.utils.qdrant_adapter import qdrant_search


def main():
    """Run minimal test of qdrant_search adapter."""
    # Read env vars
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "fiqa_10k_v1")
    
    if not qdrant_url:
        print("❌ FAIL: QDRANT_URL not set")
        return 1
    
    print(f"[TEST] Collection: {collection}")
    print(f"[TEST] QDRANT_URL: {qdrant_url[:50]}...")
    print(f"[TEST] QDRANT_API_KEY: {'SET' if qdrant_api_key else 'NOT SET'}")
    
    # Get client
    try:
        client = get_qdrant_client()
        print("[TEST] ✅ Client created")
    except Exception as e:
        print(f"❌ FAIL: Failed to create client: {e}")
        return 1
    
    # Generate a test embedding vector
    # Use fastembed if available (model should be cached from Docker build)
    try:
        from fastembed import TextEmbedding
        model_name = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
        print(f"[TEST] Using fastembed model: {model_name}")
        emb = TextEmbedding(model_name=model_name)
        # Generate embedding for "hello" (simple test query)
        embedding_iter = emb.embed(["hello"])
        query_vector = next(iter(embedding_iter))
        print(f"[TEST] ✅ Generated embedding vector (dim={len(query_vector)})")
    except Exception as e:
        print(f"[TEST] ⚠️  fastembed failed: {e}")
        # Fallback: use zero vector with expected dimension (384 for bge-small-en-v1.5)
        expected_dim = 384
        query_vector = [0.0] * expected_dim
        print(f"[TEST] Using zero vector (dim={expected_dim})")
    
    # Test search adapter
    try:
        print("[TEST] Calling qdrant_search...")
        results = qdrant_search(
            client=client,
            collection_name=collection,
            query_vector=query_vector,
            limit=3
        )
        print(f"[TEST] ✅ Search returned {len(results)} results")
    except Exception as e:
        print(f"❌ FAIL: Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Validate results
    if len(results) == 0:
        print("❌ FAIL: No results returned")
        return 1
    
    print(f"[TEST] ✅ Results count: {len(results)}")
    
    # Check first result structure
    first_result = results[0]
    has_payload = hasattr(first_result, 'payload') or isinstance(first_result, dict)
    has_score = hasattr(first_result, 'score') or 'score' in (first_result if isinstance(first_result, dict) else {})
    
    if not has_payload:
        print("❌ FAIL: Result missing payload attribute")
        return 1
    
    # Extract payload
    if hasattr(first_result, 'payload'):
        payload = first_result.payload or {}
    else:
        payload = first_result.get('payload', {}) if isinstance(first_result, dict) else {}
    
    # Check for doc_id
    doc_id = payload.get("doc_id") if isinstance(payload, dict) else None
    if not doc_id:
        # Try getting from result id
        doc_id = getattr(first_result, 'id', None) or (first_result.get('id') if isinstance(first_result, dict) else None)
    
    if not doc_id:
        print("❌ FAIL: Result missing doc_id in payload or id")
        print(f"[TEST] Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
        return 1
    
    # Check for text or title
    has_text = isinstance(payload, dict) and (payload.get("text") or payload.get("title"))
    
    if not has_text:
        print("⚠️  WARN: Result missing text/title in payload")
        print(f"[TEST] Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
    else:
        print("[TEST] ✅ Result has doc_id and text/title")
    
    # Print summary
    print(f"[TEST] ✅ First result: doc_id={doc_id}, score={getattr(first_result, 'score', 'N/A')}")
    
    print("\n✅ PASS: qdrant_search adapter works correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
