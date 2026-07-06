# WeCom Q0.8.5 — DB Stability Root-Cause Analysis and Migration Plan

**Status:** Decision doc (Q0.8.5). No migration executed. No live smoke scheduled.

**Context:** CaseIQ / WeCom AI Insurance Workspace on Cloud Run (`fiqa-api`, region `us-west1`, project `optimal-disk-472305-e2`). Postgres today is Neon serverless (`us-west-2`). Q0.8.4 Phase 2 smoke is **PARTIAL** — callback and enqueue work; drain under load still fails.

**Evidence:** [`docs/evidence/wecom_q0_smoke_2026-07-04.md`](evidence/wecom_q0_smoke_2026-07-04.md) (sections I = Q0.8.2, J = Q0.8.4).

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| What broke? | Cloud Run → Neon connectivity flaps **during drain**, not during idle preflight. |
| Why preflight passes but drain fails? | Preflight is one short `SELECT 1`; drain opens many connections, holds the request ~30–60s, calls WeCom `sync_msg`, then writes again — a very different load profile. |
| Root cause class | **Cross-provider serverless networking** (Cloud Run NAT egress → Neon pooler/direct over public internet), compounded by **connection-per-operation churn** and **no connection pool**. |
| Recommendation | **Prepare Cloud SQL Postgres migration before the next live smoke.** One more Neon hardening pass is acceptable only for a throwaway demo, not for pilot/production. |

---

## 2. What failed in Q0.8.2 and Q0.8.4

### Q0.8.2 (Cloud Run admin drain, Phase 2)

| Step | Result |
|------|--------|
| Callback → inbox enqueue | PASS — HTTP 200, row pending in Postgres |
| Admin auth | PASS |
| Cloud Run `sync_msg` | PASS — NAT egress IP whitelisted (not errcode 60020) |
| Outbox Postgres enqueue | **FAIL** — `memory_degraded` fallback used while Neon flapped mid-drain |
| Inbox completion | **FAIL** — row id=7 stuck `processing` after HTTP 500 on drain |
| Outbox rows in Postgres | **0** |

Errors observed: IPv6 unreachable, IPv4 connection reset, pooled/direct endpoint instability from Cloud Run.

### Q0.8.4 (Q0.8.3 fail-closed + pooled Neon + preflight 3×)

| Step | Result |
|------|--------|
| Q0.8.3 deployed (no memory fallback when flags on) | PASS |
| Secret updated to Neon **pooled** URL (secret v2) | PASS — local preflight OK |
| Admin status 3× before message | PASS — `db_preflight.ok=true` each time |
| Stale repair (id=7) + cleanup drain | PASS |
| Callback → 4 inbox rows for 1 test message | PASS enqueue, **unexpected multiplicity** (WeCom duplicate callbacks; different dedup keys) |
| Cloud Run drain `limit=1` | **FAIL** — HTTP **503** after ~53s |
| Outbox Postgres | **0 rows** — enqueue failed fail-closed (no `memory_degraded`) |
| Inbox id=8 | Stuck **`processing`**; ids 9–11 still **`pending`** |

Q0.8.3 behaved correctly: fail-closed prevented silent outbox loss. The **underlying Neon path is still unstable under real drain**.

---

## 3. Current DB usage (code paths)

All WeCom queue/case tables share one env var: `SERVICE_RECORD_DATABASE_URL` (fallback `DATABASE_URL`), resolved in `service_record_settings.py`. Every Postgres call uses `service_record_connection()` in `service_record_repository.py`:

```62:77:services/fiqa_api/db/service_record_repository.py
@contextmanager
def service_record_connection() -> Generator[Any, None, None]:
    import psycopg

    url = service_record_database_url()
    if not url:
        raise RuntimeError("no service record database URL configured")
    conn = psycopg.connect(url, connect_timeout=3)
    try:
        yield conn
    finally:
        conn.close()
```

