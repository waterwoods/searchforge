# Runbook Knowledge Base

Operational runbooks for common symptoms across services. Each runbook includes symptom detection, diagnosis steps, and remediation actions.

---

## [service=payment-service][symptom=high-error-rate]

**When to use**: Payment service error rate > 2% for 5+ minutes

**Symptom Detection**:
- Error rate metric: `payment_errors_total / payment_requests_total > 0.02`
- Alert: "Payment service error rate critical"
- Dashboard: Payment Service Health → Error Rate panel

**Step-by-step Actions**:

1. **Check external payment gateway status**
   - Visit Stripe status page: https://status.stripe.com
   - Visit Adyen status page: https://status.adyen.com
   - If gateway is down → Enable circuit breaker and failover to secondary gateway
   
2. **Analyze error breakdown (5xx vs 4xx)**
   - Query: `payment_errors_total{code=~"5.."} / payment_errors_total`
   - 5xx errors (>80%) → Gateway or downstream issues (proceed to step 3)
   - 4xx errors (>80%) → Client validation issues (proceed to step 5)

3. **Verify payment gateway connectivity**
   - Check gateway API latency: `payment_gateway_latency_seconds{p95} > 5.0`
   - Check gateway timeout rate: `payment_gateway_timeouts_total`
   - If latency > 5s or timeouts > 1% → Enable circuit breaker immediately

4. **Review retry logic and backoff**
   - Check current retry config: `kubectl get configmap payment-service-config`
   - Expected: max_retries=3, backoff=[100ms, 500ms, 2000ms], jitter=true
   - If retry config is aggressive (no backoff) → Update config and restart pods

5. **Check for validation errors (4xx case)**
   - Query logs: `payment-service` + `level=ERROR` + `validation_failed`
   - Common issues: expired cards, insufficient funds, invalid CVV
   - If validation errors are legit → No action needed (customer issue)
   - If validation errors are unexpected → Check payment form data integrity

6. **Enable circuit breaker if needed**
   ```bash
   kubectl set env deployment/payment-service CIRCUIT_BREAKER_ENABLED=true
   kubectl set env deployment/payment-service CIRCUIT_BREAKER_THRESHOLD=50
   ```

7. **Page on-call if error rate persists > 5% for > 5 minutes**
   - Critical service - immediate escalation required
   - Include: error rate graph, recent deployment history, gateway status

**Verification**:
- Error rate should drop below 2% within 5 minutes of mitigation
- Check successful transaction count is recovering
- Monitor customer complaints/support tickets

---

## [service=api-gateway][symptom=high-latency]

**When to use**: API gateway p95 latency > 500ms for 5+ minutes

**Symptom Detection**:
- Latency metric: `http_request_duration_seconds{service="api-gateway",quantile="0.95"} > 0.5`
- Alert: "API gateway latency high"
- Dashboard: API Gateway Health → Latency panel

**Step-by-step Actions**:

1. **Check downstream service health**
   - Query: `http_request_duration_seconds{service=~"search-service|user-service|payment-service"}`
   - If any downstream p95 > 300ms → Investigate that service first
   - Common culprits: search-service (vector DB), payment-service (gateway API)

2. **Review connection pool utilization**
   - Query: `db_connection_pool_active / db_connection_pool_max > 0.8`
   - If utilization > 80% → Increase pool size immediately
   - Recommended: maxConnections=150-200 for prod workloads

