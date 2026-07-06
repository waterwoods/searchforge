# WeCom Q0.9.6.1 — Cloud SQL Smoke Queue Cleanup Evidence

**Date:** 2026-07-04  
**Task:** Q0.9.6.1 — Clean Cloud SQL smoke queue tables and verify 2× empty drain  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com  
**Final verdict:** **PASS**

---

## 1. Cloud Run state (pre-check)

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Revision | `fiqa-api-00135-8zw` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private:latest` |
| Cloud SQL connector | absent (`run.googleapis.com/cloudsql-instances: ''`) |
| VPC egress | `all-traffic` (Direct VPC, network `default`, subnet `default`) |
| Cloud NAT / WeCom IP | unchanged — `8.235.43.132` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_QUEUE_ADMIN_TOKEN` | set (not logged) |

---

## 2. Target DB confirmation

| Check | Result |
|-------|--------|
| Admin status HTTP | **200** |
| `db_preflight.ok` | **true** |
| Cloud Run DB secret name | `fiqa-service-record-database-url-cloudsql-private` |
| Cloud Run DB host (private IP) | `10.73.0.3` |
| Database name | `caseiq` |
| Instance | `caseiq-pilot-pg` (`us-west1`) |
| Is Neon? | **No** — Neon secret `fiqa-service-record-database-url` untouched |
| Operator SQL path | public IP `34.169.226.245` (authorized network `76.175.219.134/32`) — same `caseiq` DB |

Cleanup SQL was executed via operator public-IP path against the same Cloud SQL database Cloud Run reaches via private IP `10.73.0.3`.

---

## 3. Queue counts before cleanup

**Cloud Run admin status (pre-cleanup):**

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | 0 | 0 | 1 | 0 |
| outbox | 11 | 0 | 0 | 2 |

**Direct Cloud SQL query (same DB, public IP path):**

| Table | Status breakdown |
|-------|------------------|
| `wecom_inbox_events` | `processed=1` (id=1, attempt_count=2) |
| `wecom_reply_outbox` | `pending=11` (ids 3–13), `failed=2` (ids 1–2, errcode 95018) |

**Recent row metadata (no payload bodies):**

- Inbox id=1: status=processed, created 2026-07-04T23:00:37Z, processed 2026-07-04T23:47:33Z
- Outbox ids 1–13: all from Q0.9.4 smoke residue (2026-07-04T23:03:17Z batch)

**Business tables (read-only, not modified):**

| Table | Count |
|-------|-------|
| `service_records` | 1 |
| `wecom_reply_dedup` | 15 |
| `record_messages` | 1 |

**FK check:** no foreign keys reference `wecom_inbox_events` or `wecom_reply_outbox`.

---

## 4. Cleanup SQL executed

Safety checks passed (Cloud SQL `caseiq`, not Neon; no FK constraints; only queue tables targeted).

```sql
TRUNCATE TABLE wecom_reply_outbox;
TRUNCATE TABLE wecom_inbox_events;
```

**Not truncated:** `service_records`, `record_messages`, `structured_record_data`, `state_history`, `office_actions`, `intake_sessions`, `intake_entities`, `wecom_reply_dedup`.

---

## 5. Queue counts after cleanup

| Table | Total rows |
|-------|------------|
| `wecom_inbox_events` | **0** |
| `wecom_reply_outbox` | **0** |

**Business tables unchanged:**

| Table | Count |
|-------|-------|
| `service_records` | 1 |
| `wecom_reply_dedup` | 15 |
| `record_messages` | 1 |

**Cloud Run admin status (post-cleanup):** HTTP **200**, `db_preflight.ok=true`

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | 0 | 0 | 0 | 0 |
| outbox | 0 | 0 | 0 | 0 |

---

## 6. Empty drain stability (2× via Cloud Run admin)

Endpoint: `POST /api/admin/wecom/queues/drain?limit=1`

### Drain #1

| Field | Value |
|-------|-------|
| HTTP | **200** |
| `ok` | true |
| `inbox.claimed` | 0 |
| `inbox.processed` | 0 |
| `inbox.failed` | 0 |
| `outbox.claimed` | 0 |
| `outbox.sent` | 0 |
| `outbox.failed` | 0 |
| `memory_degraded` | absent |
| `status_after.db_preflight.ok` | true |
| Stuck processing/sending | none |

### Drain #2

| Field | Value |
|-------|-------|
| HTTP | **200** |
| `ok` | true |
| `inbox.claimed` | 0 |
| `inbox.processed` | 0 |
| `inbox.failed` | 0 |
| `outbox.claimed` | 0 |
| `outbox.sent` | 0 |
| `outbox.failed` | 0 |
| `memory_degraded` | absent |
| `status_after.db_preflight.ok` | true |
| Stuck processing/sending | none |

No WeCom `send_msg` calls triggered (claimed=0 on both runs). No HTTP 500/503.

---

## 7. Acceptance criteria scorecard

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Only Cloud SQL smoke queue tables cleaned | **PASS** |
| 2 | Neon untouched | **PASS** |
| 3 | Business/case tables untouched | **PASS** |
| 4 | Queue status clean after cleanup | **PASS** |
| 5 | Two Cloud Run empty drains: claimed=0, failed=0 | **PASS** |
| 6 | Evidence updated | **PASS** (this doc) |
| 7 | No WeCom messages sent | **PASS** |
| 8 | No live Phase 2 smoke run | **PASS** |

---

## 8. Final verdict and next action

**Verdict: PASS**

Q0.9.6.1 clean-room criteria met. Cloud SQL private IP path from Q0.9.6 remains stable; stale Q0.9.4 queue residue removed.

**Recommended next step:** Proceed to **Q0.9.7 — final Phase 2 live WeCom smoke** (enable queue flags, send one test message, drain limit=1). Do not run live smoke until operator explicitly approves.

**Related evidence:**

- Q0.9.6 private IP networking: [`wecom_q0_private_ip_network_2026-07-04.md`](wecom_q0_private_ip_network_2026-07-04.md)
- Q0.9.4 original smoke (residue source): [`wecom_q0_cloud_sql_smoke_2026-07-04.md`](wecom_q0_cloud_sql_smoke_2026-07-04.md)

---

*No passwords, tokens, payload bodies, or WeCom secrets recorded.*
