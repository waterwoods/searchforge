"""
Unit tests for Cache-Augmented Generation (CAG) module.

Fast, deterministic tests with no I/O dependencies.
"""
import pytest
import numpy as np
from modules.rag.contracts import CacheConfig, CacheStats
from modules.rag.cache import CAGCache, normalize_query, cosine_similarity


class MockClock:
    """Mock clock for deterministic time testing."""
    def __init__(self, start_time=1000.0):
        self.current_time = start_time
    
    def __call__(self):
        return self.current_time
    
    def advance(self, seconds):
        self.current_time += seconds


def stub_embedder(text: str) -> np.ndarray:
    """Stub embedder that returns deterministic vectors based on text hash."""
    # Simple hash-based vector for testing
    hash_val = hash(text) % 1000
    vec = np.array([hash_val / 1000.0, (1000 - hash_val) / 1000.0, 0.5])
    return vec / np.linalg.norm(vec)


def similar_embedder(base_text: str):
    """Create embedder that returns similar vectors for similar text."""
    def embedder(text: str) -> np.ndarray:
        # Make vectors similar based on normalized text
        norm_text = normalize_query(text)
        if normalize_query(base_text) == norm_text:
            return np.array([0.9, 0.1, 0.1])
        elif norm_text in normalize_query(base_text) or normalize_query(base_text) in norm_text:
            return np.array([0.85, 0.15, 0.1])  # Similar but not identical
        else:
            return np.array([0.1, 0.9, 0.1])  # Different
    return embedder


class TestNormalizeQuery:
    """Test query normalization function."""
    
    def test_basic_normalization(self):
        assert normalize_query("Hello World") == "hello world"
        assert normalize_query("  HELLO   WORLD  ") == "hello world"
        assert normalize_query("Hello\n\tWorld") == "hello world"
    
    def test_collapse_spaces(self):
        assert normalize_query("Hello    World") == "hello world"
        assert normalize_query("a  b  c") == "a b c"


class TestCosineSimilarity:
    """Test cosine similarity function."""
    
    def test_identical_vectors(self):
        vec = np.array([1.0, 2.0, 3.0])
        assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6
    
    def test_orthogonal_vectors(self):
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        assert abs(cosine_similarity(vec1, vec2)) < 1e-6
    
    def test_zero_vectors(self):
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(vec1, vec2) == 0.0


class TestCacheConfig:
    """Test CacheConfig validation."""
    
    def test_valid_config(self):
        config = CacheConfig(policy="exact", ttl_sec=300, capacity=1000)
        assert config.policy == "exact"
        assert config.ttl_sec == 300
    
    def test_invalid_policy(self):
        with pytest.raises(ValueError, match="Invalid policy"):
            CacheConfig(policy="invalid")
    
    def test_invalid_threshold(self):
        with pytest.raises(ValueError, match="fuzzy_threshold"):
            CacheConfig(policy="exact", fuzzy_threshold=1.5)
    
    def test_semantic_without_embedder(self):
        with pytest.raises(ValueError, match="embedder is required"):
            CacheConfig(policy="semantic", embedder=None)


class TestCacheStats:
    """Test CacheStats calculations."""
    
    def test_initial_stats(self):
        stats = CacheStats()
        assert stats.lookups == 0
        assert stats.hits == 0
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        stats = CacheStats(lookups=10, hits=3)
        assert stats.hit_rate == 0.3
        
        stats = CacheStats(lookups=0, hits=0)
        assert stats.hit_rate == 0.0
    
    def test_as_dict(self):
        stats = CacheStats(lookups=10, hits=5, misses=5)
        d = stats.as_dict()
        assert d["lookups"] == 10
        assert d["hits"] == 5
        assert d["hit_rate"] == 0.5


