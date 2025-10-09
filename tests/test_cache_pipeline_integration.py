"""
Integration test for CAG cache with SearchPipeline.

Tests that cache can be enabled and works without breaking the pipeline.
"""
import pytest
from modules.rag.contracts import CacheConfig
from modules.rag.cache import CAGCache


def test_cache_config_validation():
    """Test that cache config validates properly."""
    # Valid configs
    config = CacheConfig(policy="exact")
    assert config.policy == "exact"
    
    config = CacheConfig(policy="normalized", normalize=True)
    assert config.policy == "normalized"
    
    # Invalid config
    with pytest.raises(ValueError):
        CacheConfig(policy="invalid_policy")


def test_cache_basic_operations():
    """Test basic cache operations."""
    config = CacheConfig(policy="exact", ttl_sec=60)
    cache = CAGCache(config)
    
    # Miss
    result = cache.get("test query")
    assert result is None
    
    # Put
    cache.put("test query", "test answer", {"source": "test"})
    
    # Hit
    result = cache.get("test query")
    assert result is not None
    assert result["answer"] == "test answer"
    
    # Stats
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.lookups == 2


def test_pipeline_config_structure():
    """Test that pipeline config can include cache settings."""
    from modules.search.search_pipeline import SearchPipeline
    
    config = {
        "retriever": {"type": "vector", "top_k": 10},
        "cache": {
            "enabled": False,  # Disabled for this test
            "policy": "exact",
            "ttl_sec": 600
        }
    }
    
    # Should not raise
    pipeline = SearchPipeline(config)
    assert pipeline.cache is None  # Cache not enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

