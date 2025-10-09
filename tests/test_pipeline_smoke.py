import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline
from modules.types import Document, ScoredDocument


def test_pipeline_with_reranker():
    """Test the search pipeline with reranker integration using mocked vector search."""
    
    # Mock configuration
    config = {
        "retriever": {
            "type": "qdrant",
            "top_k": 20
        },
        "reranker": {
            "type": "cross_encoder",
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "top_k": 50
        }
    }
    
    # Create mock documents
    mock_docs = [
        Document(id="1", text="Machine learning is a subset of artificial intelligence", metadata={"topic": "AI"}),
        Document(id="2", text="Deep learning uses neural networks with multiple layers", metadata={"topic": "AI"}),
        Document(id="3", text="Natural language processing helps computers understand text", metadata={"topic": "NLP"}),
        Document(id="4", text="Computer vision enables machines to interpret visual information", metadata={"topic": "CV"}),
        Document(id="5", text="Data science combines statistics and programming", metadata={"topic": "Data"}),
    ]
    
    # Mock ScoredDocument results from vector search
    mock_results = [
        ScoredDocument(document=mock_docs[0], score=0.95, explanation="Vector search result #1"),
        ScoredDocument(document=mock_docs[1], score=0.88, explanation="Vector search result #2"),
        ScoredDocument(document=mock_docs[2], score=0.82, explanation="Vector search result #3"),
        ScoredDocument(document=mock_docs[3], score=0.75, explanation="Vector search result #4"),
        ScoredDocument(document=mock_docs[4], score=0.68, explanation="Vector search result #5"),
    ]
    
    # Create pipeline with mocked vector search
    pipeline = SearchPipeline(config)
    
    # Mock the vector search method
    with patch.object(pipeline.vector_search, 'vector_search', return_value=mock_results):
        query = "What is machine learning?"
        results = pipeline.search(query)
        
        assert results, "No results returned"
        print(f"\nFound {len(results)} results:")
        for i, r in enumerate(results[:5]):
            print(f"{i+1}. ID: {r.document.id}, Score: {r.score:.3f}, Text: {r.document.text[:60]}...")
        
        # Verify that we have ScoredDocument objects
        assert all(hasattr(r, 'document') and hasattr(r, 'score') for r in results), "Results should be ScoredDocument objects"
        
        # Verify that scores are reasonable (cross-encoder scores can be negative)
        assert all(isinstance(r.score, (int, float)) for r in results), "Scores should be numeric"
        
        print(f"\nTest passed! Pipeline with reranker is working correctly.")


def test_pipeline_without_reranker():
    """Test the search pipeline without reranker."""
    
    # Mock configuration without reranker
    config = {
        "retriever": {
            "type": "qdrant",
            "top_k": 20
        }
    }
    
    # Create mock documents
    mock_docs = [
        Document(id="1", text="Machine learning is a subset of artificial intelligence", metadata={"topic": "AI"}),
        Document(id="2", text="Deep learning uses neural networks with multiple layers", metadata={"topic": "AI"}),
    ]
    
    # Mock ScoredDocument results from vector search
    mock_results = [
        ScoredDocument(document=mock_docs[0], score=0.95, explanation="Vector search result #1"),
        ScoredDocument(document=mock_docs[1], score=0.88, explanation="Vector search result #2"),
    ]
    
    # Create pipeline with mocked vector search
    pipeline = SearchPipeline(config)
    
    # Mock the vector search method
    with patch.object(pipeline.vector_search, 'vector_search', return_value=mock_results):
        query = "What is machine learning?"
        results = pipeline.search(query)
        
        assert results, "No results returned"
        assert len(results) == 2, "Should return 2 results"
        
        # Verify that reranker is None
        assert pipeline.reranker is None, "Reranker should be None when not configured"
        
        print(f"\nTest passed! Pipeline without reranker is working correctly.")


if __name__ == "__main__":
    test_pipeline_with_reranker()
    test_pipeline_without_reranker()