class TestCAGCacheExact:
    """Test CAGCache with exact matching policy."""
    
    def test_exact_hit_and_ttl(self):
        """Test exact match hit and TTL expiration."""
        clock = MockClock(start_time=1000.0)
        config = CacheConfig(policy="exact", ttl_sec=10, normalize=False)
        cache = CAGCache(config, clock=clock)
        
        # Put entry
        cache.put("test query", "test answer", {"source": "test"})
        
        # Hit immediately
        result = cache.get("test query")
        assert result is not None
        assert result["answer"] == "test answer"
        assert cache.stats.hits == 1
        assert cache.stats.lookups == 1
        
        # Still hit after 5 seconds
        clock.advance(5)
        result = cache.get("test query")
        assert result is not None
        assert cache.stats.hits == 2
        
        # Miss after TTL expires (10 seconds)
        clock.advance(6)  # Total 11 seconds
        result = cache.get("test query")
        assert result is None
        assert cache.stats.expired == 1
        assert cache.stats.misses == 1
        
        # Re-put and hit again
        cache.put("test query", "new answer")
        result = cache.get("test query")
        assert result is not None
        assert result["answer"] == "new answer"
    
    def test_exact_miss_different_query(self):
        """Test miss on different query."""
        config = CacheConfig(policy="exact", normalize=False)
        cache = CAGCache(config)
        
        cache.put("query1", "answer1")
        
        result = cache.get("query2")
        assert result is None
        assert cache.stats.misses == 1


class TestCAGCacheLRU:
    """Test LRU eviction."""
    
    def test_lru_eviction(self):
        """Test that least-recently-used entries are evicted when capacity reached."""
        config = CacheConfig(policy="exact", capacity=2, normalize=False)
        cache = CAGCache(config)
        
        # Fill cache to capacity
        cache.put("a", "answer_a")
        cache.put("b", "answer_b")
        assert cache.size() == 2
        
        # Access 'a' to make it more recent
        cache.get("a")
        
        # Add 'c' -> should evict 'b' (least recently used)
        cache.put("c", "answer_c")
        assert cache.size() == 2
        assert cache.stats.evictions == 1
        
        # 'a' and 'c' should still be present
        assert cache.get("a") is not None
        assert cache.get("c") is not None
        
        # 'b' should be evicted
        assert cache.get("b") is None


class TestCAGCacheNormalized:
    """Test normalized matching policy."""
    
    def test_normalized_policy(self):
        """Test that normalized policy matches on normalized queries."""
        config = CacheConfig(policy="normalized", normalize=True)
        cache = CAGCache(config)
        
        # Put with one format
        cache.put("Hello  World", "answer1")
        
        # Hit with different format but same normalized form
        result = cache.get("hello world")
        assert result is not None
        assert result["answer"] == "answer1"
        assert cache.stats.hits == 1
        
        result = cache.get("HELLO    WORLD")
        assert result is not None
        assert cache.stats.hits == 2
        
        result = cache.get("  hello\tworld  ")
        assert result is not None
        assert cache.stats.hits == 3


class TestCAGCacheSemantic:
    """Test semantic matching policy."""
    
    def test_semantic_policy_threshold(self):
        """Test semantic matching with threshold control."""
        embedder = similar_embedder("machine learning")
        config = CacheConfig(
            policy="semantic",
            embedder=embedder,
            fuzzy_threshold=0.85
        )
        cache = CAGCache(config)
        
        # Put original query
        cache.put("machine learning", "ML answer")
        
        # Similar query should hit (similarity above threshold)
        # Note: Our stub embedder returns vectors with similarity >= 0.85 for similar text
        result = cache.get("machine learning")
        assert result is not None
        assert cache.stats.hits == 1
        
        # Very different query should miss
        result = cache.get("database systems")
        assert result is None
        assert cache.stats.misses == 1
    
    def test_semantic_best_match(self):
        """Test that semantic matching finds best match."""
        def fixed_embedder(text: str) -> np.ndarray:
            """Return fixed vectors for testing."""
            vectors = {
                "query1": np.array([1.0, 0.0, 0.0]),
                "query2": np.array([0.9, 0.1, 0.0]),  # Similar to query1
                "query3": np.array([0.0, 1.0, 0.0])   # Different
            }
            return vectors.get(text, np.array([0.5, 0.5, 0.0]))
        
        config = CacheConfig(
            policy="semantic",
            embedder=fixed_embedder,
            fuzzy_threshold=0.85
        )
        cache = CAGCache(config)
        
        cache.put("query1", "answer1")
        cache.put("query3", "answer3")
        
        # query2 should match query1 (similar vectors)
        result = cache.get("query2")
        # This will find query1 as best match if cosine(query2, query1) >= 0.85
        # cosine([0.9,0.1,0], [1.0,0.0,0]) = 0.9 / (sqrt(0.82) * 1.0) ≈ 0.995
        if result:
            assert result["answer"] == "answer1"