**There is no connection pool.** Each `with service_record_connection()` opens and closes a TCP connection.

### 3.1 Table / module map

| Table / concern | Module(s) | When DB is touched |
|-----------------|-----------|-------------------|
| `wecom_inbox_events` | `inbox_queue.py`, `inbox_worker.py`, `queue_admin.py` | Callback enqueue; worker claim/mark; admin status/drain/repair |
| `wecom_reply_outbox` | `reply_outbox.py`, `queue_admin.py` | Slice enqueue; outbox sender claim/mark; admin |
| `wecom_reply_dedup` | `reply_dedup.py`, `slice.py` | Before every outbound reply (`claim_reply_send`) |
| `service_records` + related | `service_record_repository.py`, `case_truth_repository.py`, `active_case_bridge.py` | Draft case create/append/read during slice |
| `intake_sessions` | `session_repository.py` | Separate connection helper (`connect_timeout=10`) — same URL |
| Queue preflight | `queue_db.py` | Admin status/drain/repair **before** claiming rows |

Schema files: `db/schema/wecom_inbox_events.sql`, `wecom_reply_outbox.sql`, `stage1_service_record.sql`, `intake_sessions.sql`, `intake_entities.sql`. `wecom_reply_dedup` is create-if-not-exists in code (no standalone `.sql`).

### 3.2 Connection pattern per admin drain (one inbox row)

Typical sequence for `POST /api/admin/wecom/queues/drain?limit=1`:

1. **Preflight** — `preflight_wecom_queue_db()`: 1 connection, `SELECT 1` + `SELECT 1 FROM wecom_* LIMIT 0`.
2. **Optional status snapshot** — another connection for counts.
3. **Claim inbox row** — 1 connection, short transaction (`FOR UPDATE SKIP LOCKED`, update to `processing`).
4. **Process row** (outside DB transaction):
   - WeCom **`sync_msg`** — external HTTP, **no DB connection held** ✓
   - For each pulled message (batch can be large — no sync cursor today):
     - Case read/write — 1+ connections via `case_truth_repository`
     - `claim_reply_send` — 1 connection
     - `enqueue_wecom_reply` — 1 connection (when `WECOM_REPLY_OUTBOX=1`)
5. **Mark processed/failed** — 1 connection.
6. **Outbox sender** (if inbox succeeded) — claim + send + mark: 3+ connections.
7. **Status after** — preflight + counts again.

**Estimated connections per drain:** ~8–15+ for one inbox row with a multi-message `sync_msg` batch, each a fresh TCP+TLS handshake to Neon.

### 3.3 Transactions and external I/O

| Operation | Transaction length | Holds DB during WeCom API? |
|-----------|-------------------|----------------------------|
| Inbox enqueue (callback) | Short — single INSERT | No |
| Inbox claim | Short — SELECT FOR UPDATE + UPDATE | No |
| Inbox process | **Long wall time**, but DB released after claim | **No** — `sync_msg` runs after claim txn commits |
| Outbox claim | Short | No |
| Outbox send | **WeCom `send_msg` after claim** | **No** |
| Case persist during slice | Short per call | No |

Worker design is correct: **claim → release connection → external work → new connection to mark**. The problem is **many reconnects** after long external work, when Neon or the network path may have gone cold.

### 3.4 Retries and stuck rows

| Location | Retry behavior |
|----------|----------------|
| `queue_db.preflight_wecom_queue_db` | None — fail fast |
| `service_record_connection` | `connect_timeout=3` only — no query retry |
| Inbox/outbox enqueue (Q0.8.3) | Fail-closed when flags on — **no retry** |
| `reply_dedup.claim_reply_send` | On DB error, degrades to in-process (not fail-closed) |
| Worker mark processed/failed | `_try_mark_*` logs error; row stays `processing`/`sending` if mark fails |
| Stale reclaim | Worker reclaims `processing` after `locked_at` + 600s; `repair-stale` admin route |

