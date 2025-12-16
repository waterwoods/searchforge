#!/usr/bin/env python3
"""
ops_rag_smoke.py - Smoke test for Ops RAG retrieval

Tests vector search retrieval with sample service/symptom queries.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.ops_rag_retriever import retrieve_ops_knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Test queries
TEST_QUERIES = [
    {
        "service_name": "payment-service",
        "symptom": "high_error_rate",
        "description": "Payment service high error rate",
    },
    {
        "service_name": "api-gateway",
        "symptom": "high_latency",
        "description": "API gateway high latency",
    },
    {
        "service_name": "search-api",
        "symptom": "high_cpu",
        "description": "Search API high CPU",
    },
    {
        "service_name": "payment-service",
        "symptom": None,
        "description": "Payment service (no symptom)",
    },
]


def print_result(rank: int, result: dict):
    """Print a single search result."""
    print(f"  [{rank}] Score: {result['score']:.4f}")
    print(f"      Source: {result['source_file']}")
    if result.get('service_hint'):
        print(f"      Service hint: {result['service_hint']}")
    if result.get('symptom_hint'):
        print(f"      Symptom hint: {result['symptom_hint']}")
    
    # Print first 120 chars of text
    text_preview = result['text'][:120].replace('\n', ' ')
    if len(result['text']) > 120:
        text_preview += "..."
    print(f"      Text: {text_preview}")
    print()


def main():
    print("=" * 80)
    print("Ops RAG Smoke Test")
    print("=" * 80)
    print()
    
    total_queries = len(TEST_QUERIES)
    successful_queries = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{total_queries}] Query: {query['description']}")
        print(f"  Service: {query['service_name']}")
        if query['symptom']:
            print(f"  Symptom: {query['symptom']}")
        print()
        
        try:
            results = retrieve_ops_knowledge(
                service_name=query['service_name'],
                symptom=query['symptom'],
                top_k=3,
            )
            
            if not results:
                print("  ⚠️  No results returned (index may not exist or Qdrant unavailable)")
                print("  💡 Run: python experiments/build_ops_kb_index.py --recreate")
                print()
                continue
            
            print(f"  ✅ Retrieved {len(results)} results:")
            print()
            
            for rank, result in enumerate(results, 1):
                print_result(rank, result)
            
            successful_queries += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 80)
    print(f"Summary: {successful_queries}/{total_queries} queries successful")
    
    if successful_queries == 0:
        print()
        print("⚠️  No queries returned results. Possible issues:")
        print("  1. Index not built - Run: python experiments/build_ops_kb_index.py --recreate")
        print("  2. Qdrant not running - Check QDRANT_HOST and QDRANT_PORT env vars")
        print("  3. Collection name mismatch - Check collection_name in ops_rag_retriever.py")
        return 1
    
    print("✅ Smoke test passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