3. **Check database query performance**
   - Query slow query logs: `db_query_duration_seconds{p95} > 1.0`
   - If slow queries detected → Kill long-running queries or add indexes
   - Emergency: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query_start < now() - interval '30 seconds'`

4. **Enable circuit breakers for slow downstream services**
   - Set timeout = 2x p99 latency of downstream service
   - Example: If search-service p99 = 200ms, set timeout = 400ms
   - Update config: `kubectl edit configmap api-gateway-config`

5. **Scale horizontally if CPU > 70%**
   - Query: `container_cpu_usage_percent{service="api-gateway"} > 70`
   - If true → Add 2-3 replicas gradually
   ```bash
   kubectl scale deployment api-gateway --replicas=8
   ```
   - Wait 2-3 minutes and monitor latency improvement

6. **Check for cache misses**
   - Query: `cache_hit_rate < 0.6`
   - If cache hit rate < 60% → Increase cache size or TTL
   - Consider pre-warming cache for popular endpoints

**Verification**:
- p95 latency should drop below 300ms within 10 minutes
- p99 latency should drop below 500ms within 10 minutes
- Check QPS is stable and not dropping

---

## [service=search-api][symptom=high-latency]

**When to use**: Search API p95 latency > 300ms for 5+ minutes

**Symptom Detection**:
- Latency metric: `search_query_duration_seconds{quantile="0.95"} > 0.3`
- Alert: "Search API latency degraded"
- Dashboard: Search Service Health → Query Latency panel

**Step-by-step Actions**:

1. **Check vector DB query latency**
   - Query: `qdrant_query_duration_seconds{p95}`
   - Target: p95 < 100ms
   - If p95 > 100ms → Vector DB is bottleneck (proceed to step 2)

2. **Review cache hit rate**
   - Query: `search_cache_hit_rate`
   - Expected: > 60% for production traffic
   - If < 60% → Increase cache size or adjust TTL
   ```bash
   kubectl set env deployment/search-api CACHE_SIZE_MB=2048
   kubectl set env deployment/search-api CACHE_TTL_SECONDS=600
   ```

3. **Analyze slow queries**
   - Query logs: `search-api` + `query_duration > 500ms`
   - Check for complex queries (multiple filters, large result sets)
   - If slow queries are legitimate → Consider query optimization or pagination

4. **Check vector DB resource usage**
   - Query: `qdrant_cpu_usage_percent` and `qdrant_memory_usage_percent`
   - If CPU > 80% or memory > 85% → Scale vector DB
   ```bash
   kubectl scale statefulset qdrant --replicas=3
   ```

5. **Consider adding read replicas**
   - If query load > 1000 QPS → Add read replicas for vector DB
   - Expected improvement: ~30-40% latency reduction per replica
   - Verify replication lag < 1s before routing traffic

6. **Enable query caching for popular queries**
   - Identify top 100 queries by frequency
   - Pre-warm cache with these queries
   - Set longer TTL (10-15 minutes) for stable results

**Verification**:
- p95 latency should drop below 200ms within 5 minutes
- Cache hit rate should increase to > 70%
- Vector DB query latency should be < 100ms

---

## [service=*][symptom=high-cpu]

**When to use**: Service CPU usage > 85% for 5+ minutes

**Symptom Detection**:
- CPU metric: `container_cpu_usage_percent > 85`
- Alert: "{service} CPU usage critical"
- Dashboard: Service Health → CPU Usage panel

**Step-by-step Actions**:

1. **Check QPS against baseline**
   - Query: `http_requests_total{service="{service}"}`
   - Compare with 7-day average
   - If QPS spike > 50% → Traffic surge (proceed to step 2)
   - If QPS stable → Code inefficiency or resource leak (proceed to step 4)

2. **Scale horizontally for traffic surges**
   - Add replicas to distribute load
   - Target: CPU < 70% after scaling
   ```bash
   kubectl scale deployment {service} --replicas=10
   ```
   - Monitor CPU for 3-5 minutes

3. **Check for recent deployments**
   - Query: `kubectl rollout history deployment/{service}`
   - If deployment within last 2 hours → Consider rollback
   - If CPU spike correlates with deployment → Rollback immediately
   ```bash
   kubectl rollout undo deployment/{service}
   ```

4. **Review CPU profiler traces**
   - Enable CPU profiling: `kubectl exec {pod} -- kill -SIGUSR1 1`
   - Download profile: `kubectl cp {pod}:/tmp/cpu.prof ./cpu.prof`
   - Analyze with pprof: `go tool pprof cpu.prof`
   - Look for hot code paths (>20% CPU time)

5. **Check for infinite loops or deadlocks**
   - Query logs for repeated error patterns
   - Check thread count: `ps -eLf | grep {service} | wc -l`
   - If thread count > 1000 → Potential thread leak, restart pod

6. **Enable request caching if applicable**
   - For read-heavy endpoints: cache TTL = 60-300s
   - For expensive computations: cache computed results
   - Expected improvement: 30-50% CPU reduction

**Verification**:
- CPU usage should drop below 70% within 5-10 minutes
- Latency should remain stable or improve
- Check memory usage is not increasing (rule out memory leak)

---

## [service=*][symptom=disk-near-full]

**When to use**: Disk usage > 85% on any service instance

**Symptom Detection**:
- Disk metric: `disk_usage_percent > 85`
- Alert: "{service} disk usage critical"
- Dashboard: Infrastructure Health → Disk Usage panel

**Step-by-step Actions**:

1. **Check disk usage by directory**
   ```bash
   kubectl exec {pod} -- du -sh /var/log /tmp /app 2>/dev/null | sort -h
   ```
   - Identify largest directories
   - Common culprits: /var/log (logs), /tmp (temp files), /app/cache (caches)

2. **Rotate and compress old log files**
   - Keep only last 7 days of logs
   ```bash
   kubectl exec {pod} -- find /var/log -name "*.log" -mtime +7 -delete
   kubectl exec {pod} -- find /var/log -name "*.log.[0-9]" -exec gzip {} \;
   ```
   - Expected space recovery: 40-60%

3. **Clear temporary files and caches**
   - Safe to delete /tmp contents (check for active files first)
   ```bash
   kubectl exec {pod} -- find /tmp -type f -mtime +1 -delete
   kubectl exec {pod} -- rm -rf /app/cache/* 2>/dev/null
   ```
   - Expected space recovery: 10-30%

4. **Review log rotation configuration**
   - Check logrotate config: `kubectl exec {pod} -- cat /etc/logrotate.conf`
   - Recommended: rotate daily, keep 7 days, compress after rotation
   - Update if needed and restart pod

5. **Check for core dumps or debug files**
   ```bash
   kubectl exec {pod} -- find / -name "core.*" -o -name "*.dump" 2>/dev/null
   ```
   - Delete if found (after copying for debugging if needed)

6. **Increase disk size (long-term fix)**
   - For persistent volumes:
   ```bash
   kubectl patch pvc {pvc-name} -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
   ```
   - For ephemeral volumes: update deployment spec and redeploy

7. **Monitor disk usage trend**
   - If disk usage increases steadily (>5%/day) → Investigate data retention policies
   - If disk usage spikes suddenly → Check for runaway processes or log floods

**Verification**:
- Disk usage should drop below 75% after cleanup
- Monitor for 24 hours to ensure no rapid re-growth
- If re-growth occurs → Investigate and fix root cause

---

## [service=*][symptom=memory-pressure]

**When to use**: Service memory usage > 85% for 5+ minutes

**Symptom Detection**:
- Memory metric: `container_memory_usage_percent > 85`
- Alert: "{service} memory pressure"
- Dashboard: Service Health → Memory Usage panel

**Step-by-step Actions**:

1. **Check for memory leaks**
   - Query memory usage trend over last 6 hours
   - If steady increase (>10%/hour) → Likely memory leak (proceed to step 2)
   - If sudden spike → Likely traffic surge or cache bloat (proceed to step 4)

2. **Capture heap dump for analysis**
   ```bash
   kubectl exec {pod} -- jmap -dump:format=b,file=/tmp/heap.hprof 1
   kubectl cp {pod}:/tmp/heap.hprof ./heap.hprof
   ```
   - Analyze with tools like Eclipse MAT or VisualVM
   - Look for large object retention or unbounded collections

3. **Restart service if memory > 90% (temporary fix)**
   ```bash
   kubectl delete pod {pod-name}
   ```
   - Monitor new pod for memory growth pattern
   - If leak persists → Deploy fix or rollback to previous version

4. **Review cache eviction policies**
   - Check cache configuration
   - Expected: LRU cache with size limit and TTL
   ```bash
   kubectl exec {pod} -- grep -i cache /app/config.yaml
   ```
   - If no eviction policy → Add one immediately

5. **Check active session/connection count**
   - Query: `active_sessions` or `connection_pool_active`
   - If count is abnormally high → Investigate session leaks
   - Recommended: session TTL < 1 hour, max sessions < 50K

6. **Scale horizontally to distribute memory load**
   - Add replicas if memory pressure is due to traffic
   ```bash
   kubectl scale deployment {service} --replicas=8
   ```
   - Expected: memory per pod should decrease proportionally

7. **Review recent code changes**
   - Check for new caching logic, in-memory data structures
   - Common issues: unbounded maps, unclosed connections, retained event listeners

**Verification**:
- Memory usage should drop below 75% after mitigation
- Memory usage should be stable over next 2-4 hours
- Check for OOMKilled events in pod status

