# Cache-Augmented Generation (CAG) Module

A plug-and-play cache for RAG pipelines with multiple matching strategies, TTL-based freshness, LRU capacity management, and comprehensive metrics.

## Features

- **Multiple Matching Policies**:
  - `exact`: Exact string matching (optionally with normalization)
  - `normalized`: Lowercase, strip, collapse whitespace
  - `semantic`: Cosine similarity with configurable threshold

- **TTL-Based Freshness**: Automatic expiration of stale entries
- **LRU Capacity Management**: Automatic eviction when capacity is reached
- **Comprehensive Metrics**: Hit rate, saved latency, evictions, expirations

## Quick Start

### Basic Usage

```python
from modules.rag.contracts import CacheConfig
from modules.rag.cache import CAGCache

# Create cache with exact matching
config = CacheConfig(
    policy="exact",
    ttl_sec=600,        # 10 minutes
    capacity=10_000     # Max 10k entries
)
cache = CAGCache(config)

# Use in your pipeline
cached = cache.get(query)
if cached:
    return cached["answer"]
else:
    answer = your_retrieval_pipeline(query)
    cache.put(query, answer, {"cost_ms": 120})
    return answer

# Check metrics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Saved latency: {stats.saved_latency_ms:.1f}ms")
```

### Pipeline Integration

Add cache configuration to your pipeline config:

```yaml
cache:
  enabled: true
  policy: "normalized"  # or "exact", "semantic"
  ttl_sec: 600
  capacity: 10000
  normalize: true
  fuzzy_threshold: 0.85  # for semantic policy only
```

Or use environment variables:

```bash
export USE_CACHE=1
export CACHE_POLICY=normalized
export CACHE_TTL_SEC=600
export CACHE_CAPACITY=10000
export CACHE_FUZZY_THRESHOLD=0.85
```

## Configuration

### CacheConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `policy` | str | "exact" | Matching policy: "exact", "normalized", or "semantic" |
| `ttl_sec` | int | 600 | Time-to-live in seconds |
| `capacity` | int | 10000 | Maximum cache entries (LRU eviction) |
| `fuzzy_threshold` | float | 0.85 | Similarity threshold for semantic matching [0,1] |
| `normalize` | bool | True | Normalize queries (lowercase, strip, collapse spaces) |
| `embedder` | Callable | None | Function to convert string to vector (required for semantic) |

### Metrics (CacheStats)

- `lookups`: Total cache lookups
- `hits`: Cache hits
- `misses`: Cache misses
- `hit_rate`: Ratio of hits to lookups
- `evictions`: Entries evicted due to capacity
- `expired`: Entries expired due to TTL
- `served_from_cache`: Queries served from cache
- `saved_latency_ms`: Accumulated latency savings

## Evaluation

Run synthetic evaluation to validate cache performance:

```bash
python scripts/eval_cache_cag.py
```

Expected results (200 queries, 30% repeat rate):
- Exact/Normalized: ~30% hit rate, ~30% mean latency improvement
- Semantic: Higher hit rate with appropriate embedder

Results saved to: `reports/rag/cache_eval.json`

## Testing

Run unit tests (< 1 second):

```bash
pytest tests/test_cache_cag.py -v
pytest tests/test_cache_pipeline_integration.py -v
```

All tests should pass with 100% coverage of core cache functionality.

## Implementation Notes

### Matching Policies

1. **Exact**: Simple string matching. Fast but strict.
   - Use when queries are identical (e.g., API calls)
   - Set `normalize=True` to handle case/whitespace variations

2. **Normalized**: Case-insensitive with whitespace normalization.
   - Use for user-facing queries with variations
   - Best balance of speed and flexibility

3. **Semantic**: Cosine similarity-based matching.
   - Use when queries have semantic overlap
   - Requires embedder function (e.g., sentence-transformers)
   - Higher hit rate but slower lookups

### Performance Characteristics

- **Lookup**: O(1) for exact/normalized, O(n) for semantic
- **Put**: O(1) amortized (with occasional LRU eviction)
- **Memory**: ~200 bytes per entry + answer size
- **Eviction**: LRU based on last_access time

### Integration Events

The pipeline emits these events when cache is enabled:

- `CACHE_HIT`: Query served from cache
- `CACHE_MISS`: Cache miss, reason=not_found/expired/threshold
- `CACHE_PUT`: Result written to cache

## Future Enhancements

- [ ] Redis/Memcached backend for distributed caching
- [ ] Bloom filter for fast negative lookups
- [ ] Adaptive TTL based on query patterns
- [ ] Cache warming from logs
- [ ] Multi-level cache hierarchy

## License

Same as parent project.