**How a row gets stuck `processing`:** Row claimed → `sync_msg` + slice succeed → outbox enqueue or `_mark_row_processed` hits Neon flap → mark fails → row stays `processing` until stale timeout or manual repair.

### 3.5 Callback vs worker dedup

- **Callback dedup:** `wecom_inbox_events.dedup_key` UNIQUE — same WeCom Token → duplicate suppressed.
- **One user message, four inbox rows (Q0.8.4):** WeCom sent multiple `kf_msg_or_event` callbacks with **different Tokens** within ~1 minute — each got a new dedup key. This is a WeCom delivery pattern issue, not Postgres; it multiplies drain load.

---

## 4. Current Neon configuration (no secrets)

Inferred from docs, deploy scripts, and Q0.8.4 evidence — **do not treat local `.env.cloudrun` as the live Cloud Run truth** without verifying Secret Manager.

| Setting | Current state |
|---------|---------------|
| Env var | `SERVICE_RECORD_DATABASE_URL` via Secret Manager secret `fiqa-service-record-database-url` (`:latest` → version 2 after Q0.8.4) |
| Provider | Neon serverless Postgres |
| Host region | **`us-west-2`** (Neon) vs Cloud Run **`us-west1`** — cross-region latency and egress |
| Q0.8.4 change | Switched from **direct** host (`*.neon.tech`) to **pooled** host (`*-pooler.*.neon.tech`) |
| `sslmode` | Expected `require` (Neon default; local template uses `sslmode=require`) |
| `channel_binding` | May be present in connection string (local template had it) |
| Pooler suffix | Yes after Q0.8.4 secret v2 |
| `connect_timeout` | **3s** in `service_record_repository`; **10s** in `session_repository` — not in URL |
| Keepalive / pool size | **Not configured** — no PgBouncer session settings in app |
| IPv4/IPv6 | Smoke logs: **IPv6 unreachable** from Cloud Run; **IPv4 reset** on pooled endpoint |
| Memory fallback | **Removed** for queue/outbox when `WECOM_INBOX_QUEUE=1` or `WECOM_REPLY_OUTBOX=1` (Q0.8.3) unless `WECOM_QUEUE_ALLOW_MEMORY_FALLBACK=1` (tests only) |

Deploy reference: `scripts/deploy_cloud_run_core.sh` binds `SERVICE_RECORD_DATABASE_URL=${SM_DB}:latest` when `CLOUD_RUN_USE_SECRET_MANAGER=1`.

---

## 5. Root-cause note

### 5.1 Why idle preflight passes but drain fails

```
  Admin GET /status                    Admin POST /drain?limit=1
  ─────────────────────                ─────────────────────────────
  1× SELECT 1  (~50–200ms)             preflight + claim + process + mark
  No WeCom I/O                         + sync_msg (seconds)
  No case writes                       + N × (case + dedup + outbox)
  Request < 1s                         + outbox sender
                                       8–15+ TCP connections
                                       Request 30–60s
```

Preflight proves **“can I open one connection right now?”** Drain proves **“can I sustain many connections over tens of seconds while also calling WeCom?”** Neon serverless compute and pooler endpoints can wake/sleep or reset connections; Cloud Run NAT egress adds another failure domain. These failures are **intermittent** — status returns 200 a minute later.

### 5.2 Why memory fallback was removed (Q0.8.3)

Q0.8.2 showed the worst case: outbox rows enqueued to **in-memory dedup only** (`memory_degraded`) while Postgres was down — **zero outbox rows in Postgres**, no durable send tracking, risk of untracked sends. Fail-closed is correct for pilot integrity: if Postgres is unavailable, **do not pretend the queue worked**.

### 5.3 Why repeated smoke tests should stop until DB is stable

Each failed Phase 2 run:

