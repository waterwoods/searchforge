"""
Data contracts for Cache-Augmented Generation (CAG) module.
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any
import numpy as np


@dataclass
class CacheConfig:
    """Configuration for CAG cache.
    
    Attributes:
        policy: Matching policy - "exact", "normalized", or "semantic"
        ttl_sec: Time-to-live in seconds for cache entries (default 600)
        capacity: Maximum number of entries in cache (LRU eviction, default 10_000)
        fuzzy_threshold: Similarity threshold for semantic matching [0,1] (default 0.85)
        normalize: Whether to normalize queries (lower, strip, collapse spaces, default True)
        embedder: Optional callable that converts string to np.ndarray for semantic keys
    """
    # [CORE: config-dataclasses] Core configuration dataclass with validation
    policy: str = "exact"  # exact, normalized, semantic
    ttl_sec: int = 600
    capacity: int = 10_000
    fuzzy_threshold: float = 0.85
    normalize: bool = True
    embedder: Optional[Callable[[str], np.ndarray]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.policy not in ["exact", "normalized", "semantic"]:
            raise ValueError(f"Invalid policy: {self.policy}. Must be one of: exact, normalized, semantic")
        if self.fuzzy_threshold < 0 or self.fuzzy_threshold > 1:
            raise ValueError(f"fuzzy_threshold must be in [0,1], got {self.fuzzy_threshold}")
        if self.policy == "semantic" and self.embedder is None:
            raise ValueError("embedder is required for semantic policy")


@dataclass
class CacheStats:
    """Statistics for cache performance.
    
    Attributes:
        lookups: Total number of cache lookups
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of entries evicted due to capacity
        expired: Number of entries expired due to TTL
        served_from_cache: Count of queries served from cache
        saved_latency_ms: Accumulated latency savings in milliseconds
    """
    # [CORE: config-dataclasses] Core statistics tracking dataclass
    lookups: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    served_from_cache: int = 0
    saved_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        return self.hits / self.lookups if self.lookups > 0 else 0.0
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for reporting."""
        # [CORE: stats-as-dict] Convert stats to dict for reporting and analysis
        return {
            "lookups": self.lookups,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "evictions": self.evictions,
            "expired": self.expired,
            "served_from_cache": self.served_from_cache,
            "saved_latency_ms": self.saved_latency_ms
        }