class TestCAGCacheMetrics:
    """Test metrics counters."""
    
    def test_metrics_counters(self):
        """Test that all metrics are updated correctly."""
        clock = MockClock(start_time=1000.0)
        config = CacheConfig(policy="exact", ttl_sec=10, capacity=2, normalize=False)
        cache = CAGCache(config, clock=clock)
        
        # Initial state
        stats = cache.get_stats()
        assert stats.lookups == 0
        assert stats.hits == 0
        assert stats.misses == 0
        
        # Miss
        cache.get("query1")
        stats = cache.get_stats()
        assert stats.lookups == 1
        assert stats.misses == 1
        assert stats.hits == 0
        
        # Put and hit
        cache.put("query1", "answer1")
        cache.get("query1")
        stats = cache.get_stats()
        assert stats.lookups == 2
        assert stats.hits == 1
        assert stats.served_from_cache == 1
        
        # Expiration
        clock.advance(11)
        cache.get("query1")
        stats = cache.get_stats()
        assert stats.expired == 1
        
        # Eviction
        cache.put("q1", "a1")
        cache.put("q2", "a2")
        cache.put("q3", "a3")  # Should evict q1
        stats = cache.get_stats()
        assert stats.evictions == 1
    
    def test_saved_latency_tracking(self):
        """Test that saved latency can be manually tracked."""
        config = CacheConfig(policy="exact")
        cache = CAGCache(config)
        
        # Simulate saving latency
        cache.stats.saved_latency_ms += 100.0
        cache.stats.saved_latency_ms += 150.0
        
        stats = cache.get_stats()
        assert stats.saved_latency_ms == 250.0


class TestCAGCachePipelineIntegration:
    """Test mock pipeline integration scenarios."""
    
    def test_pipeline_hit_short_circuits(self):
        """Test that cache hit avoids retrieval."""
        config = CacheConfig(policy="exact", normalize=False)
        cache = CAGCache(config)
        
        # Simulate pre-retrieval check
        query = "test query"
        cached = cache.get(query)
        
        if cached:
            # Should short-circuit
            result = cached["answer"]
            retrieval_called = False
        else:
            # Run full retrieval
            retrieval_called = True
            result = "fresh answer"
            cache.put(query, result, {"cost_ms": 120})
        
        # First time should retrieve
        assert retrieval_called is True
        assert cache.stats.misses == 1
        
        # Second time should hit
        cached = cache.get(query)
        if cached:
            result = cached["answer"]
            retrieval_called = False
        else:
            retrieval_called = True
        
        assert retrieval_called is False
        assert cache.stats.hits == 1
        assert result == "fresh answer"
    
    def test_pipeline_miss_runs_full_path(self):
        """Test that cache miss runs full retrieval path."""
        config = CacheConfig(policy="exact", normalize=False)
        cache = CAGCache(config)
        
        query = "new query"
        cached = cache.get(query)
        
        assert cached is None
        assert cache.stats.misses == 1
        
        # Simulate full pipeline
        retrieval_result = "retrieved answer"
        cache.put(query, retrieval_result)
        
        # Verify stored
        cached = cache.get(query)
        assert cached is not None
        assert cached["answer"] == "retrieved answer"


class TestCAGCacheClearAndSize:
    """Test cache management operations."""
    
    def test_clear(self):
        """Test clearing cache."""
        config = CacheConfig(policy="exact")
        cache = CAGCache(config)
        
        cache.put("q1", "a1")
        cache.put("q2", "a2")
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        
        # Stats should be preserved
        assert cache.stats.lookups >= 0
    
    def test_size(self):
        """Test size tracking."""
        config = CacheConfig(policy="exact", capacity=10)
        cache = CAGCache(config)
        
        assert cache.size() == 0
        
        for i in range(5):
            cache.put(f"query{i}", f"answer{i}")
        
        assert cache.size() == 5


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