- Leaves **stuck `processing` / pending inbox rows**
- May pull **historical `sync_msg` batches** (no cursor) — amplifying work
- Sends **multiple WeCom callbacks** per test message
- Wastes operator time debugging symptoms (outbox empty, 503 drain) instead of the network/DB layer

Further smoke on the same Neon path without architectural change is **unlikely to pass reliably**.

### 5.4 Why Cloud Run + Neon serverless is a poor fit for this worker path

| Factor | Impact |
|--------|--------|
| Serverless DB scale-to-zero / pooler | Cold starts and connection drops under burst |
| Public internet egress | NAT → AWS (Neon) — IPv6/IPv4 path issues observed |
| Cross-region (`us-west1` → `us-west-2`) | Extra latency; more timeout pressure with `connect_timeout=3` |
| Connection-per-call pattern | Amplifies pooler churn; no reuse across slice steps |
| Long-running drain HTTP request | Cloud Run request timeout (60s) aligns with observed 503/504 |

### 5.5 Best-practice architecture (target)

```
WeCom callback ──► Cloud Run (us-west1)
                      │
                      ├─ fast enqueue ──► Postgres (same region, private or connector)
                      │
                      └─ admin drain ──► worker
                            ├─ short DB tx: claim
                            ├─ WeCom sync_msg / send_msg (no DB held)
                            └─ short DB tx: mark + outbox
```

- **Colocated DB:** Cloud SQL Postgres in `us-west1`, same GCP project.
- **Stable connectivity:** Cloud SQL Auth Proxy / connector / private IP — not public Neon pooler over internet.
- **Optional later:** connection pooler (PgBouncer) or SQLAlchemy pool if connection count remains high — but colocation alone likely fixes the observed flaps.

---

## 6. Option A vs Option B

### Option A — Harden current Neon

| Action | Purpose |
|--------|---------|
| Use Neon **pooled** URL with `sslmode=require` | Already done in Q0.8.4 — still failed under drain |
| Force **IPv4-only** (disable IPv6 resolution or Neon IPv4 host) | Address IPv6 unreachable from Cloud Run |
| Add `connect_timeout` to URL if not present | Align with app-level 3s timeout |
| Reduce connection churn | Reuse one connection per drain batch or add small pool — **code change** |
| Bounded retry on **short** writes only (enqueue, mark) | Transient blips — must not retry after WeCom send |
| Never hold connection during `sync_msg` | Already true — keep it |
| Neon **always-on** / paid tier (disable auto-suspend) | Reduce cold-start drops |
| Monitor connection errors | Cloud Run logs + Neon dashboard |

**Pros:** Smallest infra change; no migration.

**Cons:** Still cross-provider serverless; Q0.8.2 and Q0.8.4 **already failed under real drain** after pooled URL; likely more trial-and-error on NAT/IPv6/pooler tuning; not aligned with “real pilot” expectations.

### Option B — Move to Google Cloud SQL Postgres

| Action | Purpose |
|--------|---------|
| Cloud SQL instance in **`us-west1`** (same as Cloud Run) | Low latency, same-region SLA |
| Cloud SQL Python Connector or Unix socket on Cloud Run | Stable auth path; no public internet to third-party DB |
| Migrate schema + optional data | Same SQL files; `wecom_*` + service_records |
| Update Secret Manager `fiqa-service-record-database-url` | Point Cloud Run at Cloud SQL |
| IAM, backups, monitoring in GCP console | Operational fit for CaseIQ on GCP |

**Pros:** Production-grade for Cloud Run; fewer cross-network surprises; easier reasoning for pilot; matches founder preference for real pilot path.

**Cons:** Setup work (instance, user, secrets, validation); **may cost more** than Neon free/low tier; migration must be validated before smoke.

---

## 7. Recommendation

**Prepare Cloud SQL Postgres migration before the next live smoke test.**

| Goal | Path |
|------|------|
| **Real pilot / production** | **Cloud SQL** (Option B) — do not block pilot on another Neon tuning cycle |
| **Quick one-off demo only** | One more Neon hardening pass (Option A tasks below) is **acceptable but not recommended** given two failed drains |

