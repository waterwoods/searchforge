"""
test_ecommerce_rag_retriever.py - Tests for ecommerce RAG retriever

Simple tests to verify that the RAG retriever can load index and retrieve policy snippets.
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ecommerce.ecommerce_rag_retriever import (
    retrieve_policy_snippets,
    PolicySnippet,
    _load_index,
)


def test_retrieve_policy_snippets_basic():
    """
    Test that retrieve_policy_snippets returns non-empty results for a relevant query.
    
    Note: This test requires the index to be built first.
    Run: python experiments/build_ecommerce_kb_index.py
    """
    # Skip if index doesn't exist
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        pytest.skip("Index not found. Run experiments/build_ecommerce_kb_index.py first.")
    
    # Test query
    query = "damaged item refund"
    results = retrieve_policy_snippets(query, k=2)
    
    # Assertions
    assert isinstance(results, list)
    assert len(results) > 0, "Should return at least one snippet"
    
    # Check structure
    for snippet in results:
        assert isinstance(snippet, PolicySnippet)
        assert snippet.id is not None
        assert snippet.source is not None
        assert snippet.text is not None
        assert len(snippet.text) > 0


def test_retrieve_policy_snippets_empty_query():
    """Test that retrieve_policy_snippets handles edge cases gracefully."""
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        pytest.skip("Index not found. Run experiments/build_ecommerce_kb_index.py first.")
    
    # Empty query should still work (may return less relevant results)
    results = retrieve_policy_snippets("", k=1)
    # Should not crash, but may return empty list or results
    assert isinstance(results, list)


def test_load_index():
    """Test that _load_index can load the index files."""
    index_meta_path = project_root / "data" / "ecommerce_kb_index" / "index_meta.json"
    if not index_meta_path.exists():
        pytest.skip("Index not found. Run experiments/build_ecommerce_kb_index.py first.")
    
    embeddings_array, snippets = _load_index()
    
    assert embeddings_array is not None
    assert len(snippets) > 0
    assert embeddings_array.shape[0] == len(snippets), "Embeddings and metadata should match in length"
    
    # Check snippet structure
    for snippet in snippets[:3]:  # Check first 3
        assert isinstance(snippet, PolicySnippet)
        assert snippet.id is not None
        assert snippet.source is not None
        assert snippet.text is not None

