# Lessons Learned

High-level operational wisdom and best practices derived from production incidents and experience.

---

## Retry and Backoff Strategies

**Lesson**: Avoid retry storms against single-region dependencies

**Context**:  
Multiple incidents (payment-service 2024-11-05, api-gateway 2024-10-28) were caused or amplified by aggressive retry logic. When downstream services degrade, immediate retries without backoff create a feedback loop that makes the situation worse.

**What We Learned**:
- **Immediate retries are almost never the right choice**. By the time a request fails (timeout, connection refused, 503), the downstream service is already under stress. Immediately retrying just adds more load.
- **Exponential backoff with jitter is essential**. Backoff reduces load on the struggling service. Jitter prevents thundering herd (all clients retrying simultaneously).
- **Circuit breakers prevent cascading failures**. After N consecutive failures, stop sending requests for a cooldown period. This gives the downstream service time to recover.
- **Distinguish between retryable and non-retryable errors**. Never retry 4xx errors (validation failures). Only retry 5xx errors and timeouts.

**Best Practice**:
```yaml
retry_policy:
  max_retries: 3
  backoff: [100ms, 500ms, 2000ms]  # Exponential: 100ms, 500ms, 2s
  jitter: true                      # Random ±25% to spread load
  retry_on: [500, 502, 503, 504, timeout]
  do_not_retry_on: [400, 401, 403, 404, 422]
  
circuit_breaker:
  failure_threshold: 50%            # Open after 50% error rate
  success_threshold: 80%            # Close after 80% success rate
  timeout: 10s                      # Check every 10s
  min_requests: 10                  # Need at least 10 requests to evaluate
```

**Warning Signs**:
- Error rate increases proportionally to retry count (1 error becomes 3-5 errors)
- Downstream service CPU/memory spikes during incident
- Timeouts increase even as downstream service starts recovering

---

## Connection Pool Sizing and Failover

**Lesson**: Prefer horizontal scaling before increasing per-pod resource limits

**Context**:  
API gateway connection pool exhaustion (2024-10-28) and payment-service database failover (2024-08-20) taught us that connection pools need careful tuning and fast failover detection.

**What We Learned**:
- **Connection pool size should match expected concurrency**. Rule of thumb: pool size = expected QPS × p95 query latency (in seconds). Example: 2000 QPS × 0.1s = 200 connections.
- **Idle timeout should be short (< 1 min)** to detect failovers quickly. Long idle timeout (5+ minutes) means stale connections stay in pool after database restart/failover.
- **Always use connection validation queries** ("SELECT 1" for Postgres, "PING" for Redis). This prevents using stale connections that fail on first real query.
- **Set max connection lifetime** (30-60 minutes) to prevent leaks. Connections should be closed and reopened periodically to avoid long-term resource leaks.

**Best Practice**:
```yaml
connection_pool:
  max_connections: <QPS × p95_latency × 2>  # 2x for burst headroom
  min_idle: <max_connections / 4>           # Keep 25% warm
  idle_timeout: 30s                          # Detect failover quickly
  max_lifetime: 1800s                        # 30 min, prevent leaks
  connection_timeout: 10s                    # Fail fast if DB unavailable
  validation_query: "SELECT 1"               # Verify connection health
```

**For horizontal scaling**:
- Adding replicas is safer than increasing resources per pod (limits blast radius)
- Target: CPU < 70%, memory < 85% per pod after scaling
- Scale before reaching resource limits, not after

**Warning Signs**:
- Connection pool utilization > 80% sustained for 5+ minutes
- Connection timeout errors in logs
- Query latency increases even though database CPU is low (suggests pool exhaustion)

---

## Cache Invalidation and Stampede Prevention

**Lesson**: Cache invalidation requires careful coordination to prevent stampedes

**Context**:  
User-service cache stampede (2024-09-30) and search-api index corruption (2024-10-15) highlighted the danger of mass cache invalidation.

**What We Learned**:
- **Never invalidate large cache segments simultaneously**. Batch invalidation of 50K sessions caused 50K cache misses → 50K database queries → connection pool exhaustion → cascading failure.
- **Implement staggered invalidation**: Spread cache invalidation over 5-10 minutes (max 100-200 invalidations per second).
- **Use probabilistic cache expiration**: Add random jitter to TTL (e.g., TTL = 600s ± 60s) to prevent synchronized cache expiration.
- **Pre-warm cache after deployments**: Populate top N popular queries/sessions before routing traffic.

