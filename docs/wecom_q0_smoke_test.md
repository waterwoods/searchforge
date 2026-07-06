# WeCom Q0 Queued Pipeline — Real Postgres / Cloud Run Smoke Test

**Purpose:** Safely validate the queued WeCom pipeline against real Neon/Postgres and production-like Cloud Run behavior **without** turning on scheduler, cron, Cloud Run Jobs, Pub/Sub, or Cloud Tasks.

**Prerequisites (Q0.1–Q0.5 shipped):**

| Component | Location |
|-----------|----------|
| Fast ack + inbox queue | `WECOM_INBOX_QUEUE` → `wecom_inbox_events` |
| Inbox worker | `process_pending_wecom_inbox_events()` |
| Reply outbox | `WECOM_REPLY_OUTBOX` → `wecom_reply_outbox` |
| Reply sender | `process_pending_wecom_reply_outbox()` |
| Manual drain / status CLI | `scripts/wecom_drain_queues.py` |

**Related runbooks:**

- WeCom admin / sync_msg diagnostics: [`docs/p16/WECOM_ADMIN_DIAGNOSTIC.md`](p16/WECOM_ADMIN_DIAGNOSTIC.md)
- WeCom readiness report: `PYTHONPATH=. python3 scripts/wecom_readiness.py`
- **Q0.7 execution record (fill-in template):** [`docs/wecom_q0_smoke_execution_record.md`](wecom_q0_smoke_execution_record.md)

---

## Safety rules (read first)

