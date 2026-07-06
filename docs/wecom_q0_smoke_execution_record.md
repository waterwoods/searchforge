# WeCom Q0 Smoke Test — Execution Record

**Purpose:** Fill-in-the-blank record for **one** real smoke test run against Cloud Run + Neon/Postgres + WeCom.

**Runbook:** Follow steps in [`wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md). Paste evidence into this document as you go.

**Safety:** This record does not deploy, flip flags, or send messages. The operator performs every action manually.

---

## A. Run metadata

| Field | Value |
|-------|-------|
| **Date / time (start)** | |
| **Date / time (end)** | |
| **Operator** | |
| **Git commit** | `git rev-parse HEAD` → |
| **Cloud Run service name** | |
| **Cloud Run revision id (start)** | |
| **Environment** | ☐ local ☐ staging ☐ production-like ☐ production |
| **Test WeCom account used** | |
| **Broker Workbench URL checked** | |

---

## B. Pre-check evidence

| Check | Value |
|-------|-------|
| `SERVICE_RECORD_DATABASE_URL` present? | ☐ yes ☐ no |
| `WECOM_INBOX_QUEUE` current value | |
| `WECOM_REPLY_OUTBOX` current value | |
| `WECOM_SLICE_SEND_REPLY` current value | |
| Schema applied (`wecom_inbox_events`, `wecom_reply_outbox`)? | ☐ yes ☐ no |

**Initial queue status** (`PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status`):

```text
(paste output here)
```

---

## C. Phase 1 — Inbox only

**Config:** `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=0`, `WECOM_SLICE_SEND_REPLY=1`

| Field | Value |
|-------|-------|
| Cloud Run revision id (Phase 1) | |
| Test message sent (exact text) | |
| Message sent timestamp | |

**Expected:** One inbox row appears; no outbox pending until worker runs; reply may be direct (outbox OFF).

**Queue status before drain:**

```text
(paste output here)
```

**Drain command:**

```bash
set -a && source .env.cloudrun && set +a
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

**Drain output:**

```text
(paste output here)
```

**Queue status after drain:**

```text
(paste output here)
```

| Result | Value |
|--------|-------|
| Inbox row processed? | ☐ yes ☐ no |
| Phone reply count | |
| Draft Case count (Broker Workbench) | |
| Duplicate reply? | ☐ yes ☐ no |
| Duplicate Draft? | ☐ yes ☐ no |
| Cloud Run 5xx on callback? | ☐ yes ☐ no |

**Notes / screenshots:**

```text
(paste phone screenshot ref, Workbench screenshot ref, or log snippet)
```

---

## D. Phase 2 — Inbox + Outbox

**Config:** `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`, `WECOM_SLICE_SEND_REPLY=1`

| Field | Value |
|-------|-------|
| Cloud Run revision id (Phase 2) | |
| Test message sent (exact text) | |
| Message sent timestamp | |

**Expected:** One inbox row, one outbox row after drain; exactly one WeCom reply.

**Queue status before drain:**

```bash
curl -sS "$SERVICE_URL/api/admin/wecom/queues/status" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

```text
(paste output here)
```

**Drain command (Q0.8.1 — Cloud Run admin endpoint, preferred for Phase 2):**

```bash
SERVICE_URL="https://<your-cloud-run-url>"
export WECOM_QUEUE_ADMIN_TOKEN="<token>"

curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/drain?limit=1" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN"
```

Local CLI alternative (only if laptop IP whitelisted in WeCom):

```bash
set -a && source .env.cloudrun && set +a
export WECOM_INBOX_QUEUE=1 WECOM_REPLY_OUTBOX=1 WECOM_SLICE_SEND_REPLY=1
PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 1
```

**Drain output:**

```text
(paste output here)
```

**Queue status after drain:**

```text
(paste output here)
```

| Result | Value |
|--------|-------|
| Inbox processed? | ☐ yes ☐ no |
| Outbox sent? | ☐ yes ☐ no |
| Phone received exactly one reply? | ☐ yes ☐ no |
| Broker Workbench shows at most one related Draft Case? | ☐ yes ☐ no |
| Duplicate reply? | ☐ yes ☐ no |
| Duplicate Draft? | ☐ yes ☐ no |

**Notes / screenshots:**

```text
(paste evidence)
```

---

## E. Duplicate safety check

**Method used:** ☐ callback replay (same Token/body) ☐ repeated test message (same text)

| Field | Value |
|-------|-------|
| Action taken | |
| Expected behavior | No duplicate uncontrolled reply; no duplicate open Draft for same test user / add-car flow |

**Queue status before second drain:**

```text
(paste output here)
```

**Second drain output** (`--limit 1`):

```text
(paste output here)
```

**Third drain output** (no-op expected if no pending rows):

```text
(paste output here)
```

| Confirm | Value |
|---------|-------|
| No duplicate uncontrolled reply | ☐ yes ☐ no |
| No duplicate open Draft for same test user / add-car flow | ☐ yes ☐ no |
| Second drain no-op (claimed/processed/sent = 0) | ☐ yes ☐ no ☐ N/A |

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

**Stop triggered?** ☐ no ☐ yes — if yes, note which condition and when:

```text

```

---

## G. Rollback evidence

**Commands used to disable queue flags:**

```bash
gcloud run services update SERVICE_NAME \
  --region REGION \
  --project PROJECT_ID \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

| Field | Value |
|-------|-------|
| Rollback revision id | |
| Rollback timestamp | |

**Final queue status** (`--status`):

```text
(paste output here)
```

| Confirm | Value |
|---------|-------|
| Old synchronous behavior restored or service stable | ☐ yes ☐ no |

**Notes:**

```text

```

---

## H. Final verdict

| Field | Value |
|-------|-------|
| **Verdict** | ☐ PASS ☐ FAIL ☐ PARTIAL |
| **Blockers** (if FAIL or PARTIAL) | |
| **Next action** | |

**Sign-off:**

```text
Operator:
Date:
```

---

*Copy this file per run (e.g. `docs/evidence/wecom_q0_smoke_YYYY-MM-DD.md`) or fill in place and archive. Do not commit secrets or `.env.cloudrun` contents.*
