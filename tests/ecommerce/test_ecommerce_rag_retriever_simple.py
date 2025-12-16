#!/usr/bin/env python3
"""
Simple test script for ecommerce RAG retriever (no pytest dependency)

Run: python3 tests/ecommerce/test_ecommerce_rag_retriever_simple.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ecommerce.ecommerce_rag_retriever import (
    retrieve_policy_snippets,
    PolicySnippet,
    _load_index,
)


def test_retrieve_policy_snippets_basic():
    """Test that retrieve_policy_snippets returns non-empty results for a relevant query."""
    print("\n" + "=" * 80)
    print("Test 1: Basic retrieval test")
    print("=" * 80)
    
    # Check if index exists
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        print("❌ SKIP: Index not found. Run experiments/build_ecommerce_kb_index.py first.")
        return False
    
    # Test query
    query = "damaged item refund"
    print(f"Query: '{query}'")
    
    try:
        results = retrieve_policy_snippets(query, k=2)
        
        # Assertions
        if not isinstance(results, list):
            print(f"❌ FAIL: Expected list, got {type(results)}")
            return False
        
        if len(results) == 0:
            print("❌ FAIL: Should return at least one snippet")
            return False
        
        print(f"✅ PASS: Retrieved {len(results)} snippets")
        
        # Check structure
        for idx, snippet in enumerate(results, 1):
            if not isinstance(snippet, PolicySnippet):
                print(f"❌ FAIL: Snippet {idx} is not a PolicySnippet instance")
                return False
            
            if not snippet.id:
                print(f"❌ FAIL: Snippet {idx} missing id")
                return False
            
            if not snippet.source:
                print(f"❌ FAIL: Snippet {idx} missing source")
                return False
            
            if not snippet.text or len(snippet.text) == 0:
                print(f"❌ FAIL: Snippet {idx} missing or empty text")
                return False
            
            print(f"  Snippet {idx}: [{snippet.source}] {snippet.text[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_index():
    """Test that _load_index can load the index files."""
    print("\n" + "=" * 80)
    print("Test 2: Index loading test")
    print("=" * 80)
    
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        print("❌ SKIP: Index not found. Run experiments/build_ecommerce_kb_index.py first.")
        return False
    
    try:
        embeddings_array, snippets = _load_index()
        
        if embeddings_array is None:
            print("❌ FAIL: embeddings_array is None")
            return False
        
        if len(snippets) == 0:
            print("❌ FAIL: No snippets loaded")
            return False
        
        if embeddings_array.shape[0] != len(snippets):
            print(f"❌ FAIL: Embeddings ({embeddings_array.shape[0]}) and snippets ({len(snippets)}) count mismatch")
            return False
        
        print(f"✅ PASS: Loaded {len(snippets)} snippets, embedding dim={embeddings_array.shape[1]}")
        
        # Check snippet structure
        for idx, snippet in enumerate(snippets[:3], 1):  # Check first 3
            if not isinstance(snippet, PolicySnippet):
                print(f"❌ FAIL: Snippet {idx} is not a PolicySnippet instance")
                return False
            
            if not snippet.id:
                print(f"❌ FAIL: Snippet {idx} missing id")
                return False
            
            if not snippet.source:
                print(f"❌ FAIL: Snippet {idx} missing source")
                return False
            
            if not snippet.text:
                print(f"❌ FAIL: Snippet {idx} missing text")
                return False
            
            print(f"  Snippet {idx}: [{snippet.source}] {snippet.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieve_different_queries():
    """Test retrieval with different query types."""
    print("\n" + "=" * 80)
    print("Test 3: Different query types")
    print("=" * 80)
    
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        print("❌ SKIP: Index not found. Run experiments/build_ecommerce_kb_index.py first.")
        return False
    
    test_queries = [
        "return policy 30 days",
        "refund amount damaged",
        "shipping cost refund",
    ]
    
    all_passed = True
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = retrieve_policy_snippets(query, k=1)
            if len(results) > 0:
                print(f"  ✅ Retrieved {len(results)} snippet(s)")
                print(f"     [{results[0].source}] {results[0].text[:60]}...")
            else:
                print(f"  ⚠️  No results (may be acceptable)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("=" * 80)
    print("Ecommerce RAG Retriever Simple Tests")
    print("=" * 80)
    
    results = []
    
    results.append(("Basic retrieval", test_retrieve_policy_snippets_basic()))
    results.append(("Index loading", test_load_index()))
    results.append(("Different queries", test_retrieve_different_queries()))
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL/SKIP"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or skipped")
        sys.exit(1)

