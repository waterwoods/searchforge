# Configuration Knowledge Base

Known risky configurations, best practices, and trade-offs for production services.

---

## [payment-service][prod] Known risky configurations

**Service**: payment-service  
**Environment**: prod  
**Last Updated**: 2024-11-15

### Retry Configuration

**Current Settings**:
```yaml
max_retries: 3
retry_backoff: [100ms, 500ms, 2000ms]
retry_jitter: true
retry_timeout: 5s
```

**Known Risks**:
- **Aggressive retry without backoff** can amplify load on payment gateway during degradation
- **No jitter** leads to thundering herd problem (all clients retry simultaneously)
- **Short timeout (< 3s)** causes premature failures for legitimate slow transactions

**Best Practices**:
- Use exponential backoff: 100ms, 500ms, 2000ms (current config is good)
- Always enable jitter to spread retry load over time
- Set timeout to 2x p99 latency (currently 5s is appropriate for p99 ~2s)
- **Never retry on 4xx errors** (validation failures) - only retry on 5xx and timeouts

**Trade-offs**:
- More aggressive retries → Higher success rate but risk amplifying failures during outages
- Conservative retries → Lower load on gateway but higher initial failure rate
- Recommendation: Current config is balanced for payment-service criticality

---

## [api-gateway][prod] Connection pool and timeout settings

**Service**: api-gateway  
**Environment**: prod  
**Last Updated**: 2024-10-30

### Database Connection Pool

**Current Settings**:
```yaml
max_connections: 200
min_idle: 50
idle_timeout: 30s
max_lifetime: 1800s
connection_timeout: 10s
validation_query: "SELECT 1"
```

**Known Risks**:
- **Small pool size (< 100)** causes connection exhaustion during traffic spikes
- **Long idle_timeout (> 5min)** prevents fast detection of database failover
- **No validation query** allows stale connections to stay in pool after DB restart
- **No max_lifetime** causes connection leaks and gradual pool degradation

**Best Practices**:
- Pool size should be 2-3x expected concurrent queries (current 200 is good for ~2500 QPS)
- Idle timeout should be < 1min to detect failovers quickly
- Always set max_lifetime to prevent connection leaks (1800s = 30min is reasonable)
- Use validation query ("SELECT 1") to verify connection health before use

**Trade-offs**:
- Larger pool → Higher memory usage but better performance under load
- Smaller idle_timeout → More connection churn but faster failover detection
- Recommendation: Current config is solid, consider increasing max_connections to 250 if QPS > 3000

### Downstream Timeout Configuration

**Current Settings**:
```yaml
search_service_timeout: 500ms
user_service_timeout: 200ms
payment_service_timeout: 3000ms
default_timeout: 1000ms
```

**Known Risks**:
- **Timeout too short** causes premature failures for legitimate slow requests
- **Timeout too long** causes request queuing and cascading failures
- **No circuit breaker** allows continuous retry of failing downstream service

**Best Practices**:
- Set timeout to 2x p99 latency of downstream service
  - search_service: p99 ~200ms → timeout 500ms ✓ (good)
  - user_service: p99 ~100ms → timeout 200ms ✓ (good)
  - payment_service: p99 ~1500ms → timeout 3000ms ✓ (good)
- Enable circuit breaker: open after 50% error rate over 10s window
- Use bulkhead pattern: limit concurrent requests per downstream service

**Trade-offs**:
- Shorter timeout → Faster failure detection but higher false positive rate
- Longer timeout → Better success rate but risk of cascading failures
- Recommendation: Current timeouts are appropriate for p99 latencies

---

## [search-api][prod] Cache and vector DB settings

**Service**: search-api  
**Environment**: prod  
**Last Updated**: 2024-11-20

### Cache Configuration

**Current Settings**:
```yaml
cache_enabled: true
cache_type: redis
cache_size_mb: 2048
cache_ttl_seconds: 600
cache_max_entries: 100000
eviction_policy: lru
```

**Known Risks**:
- **No cache warming** leads to cold start latency spikes after deployment
- **Long TTL (> 15min)** causes stale results for dynamic data
- **No size limit** (or very high limit) can cause memory pressure
- **No cache invalidation** strategy for data updates

**Best Practices**:
- Cache size should be 10-20% of active query set (2048MB is good for ~100K queries)
- TTL should match data freshness requirement (10 min = 600s is reasonable for search)
- Use LRU eviction to prioritize popular queries
- Implement cache warming: pre-populate top 1000 queries after deployment
- Add cache invalidation hooks for data updates

**Trade-offs**:
- Longer TTL → Higher hit rate but more stale results
- Larger cache → Better hit rate but higher memory usage
- Recommendation: Consider reducing TTL to 300s (5 min) for better freshness

### Vector DB (Qdrant) Configuration

**Current Settings**:
```yaml
qdrant_url: "http://qdrant:6333"
collection_name: "search_embeddings"
vector_size: 768
distance_metric: cosine
hnsw_m: 16
hnsw_ef_construct: 100
query_ef: 128
```

