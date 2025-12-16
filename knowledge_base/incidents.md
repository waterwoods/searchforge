# Incident Knowledge Base

Historical incidents across services and environments. Each incident includes summary, impact, root cause, mitigations, and follow-up actions.

---

## [payment-service][prod][us-east-1][2024-11-05] Latency spike and error storm

**Date**: 2024-11-05 14:23 UTC  
**Duration**: 45 minutes  
**Severity**: Critical

**Summary**:  
Payment service experienced a sudden latency spike (p95 > 3000ms) followed by 8% error rate. Transactions were delayed or failing, causing customer complaints and revenue loss.

**Impact**:  
- ~15,000 failed payment transactions
- Revenue impact: ~$125K in delayed/failed payments
- Customer-facing error rate: 8.2%
- 3 major merchants reported checkout issues

**Root Cause**:  
External payment gateway (Stripe) API experienced regional degradation in us-east-1. Our retry logic was too aggressive (immediate retry x5), which amplified the load and triggered rate limiting on our side, creating a cascading failure.

**Mitigations Taken**:  
1. Enabled circuit breaker for Stripe API (at 14:35 UTC)
2. Failed over to secondary payment gateway (Adyen) for new transactions (at 14:40 UTC)
3. Implemented exponential backoff with jitter (deployed at 14:55 UTC)
4. Manually processed stuck transactions from queue after recovery

**Follow-up Actions**:  
- [DONE] Updated retry policy: max 3 retries with exponential backoff (100ms, 500ms, 2000ms) + jitter
- [DONE] Added circuit breaker configuration to payment-service deployment
- [IN PROGRESS] Build automatic failover logic between payment gateways
- [TODO] Add payment gateway health check dashboard

---

## [api-gateway][prod][us-west-2][2024-10-28] Connection pool exhaustion

**Date**: 2024-10-28 09:15 UTC  
**Duration**: 1.5 hours  
**Severity**: High

**Summary**:  
API gateway experienced connection pool exhaustion during morning traffic spike. p95 latency increased from 180ms to 950ms. Error rate climbed to 3.5%.

**Impact**:  
- All downstream services impacted (search, user, payment)
- Customer-facing latency increased by 400%
- 2,500+ timeout errors logged
- Mobile app performance degraded significantly

**Root Cause**:  
Database connection pool was configured with maxConnections=50, which was insufficient for peak QPS (2800 req/s). Under load, all 50 connections were held by long-running queries, causing new requests to queue and timeout.

**Mitigations Taken**:  
1. Emergency scaling: increased connection pool to maxConnections=150 (at 09:30 UTC)
2. Added 2 additional api-gateway replicas to distribute load (at 09:45 UTC)
3. Killed 3 slow queries that were holding connections for >30s (at 09:50 UTC)
4. Service recovered fully by 10:45 UTC

**Follow-up Actions**:  
- [DONE] Updated connection pool config: maxConnections=200, idleTimeout=30s, maxLifetime=1800s
- [DONE] Added connection pool utilization alerts (warning at 70%, critical at 85%)
- [DONE] Implemented query timeout enforcement (5s max for API queries, 15s for analytics)
- [TODO] Consider separating read/write connection pools

---

## [search-api][prod][us-east-1][2024-10-15] Vector DB index corruption

**Date**: 2024-10-15 03:20 UTC  
**Duration**: 2 hours  
**Severity**: High

**Summary**:  
Search API started returning stale and incorrect results. Error rate increased to 2.1%. Some queries returned empty results despite valid data existing.

**Impact**:  
- 40% of search queries returned stale results (> 24 hours old)
- 12% of queries returned empty results incorrectly
- Customer complaints about search quality increased by 300%
- Recall@10 dropped from 0.85 to 0.42

**Root Cause**:  
Vector DB (Qdrant) index was corrupted after an unclean shutdown during planned maintenance. The corruption was not detected immediately because health checks only verified API availability, not data integrity.

**Mitigations Taken**:  
1. Stopped accepting new writes to vector DB (at 03:30 UTC)
2. Restored vector DB from last known good snapshot (2 hours old) (at 04:00 UTC)
3. Reindexed delta data from Postgres (at 04:30 UTC)
4. Verified data integrity with sample queries (at 05:00 UTC)
5. Re-enabled writes and resumed normal operation (at 05:20 UTC)

**Follow-up Actions**:  
- [DONE] Added data integrity checks to vector DB health endpoint
- [DONE] Implemented automated snapshot verification (daily)
- [DONE] Added index consistency monitoring (checks every 15 minutes)
- [IN PROGRESS] Build redundant vector DB replica for failover
- [TODO] Add canary queries to detect stale results early

---