Rationale: Q0.8.3 proved application correctness (fail-closed, preflight, admin auth). Q0.8.4 proved **infrastructure** is the blocker. Colocating Postgres with Cloud Run removes the failure mode we hit twice; Neon hardening is incremental and already partially applied without success under load.

**Do not run Phase 2 smoke again until:** DB layer validated with empty drain from Cloud Run (see §9).

---

## 8. Cloud SQL migration plan (do not execute until approved)

### A. Create Cloud SQL Postgres instance

1. GCP project: `optimal-disk-472305-e2` (or pilot project).
2. Region: **`us-west1`** (match Cloud Run).
3. Instance tier: small pilot (e.g. `db-f1-micro` or `db-g1-small`) — scale later.
4. Postgres version: **15 or 16** (compatible with Neon 15+; confirm Neon version in console before create).
5. Storage: 10–20 GB SSD, autoresize on.
6. Create database (e.g. `caseiq`) and user (e.g. `caseiq_app`) with least privilege.
7. Store connection string in Secret Manager as new version of `fiqa-service-record-database-url` (or new secret + deploy script update).
8. **Do not delete Neon secret version** — keep for rollback.

**Connection options (pick one for Cloud Run):**

| Method | Notes |
|--------|-------|
| **Cloud SQL Auth Proxy / Python Connector** | Recommended for Cloud Run — IAM auth, no public IP required |
| **Private IP + VPC connector** | If Direct VPC egress already used for WeCom NAT — add Cloud SQL private IP to same VPC |
| **Public IP + SSL + authorized networks** | Simplest for first test; tighten for production |

Example connection string shape (values are placeholders):

```text
postgresql://USER:PASS@/caseiq?host=/cloudsql/PROJECT:us-west1:INSTANCE
```

