"""
Unit tests for hybrid fusion functionality.

Tests the hybrid fusion algorithm with various scenarios including
boundary cases and score normalization.
"""

import unittest
from typing import List
from modules.search.hybrid import fuse, normalize_scores, get_fusion_stats
from modules.types import Document, ScoredDocument


class TestHybridFusion(unittest.TestCase):
    """Test cases for hybrid fusion functionality."""
    
    def setUp(self):
        """Set up test documents and scored results."""
        self.doc1 = Document(id="1", text="Machine learning is fascinating", metadata={})
        self.doc2 = Document(id="2", text="Deep learning and neural networks", metadata={})
        self.doc3 = Document(id="3", text="Natural language processing techniques", metadata={})
        self.doc4 = Document(id="4", text="Computer vision and image recognition", metadata={})
        
        # Create sample scored documents
        self.vector_hits = [
            ScoredDocument(document=self.doc1, score=0.9, explanation="Vector score"),
            ScoredDocument(document=self.doc2, score=0.8, explanation="Vector score"),
            ScoredDocument(document=self.doc3, score=0.7, explanation="Vector score"),
        ]
        
        self.bm25_hits = [
            ScoredDocument(document=self.doc2, score=0.85, explanation="BM25 score"),
            ScoredDocument(document=self.doc3, score=0.75, explanation="BM25 score"),
            ScoredDocument(document=self.doc4, score=0.65, explanation="BM25 score"),
        ]
    
    def test_normalize_scores(self):
        """Test score normalization functionality."""
        # Test with different scores
        scored_docs = [
            ScoredDocument(document=self.doc1, score=0.1, explanation="test"),
            ScoredDocument(document=self.doc2, score=0.5, explanation="test"),
            ScoredDocument(document=self.doc3, score=0.9, explanation="test"),
        ]
        
        normalized = normalize_scores(scored_docs)
        
        # Check that scores are normalized to [0, 1] range
        self.assertEqual(len(normalized), 3)
        self.assertEqual(normalized[0].score, 0.0)  # min score
        self.assertEqual(normalized[1].score, 0.5)  # middle score
        self.assertEqual(normalized[2].score, 1.0)  # max score
        
        # Check that documents are preserved
        self.assertEqual(normalized[0].document.id, "1")
        self.assertEqual(normalized[1].document.id, "2")
        self.assertEqual(normalized[2].document.id, "3")
    
    def test_normalize_scores_same_values(self):
        """Test normalization when all scores are the same."""
        scored_docs = [
            ScoredDocument(document=self.doc1, score=0.5, explanation="test"),
            ScoredDocument(document=self.doc2, score=0.5, explanation="test"),
        ]
        
        normalized = normalize_scores(scored_docs)
        
        # When all scores are the same, should be normalized to 1.0
        self.assertEqual(normalized[0].score, 1.0)
        self.assertEqual(normalized[1].score, 1.0)
    
    def test_normalize_scores_empty_list(self):
        """Test normalization with empty list."""
        normalized = normalize_scores([])
        self.assertEqual(normalized, [])
    
    def test_fuse_alpha_boundary_cases(self):
        """Test fusion with alpha boundary values (0.0 and 1.0)."""
        # Test alpha = 0.0 (pure BM25)
        pure_bm25 = fuse(self.vector_hits, self.bm25_hits, alpha=0.0, top_k=5)
        self.assertEqual(len(pure_bm25), 4)  # Should have 4 unique documents (all from both lists)
        # Check that BM25-only documents appear
        doc_ids = [doc.document.id for doc in pure_bm25]
        self.assertIn("4", doc_ids)  # doc4 only in BM25 results
        
        # Test alpha = 1.0 (pure vector)
        pure_vector = fuse(self.vector_hits, self.bm25_hits, alpha=1.0, top_k=5)
        self.assertEqual(len(pure_vector), 4)  # Should have 4 unique documents (all from both lists)
        # Check that vector-only documents appear
        doc_ids = [doc.document.id for doc in pure_vector]
        self.assertIn("1", doc_ids)  # doc1 only in vector results
    
    def test_fuse_alpha_0_5(self):
        """Test fusion with alpha = 0.5 (equal weighting)."""
        fused = fuse(self.vector_hits, self.bm25_hits, alpha=0.5, top_k=5)
        
        # Should have 4 unique documents (doc1, doc2, doc3, doc4)
        self.assertEqual(len(fused), 4)
        
        # Check that all documents are present
        doc_ids = [doc.document.id for doc in fused]
        expected_ids = ["1", "2", "3", "4"]
        self.assertEqual(set(doc_ids), set(expected_ids))
        
        # Check that results are sorted by score (descending)
        scores = [doc.score for doc in fused]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_fuse_top_k_limit(self):
        """Test that fusion respects top_k limit."""
        fused = fuse(self.vector_hits, self.bm25_hits, alpha=0.6, top_k=2)
        
        # Should return only top 2 results
        self.assertEqual(len(fused), 2)
        
        # Results should be sorted by score
        scores = [doc.score for doc in fused]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_fuse_invalid_alpha(self):
        """Test that invalid alpha values raise ValueError."""
        with self.assertRaises(ValueError):
            fuse(self.vector_hits, self.bm25_hits, alpha=-0.1, top_k=5)
        
        with self.assertRaises(ValueError):
            fuse(self.vector_hits, self.bm25_hits, alpha=1.1, top_k=5)
    
    def test_fuse_empty_inputs(self):
        """Test fusion with empty input lists."""
        # Empty vector results
        fused = fuse([], self.bm25_hits, alpha=0.6, top_k=5)
        self.assertEqual(len(fused), 3)  # Should return BM25 results
        
        # Empty BM25 results
        fused = fuse(self.vector_hits, [], alpha=0.6, top_k=5)
        self.assertEqual(len(fused), 3)  # Should return vector results
        
        # Both empty
        fused = fuse([], [], alpha=0.6, top_k=5)
        self.assertEqual(len(fused), 0)
    
    def test_fuse_score_ordering(self):
        """Test that fusion maintains proper score ordering."""
        # Create predictable test data
        doc1 = Document(id="1", text="test", metadata={})
        doc2 = Document(id="2", text="test", metadata={})
        
        # Vector gives doc1 higher score, BM25 gives doc2 higher score
        vector_hits = [
            ScoredDocument(document=doc1, score=0.9, explanation="vector"),
            ScoredDocument(document=doc2, score=0.1, explanation="vector"),
        ]
        
        bm25_hits = [
            ScoredDocument(document=doc1, score=0.1, explanation="bm25"),
            ScoredDocument(document=doc2, score=0.9, explanation="bm25"),
        ]
        
        # With alpha=0.5, both should get similar scores
        fused = fuse(vector_hits, bm25_hits, alpha=0.5, top_k=2)
        
        self.assertEqual(len(fused), 2)
        # Both documents should have similar fused scores
        score1 = next(doc.score for doc in fused if doc.document.id == "1")
        score2 = next(doc.score for doc in fused if doc.document.id == "2")
        
        # Scores should be close to each other (around 0.5)
        self.assertAlmostEqual(score1, score2, places=1)
    
    def test_get_fusion_stats(self):
        """Test fusion statistics calculation."""
        stats = get_fusion_stats(self.vector_hits, self.bm25_hits, [])
        
        self.assertEqual(stats["vector_results"], 3)
        self.assertEqual(stats["bm25_results"], 3)
        self.assertEqual(stats["vector_bm25_overlap"], 2)  # doc2 and doc3
        self.assertEqual(stats["vector_only"], 1)  # doc1
        self.assertEqual(stats["bm25_only"], 1)  # doc4
        self.assertEqual(stats["unique_documents"], 4)
    
    def test_fusion_explanations(self):
        """Test that fusion preserves and enhances explanations."""
        fused = fuse(self.vector_hits, self.bm25_hits, alpha=0.6, top_k=5)
        
        for doc in fused:
            self.assertIn("Hybrid", doc.explanation)
            self.assertIn("α=0.6", doc.explanation)
            self.assertIn("Final:", doc.explanation)


if __name__ == '__main__':
    unittest.main()