**Best Practice**:
```yaml
cache_config:
  ttl: 600                           # 10 minutes base TTL
  ttl_jitter: 60                     # ±60s jitter (10%)
  max_invalidation_rate: 100         # Max 100/sec invalidation
  warm_cache_on_startup: true        # Pre-populate top 1000 entries
  warm_cache_queries: 1000
  
batch_operations:
  max_rate: 100                      # Max 100 ops/sec for batch jobs
  rate_limit_enabled: true
```

**Warning Signs**:
- Sudden spike in database queries after cache invalidation
- Connection pool exhaustion after scheduled cache clear
- Latency spike at regular intervals (suggests synchronized cache expiration)

---

## Observability and Proactive Monitoring

**Lesson**: Alerts should fire before customer impact, not after

**Context**:  
Multiple incidents were detected by customer complaints before internal alerts fired. We learned to be more proactive.

**What We Learned**:
- **Lead indicators > lag indicators**. Alert on connection pool utilization (lead) before connection timeouts (lag). Alert on error rate trend (increasing) before absolute threshold.
- **Use percentiles, not averages**. Average latency can be low even when p95/p99 is unacceptable. Monitor p95 and p99, not mean.
- **Correlate metrics across services**. A single service's metrics don't tell the full story. Latency spike in api-gateway might be caused by slow search-service.
- **Alert fatigue is real**. Too many alerts → people ignore them. Set thresholds conservatively (alert when action is needed, not "might be needed").

**Best Practice Alert Thresholds**:
```yaml
alerts:
  # Proactive (lead indicators)
  - name: "Connection pool high"
    metric: "db_connection_pool_utilization"
    threshold: 0.80                   # Warning at 80%
    duration: "5m"                    # Sustained for 5 min
    
  - name: "Error rate increasing"
    metric: "error_rate_change"
    threshold: "+50%"                 # 50% increase over 5 min
    duration: "3m"
    
  - name: "Latency p95 degraded"
    metric: "http_request_duration_p95"
    threshold: "2x_baseline"          # 2x normal p95
    duration: "5m"
    
  # Reactive (lag indicators, higher severity)
  - name: "Error rate critical"
    metric: "error_rate"
    threshold: 0.05                   # 5% absolute
    duration: "2m"
    severity: "critical"
    page: true
```

**Key Metrics to Monitor**:
1. **Golden Signals**: Latency (p95, p99), Traffic (QPS), Errors (rate), Saturation (CPU, memory, connections)
2. **Lead Indicators**: Connection pool utilization, cache hit rate, queue depth, pending requests
3. **Business Metrics**: Transaction success rate, customer-facing error rate, revenue impact

---

## Deployment and Rollback Safety

**Lesson**: Fast rollback is more valuable than slow debugging in production

**Context**:  
Several incidents (api-gateway staging 2024-11-12, payment-service 2024-10-28) were prolonged because teams tried to debug in production instead of rolling back immediately.

**What We Learned**:
- **When in doubt, roll back**. If a deployment correlates with an incident (within 2 hours), roll back first, debug later. Customer impact > engineer pride.
- **Automated rollback triggers save time**. If error rate > 5% for 5 minutes after deployment → automatic rollback.
- **Canary deployments catch issues early**. Deploy to 5% of pods first, monitor for 15 minutes, then proceed to full rollout.
- **Feature flags allow instant disable**. For new features, use feature flags so you can disable without deployment/rollback.

**Best Practice Deployment Process**:
```yaml
deployment_pipeline:
  # Stage 1: Canary (5% traffic)
  - canary_replicas: 1
    canary_traffic_percent: 5
    canary_duration: 15m
    canary_rollback_threshold:
      error_rate: 0.03              # 3% error rate
      latency_p95_increase: 50%     # 50% latency increase
      
  # Stage 2: Progressive rollout
  - rollout_strategy: "progressive"
    stages: [10%, 25%, 50%, 100%]
    stage_duration: 10m
    auto_rollback: true
    
  # Stage 3: Monitoring period
  - monitoring_duration: 30m
    alerts_enabled: true
    rollback_on_alert: true
```

**When to Roll Back Immediately**:
- Error rate > 5% sustained for 5+ minutes after deployment
- Latency p95 increases > 100% after deployment
- Any CRITICAL alert fires within 30 minutes of deployment
- Customer complaints spike within 1 hour of deployment

**When to Debug First**:
- Isolated errors (1-2 customers, not widespread)
- Non-critical service in staging/dev environment
- Issue is clearly unrelated to recent deployment

---

## Resource Limits and Capacity Planning

**Lesson**: Plan capacity for 2-3x peak load, not average load

**Context**:  
Multiple incidents involved resource exhaustion during traffic spikes that were within "expected" range but still overwhelmed the system.