Or with connector library — follow [Cloud Run + Cloud SQL](https://cloud.google.com/sql/docs/postgres/connect-run) for current `fiqa-api` deploy style.

### B. Apply schema

From repo root with Cloud SQL URL in env (operator machine or Cloud Shell):

```bash
set -a && source .env.cloudrun && set +a   # after updating URL to Cloud SQL
# Apply in order:
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/stage1_service_record.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/intake_sessions.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/intake_entities.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/wecom_inbox_events.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/wecom_reply_outbox.sql
```

`wecom_reply_dedup` is created on first use by application code.

Verify:

```bash
PYTHONPATH=. python3 -c "
from services.fiqa_api.wecom.queue_db import preflight_wecom_queue_db
print(preflight_wecom_queue_db())
"
```

### C. Migrate or skip data

| Scenario | Action |
|----------|--------|
| **Next smoke test** | **Clean DB** acceptable — no row migration; repair stale rows on Neon separately if needed |
| **Pilot with existing cases** | `pg_dump` / `pg_restore` selective tables: `service_records`, `record_messages`, `structured_record_data`, `state_history`, `intake_sessions`, optional `wecom_*` if preserving queue history |
| **WeCom queue tables** | Recommend **empty** on Cloud SQL for smoke — old stuck rows (ids 8–11 on Neon) should not carry over |

### D. Update Cloud Run

1. Add new secret version with Cloud SQL URL (or configure Cloud SQL connection on service).
2. If using connector: add Cloud SQL instance annotation to Cloud Run service; grant `roles/cloudsql.client` to runtime SA.
3. Deploy with `bash scripts/deploy_paid_pilot.sh` (or update secret only + new revision if code unchanged).
4. Confirm describe output shows updated secret version — not stale Neon direct URL.

**Flags for validation deploy:** Keep `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0` until empty-drain checks pass.

### E. Verify (before any WeCom message)

1. Admin status 3× from Cloud Run: `db_preflight.ok=true`.
2. **Empty drain:** `POST .../drain?limit=1` → `claimed=0`, HTTP 200, no 503.
3. `repair-stale` dry_run → 0 rows (or repair if needed).
4. Queue counts: `pending=0`, `processing=0`, no stale.
5. Only then enable Phase 2 flags and send **one** test message.

### F. Rollback

1. Point Secret Manager back to Neon URL (previous version).
2. Redeploy or force new revision picking `:latest` after revert.
3. Set `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0`.
4. Keep Neon database intact — Cloud SQL can remain for later retry.
5. Run `repair-stale` on Neon if stuck rows remain.

---

## 9. Alternative — one more Neon hardening pass (demo only)

**Do not run live smoke until tasks 1–6 pass from Cloud Run.**

| # | Task |
|---|------|
| 1 | Confirm Secret Manager `fiqa-service-record-database-url` is **pooled** URL with `sslmode=require` (version pinned; verify Cloud Run revision picked it up) |
| 2 | Add explicit `connect_timeout=5` (or 10) to connection URL for parity with long drains |
| 3 | Force IPv4: use Neon IPv4-compatible pooled host; or set client/network policy so psycopg does not prefer IPv6 |
| 4 | **Code (optional):** bounded retry (2–3 attempts, exponential backoff) on short writes only — enqueue, claim mark, preflight — not on paths after WeCom send |
| 5 | **Code (optional):** reuse one DB connection per drain batch to cut handshake count |
| 6 | Empty drain from Cloud Run admin **3×** — all HTTP 200, no 503 |
| 7 | `repair-stale` until no stuck rows on Neon |
| 8 | Only then Phase 2 with **one** test message |

If task 6 still 503s, **stop** and proceed to Cloud SQL (§8).

---

## 10. Safety checklist — before next live smoke

Complete **all** items; any failure → stop, no WeCom test message.

- [ ] **DB decision executed:** Cloud SQL migrated *or* Neon hardening tasks 1–6 complete
- [ ] **`db_preflight.ok=true`** on admin status **3 times** (from Cloud Run, not only laptop)
- [ ] **Empty drain succeeds** — `POST /api/admin/wecom/queues/drain?limit=1` → HTTP 200, inbox/outbox claimed=0
- [ ] **No pending/processing/stale rows** (or repaired and verified)
- [ ] **No `memory_degraded`** in logs (should be impossible with Q0.8.3 when flags on)
- [ ] **Flags understood:** document exact values for Phase 1 vs Phase 2
- [ ] **Only one test message** per phase; note exact text and timestamp
- [ ] **Rollback ready:** command to set `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0` and revision id recorded
- [ ] **Queue admin token** valid; wrong token returns 401
- [ ] **WeCom sync_msg** whitelisted for Cloud Run NAT IP (not local laptop unless whitelisted)
- [ ] **Operator confirms** phone reply count and Workbench draft count after drain

---

## 11. Out of scope (Q0.8.5)

- No live smoke, WeCom messages, or Phase 2 rerun
- No DB migration execution (plan only)
- No scheduler / Cloud Run Job / PubSub / Cloud Tasks
- No UI or product behavior changes
- No sync_msg cursor fix (noted as follow-up — reduces batch load but does not fix DB path)

---

## 12. References

| Doc / code | Purpose |
|------------|---------|
| [`docs/evidence/wecom_q0_smoke_2026-07-04.md`](evidence/wecom_q0_smoke_2026-07-04.md) | Q0.8.2 / Q0.8.4 execution evidence |
| [`docs/wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md) | Smoke runbook |
| `services/fiqa_api/wecom/queue_db.py` | Preflight fail-closed |
| `services/fiqa_api/wecom/inbox_worker.py` | Claim → process → mark |
| `services/fiqa_api/wecom/queue_admin.py` | Admin drain orchestration |
| `scripts/deploy_cloud_run_core.sh` | Secret Manager binding |

---

*Q0.8.5 — Andy + Cursor — 2026-07-04*