**Known Risks**:
- **High hnsw_ef_construct (> 200)** slows down indexing significantly
- **Low query_ef (< 64)** reduces recall quality
- **No replication** creates single point of failure
- **No backup strategy** risks data loss on corruption

**Best Practices**:
- HNSW parameters: m=16 (good), ef_construct=100 (good), query_ef=128 (good)
- Enable replication: 2-3 replicas for production
- Snapshot frequency: daily automated snapshots with 7-day retention
- Monitor index health: check query latency p95 < 100ms, recall > 0.85

**Trade-offs**:
- Higher query_ef → Better recall but slower queries
- More replicas → Higher availability but higher resource cost
- Recommendation: Current HNSW config is balanced, add 2 replicas for HA

---

## [user-service][prod] Session and authentication settings

**Service**: user-service  
**Environment**: prod  
**Last Updated**: 2024-09-15

### Session Configuration

**Current Settings**:
```yaml
session_store: redis
session_ttl: 3600  # 1 hour
session_cache_size: 50000
session_cookie_secure: true
session_cookie_httponly: true
session_cookie_samesite: "strict"
```

**Known Risks**:
- **Long session TTL (> 2 hours)** increases security risk from stolen tokens
- **No session cache limit** can cause memory leak (unbounded growth)
- **No rate limiting** allows session enumeration attacks
- **Single Redis instance** creates SPOF for authentication

**Best Practices**:
- Session TTL: 1 hour for web, 24 hours for mobile (current config is good)
- Cache size limit: 50K sessions is reasonable for ~10K active users
- Enable rate limiting: max 10 login attempts per IP per minute
- Use Redis Sentinel or Redis Cluster for HA (avoid SPOF)
- Implement session rotation on privilege escalation

**Trade-offs**:
- Shorter TTL → Better security but more frequent re-authentication (user friction)
- Larger cache → More memory but better hit rate
- Recommendation: Add Redis Sentinel for HA, keep current TTL

### JWT Token Settings

**Current Settings**:
```yaml
jwt_secret: <REDACTED>
jwt_algorithm: HS256
jwt_expiry: 3600  # 1 hour
jwt_refresh_expiry: 86400  # 24 hours
jwt_issuer: "user-service"
```

**Known Risks**:
- **Symmetric key (HS256)** requires sharing secret across services (security risk)
- **No token rotation** allows long-lived compromised tokens
- **Short expiry (< 30min)** causes frequent refresh churn
- **No blacklist** allows revoked tokens to remain valid until expiry

**Best Practices**:
- Consider asymmetric keys (RS256) for multi-service architecture
- Token expiry: 1 hour (good), refresh expiry: 24 hours (good for web), 7 days (better for mobile)
- Implement token blacklist (Redis set) for immediate revocation
- Rotate JWT secret quarterly (with graceful migration period)

**Trade-offs**:
- Shorter expiry → Better security but higher refresh load
- Symmetric vs asymmetric → HS256 is faster, RS256 is more secure
- Recommendation: Migrate to RS256 for better security, keep current expiry

---

## [all-services][prod] Observability and resource limits

### Resource Limits (Kubernetes)

**Standard Configuration**:
```yaml
resources:
  requests:
    cpu: "1000m"    # 1 core
    memory: "2Gi"   # 2 GB
  limits:
    cpu: "2000m"    # 2 cores
    memory: "4Gi"   # 4 GB
```

**Known Risks**:
- **No resource limits** allows runaway processes to impact node stability
- **Limits = Requests** disables CPU throttling but prevents overcommit
- **Low memory limits** cause OOMKilled errors during traffic spikes
- **High CPU limits** allow one pod to starve others on same node

**Best Practices**:
- Always set both requests and limits (current config is good)
- Memory: limits should be 1.5-2x requests for burst headroom
- CPU: limits should be 2x requests (allows bursting without starvation)
- Monitor actual usage: CPU p95 < 70%, memory p95 < 85%

**Trade-offs**:
- Higher limits → Better performance but lower cluster density
- Tighter limits → Higher density but more frequent OOMKills
- Recommendation: Start with 1 core / 2GB requests, 2 core / 4GB limits, tune based on actual usage

### Logging Configuration

**Standard Configuration**:
```yaml
log_level: "info"
log_format: "json"
log_output: "stdout"
log_sampling_rate: 1.0  # 100% of logs
structured_logging: true
```

**Known Risks**:
- **Debug logging in prod** generates excessive logs (cost and noise)
- **100% sampling** can cause log floods during incidents
- **No log rate limiting** allows single error to spam logs
- **Unstructured logs** are hard to query and aggregate

**Best Practices**:
- Log level: "info" for prod, "debug" for troubleshooting only
- Use JSON structured logging for easy parsing
- Implement log sampling: 100% for ERROR/WARN, 10% for INFO, 1% for DEBUG
- Add rate limiting: max 100 logs/sec per error type
- Always include: timestamp, service, request_id, severity

**Trade-offs**:
- More detailed logs → Easier debugging but higher cost and noise
- Aggressive sampling → Lower cost but may miss important events
- Recommendation: Use adaptive sampling - 100% for first 10 occurrences of each error, then 10%

