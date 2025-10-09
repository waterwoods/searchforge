"""
Cache-Augmented Generation (CAG) module.

Provides a plug-and-play cache for RAG pipelines with multiple matching strategies,
TTL-based freshness, LRU capacity management, and comprehensive metrics.
"""
import time
import re
from collections import OrderedDict
from typing import Optional, Dict, Any, Callable
import numpy as np

from .contracts import CacheConfig, CacheStats


def normalize_query(query: str) -> str:
    """Normalize query: lowercase, strip, collapse whitespace."""
    # [CORE: normalize] Core normalization logic for consistent key generation
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)
    return query


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    # [CORE: cosine-sim] Core similarity calculation for semantic matching
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


class CAGCache:
    """Cache-Augmented Generation cache with multiple matching strategies.
    
    Supports:
    - Exact matching (optionally with normalization)
    - Normalized matching (lowercase, strip, collapse spaces)
    - Semantic matching (cosine similarity with threshold)
    - TTL-based expiration
    - LRU eviction when capacity is reached
    - Comprehensive metrics tracking
    """
    
    def __init__(self, config: CacheConfig, clock: Optional[Callable[[], float]] = None):
        """Initialize CAG cache.
        
        Args:
            config: Cache configuration
            clock: Optional clock function for testing (defaults to time.time)
        """
        self.config = config
        self.clock = clock or time.time
        self.stats = CacheStats()
        
        # Cache storage: key -> {answer, meta, ts_ms, last_access}
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # For semantic matching: key -> (embedding_vector, original_key)
        self._semantic_vectors: OrderedDict[str, tuple] = OrderedDict()
    
    def _make_key(self, query: str) -> str:
        """Generate cache key based on policy."""
        # [CORE: keying-exact] Exact key generation (no normalization)
        # [CORE: keying-normalized] Normalized key generation (lower/strip/collapse)
        if self.config.policy == "normalized" or (self.config.policy == "exact" and self.config.normalize):
            return normalize_query(query)
        return query
    
    def _find_semantic_match(self, query: str) -> Optional[str]:
        """Find semantic match for query using embedder and threshold.
        
        Args:
            query: Query string to match
            
        Returns:
            Cache key if match found, None otherwise
        """
        # [CORE: keying-semantic] Semantic key matching with cosine similarity
        if not self.config.embedder:
            return None
        
        query_vec = self.config.embedder(query)
        
        best_key = None
        best_score = -1.0
        
        for cache_key, (stored_vec, _) in self._semantic_vectors.items():
            similarity = cosine_similarity(query_vec, stored_vec)
            if similarity >= self.config.fuzzy_threshold and similarity > best_score:
                best_score = similarity
                best_key = cache_key
        
        return best_key
    
    def _evict_lru(self):
        """Evict least-recently-used entry to maintain capacity."""
        # [CORE: lru-eviction] LRU eviction when capacity limit reached
        if len(self._cache) >= self.config.capacity:
            # Remove oldest (least recently accessed) entry
            lru_key = next(iter(self._cache))
            del self._cache[lru_key]
            if lru_key in self._semantic_vectors:
                del self._semantic_vectors[lru_key]
            self.stats.evictions += 1
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result for query.
        
        Args:
            query: Query string
            
        Returns:
            Cached result dict with {answer, meta} if hit and fresh, None otherwise
        """
        # [CORE: stats-increment] Increment lookup counter for metrics tracking
        self.stats.lookups += 1
        
        # Determine cache key based on policy
        if self.config.policy == "semantic":
            cache_key = self._find_semantic_match(query)
        else:
            cache_key = self._make_key(query)
        
        if cache_key is None or cache_key not in self._cache:
            self.stats.misses += 1
            return None
        
        entry = self._cache[cache_key]
        current_time_ms = self.clock() * 1000
        
        # [CORE: ttl-expiry-check] Check if entry has expired based on TTL
        age_ms = current_time_ms - entry["ts_ms"]
        if age_ms > self.config.ttl_sec * 1000:
            # Expired
            del self._cache[cache_key]
            if cache_key in self._semantic_vectors:
                del self._semantic_vectors[cache_key]
            self.stats.expired += 1
            self.stats.misses += 1
            return None
        
        # Update last_access for LRU (move to end)
        self._cache.move_to_end(cache_key)
        entry["last_access"] = current_time_ms
        
        # [CORE: hit-short-circuit] Cache hit - return cached result without retrieval
        self.stats.hits += 1
        self.stats.served_from_cache += 1
        
        return {
            "answer": entry["answer"],
            "meta": entry["meta"]
        }
    
    def put(self, query: str, answer: Any, meta: Optional[Dict[str, Any]] = None):
        """Store query result in cache.
        
        Args:
            query: Query string
            answer: Answer/result to cache
            meta: Optional metadata dict (should include ts_ms, source, cost_ms)
        """
        cache_key = self._make_key(query)
        current_time_ms = self.clock() * 1000
        
        if meta is None:
            meta = {}
        
        # Ensure ts_ms is set
        if "ts_ms" not in meta:
            meta["ts_ms"] = current_time_ms
        
        # Evict if at capacity
        self._evict_lru()
        
        # Store entry
        entry = {
            "answer": answer,
            "meta": meta,
            "ts_ms": current_time_ms,
            "last_access": current_time_ms
        }
        
        self._cache[cache_key] = entry
        
        # For semantic policy, store embedding
        if self.config.policy == "semantic" and self.config.embedder:
            query_vec = self.config.embedder(query)
            self._semantic_vectors[cache_key] = (query_vec, query)
    
    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        return self.stats
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._semantic_vectors.clear()
        # Note: stats are preserved across clear
    
    def size(self) -> int:
        """Get current number of entries in cache."""
        return len(self._cache)

