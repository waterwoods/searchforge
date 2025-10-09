"""
Basic unit tests for rerankers module.

Tests reranking logic, factory creation, and error handling using fake implementations
to avoid dependency on external models.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from modules.types import Document, ScoredDocument
from modules.rerankers.base import AbstractReranker
from modules.rerankers.factory import create_reranker
from modules.rerankers.simple_ce import CrossEncoderReranker


class FakeCrossEncoder:
    """Fake CrossEncoder for testing without real model dependencies."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def predict(self, pairs: List[tuple], batch_size: int = 16) -> List[float]:
        """Return fake scores based on text length and query match."""
        query, _ = pairs[0] if pairs else ("", "")
        scores = []
        for _, text in pairs:
            # Simple scoring: longer text gets higher score, with some variation
            base_score = len(text) * 0.1
            # Add some variation based on text content
            if "important" in text.lower():
                base_score += 0.5
            if query.lower() in text.lower():
                base_score += 0.3
            scores.append(base_score)
        return scores


class TestCrossEncoderReranker:
    """Test CrossEncoderReranker with fake model."""
    
    def setup_method(self):
        """Setup test data."""
        self.docs = [
            Document(id="1", text="short text"),
            Document(id="2", text="medium length text with important content"),
            Document(id="3", text="very long text that should score higher than others"),
            Document(id="4", text="another medium text"),
        ]
        self.query = "test query"
    
    @patch('sentence_transformers.CrossEncoder')
    def test_rerank_basic_functionality(self, mock_cross_encoder):
        """Test basic reranking functionality."""
        # Setup mock
        mock_cross_encoder.return_value = FakeCrossEncoder("fake-model")
        
        reranker = CrossEncoderReranker(model_name="fake-model")
        result = reranker.rerank(self.query, self.docs, top_k=3)
        
        # Verify results
        assert len(result) == 3  # top_k=3
        assert all(isinstance(item, ScoredDocument) for item in result)
        assert all(item.document in self.docs for item in result)
        
        # Verify sorting (should be in descending order)
        scores = [item.score for item in result]
        assert scores == sorted(scores, reverse=True)
    
    @patch('sentence_transformers.CrossEncoder')
    def test_rerank_empty_docs(self, mock_cross_encoder):
        """Test reranking with empty document list."""
        mock_cross_encoder.return_value = FakeCrossEncoder("fake-model")
        
        reranker = CrossEncoderReranker()
        result = reranker.rerank(self.query, [], top_k=10)
        
        assert result == []
    
    @patch('sentence_transformers.CrossEncoder')
    def test_rerank_top_k_larger_than_docs(self, mock_cross_encoder):
        """Test when top_k is larger than available documents."""
        mock_cross_encoder.return_value = FakeCrossEncoder("fake-model")
        
        reranker = CrossEncoderReranker()
        result = reranker.rerank(self.query, self.docs[:2], top_k=10)
        
        assert len(result) == 2  # Should return all available docs
    
    @patch('sentence_transformers.CrossEncoder')
    def test_rerank_max_pairs_limit(self, mock_cross_encoder):
        """Test max_pairs parameter limits the number of documents processed."""
        mock_cross_encoder.return_value = FakeCrossEncoder("fake-model")
        
        # Create many documents
        many_docs = [Document(id=str(i), text=f"text {i}") for i in range(100)]
        
        reranker = CrossEncoderReranker(max_pairs=5)
        result = reranker.rerank(self.query, many_docs, top_k=10)
        
        # Should only process first 5 documents due to max_pairs
        assert len(result) <= 5
    
    def test_reranker_name(self):
        """Test reranker name attribute."""
        reranker = CrossEncoderReranker()
        assert reranker.name == "cross_encoder"
    
    def test_reranker_initialization(self):
        """Test reranker initialization with custom parameters."""
        reranker = CrossEncoderReranker(
            model_name="custom-model",
            batch_size=32,
            max_pairs=100
        )
        
        assert reranker.model_name == "custom-model"
        assert reranker.batch_size == 32
        assert reranker.max_pairs == 100


class TestRerankerFactory:
    """Test reranker factory functionality."""
    
    def test_create_reranker_none_config(self):
        """Test factory with None config returns None."""
        result = create_reranker(None)
        assert result is None
    
    def test_create_reranker_empty_config(self):
        """Test factory with empty config returns None."""
        result = create_reranker({})
        assert result is None
    
    def test_create_reranker_none_type(self):
        """Test factory with type='none' returns None."""
        configs = [
            {"type": "none"},
            {"type": "off"},
            {"type": "false"},
            {"type": "NONE"},
        ]
        
        for config in configs:
            result = create_reranker(config)
            assert result is None
    
    @patch('sentence_transformers.CrossEncoder')
    def test_create_reranker_cross_encoder(self, mock_cross_encoder):
        """Test factory creates CrossEncoderReranker correctly."""
        mock_cross_encoder.return_value = FakeCrossEncoder("test-model")
        
        config = {
            "type": "cross_encoder",
            "params": {
                "model_name": "test-model",
                "batch_size": 32,
                "max_pairs": 50
            }
        }
        
        result = create_reranker(config)
        
        assert isinstance(result, CrossEncoderReranker)
        assert result.model_name == "test-model"
        assert result.batch_size == 32
        assert result.max_pairs == 50
    
    @patch('sentence_transformers.CrossEncoder')
    def test_create_reranker_ce_alias(self, mock_cross_encoder):
        """Test factory accepts 'ce' as alias for cross_encoder."""
        mock_cross_encoder.return_value = FakeCrossEncoder("test-model")
        
        config = {"type": "ce", "params": {"model_name": "test-model"}}
        result = create_reranker(config)
        
        assert isinstance(result, CrossEncoderReranker)
    
    def test_create_reranker_unknown_type(self):
        """Test factory raises ValueError for unknown types."""
        config = {"type": "unknown_reranker"}
        
        with pytest.raises(ValueError, match="Unsupported reranker type: unknown_reranker"):
            create_reranker(config)
    
    @patch('sentence_transformers.CrossEncoder')
    def test_create_reranker_no_params(self, mock_cross_encoder):
        """Test factory with no params uses defaults."""
        mock_cross_encoder.return_value = FakeCrossEncoder("default-model")
        
        config = {"type": "cross_encoder"}
        result = create_reranker(config)
        
        assert isinstance(result, CrossEncoderReranker)
        # Should use default values
        assert result.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert result.batch_size == 16
        assert result.max_pairs == 200


class TestRerankerIntegration:
    """Integration tests for reranker functionality."""
    
    @patch('sentence_transformers.CrossEncoder')
    def test_end_to_end_reranking(self, mock_cross_encoder):
        """Test complete reranking pipeline."""
        mock_cross_encoder.return_value = FakeCrossEncoder("test-model")
        
        # Create documents with different characteristics
        docs = [
            Document(id="1", text="short"),
            Document(id="2", text="medium length text"),
            Document(id="3", text="very long text that should score highest"),
            Document(id="4", text="another medium text with important content"),
        ]
        
        # Create reranker via factory
        config = {
            "type": "cross_encoder",
            "params": {
                "model_name": "test-model",
                "max_pairs": 10
            }
        }
        reranker = create_reranker(config)
        
        # Perform reranking
        query = "test query"
        result = reranker.rerank(query, docs, top_k=2)
        
        # Verify results
        assert len(result) == 2
        assert all(isinstance(item, ScoredDocument) for item in result)
        assert all(item.explanation == "ce_score" for item in result)
        
        # Verify sorting
        scores = [item.score for item in result]
        assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