## [api-gateway][staging][us-east-1][2024-11-12] Memory leak from middleware

**Date**: 2024-11-12 16:45 UTC  
**Duration**: 3 hours  
**Severity**: Medium

**Summary**:  
Staging API gateway pods were crashing every 2-3 hours with OOM (Out Of Memory) errors. Memory usage gradually increased from 60% to 95% before crash.

**Impact**:  
- Staging environment unstable, blocked QA testing
- 8 pod restarts in 24 hours
- Developer productivity impacted
- No customer impact (staging only)

**Root Cause**:  
Newly deployed logging middleware (v3.2.1) was leaking memory due to unbounded request context cache. Each request added an entry to an in-memory cache without TTL or size limit, causing memory to grow indefinitely.

**Mitigations Taken**:  
1. Rolled back logging middleware to v3.1.5 (at 17:00 UTC)
2. Restarted all staging pods to clear memory (at 17:10 UTC)
3. Added memory limit alerts for staging (warning at 85%, critical at 95%) (at 18:00 UTC)

**Follow-up Actions**:  
- [DONE] Fixed memory leak in logging middleware v3.2.2 (added LRU cache with 10K entry limit + 1h TTL)
- [DONE] Added memory profiling to staging deployment pipeline
- [DONE] Deployed fixed version (v3.2.2) to staging and monitored for 48h
- [DONE] Promoted v3.2.2 to production after validation
- [TODO] Add automated memory leak detection to CI/CD

---

## [user-service][prod][us-east-1][2024-09-30] Session cache stampede

**Date**: 2024-09-30 11:00 UTC  
**Duration**: 30 minutes  
**Severity**: High

**Summary**:  
User service experienced sudden latency spike (p95 from 80ms to 1200ms) and CPU saturation (98%) during session cache invalidation. Error rate increased to 4.5%.

**Impact**:  
- Login/logout operations severely delayed
- 5,000+ authentication timeouts
- Session validation failures across all services
- Customer complaints about "can't log in" increased 10x

**Root Cause**:  
A batch session invalidation operation (admin action) triggered cache stampede. When 50K sessions were invalidated simultaneously, all subsequent requests for those sessions hit the database, overwhelming it with 50K concurrent queries. The database connection pool was exhausted within seconds.

**Mitigations Taken**:  
1. Killed the batch invalidation job (at 11:05 UTC)
2. Scaled user-service from 4 to 8 replicas (at 11:10 UTC)
3. Increased database connection pool from 100 to 250 (at 11:15 UTC)
4. Manually warmed cache with top 10K active sessions (at 11:20 UTC)
5. Service recovered by 11:30 UTC

**Follow-up Actions**:  
- [DONE] Implemented cache warming strategy (pre-fetch popular sessions)
- [DONE] Added rate limiting to batch operations (max 100 invalidations/second)
- [DONE] Implemented staggered cache invalidation (spread over 5-10 minutes)
- [DONE] Added cache stampede detection alerts
- [TODO] Consider using probabilistic cache TTL to avoid synchronized expirations

---

## [payment-service][prod][eu-west-1][2024-08-20] Database failover cascade

**Date**: 2024-08-20 22:30 UTC  
**Duration**: 12 minutes  
**Severity**: Critical

**Summary**:  
Payment service database (Postgres) primary failed over to replica in eu-west-1. During failover window, payment-service experienced 100% error rate for ~8 minutes, then gradual recovery over 4 minutes.

**Impact**:  
- ~800 failed payment transactions during outage window
- Revenue impact: ~$45K in failed transactions
- Customer-facing error rate: 100% for 8 minutes, then 15% for 4 minutes
- Manual intervention required to process stuck payments

**Root Cause**:  
Database primary instance experienced hardware failure. Automatic failover to replica took 4 minutes as expected, but application layer didn't detect the failover immediately. Connection pool held stale connections to the old primary for another 4 minutes until connection timeout (5min configured). During this time, all queries failed.

**Mitigations Taken**:  
1. Manual connection pool drain and reconnect (at 22:38 UTC)
2. Verified all payment-service pods reconnected to new primary (at 22:40 UTC)
3. Processed stuck transactions from dead letter queue (at 22:50 UTC)
4. Monitored for data inconsistencies (none found)

**Follow-up Actions**:  
- [DONE] Reduced connection pool idle timeout from 5min to 30s
- [DONE] Added connection validation query ("SELECT 1") before query execution
- [DONE] Implemented fast-fail logic: detect failover within 10s instead of waiting for timeout
- [DONE] Added database replica lag monitoring (alert if lag > 1s)
- [IN PROGRESS] Build payment transaction replay logic for automatic recovery
- [TODO] Test failover scenario in staging quarterly