- Use a **test WeCom customer account only** — not real customer traffic.
- Start with **`--limit 1`** on every drain. Do not run large batches first.
- **Do not** enable scheduler/automation yet.
- Both queue flags default **OFF**; turning them OFF restores synchronous callback behavior.
- Manual drain runs **on your machine** (or any host with DB + WeCom secrets) — it does **not** run inside Cloud Run unless you explicitly exec there.
- **Stop immediately** if any [Stop condition](#i-stop-conditions) triggers.

---

## A. Pre-check

Run these before changing flags or sending test traffic.

### A1. Confirm latest code is deployed

```bash
# From repo root — adjust SERVICE_NAME / REGION / PROJECT_ID to your pilot
gcloud run services describe fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --format='value(status.latestReadyRevisionName,status.url)'
```

Record:

- [ ] Cloud Run **revision id** (e.g. `fiqa-api-00042-abc`)
- [ ] Service **URL**

Confirm the revision includes Q0.1–Q0.5 (inbox queue, worker, reply outbox, drain CLI).

### A2. Confirm Postgres URL is configured

On Cloud Run (via console or):

```bash
gcloud run services describe fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --format='yaml(spec.template.spec.containers[0].env)' \
  | grep -E 'SERVICE_RECORD_DATABASE_URL|DATABASE_URL'
```

**Neon / Cloud Run connection guidance (Q0.8.3):**

- Prefer Neon's **pooled** connection string (`-pooler` host) for Cloud Run — direct connections can flap under serverless concurrency.
- If logs show IPv6 unreachable or IPv4 reset (`connection reset by peer`), switch to the **IPv4-compatible pooled endpoint** from the Neon console (Connection details → Pooled connection).
- Confirm Cloud Run uses the intended URL: `SERVICE_RECORD_DATABASE_URL` should match the pooled string you tested locally — not a stale direct URL in a secret version.
- Before drain or smoke, hit admin status **twice** (or run `--status` twice locally) and confirm both return `200` with `db_preflight.ok: true`:

```bash
curl -s -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN" \
  "$CLOUD_RUN_URL/api/admin/wecom/queues/status" | jq '.db_preflight'
```

Locally for drain/status commands:

```bash
# Load pilot secrets — do not commit this file
set -a && source .env.cloudrun && set +a

# Must print a non-empty postgres URL (Neon connection string)
python3 -c "from services.fiqa_api.db.service_record_settings import service_record_database_url as u; print('ok' if u() else 'MISSING')"
```

Expected: prints `ok`.

If missing, drain/status will fail with:

```text
wecom_queue_admin_db_required_v1: set SERVICE_RECORD_DATABASE_URL ...
```

### A3. Confirm queue flags are initially OFF

On Cloud Run, verify **both unset or explicitly 0**:

| Flag | Safe baseline |
|------|----------------|
| `WECOM_INBOX_QUEUE` | `0` or unset |
| `WECOM_REPLY_OUTBOX` | `0` or unset |

```bash
gcloud run services describe fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --format='yaml(spec.template.spec.containers[0].env)' \
  | grep -E 'WECOM_INBOX_QUEUE|WECOM_REPLY_OUTBOX|WECOM_SLICE_SEND_REPLY'
```

Also confirm send is enabled if you expect replies during smoke:

| Flag | Typical smoke value |
|------|---------------------|
| `WECOM_SLICE_SEND_REPLY` | `1` |

### A4. Confirm rollback path

Before enabling queue flags, confirm you can restore synchronous behavior:

- Set `WECOM_INBOX_QUEUE=0`
- Set `WECOM_REPLY_OUTBOX=0`
- Keep `WECOM_SLICE_SEND_REPLY=1` if direct replies are required
- Update Cloud Run env (see [G. Rollback](#g-rollback))

No schema rollback is required — tables are inert when flags are OFF.

### A5. Optional — WeCom API readiness

```bash
cd /path/to/searchforge
PYTHONPATH=. python3 scripts/wecom_readiness.py --env-file .env.cloudrun
```

Expect: callback PASS, gettoken PASS, sync_msg PASS (errcode 0).  
If sync_msg fails, fix admin config per [`WECOM_ADMIN_DIAGNOSTIC.md`](p16/WECOM_ADMIN_DIAGNOSTIC.md) **before** queue smoke.

---

## B. Apply schema manually

Apply once per Neon database (idempotent — safe to re-run).

```bash
cd /path/to/searchforge
set -a && source .env.cloudrun && set +a

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_inbox_events.sql

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_reply_outbox.sql
```

Verify tables exist:

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -c "\dt wecom_*"
```

Expected tables:

- `wecom_inbox_events`
- `wecom_reply_outbox`

Optional — reply dedup table (created automatically on first send; not required pre-smoke):

```sql
-- wecom_reply_dedup (auto-created by reply_dedup module)
```

---

## C. Check queue status before test

```bash
cd /path/to/searchforge
set -a && source .env.cloudrun && set +a

PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
```

Expected baseline (clean queue):

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
  ...
Outbox (wecom_reply_outbox)
  pending:            0
  sending:            0
  sending_stale:      0
  failed:             0
  ...
  exhausted:          0
```

JSON alternative:

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status --json
```

**Do not proceed** if unexpected pending/stale/failed rows exist — investigate or clean up first.

Optional SQL spot-check:

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -c "
  SELECT status, COUNT(*) FROM wecom_inbox_events GROUP BY status;
  SELECT status, COUNT(*) FROM wecom_reply_outbox GROUP BY status;
"
```

Record: [ ] **status output before test** (paste or screenshot)

---

## D. Phase 1 — Inbox only

**Goal:** Callback fast-acks into Postgres; worker processes inline; replies still go **direct** (outbox OFF).

### D1. Enable inbox queue only

Update Cloud Run env (example — adjust service/region/project):

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

Wait for new revision to become ready. Record revision id: _______________

### D2. Send exactly one test message

From **personal WeChat** (test account), send **one** text message to the bound 客服账号.

Example: `smoke test inbox phase 1`

Expected **immediately after send**:

- [ ] Cloud Run callback returns **200** quickly (check logs — no long sync_msg in callback path)
- [ ] Customer may **not** receive a business reply yet (reply waits for manual drain)
- [ ] One new row in `wecom_inbox_events`

### D3. Check status

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
```

Expected:

- [ ] `inbox pending: 1` (approximately — one new row)
- [ ] `outbox pending: 0`

### D4. Manual drain (limit 1)

Drain requires **Postgres URL + WeCom secrets** on the machine running the command:

```bash
set -a && source .env.cloudrun && set +a
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

Expected drain output:

```text
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
  ...
```

### D5. Verify Phase 1

- [ ] Inbox row status → `processed` (SQL or `--status` shows pending back to 0)
- [ ] **No duplicate Draft Case** for the test customer in Broker Workbench
- [ ] Phone receives **at most one** reply (direct send — `WECOM_REPLY_OUTBOX=0`)
- [ ] Cloud Run logs show `wecom_inbox_worker_batch_v1` / `wecom_slice_*` — no callback 5xx

Optional SQL:

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -c "
  SELECT id, status, dedup_key, event_type, created_at, processed_at
  FROM wecom_inbox_events ORDER BY id DESC LIMIT 5;
"
```

---

## E. Phase 2 — Inbox + Outbox

**Goal:** Full queued pipeline — callback → inbox → worker → outbox enqueue → manual sender → one WeCom reply.

### E1. Enable both queue flags

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=1,WECOM_SLICE_SEND_REPLY=1
```

Record revision id: _______________

### E2. Send exactly one test message

From the **same test WeCom account**, send **one new** message (different text so intent/dedup is unambiguous):

Example: `smoke test outbox phase 2`

Expected **immediately after send**:

- [ ] Fast callback 200
- [ ] **No immediate reply** on phone (business path enqueues outbox; sender not run yet)

### E3. Check status

**Preferred for Phase 2 (Cloud Run NAT IP — sync_msg whitelisted):**

```bash
SERVICE_URL="https://fiqa-api-g7zatxrycq-uw.a.run.app"  # your Cloud Run URL
curl -sS "$SERVICE_URL/api/admin/wecom/queues/status" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

**Local CLI** (works for counts; Phase 1 drain OK; Phase 2 drain may fail sync_msg if laptop IP not whitelisted):

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
```

Expected before drain:

- [ ] `inbox pending: 1`
- [ ] `outbox pending: 0` (outbox row created only after worker runs)

### E4. Manual drain (limit 1)

**Preferred for Phase 2 — drain inside Cloud Run** (uses whitelisted NAT egress IP for `sync_msg`):

Prerequisites:

- Set `WECOM_QUEUE_ADMIN_TOKEN` on Cloud Run before smoke (long random secret; never commit).
- Cloud Run env must have `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`, `WECOM_SLICE_SEND_REPLY=1`.

```bash
SERVICE_URL="https://fiqa-api-g7zatxrycq-uw.a.run.app"
export WECOM_QUEUE_ADMIN_TOKEN="<your-admin-token>"  # from Secret Manager or env — do not log

curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/drain?limit=1" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

Expected JSON (abbreviated):

```json
{
  "ok": true,
  "limit": 1,
  "inbox": {"claimed": 1, "processed": 1, "failed": 0, "skipped": 0},
  "outbox": {"claimed": 1, "sent": 1, "failed": 0, "skipped": 0},
  "status_before": { "...": "..." },
  "status_after": { "...": "..." }
}
```

Alternative header: `X-Admin-Token: $WECOM_QUEUE_ADMIN_TOKEN`

**Local CLI drain** (Phase 1 only, or when operator laptop IP is whitelisted in WeCom admin):

```bash
set -a && source .env.cloudrun && set +a
export WECOM_INBOX_QUEUE=1 WECOM_REPLY_OUTBOX=1 WECOM_SLICE_SEND_REPLY=1
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

If local drain hits `errcode=60020 not allow to access from your ip`, use the Cloud Run admin drain endpoint above instead.

Expected:

```text
Inbox worker
  claimed:   1
  processed: 1
  failed:    0
Reply outbox sender
  claimed:   1
  sent:      1
  failed:    0
```

Exit code: **0**. If exit code **1**, see [Stop conditions](#i-stop-conditions).

### E5. Verify Phase 2

- [ ] One inbox row → `processed`
- [ ] One outbox row → `sent`
- [ ] Phone receives **exactly one** reply
- [ ] Broker Workbench shows **at most one** related Draft Case for this test flow
- [ ] Cloud Run logs: `wecom_reply_enqueued_v1` during worker processing; `wecom_reply_outbox_batch_v1` during drain — **no** direct `send_msg` from callback path

Optional SQL:

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -c "
  SELECT id, status, msg_id, reply_type, sent_at, errcode
  FROM wecom_reply_outbox ORDER BY id DESC LIMIT 5;
"
```

---

## F. Duplicate safety check

**Goal:** Confirm idempotency — no duplicate replies or duplicate open Draft Cases.

### F1. Callback retry simulation (if available)

If you can safely replay the **same** WeCom callback (same Token / same encrypted body) — e.g. from saved logs in a staging environment — POST it twice.

Expected:

- [ ] Still **one** inbox row (dedup_key unique constraint)
- [ ] After one drain cycle, still **one** reply

If callback replay is not available, use manual message repeat:

### F2. Repeat customer message (manual)

Send the **same text again** from the test account (simulates customer repeat / sync_msg re-delivery risk).

Run status, then drain with limit 1:

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

Verify:

- [ ] **No uncontrolled duplicate replies** on phone
- [ ] **No duplicate open Draft Cases** for same customer / same Add Vehicle flow
- [ ] Reply dedup / outbox dedup logs may show `duplicate` or `reply_skipped_duplicate_v1` — that is OK

Run drain a **second** time — should be no-op:

### F3. Q0.10 — sync_msg replay guard (before live smoke)

After deploying Q0.10 (`wecom_message_processed` + `wecom_sync_cursors`):

- [ ] One test message → post-message inbox pending should be **1** (not 10+ from history replay)
- [ ] Drain limit=1 → `outbox.sent=1`, post-drain outbox **pending=0**
- [ ] Second drain limit=1 → `claimed=0`, **no second phone reply**
- [ ] Optional SQL: `SELECT COUNT(*) FROM wecom_message_processed;` grows by ~1 per new message, not by session history size

See [`docs/wecom_q0_sync_msg_watermark.md`](wecom_q0_sync_msg_watermark.md).

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

Expected second drain:

```text
  claimed:   0
  processed: 0
  sent:      0
```

---

## G. Rollback

Restore synchronous callback behavior after smoke test.

### G1. Disable queue flags

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

Or unset entirely (equivalent to OFF for these flags):

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project YOUR_PROJECT_ID \
  --remove-env-vars WECOM_INBOX_QUEUE,WECOM_REPLY_OUTBOX
```

Record rollback revision id: _______________

### G2. Confirm old behavior restored

Send one test message. Expected:

- [ ] Callback processes **inline** (no new inbox pending row, or inbox unused)
- [ ] Reply sent synchronously when `WECOM_SLICE_SEND_REPLY=1`
- [ ] Cloud Run logs show slice path in callback request (not enqueue-only)

```bash
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
```

Pending counts should not grow from new synchronous traffic.

### G3. Leave schema in place

Tables `wecom_inbox_events` and `wecom_reply_outbox` can remain — they are harmless when flags are OFF.

---

## H. What to capture (evidence checklist)

**Q0.7 — use the execution record template:** Open [`docs/wecom_q0_smoke_execution_record.md`](wecom_q0_smoke_execution_record.md) before starting. Fill sections A–H as you execute each phase. Copy the file per run (e.g. `docs/evidence/wecom_q0_smoke_YYYY-MM-DD.md`) or archive the filled-in version after rollback.

Save these for the smoke test record:

| # | Evidence | Phase |
|---|----------|-------|
| 1 | Cloud Run **revision id** (before, after each flag change, after rollback) | A, D, E, G |
| 2 | Env flags screenshot or `gcloud describe` output | A, D, E, G |
| 3 | `--status` output **before** test | C |
| 4 | `--status` output **after** message, **before** drain | D, E |
| 5 | `--status` output **after** drain | D, E, F |
| 6 | Drain command output (`--limit 1`) | D, E, F |
| 7 | Phone screenshot — reply count/timing | D, E, F |
| 8 | Broker Workbench screenshot — Draft Case count | D, E, F |
| 9 | Inbox row count / last 5 rows SQL | D, E |
| 10 | Outbox row count / last 5 rows SQL | E, F |
| 11 | Duplicate Draft appeared? **Y/N** | F |
| 12 | Duplicate reply appeared? **Y/N** | F |
| 13 | Cloud Run callback log snippet (200, no 5xx) | D, E |
| 14 | Any `failed > 0` in drain output? **Y/N** | D, E |

Legacy inline paste block (prefer the [execution record template](wecom_q0_smoke_execution_record.md)):

```text
Smoke test date:
Operator:
Cloud Run revision (start):
...
```

---

## Q0.7 — Real environment smoke execution

**Goal:** Execute this runbook against real Cloud Run + Neon/Postgres + WeCom and capture evidence — **manually**, with no automation, deploy, or flag changes from scripts.

### Before you start

1. Read [Safety rules](#safety-rules-read-first) and [Stop conditions](#i-stop-conditions).
2. Open [`docs/wecom_q0_smoke_execution_record.md`](wecom_q0_smoke_execution_record.md) — paste outputs into sections A–H as you go.
3. Load local secrets for drain/status (drain does **not** run inside Cloud Run):

```bash
cd /path/to/searchforge
set -a && source .env.cloudrun && set +a
```

### Operator command snippets

Replace `SERVICE_NAME`, `REGION`, and `PROJECT_ID` (e.g. `fiqa-api`, `us-west1`).

**View current Cloud Run env vars (flags + DB URL presence):**

```bash
gcloud run services describe SERVICE_NAME \
  --region REGION \
  --project PROJECT_ID \
  --format='yaml(spec.template.spec.containers[0].env)' \
  | grep -E 'SERVICE_RECORD_DATABASE_URL|WECOM_INBOX_QUEUE|WECOM_REPLY_OUTBOX|WECOM_SLICE_SEND_REPLY'
```

**Set queue flags (operator only — wait for new revision before sending test messages):**

```bash
# Phase 1 — inbox only
gcloud run services update SERVICE_NAME \
  --region REGION \
  --project PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1

# Phase 2 — inbox + outbox
gcloud run services update SERVICE_NAME \
  --region REGION \
  --project PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=1,WECOM_SLICE_SEND_REPLY=1

# Rollback
gcloud run services update SERVICE_NAME \
  --region REGION \
  --project PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

**Queue status (local machine, DB URL loaded):**

```bash
set -a && source .env.cloudrun && set +a
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
```

**Manual drain one batch (local machine, DB URL + WeCom secrets loaded):**

```bash
set -a && source .env.cloudrun && set +a
export WECOM_INBOX_QUEUE=1 WECOM_REPLY_OUTBOX=1 WECOM_SLICE_SEND_REPLY=1
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

**Cloud Run admin drain (Q0.8.1 — Phase 2 when local IP blocked by WeCom):**

Set on Cloud Run before use: `WECOM_QUEUE_ADMIN_TOKEN=<long-random-secret>`

```bash
SERVICE_URL="https://fiqa-api-g7zatxrycq-uw.a.run.app"
export WECOM_QUEUE_ADMIN_TOKEN="<token>"  # do not commit or log

curl -sS "$SERVICE_URL/api/admin/wecom/queues/status" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"

curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/drain?limit=1" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

Rollback queue flags after smoke; rotate/remove `WECOM_QUEUE_ADMIN_TOKEN` if desired.

### Execution flow

| Step | Runbook section | Record section |
|------|-----------------|----------------|
| Pre-check | [A](#a-pre-check), [B](#b-apply-schema-manually), [C](#c-check-queue-status-before-test) | A, B |
| Phase 1 | [D](#d-phase-1--inbox-only) | C |
| Phase 2 | [E](#e-phase-2--inbox--outbox) | D |
| Duplicate check | [F](#f-duplicate-safety-check) | E |
| Rollback | [G](#g-rollback) | G |
| Verdict | — | H |

On any [stop condition](#i-stop-conditions), check the box in record section F, run [rollback](#g-rollback), then complete G and H (verdict FAIL or PARTIAL).

---

## I. Stop conditions

**Stop the smoke test immediately** if any of these occur:

| Condition | Action |
|-----------|--------|
| **More than one reply** for one intentional test message | Rollback flags (G); capture logs + outbox rows |
| **More than one open Draft** for same customer / Add Vehicle flow | Rollback; inspect case_store + worker logs |
| Inbox row stuck in `processing` with growing `processing_stale` | Run repair-stale (below) or wait for stale reclaim; inspect `error_message`; rollback if needed |
| Outbox row stuck in `sending` with growing `sending_stale` | Same as above |
| Admin drain **503** or `db_preflight` failure | Fix Neon pooled URL on Cloud Run; confirm status succeeds twice before retry — no drain until DB stable |
| Logs show `memory_degraded` enqueue with queue flags ON | **Stop** — Q0.8.3+ should fail closed; redeploy fix before retry |
| Drain returns **`failed > 0`** | Capture full drain output; check `error_message` / `errcode` on failed rows |
| Cloud Run **5xx** on `/api/wecom/kf/callback` | Rollback queue flags; fix before retry |
| WeCom `send_msg` **errcode ≠ 0** | See [`WECOM_ADMIN_DIAGNOSTIC.md`](p16/WECOM_ADMIN_DIAGNOSTIC.md); do not retry in a loop |
| Unexpected **`exhausted > 0`** before test | Investigate stuck rows; do not drain large batches |

Drain exit codes:

- `0` — success, no failures in batch
- `1` — drain ran but inbox or outbox had failures
- `2` — missing DB URL or invalid args

---

## J. Operator notes

1. **Start with `--limit 1`.** Only increase after a clean Phase 1 + Phase 2.
2. **Do not test with real customer traffic.** Dedicated test 客服账号 + test WeChat identity only.
3. **Do not enable scheduler/cron/Cloud Run Job/Pub/Sub/Cloud Tasks** as part of this smoke — manual drain only.
4. **Status is cheap; drain is not.** Run `--status` freely; each drain may call WeCom APIs.
5. **Drain host needs secrets.** Local drain uses `.env.cloudrun` for `SERVICE_RECORD_DATABASE_URL`, `WECOM_KF_SECRET`, callback keys, etc. **Phase 2:** if WeCom blocks local `sync_msg` (errcode 60020), drain via Cloud Run admin endpoint (`WECOM_QUEUE_ADMIN_TOKEN`) — see [E4](#e4-manual-drain-limit-1).
6. **Flags live on Cloud Run; drain runs on Cloud Run for Phase 2.** Callback enqueues on Cloud Run; Phase 2 drain should run inside Cloud Run so `sync_msg` uses the whitelisted NAT IP. Local CLI remains valid for status counts and Phase 1 when IP is allowed.
7. **Phase order matters.** Complete Phase 1 (inbox only) before Phase 2 (inbox + outbox).
8. **Rollback is flag-only.** No deploy required if you use `gcloud run services update --update-env-vars`.
9. **Pending rows are normal** between message send and manual drain — that is the intended queued behavior.
10. **Re-run readiness** after any secret or admin change: `python3 scripts/wecom_readiness.py`
11. **Repair stuck rows (Q0.8.3):** After a DB flap left rows in `processing`/`sending`, reset only **stale** rows (default: locked > 600s ago):

```bash
# CLI (local or Cloud Shell with DB URL)
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --repair-stale --dry-run   # count first
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --repair-stale

# Cloud Run admin
curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/repair-stale?dry_run=true" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/repair-stale" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

Documented SQL (equivalent — only stale rows):

```sql
UPDATE wecom_inbox_events
SET status = 'pending', locked_at = NULL, updated_at = NOW()
WHERE status = 'processing'
  AND locked_at IS NOT NULL
  AND locked_at < NOW() - INTERVAL '600 seconds';
```
11. **Cloud Run admin drain (Q0.8.1):** set `WECOM_QUEUE_ADMIN_TOKEN` on Cloud Run; rotate/remove after smoke. Never log or expose the token. Endpoint does not enable queue flags — only drains existing rows.

---

## Quick reference

```bash
# Status (DB URL only)
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status

# Drain one batch (DB + WeCom secrets)
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1

# JSON for logs
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1 --json

# Apply schema
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/wecom_inbox_events.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/wecom_reply_outbox.sql

# Enable queued pipeline (Phase 2)
gcloud run services update fiqa-api --region us-west1 --project YOUR_PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=1,WECOM_SLICE_SEND_REPLY=1

# Rollback
gcloud run services update fiqa-api --region us-west1 --project YOUR_PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1

# Phase 2 drain inside Cloud Run (Q0.8.1 — preferred when local IP blocked)
curl -sS "$SERVICE_URL/api/admin/wecom/queues/status" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/drain?limit=1" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

---

*Q0 smoke test plan — manual validation only. Q0.7 adds the [execution record template](wecom_q0_smoke_execution_record.md). No production automation included.*
