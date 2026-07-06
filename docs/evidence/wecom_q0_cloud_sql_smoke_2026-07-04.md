# WeCom Q0.9.4 — Cloud SQL Phase 2 Smoke Evidence

**Date:** 2026-07-04  
**Branch:** `sprint/p16-trust-layer` @ `cb4940b`  
**GCP project:** `optimal-disk-472305-e2`  
**Final verdict:** **FAIL**

---

## 1. Pre-check

| Check | Result |
|-------|--------|
| Cloud SQL instance `caseiq-pilot-pg` | RUNNABLE, `us-west1`, `db-f1-micro` |
| Secret `fiqa-service-record-database-url-cloudsql` | v1 public IP, v2 socket URL |
| Schema / local preflight | OK |
| Admin routes | present |
| `WECOM_QUEUE_ADMIN_TOKEN` | set (not logged) |

---

## 2. Cloud Run → Cloud SQL wiring

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Cloud SQL binding | `optimal-disk-472305-e2:us-west1:caseiq-pilot-pg` |
| DB secret (during test) | `fiqa-service-record-database-url-cloudsql:latest` (v2 socket) |
| VPC egress | `all-traffic` (Direct VPC — WeCom NAT preserved) |

**Revisions:**

| Phase | Revision | Flags / DB |
|-------|----------|------------|
| Cloud SQL wired | `fiqa-api-00131-9zz` | `INBOX=0`, `OUTBOX=0`, Cloud SQL secret |
| Phase 2 enabled | `fiqa-api-00132-5mx` | `INBOX=1`, `OUTBOX=1`, Cloud SQL secret |
| Flags rolled back | `fiqa-api-00133-ng6` | `INBOX=0`, `OUTBOX=0`, Cloud SQL secret |
| **Final (Neon rollback)** | `fiqa-api-00134-5wx` | `INBOX=0`, `OUTBOX=0`, Neon secret v2, Cloud SQL connector removed |

---

## 3. Steps 4–8 (preflight phase) — PASS

| Step | Result |
|------|--------|
| Admin security | no/wrong token → 401; correct → 200 |
| 3× status preflight | all HTTP 200, `db_preflight.ok=true` |
| Empty drain | HTTP 200, `inbox.claimed=0`, `outbox.claimed=0` |
| Pre-message status | clean queues, `outbox.sent=0` |

---

## 4. Step 10 — post-message status

**HTTP 200**

```json
{
  "db_preflight": {"ok": true},
  "inbox": {"pending": 1, "processing": 0, "failed": 0},
  "outbox": {"pending": 0, "sent": 0, "failed": 0}
}
```

One inbox row enqueued from WeCom callback. User message text in logs: `"Test 094 cloud sql phase 2"` (operator variant of suggested text).

---

## 5. Step 11 — drain limit=1 — FAIL

**HTTP 503**

```json
{
  "detail": "wecom_queue_admin_drain_failed_v1: drain aborted — no new rows claimed after preflight; ... connection to server on socket \"/cloudsql/...caseiq-pilot-pg/.s.PGSQL.5432\" failed: server closed the connection unexpectedly"
}
```

**Cloud Run logs (root cause):**

```text
Cloud SQL connection failed: dial error: failed to dial (connection name = "optimal-disk-472305-e2:us-west1:caseiq-pilot-pg"): dial tcp 34.169.226.245:3307: connect: no route to host
```

Worker claimed inbox row 1, ran `sync_msg` (returned **13 historical messages** from WeCom), then multiple DB writes failed. Inbox worker: `claimed=1, processed=0, failed=1`. Outbox enqueue failed for each slice reply attempt. **No `send_msg` success in this window.**

---

## 6. Step 12 — post-drain status — FAIL

**HTTP 503** — `db_preflight.ok=false` (same Cloud SQL socket error). Recovered after flags rollback to `fiqa-api-00133-ng6`.

---

## 7. Cloud SQL DB state after failure (direct query via public IP)

| Table | State |
|-------|-------|
| `wecom_inbox_events` | 1 row, id=1, **status=processing** (stuck), attempt_count=1 |
| `wecom_reply_outbox` | **13 rows**, all **pending**, `sent=0` |
| `service_records` | 1 row (`case_7d366e317c3d`, status=`new`) |

**Note:** 13 outbox rows came from `sync_msg` replaying historical WeCom messages in the customer session during drain — not 13 duplicate callbacks for one user send.

---

## 8. Stop conditions triggered

| Condition | Triggered? |
|-----------|------------|
| `db_preflight.ok=false` during drain | yes (transient after failure) |
| Admin drain HTTP 500/503 | yes (503) |
| `outbox.sent != 1` | yes (0) |
| `inbox.failed > 0` or stuck processing | yes (stuck processing) |
| `outbox.pending=13` unexplained | explained — sync_msg history batch |

---

## 9. Root cause analysis

**Primary:** Cloud Run **Direct VPC Egress `all-traffic`** + **Cloud SQL Auth Proxy connector** conflict. Preflight (single short query) succeeded; drain (sync_msg + many concurrent DB connections over ~7s) failed with `no route to host` to Cloud SQL proxy port 3307.

**Secondary:** `sync_msg` during drain pulled **13 historical messages**, amplifying DB load on `db-f1-micro` and violating the “one test message” intent operationally (one user send, many synced msgs).

**Not the Neon-class cross-cloud issue** — same GCP region, but **network path misconfiguration** for Cloud SQL from Cloud Run with current VPC egress settings.

---

## 10. Rollback / final state

| Item | Final value |
|------|-------------|
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `SERVICE_RECORD_DATABASE_URL` | **Neon** `fiqa-service-record-database-url:2` |
| Cloud SQL connector | **removed** from Cloud Run |
| `WECOM_QUEUE_ADMIN_TOKEN` | kept (rotate at ops discretion) |
| Cloud SQL instance | left running for investigation (see Q0.9.3 cleanup doc) |

**Step 14 skipped:** 13 pending outbox rows + 1 stuck inbox — no no-op drain run.

---

## 11. Operator verification (step 13)

| Question | Answer |
|----------|--------|
| Phone replies received | **0** (operator confirmed) |
| Broker Workbench Draft Case | 1 server-side (`case_7d366e317c3d`) — operator Workbench check not recorded |
| Duplicate Draft Case | not reported |

Server-side consistent with operator report: `reply_sent=false`, `outbox.sent=0`, no successful `send_msg` in Q0.9.4 window.

---

## 12. Next actions

1. **Fix Cloud SQL connectivity from Cloud Run with Direct VPC `all-traffic`:** options include private IP + VPC peering, Cloud SQL Auth Proxy sidecar with `vpc-egress=private-ranges-only` for DB while keeping NAT for WeCom, or split egress policy — requires ops/architecture decision (no code change in this step).
2. **Clean Cloud SQL smoke DB** before retry: repair-stale inbox id=1; assess whether to truncate `wecom_reply_outbox` pending rows or recreate clean DB.
3. **Limit sync_msg batch** or drain scope in future smokes so one user message does not replay full history (product/ops note — out of Q0.9.4 scope).
4. Re-run Q0.9.4 only after Cloud Run → Cloud SQL path is proven stable under drain load (not just preflight).

---

*No passwords, tokens, or WeCom secrets recorded.*