**What We Learned**:
- **Average load is misleading**. Plan for p95 load, not average. Black Friday, flash sales, viral content → sudden 5-10x traffic spikes.
- **Autoscaling has lag**. It takes 2-5 minutes to spin up new pods. By the time autoscaling kicks in, you're already in trouble.
- **CPU throttling is insidious**. Hitting CPU limits doesn't cause crashes, just slow responses. This can cascade to downstream services.
- **Memory limits cause OOMKills**. Unlike CPU, exceeding memory limits causes immediate pod termination (OOMKilled). This is worse than throttling.

**Best Practice Capacity Planning**:
```yaml
capacity_planning:
  # Target headroom
  cpu_target: 70%                   # Keep CPU < 70% at peak
  memory_target: 85%                # Keep memory < 85% at peak
  
  # Autoscaling
  autoscale_enabled: true
  min_replicas: 3                   # Always >= 3 for HA
  max_replicas: 20                  # Set reasonable max
  scale_up_trigger: 70%             # Scale up at 70% CPU
  scale_down_trigger: 40%           # Scale down at 40% CPU
  scale_up_cooldown: 1m             # Fast scale-up
  scale_down_cooldown: 10m          # Slow scale-down
  
  # Resource requests/limits
  requests:
    cpu: "1000m"                    # 1 core
    memory: "2Gi"                   # 2 GB
  limits:
    cpu: "2000m"                    # 2 cores (2x for burst)
    memory: "4Gi"                   # 4 GB (2x for headroom)
```

**Load Testing Strategy**:
- Test at 2x expected peak load (if peak is 1000 QPS, test at 2000 QPS)
- Simulate realistic traffic patterns (ramp-up, sustained load, spike, ramp-down)
- Test failure scenarios: pod restart during load, database failover, cache clear
- Run load tests monthly, not just before major events

---

## Multi-Region and Failover Strategy

**Lesson**: Design for failure from day one; failover is not optional for critical services

**Context**:  
Payment-service database failover (2024-08-20) took 12 minutes when it should have taken 30 seconds. Application layer didn't handle failover gracefully.

**What We Learned**:
- **Failover should be automatic, not manual**. Waiting for humans to detect and react is too slow.
- **Test failover regularly** (quarterly minimum). Untested failover = broken failover.
- **Application layer must be failover-aware**. Don't rely on infrastructure alone. App should detect stale connections and reconnect quickly.
- **Multi-region is expensive but essential for critical services**. Payment-service should never have single region SPOF.

**Best Practice Failover Strategy**:
```yaml
failover_config:
  # Database failover
  primary_region: "us-east-1"
  replica_regions: ["us-west-2", "eu-west-1"]
  automatic_failover: true
  failover_timeout: 30s             # Failover should complete in 30s
  
  # Application layer
  connection_validation: true        # Validate before use
  fast_fail: true                    # Detect failure in 10s, not 5 min
  reconnect_backoff: [1s, 2s, 5s]   # Fast reconnect attempts
  
  # Health checks
  health_check_interval: 10s         # Check every 10s
  health_check_timeout: 2s           # Fail fast
  unhealthy_threshold: 3             # 3 consecutive failures → unhealthy
  healthy_threshold: 2               # 2 consecutive successes → healthy
```

**Testing Failover**:
- **Chaos engineering**: Randomly kill pods, databases, regions
- **Scheduled drills**: Test failover quarterly during low-traffic windows
- **Gradual rollout**: Failover 10% of traffic first, monitor, then 100%

**Critical Services That Need Failover**:
- Payment processing (revenue critical)
- Authentication (blocks all user access)
- API gateway (single point of entry)
- Any service with SLA > 99.9% (< 43 min downtime/month)

---

## Final Wisdom

1. **Simplicity > Complexity**: Simpler systems are easier to understand, debug, and fix during incidents. Avoid over-engineering.

2. **Automation > Manual Intervention**: Automate common tasks (failover, scaling, rollback). Humans are slow and error-prone under pressure.

3. **Observability > Firefighting**: Invest in logging, metrics, tracing. You can't fix what you can't see.

4. **Graceful Degradation > Hard Failure**: Prefer degraded functionality (slower, cached, approximate) over complete failure.

5. **Test in Production (Carefully)**: Staging is not production. Use canary deployments, feature flags, and chaos engineering to test in prod safely.

6. **Blameless Postmortems**: Focus on systems and processes, not individuals. Every incident is a learning opportunity.

7. **Document Everything**: Future-you will thank present-you. Write runbooks, document decisions, keep this knowledge base updated.

