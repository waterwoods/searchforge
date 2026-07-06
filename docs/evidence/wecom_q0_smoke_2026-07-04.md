# WeCom Q0 Smoke Test — Execution Record

**Purpose:** Fill-in-the-blank record for **one** real smoke test run against Cloud Run + Neon/Postgres + WeCom.

**Runbook:** Follow steps in [`wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md). Paste evidence into this document as you go.

**Safety:** This record does not deploy, flip flags, or send messages. The operator performs every action manually.

---

## A. Run metadata

| Field | Value |
|-------|-------|
| **Date / time (start)** | 2026-07-04 ~12:15 PDT |
| **Date / time (end)** | 2026-07-04 ~19:49 UTC |
| **Operator** | Andy + Cursor agent |
| **Git commit** | `cb4940b14e04d238c7cb4842858f53d1c4285b61` (`feat(track-a): production-ready WeCom networking and authorization`) |
| **Cloud Run service name** | `fiqa-api` |
| **Cloud Run revision id (start)** | `fiqa-api-00118-h42` (deployed via `bash scripts/deploy_paid_pilot.sh`) |
| **Environment** | ☐ local ☐ staging ☑ production-like ☐ production |
| **Test WeCom account used** | (pending Phase 1 send) |
| **Broker Workbench URL checked** | https://ui-smoky-beta.vercel.app |

---

## B. Pre-check evidence

| Check | Value |
|-------|-------|
| `SERVICE_RECORD_DATABASE_URL` present? | ☑ yes ☐ no (Secret Manager on Cloud Run; local `.env.cloudrun` ok) |
| `WECOM_INBOX_QUEUE` current value | unset (OFF) |
| `WECOM_REPLY_OUTBOX` current value | unset (OFF) |
| `WECOM_SLICE_SEND_REPLY` current value | `1` |
| Schema applied (`wecom_inbox_events`, `wecom_reply_outbox`)? | ☑ yes ☐ no |

**Schema apply** (via psycopg — `psql` not installed locally):

```text
Applying services/fiqa_api/db/schema/wecom_inbox_events.sql...
  OK
Applying services/fiqa_api/db/schema/wecom_reply_outbox.sql...
  OK
Tables: ['wecom_inbox_events', 'wecom_reply_dedup', 'wecom_reply_outbox']
```

**Deploy notes:** `bash scripts/deploy_paid_pilot.sh` succeeded. Revision `fiqa-api-00118-h42`, URL `https://fiqa-api-g7zatxrycq-uw.a.run.app`. Health/readyz OK. Queue flags not in deploy bundle → remain OFF.

**Initial queue status** (`PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status`):

```text
WeCom Queue Report
==================
mode: status
max_attempts: 3
stale_timeout_seconds: 600

Inbox (wecom_inbox_events)
  pending:            0
  processing:         0
  processing_stale:   0
  failed:             0
  processed:          0
  exhausted:          0

Outbox (wecom_reply_outbox)
  pending:            0
  sending:            0
  sending_stale:      0
  failed:             0
  sent:               0
  exhausted:          0
```

---

## C. Phase 1 — Inbox only

**Config:** `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=0`, `WECOM_SLICE_SEND_REPLY=1`

| Field | Value |
|-------|-------|
| Cloud Run revision id (Phase 1) | `fiqa-api-00119-m9w` |
| Test message sent (exact text) | `smoke test inbox phase 1` (operator confirmed sent) |
| Message sent timestamp | 2026-07-04 19:24:10 UTC (Cloud Run logs) |

**Expected:** One inbox row appears; no outbox pending until worker runs; reply may be direct (outbox OFF).

**Cloud Run callback evidence:** Two POSTs to `/api/wecom/kf/callback` → both **200**. First enqueue `created: true`; second `duplicate: true` (dedup OK). No 5xx.

**Queue status before drain** (agent check — row already processed; operator likely drained locally ~19:24:28 UTC):

```text
WeCom Queue Report
==================
mode: status
...
Inbox (wecom_inbox_events)
  pending:            0
  processing:         0
  processing_stale:   0
  failed:             0
  processed:          1
  exhausted:          0

Outbox (wecom_reply_outbox)
  pending:            0
  ...
```

**Inbox row SQL:** `(id=1, status=processed, dedup_key=wktLevSg...:ENC44BX7..., event_type=kf_msg_or_event, created_at=2026-07-04 19:24:11 UTC, processed_at=2026-07-04 19:24:28 UTC)`

**Drain command:**

```bash
set -a && source .env.cloudrun && set +a
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

**Drain output:**

```text
WeCom Queue Report
==================
mode: drain
limit: 1
...
Inbox worker
  claimed:   0
  processed: 0
  failed:    0
  skipped:   0

Reply outbox sender
  claimed:   0
  sent:      0
  failed:    0
  skipped:   0
```

(No-op — inbox already processed before agent drain.)

**Queue status after drain:**

```text
Inbox: pending=0, processed=1, failed=0
Outbox: pending=0, sent=0, failed=0
```

| Result | Value |
|--------|-------|
| Inbox row processed? | ☑ yes ☐ no |
| Phone reply count | (operator to confirm — expected ≤1) |
| Draft Case count (Broker Workbench) | 0 in DB last 2h (no new service_records) |
| Duplicate reply? | ☐ yes ☑ no (callback dedup; no evidence of duplicate send) |
| Duplicate Draft? | ☐ yes ☑ no |
| Cloud Run 5xx on callback? | ☐ yes ☑ no |

**Notes / screenshots:**

```text
Callback logs: wecom_inbox_enqueued_v1 created=true then duplicate=true; POST → 200 (1626ms, 277ms).
Worker ran locally (processed_at 19:24:28; no Cloud Run worker logs — expected for manual drain).
```

---

## D. Phase 2 — Inbox + Outbox

**Config:** `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`, `WECOM_SLICE_SEND_REPLY=1`

| Field | Value |
|-------|-------|
| Cloud Run revision id (Phase 2) | `fiqa-api-00120-vvm` (flags: INBOX=1, OUTBOX=1) |
| Test message sent (exact text) | `smoke test outbox phase 2` (operator confirmed sent) |
| Message sent timestamp | 2026-07-04 19:33:18 UTC (Cloud Run logs) |

**Expected:** One inbox row, one outbox row after drain; exactly one WeCom reply.

**Queue status before drain:**

```text
WeCom Queue Report
==================
mode: status
...
Inbox (wecom_inbox_events)
  pending:            1
  processing:         0
  processing_stale:   0
  failed:             0
  processed:          1
  exhausted:          0

Outbox (wecom_reply_outbox)
  pending:            0
  sending:            0
  sending_stale:      0
  failed:             0
  sent:               0
  exhausted:          0
```

**Inbox row before drain:** `(id=3, status=pending, dedup_key=...ENC4xg9Zf..., created_at=2026-07-04 19:33:18 UTC)`

**Drain command:**

```bash
set -a && source .env.cloudrun && set +a
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

**Drain output:**

```text
WeCom Queue Report
==================
mode: drain
limit: 1
...
Inbox worker
  claimed:   1
  processed: 1
  failed:    0
  skipped:   0

Reply outbox sender
  claimed:   0
  sent:      0
  failed:    0
  skipped:   0
```

**Queue status after drain:**

```text
Inbox: pending=0, processed=2, failed=0
Outbox: pending=0, sent=0, failed=0 (no outbox rows created)
```

| Result | Value |
|--------|-------|
| Inbox processed? | ☑ yes ☐ no |
| Outbox sent? | ☐ yes ☑ no |
| Phone received exactly one reply? | ☐ yes ☐ no ☐ unknown (no reply_dedup entry for Phase 2 msg) |
| Broker Workbench shows at most one related Draft Case? | ☐ yes ☑ no ☐ unknown (0 new service_records) |
| Duplicate reply? | ☐ yes ☑ no |
| Duplicate Draft? | ☐ yes ☑ no |

**Notes / screenshots:**

```text
Callback: POST /api/wecom/kf/callback → 200 (19:33:18 UTC). Inbox id=3 enqueued and processed.
Outbox path NOT exercised: local drain host did not have WECOM_REPLY_OUTBOX=1 in .env.cloudrun,
so worker used direct-send path (outbox disabled locally). Runbook gap: drain host must export
WECOM_REPLY_OUTBOX=1 to match Cloud Run during Phase 2 smoke.
No wecom_reply_outbox rows; no new wecom_reply_dedup entries after Phase 2.
```

---

## D.2 Phase 2 rerun (with local flag parity)

**Config:** Cloud Run + local drain host both `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`, `WECOM_SLICE_SEND_REPLY=1`

| Field | Value |
|-------|-------|
| Cloud Run revision id (Phase 2 rerun) | `fiqa-api-00122-9qx` |
| Test message sent (exact text) | `smoke test outbox phase 2 rerun` |
| Message sent timestamp | 2026-07-04 19:45:24 UTC (Cloud Run logs) |

**Local drain host setup:**

```bash
set -a && source .env.cloudrun && set +a
export WECOM_INBOX_QUEUE=1
export WECOM_REPLY_OUTBOX=1
export WECOM_SLICE_SEND_REPLY=1
```

**Baseline status** (before message):

```text
Inbox: pending=0, processed=2, failed=0
Outbox: pending=0, sent=0, failed=0
```

**Queue status before drain** (after message):

```text
Inbox: pending=1, processed=2, failed=0
Outbox: pending=0, sent=0, failed=0
```

**Inbox row:** `(id=5, dedup_key=...ENC3XsQES..., created_at=2026-07-04 19:45:24 UTC)`

**Callback evidence:** POST → **200** (2000ms + 240ms duplicate retry). `wecom_inbox_enqueued_v1` created=true then duplicate=true.

**Drain output:**

```text
Inbox worker
  claimed:   1
  processed: 1
  failed:    0
  skipped:   0

Reply outbox sender
  claimed:   0
  sent:      0
  failed:    0
  skipped:   0
```

**Queue status after drain:**

```text
Inbox: pending=0, processed=3, failed=0
Outbox: pending=0, sent=0, failed=0 (still empty)
```

| Result | Value |
|--------|-------|
| Inbox processed? | ☑ yes ☐ no |
| Outbox sent? | ☐ yes ☑ no |
| Phone received exactly one reply? | ☐ yes ☑ no ☐ unknown |
| Broker Workbench shows at most one related Draft Case? | ☑ yes (0 new service_records) |
| Duplicate reply? | ☐ yes ☑ no |
| Duplicate Draft? | ☐ yes ☑ no |
| Failed rows? | ☐ yes ☑ no |

**Root cause (replay diagnostic):**

```text
wecom_slice_sync_msg_failed_v1 errcode=60020 errmsg=not allow to access from your ip
from ip: 76.175.219.134 (local drain host)

Local drain calls WeCom sync_msg API; IP not in WeCom admin whitelist.
Worker marks inbox processed even when sync_msg fails (no messages pulled → no reply → no outbox).
WECOM_REPLY_OUTBOX=1 was correctly set locally (wecom_reply_outbox_enabled()=True).
```

**Rollback after rerun:** `fiqa-api-00123-6bj` (flags OFF, WECOM_SLICE_SEND_REPLY=1)

```

## E. Duplicate safety check

**Method used:** ☐ callback replay (same Token/body) ☑ repeated test message (same text — not re-sent; verified via no-op drains)

| Field | Value |
|-------|-------|
| Action taken | Two consecutive `drain --limit 1` with `WECOM_REPLY_OUTBOX=1` exported locally; no pending rows |
| Expected behavior | No duplicate uncontrolled reply; no duplicate open Draft for same test user / add-car flow |

**Queue status before second drain:**

```text
Inbox: pending=0, processed=2, failed=0
Outbox: pending=0, sent=0, failed=0
```

**Second drain output** (`--limit 1`):

```text
Inbox worker: claimed=0, processed=0, failed=0
Reply outbox sender: claimed=0, sent=0, failed=0
```

**Third drain output** (no-op expected if no pending rows):

```text
Inbox worker: claimed=0, processed=0, failed=0
Reply outbox sender: claimed=0, sent=0, failed=0
```

| Confirm | Value |
|---------|-------|
| No duplicate uncontrolled reply | ☑ yes ☐ no |
| No duplicate open Draft for same test user / add-car flow | ☑ yes ☐ no |
| Second drain no-op (claimed/processed/sent = 0) | ☑ yes ☐ no ☐ N/A |

---

## F. Stop condition checklist

**If any box below is checked, rollback immediately** (see [G. Rollback evidence](#g-rollback-evidence) and runbook [Stop conditions](wecom_q0_smoke_test.md#i-stop-conditions)).

- [ ] More than one reply for one test message
- [ ] More than one open Draft for same customer / add-car flow
- [ ] Inbox stuck in `processing` / growing `processing_stale`
- [ ] Outbox stuck in `sending` / growing `sending_stale`
- [ ] Drain `failed > 0`
- [ ] Cloud Run 5xx on `/api/wecom/kf/callback`
- [ ] WeCom `send_msg` errcode failure

**Stop triggered?** ☑ no ☐ yes — if yes, note which condition and when:

```text

```

---

## G. Rollback evidence

**Commands used to disable queue flags:**

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

| Field | Value |
|-------|-------|
| Rollback revision id | `fiqa-api-00123-6bj` (final — after Phase 2 rerun) |
| Rollback timestamp | 2026-07-04 ~19:49 UTC |

**Final queue status** (`--status`):

```text
WeCom Queue Report
==================
mode: status
...
Inbox (wecom_inbox_events)
  pending:            0
  processing:         0
  processing_stale:   0
  failed:             0
  processed:          3
  exhausted:          0

Outbox (wecom_reply_outbox)
  pending:            0
  sending:            0
  sending_stale:      0
  failed:             0
  sent:               0
  exhausted:          0
```

| Confirm | Value |
|---------|-------|
| Old synchronous behavior restored or service stable | ☑ yes ☐ no |

**Notes:**

```text
Queue flags removed from Cloud Run env (unset/OFF). WECOM_SLICE_SEND_REPLY=1 retained.
3 processed inbox rows remain in DB (harmless). No outbox rows ever created.
Service healthy post-rollback.
```

---

## H. Final verdict

| Field | Value |
|-------|-------|
| **Verdict** | ☐ PASS ☑ PARTIAL ☐ FAIL |
| **Blockers** (if FAIL or PARTIAL) | Phase 2 outbox path not validated. Rerun confirmed local flag parity (WECOM_REPLY_OUTBOX=1) but drain host IP blocked by WeCom sync_msg (errcode 60020). Inbox rows marked processed despite sync_msg failure — no messages pulled, no outbox enqueue, no phone reply. |
| **Next action** | Run manual drain from a WeCom-whitelisted IP (Cloud Run NAT egress IP per Direct VPC setup, or Cloud Shell / ops VM). Alternatively whitelist operator drain-host IP in WeCom admin. Consider runbook note: sync_msg failure should not mark inbox processed (product fix — out of Q0.8 scope). Re-run Phase 2 drain only after IP access confirmed. |

**Sign-off:**

```text
Operator: Andy
Date: 2026-07-04
Agent: Cursor (Q0.8 smoke execution)
```

---

## I. Q0.8.2 — Cloud Run admin drain Phase 2 retry

**Date / time (start):** 2026-07-04 ~20:10 UTC

### I.1 Pre-check

| Check | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Git commit | `cb4940b14e04d238c7cb4842858f53d1c4285b61` (deploy from working tree incl. Q0.8.1 uncommitted) |
| Q0.8.1 files present | ☑ `wecom_queue_admin_gate.py`, `wecom_queue_admin.py` routes, tests |
| Router mounted | ☑ `app_main.py` |
| Tests (clean env) | ☑ 31 passed — `test_wecom_queue_admin_routes`, `test_wecom_queue_admin`, `test_wecom_queued_pipeline` |

### I.2 Deployment

| Field | Value |
|-------|-------|
| Service | `fiqa-api` |
| Deploy revision | `fiqa-api-00124-w89` (`bash scripts/deploy_paid_pilot.sh`) |
| Flags revision | `fiqa-api-00125-b47` |
| Service URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `WECOM_INBOX_QUEUE` | `1` |
| `WECOM_REPLY_OUTBOX` | `1` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_QUEUE_ADMIN_TOKEN` | set (suffix `...7b9b`) |

### I.3 Admin endpoint security

| Test | HTTP | Result |
|------|------|--------|
| No token | 401 | `wecom_queue_admin_unauthorized` |
| Wrong token | 401 | `wecom_queue_admin_unauthorized` |
| Correct token | 200 | counts only; no payload bodies |

### I.4 Baseline status (before new message)

```json
{"ok":true,"mode":"status","inbox":{"pending":0,"processing":0,"processed":3,"failed":0,"processing_stale":0,"exhausted":0},"outbox":{"pending":0,"sending":0,"sent":0,"failed":0,"sending_stale":0,"exhausted":0}}
```

**Note:** 3 prior `processed` inbox rows from Q0.8 / Q0.8 Phase 2 reruns (ids 1, 3, 5). No pending/failed/stale rows. Safe to proceed with `limit=1` for new test only.

### I.5 Phase 2 test message

| Field | Value |
|-------|-------|
| Message text | `smoke test cloud run outbox phase 2` |
| Sent timestamp | 2026-07-04 20:14:18 UTC |

**Callback:** POST → **200**. Inbox id=7 enqueued (`dedup_key=...ENCEzPjP...`).

### I.6 Status / drain / post-drain

**Status after message:**

```json
{"ok":true,"inbox":{"pending":1,"processing":0,"processed":3,"failed":0},"outbox":{"pending":0,"sent":0,"failed":0}}
```

**First drain attempt:** HTTP **500** — Cloud Run → Neon Postgres intermittent failure (IPv6 unreachable + IPv4 connection closed). Partial worker run before crash.

**Worker evidence (Cloud Run logs ~20:15:21 UTC):**

- `sync_msg` succeeded from Cloud Run NAT IP (WeCom IP blocker resolved vs Q0.8 local drain).
- Multiple historical messages pulled in one batch (no sync_msg cursor).
- Several `wecom_reply_outbox_enqueued_v1` with `backend: memory_degraded` (Postgres flaky during enqueue).
- Test message normalized: `"text": "Smoke test cloud run outbox phase 2"`, msg_id `BUGsikxkLDv7t3mA8EmnKuQYeb`.
- `reply_sent: false` on slice intents — outbox sender did not run (`sent: 0`).
- Inbox row id=7 left **`processing`** (claimed 20:14:27, never marked processed).

**Retry drain (when Postgres recovered):**

```json
{"ok":true,"limit":1,"inbox":{"claimed":0,"processed":0,"failed":0,"skipped":0},"outbox":{"claimed":0,"sent":0,"failed":0,"skipped":0}}
```

**Status after drain attempts:**

```json
{"ok":true,"inbox":{"pending":0,"processing":1,"processed":3,"failed":0,"processing_stale":0},"outbox":{"pending":0,"sent":0,"failed":0}}
```

**Local DB spot-check:** inbox id=7 `processing`, attempt_count=1, locked_at=20:14:27 UTC. **0 outbox rows in Postgres.**

### I.7 Operator verification

| Question | Answer |
|----------|--------|
| Phone reply count | **Unknown — operator confirm** (logs show enqueue only, `outbox.sent=0`; risk if memory_degraded sent outside Postgres tracking) |
| Duplicate Draft | **No** new service_records in DB |
| Stop triggered | ☑ **Yes** — inbox stuck `processing`; drain HTTP 500 during Neon outage |

### I.8 Rollback

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

| Field | Value |
|-------|-------|
| Rollback revision | `fiqa-api-00126-q8r` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_QUEUE_ADMIN_TOKEN` | still set (suffix `...7b9b`) — rotate after ops review |

### I.9 Q0.8.2 verdict

| Field | Value |
|-------|-------|
| **Verdict** | ☐ PASS ☑ PARTIAL ☐ FAIL |
| **Admin endpoint auth** | ☑ PASS (401 without/wrong token; 200 with token; counts only when DB up) |
| **Inbox enqueue** | ☑ PASS (callback 200, pending=1) |
| **Cloud Run sync_msg** | ☑ PASS (NAT IP; not 60020) |
| **Outbox Postgres path** | ☐ FAIL — `memory_degraded` enqueue; 0 Postgres outbox rows; `sent=0` |
| **Inbox worker completion** | ☐ FAIL — row id=7 stuck `processing` after Neon error mid-drain |
| **Blockers** | Intermittent Cloud Run → Neon connectivity (IPv6 + connection reset). Drain endpoint returns HTTP 500 with DB error detail on `OperationalError` (should be 503 sanitized — follow-up). Partial drain + historical sync_msg batch enqueued multiple replies to degraded memory store. |
| **Next action** | 1) Stabilize Cloud Run → Neon (IPv4-only connection string or Neon pooler; verify NAT allows Neon IPs). 2) Reclaim inbox id=7 after stale timeout or manual ops reset. 3) Re-run Phase 2 with stable Postgres before drain. 4) Operator confirm phone reply count. 5) Harden admin drain error handling (503, no stack traces). |

**Sign-off:** Operator: Andy | Agent: Cursor Q0.8.2 | Date: 2026-07-04

---

## J. Q0.8.4 — Deploy Q0.8.3, DB stability, repair stale, Phase 2 rerun

**Date / time (start):** 2026-07-04 ~20:40 PDT

### J.1 Pre-check

| Check | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Git commit | `cb4940b14e04d238c7cb4842858f53d1c4285b61` |
| Q0.8.3 files present | ☑ `queue_db.py`, `queue_admin.py`, `inbox_queue.py`, `reply_outbox.py`, `wecom_drain_queues.py`, `repair-stale` route |
| Tests | ☑ 82 passed — `test_wecom_queue_db`, `test_wecom_queue_admin*`, `test_wecom_queued_pipeline`, inbox/outbox/worker/dedup |

### J.2 Neon / Postgres connection

| Field | Value |
|-------|-------|
| DB URL present | yes (Secret Manager `fiqa-service-record-database-url`) |
| DB type (before) | direct (`***.c-3.us-west-2.aws.neon.tech`) |
| DB type (after) | **pooled** (added `-pooler` suffix; secret version 2) |
| Local pooled preflight | ☑ `preflight_wecom_queue_db()` ok |

### J.3 Deploy Q0.8.3 (preflight flags)

| Field | Value |
|-------|-------|
| Service | `fiqa-api` |
| Deploy revision | `fiqa-api-00127-mt6` (`bash scripts/deploy_paid_pilot.sh`) |
| Preflight flags revision | `fiqa-api-00128-kf2` |
| Service URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_QUEUE_ADMIN_TOKEN` | set (suffix `...7b9b`) |

### J.4 Admin endpoint security

| Test | HTTP | Result |
|------|------|--------|
| No token | 401 | `wecom_queue_admin_unauthorized` |
| Wrong token | 401 | `wecom_queue_admin_unauthorized` |
| Correct token | 200 | counts + `db_preflight.ok=true`; no payload bodies |

### J.5 DB stability preflight (3×)

All 3 attempts: HTTP 200, `db_preflight.ok=true`, no `memory_degraded`, no DB errors.

### J.6 Queue state / stale repair

**Before repair:**

| Queue | pending | processing | stale | failed |
|-------|---------|------------|-------|--------|
| inbox | 0 | 1 | 1 | 0 |
| outbox | 0 | 0 | 0 | 0 |

**repair-stale dry_run=true:** `inbox_repaired=1`, `outbox_repaired=0`

**repair-stale dry_run=false:** `inbox_repaired=1`, `outbox_repaired=0`

**After repair:** inbox `pending=1` (id=7 reclaimed from stale `processing`), no stale/failed rows.

**Cleanup drain (preflight flags, limit=1):** reclaimed id=7 processed — `inbox.claimed=1`, `processed=1`, `failed=0`; outbox `claimed=0` (OUTBOX OFF). Queue clean: `pending=0`, `processed=4`, no stuck rows.

*Note: cleanup may have sent a direct reply for the old Q0.8.2 message (OUTBOX=0 during cleanup). Operator should note any unexpected reply before Phase 2 test.*

### J.7 Phase 2 flags enabled

| Field | Value |
|-------|-------|
| Phase 2 revision | `fiqa-api-00129-fh2` |
| `WECOM_INBOX_QUEUE` | `1` |
| `WECOM_REPLY_OUTBOX` | `1` |
| `WECOM_SLICE_SEND_REPLY` | `1` |

### J.8 Pre-message status (Phase 2)

```json
{"ok":true,"db_preflight":{"ok":true},"inbox":{"pending":0,"processing":0,"processed":4,"failed":0,"processing_stale":0},"outbox":{"pending":0,"sending":0,"sent":0,"failed":0,"sending_stale":0}}
```

Queue clean — ready for new test message.

### J.9 Phase 2 test message

| Field | Value |
|-------|-------|
| Message text (requested) | `smoke test q0.8.4 cloud run db stable phase 2` |
| Sent timestamp | ~2026-07-04 20:53–20:54 UTC |
| Operator confirmed | ☑ yes |

### J.10 Status after message

```json
{"ok":true,"db_preflight":{"ok":true},"inbox":{"pending":4,"processing":0,"processed":4,"failed":0},"outbox":{"pending":0,"sent":0,"failed":0}}
```

**Note:** WeCom delivered **4** callback events within ~1 min (inbox ids 8–11), not 1. Likely duplicate `kf_msg_or_event` notifications for one send. All enqueued with `backend: postgres` (no `memory_degraded`).

| id | status (pre-drain) | created_at (UTC) |
|----|-------------------|------------------|
| 8 | pending | 20:53:27 |
| 9 | pending | 20:53:36 |
| 10 | pending | 20:53:42 |
| 11 | pending | 20:54:26 |

Callbacks: all POST → **200**.

### J.11 Drain (limit=1) — **STOP**

```json
{"detail":"wecom_queue_admin_drain_failed_v1: drain aborted — ... Postgres connection failed from Cloud Run (IPv6 unreachable + IPv4 connection reset on pooled endpoint)"}
```

| Field | Value |
|-------|-------|
| HTTP | **503** (not 500) |
| Duration | ~53s |
| `memory_degraded` | **none** (Q0.8.3 fail-closed OK) |

**Cloud Run worker logs (sanitized):**

- `sync_msg` succeeded from Cloud Run NAT IP
- Multiple historical messages pulled in batch (no sync_msg cursor)
- Reply generated (`guided_menu`, `reply_sent: false`)
- `wecom_slice_reply_send_failed_v1`: outbox enqueue failed — Postgres unreachable from Cloud Run
- `wecom_inbox_worker_batch_v1`: `claimed=1`, `processed=0`, `failed=1`
- Inbox id=8 left **`processing`** (locked_at 20:54:57 UTC)
- **0 outbox rows** in Postgres

### J.12 Post-drain status

After DB recovered (~1 min): HTTP 200, `db_preflight.ok=true`

```json
{"inbox":{"pending":3,"processing":1,"processed":4,"failed":0,"processing_stale":0},"outbox":{"pending":0,"sent":0,"failed":0}}
```

id=8 stuck `processing`; ids 9–11 still `pending`.

### J.13 Operator verification — **PENDING**

| Question | Answer |
|----------|--------|
| Phone reply count (0 / 1 / >1)? | *(operator confirm)* |
| Broker Workbench Draft Case (0 / 1 / duplicate)? | *(operator confirm)* |

*Expected from logs: 0 phone replies (outbox enqueue failed fail-closed; no direct send when OUTBOX=1).*

### J.14 Duplicate / no-op drain

Post-rollback drain attempt: HTTP **504** upstream timeout (~63s). Not completed — queue flags OFF; pending rows remain.

### J.15 Stop conditions

| Condition | Triggered? |
|-----------|------------|
| `db_preflight.ok=false` during drain | ☑ yes (transient) |
| Drain HTTP 500 | ☐ no (503) |
| `memory_degraded` | ☐ no |
| Inbox stuck `processing` | ☑ yes (id=8) |
| Outbox stuck `sending` | ☐ no |
| `failed > 0` in worker | ☑ yes (inbox worker failed=1) |
| Admin accessible without token | ☐ no |

**Stop triggered:** ☑ **yes** — drain 503 + inbox id=8 stuck `processing`

### J.16 Rollback

| Field | Value |
|-------|-------|
| Rollback revision | `fiqa-api-00130-flq` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_QUEUE_ADMIN_TOKEN` | kept (suffix `...7b9b`) |

**Final status (post-rollback):** HTTP 200, `db_preflight.ok=true`, inbox `pending=3 processing=1 processed=4 failed=0`, outbox all zero.

### J.17 Q0.8.4 verdict

| Field | Value |
|-------|-------|
| **Verdict** | ☐ PASS ☑ PARTIAL ☐ FAIL |
| **Q0.8.3 deployed** | ☑ yes |
| **Pooled Neon URL** | ☑ yes (secret v2; local preflight OK) |
| **Preflight 3× before drain** | ☑ yes |
| **Stale repair (id=7)** | ☑ yes |
| **Phase 2 enqueue** | ☑ yes (4 callback rows) |
| **Cloud Run drain inbox** | ☐ partial — claimed id=8, not marked processed |
| **Outbox Postgres path** | ☐ not exercised — 0 rows; enqueue failed fail-closed |
| **Phone reply** | ☐ unknown (expected 0 from logs) |
| **Duplicate Draft** | ☐ unknown |
| **No memory_degraded** | ☑ yes |
| **Flags rolled back** | ☑ yes |

**Blockers:** Cloud Run → Neon connectivity still flaps under drain workload even with pooled URL (IPv6 unreachable from Cloud Run NAT/VPC egress; IPv4 pooled endpoints reset). Preflight passes on idle requests but fails mid-drain. id=8 stuck `processing`; ids 9–11 pending.

**Recommended next action:**

1. Fix Cloud Run egress to Neon — force IPv4-only for Postgres client (disable IPv6 resolution or use Neon **direct** IPv4 endpoint with connection limits); verify Cloud NAT allows outbound to Neon pooler IPs.
2. `repair-stale` id=8 after stale timeout or manual reclaim before next retry.
3. Operator confirm phone reply count.
4. Consider sync_msg cursor to avoid historical message batch on drain.
5. Re-run Phase 2 only after Cloud Run status succeeds 3× **and** a test drain with empty queue completes without 503.

**Sign-off:** Operator: Andy | Agent: Cursor Q0.8.4 | Date: 2026-07-04

---

*Copy this file per run (e.g. `docs/evidence/wecom_q0_smoke_YYYY-MM-DD.md`) or fill in place and archive. Do not commit secrets or `.env.cloudrun` contents.*
