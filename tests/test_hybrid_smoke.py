"""
Smoke test for hybrid search functionality.

This test creates a minimal setup to verify that hybrid fusion works correctly
with BM25Retriever and a fake vector retriever.
"""

import pytest
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.types import Document, ScoredDocument
from modules.retrievers.bm25 import BM25Retriever
from modules.search.hybrid import fuse


class FakeRetriever:
    """Simple fake retriever for testing vector search functionality."""
    
    def __init__(self, documents: List[Document]):
        self.documents = documents
    
    def search(self, query: str, top_k: int = 5) -> List[ScoredDocument]:
        """Return fake scored documents for testing."""
        # Return the first few documents with decreasing scores
        results = []
        for i, doc in enumerate(self.documents[:top_k]):
            score = 0.9 - (i * 0.1)  # Decreasing scores: 0.9, 0.8, 0.7, ...
            results.append(ScoredDocument(
                document=doc,
                score=score,
                explanation=f"Fake vector score: {score:.2f}"
            ))
        return results


def test_hybrid_smoke():
    """Smoke test for hybrid fusion functionality."""
    
    # 1. Create 3 test documents
    documents = [
        Document(id="doc1", text="usb cable", metadata={"category": "electronics"}),
        Document(id="doc2", text="wireless charger", metadata={"category": "electronics"}),
        Document(id="doc3", text="mouse", metadata={"category": "electronics"}),
    ]
    
    print(f"Created {len(documents)} test documents:")
    for doc in documents:
        print(f"  - {doc.id}: {doc.text}")
    
    # 2. Initialize BM25Retriever
    bm25_retriever = BM25Retriever()
    bm25_retriever.fit(documents)
    print(f"\nBM25Retriever initialized and fitted with {len(documents)} documents")
    
    # 3. Initialize FakeRetriever for vector search
    fake_vector_retriever = FakeRetriever(documents)
    print("FakeRetriever initialized for vector search simulation")
    
    # 4. Test search with both retrievers
    query = "usb cable"
    
    # Get BM25 results
    bm25_results = bm25_retriever.search(query, top_k=3)
    print(f"\nBM25 search for '{query}' returned {len(bm25_results)} results:")
    for i, result in enumerate(bm25_results):
        print(f"  {i+1}. {result.document.id}: score={result.score:.4f}, text='{result.document.text}'")
    
    # Get fake vector results
    vector_results = fake_vector_retriever.search(query, top_k=3)
    print(f"\nFake vector search for '{query}' returned {len(vector_results)} results:")
    for i, result in enumerate(vector_results):
        print(f"  {i+1}. {result.document.id}: score={result.score:.4f}, text='{result.document.text}'")
    
    # 5. Test hybrid fusion with alpha=0.5
    alpha = 0.5
    top_k = 5
    fused_results = fuse(vector_results, bm25_results, alpha=alpha, top_k=top_k)
    
    print(f"\nHybrid fusion (α={alpha}) returned {len(fused_results)} results:")
    
    # 6. Verify and print results
    assert len(fused_results) > 0, "Hybrid fusion should return results"
    
    # Print first two results with details
    print(f"\nFirst 2 results:")
    for i, result in enumerate(fused_results[:2]):
        print(f"  {i+1}. ID: {result.document.id}")
        print(f"     Score: {result.score:.4f}")
        print(f"     Text: {result.document.text}")
        print(f"     Explanation: {result.explanation}")
        print()
    
    # 7. Verify scores are non-empty and properly sorted
    scores = [result.score for result in fused_results]
    assert all(score is not None for score in scores), "All scores should be non-null"
    assert len(scores) > 0, "Should have at least one score"
    
    # Verify results are sorted by score (descending)
    sorted_scores = sorted(scores, reverse=True)
    assert scores == sorted_scores, f"Scores should be sorted in descending order. Got: {scores}"
    
    print(f"✅ Hybrid smoke test passed!")
    print(f"   - Result length: {len(fused_results)}")
    print(f"   - First two doc IDs: {[r.document.id for r in fused_results[:2]]}")
    print(f"   - Score range: {min(scores):.4f} to {max(scores):.4f}")
    print(f"   - All results properly sorted: ✅")


if __name__ == "__main__":
    test_hybrid_smoke()
