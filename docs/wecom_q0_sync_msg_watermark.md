# WeCom Q0.10 — sync_msg Watermark & Message Processed Guard

**Date:** 2026-07-04  
**Status:** Implemented (code + tests; not deployed)

---

## Problem (Q0.9.7)

During Phase 2 live smoke on Cloud SQL private IP, one test WeCom message triggered `kf/sync_msg`, which returned **historical session messages** in addition to the new message. Each historical `msg_id` ran full business logic (intent, draft merge, outbox enqueue), producing **18 phantom pending outbox rows**. Only one reply was sent to the phone, but repeated drains would have sent many more.

Root causes:

1. **`pull_customer_text_messages` always started with `cursor=""`** — no persisted watermark, so WeCom could return already-seen history on each drain.
2. **`wecom_reply_dedup` only guarded outbound sends** — replayed messages still ran classification, draft ingest, and outbox enqueue.
3. **Stale draft binding** — an old `external_userid` → case binding could merge replayed generic text into a missing Draft Case while still enqueuing replies.

---

## Solution (two layers)

### Layer 1 — `wecom_message_processed` (primary)

**Table:** `wecom_message_processed`  
**Module:** `services/fiqa_api/wecom/message_processed.py`

| Column | Purpose |
|--------|---------|
| `msg_id` | Primary key — WeCom message id |
| `open_kf_id` | Optional audit |
| `external_userid` | Optional audit |
| `event_type` | Optional audit |
| `case_id` | Outcome audit |
| `outcome` | e.g. `intent_not_actionable`, `start_card_sent`, `attached` |

**Behavior:**

- At the **start** of each message loop in `process_kf_msg_or_event`, call `claim_message_processed(msg_id)`.
- `INSERT … ON CONFLICT DO NOTHING` — first caller wins and runs business logic.
- Losers skip entirely: no intent, no draft, no outbox enqueue, no reply.
- On processing exception, `release_message_processed(msg_id)` allows inbox-worker retry.
- `wecom_reply_dedup` remains as a second outbound send guard.

### Layer 2 — `wecom_sync_cursors` (incremental sync)

**Table:** `wecom_sync_cursors`  
**Module:** `services/fiqa_api/wecom/sync_cursor.py`

| Column | Purpose |
|--------|---------|
| `open_kf_id` | Primary key |
| `cursor` | Last `next_cursor` from WeCom `sync_msg` |
| `last_sync_at` | Timestamp of last successful batch |

**Behavior:**

- Before `pull_customer_text_messages`, load stored cursor for `open_kf_id`.
- Pass `start_cursor` to first `sync_msg` API call (WeCom supports cursor across calls).
- After a successful batch (no per-message processing failures), persist `next_cursor`.
- Cursor is **not** advanced if any message in the batch raises before completion.

---

## Product behavior changes (Q0.10)

| Area | Change |
|------|--------|
| Generic guide menu (B0) | Unclear/smoke text sends Guide Menu only — **skips** `ingest_wecom_text_to_active_case` and **does not merge** into an open Draft via `ingest_wecom_text_to_draft_case` (Q0.11) |
| Stale draft binding | If `find_open_draft_case_by_external_userid` returns a case id that no longer exists, binding is cleared and message falls through to normal routing |
| Start Card / Add Vehicle | Unchanged — Draft still created only on **Start** click (`start_add_car_click`) |
| Reply copy | Unchanged |

---

## Schema apply (operator, when ready)

Tables are also auto-created on first use (`CREATE TABLE IF NOT EXISTS`), same pattern as `wecom_reply_dedup`:

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_message_processed.sql
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_sync_cursors.sql
```

No migration runner or deploy required for DDL — runtime creates tables if absent.

---

## Verify before next live smoke

1. Deploy revision containing Q0.10 code.
2. Confirm tables exist (or let first admin status / drain create them).
3. Run **2× empty drain** — `claimed=0`, no new outbox rows.
4. Send **one** test message; post-message status should show **inbox pending=1** (not 10+).
5. Drain limit=1 — expect `inbox.processed=1`, `outbox.sent=1`, **outbox pending=0** after drain (not 18).
6. Repeat drain limit=1 — `claimed=0`, phone receives **no second reply**.

---

## Tests

`tests/test_wecom_message_processed.py`:

- 10 historical + 1 new msg_id → only new gets reply on first run; replay skips all
- Repeated drain does not enqueue additional outbox rows
- Generic smoke text does not create Draft Case (B0)
- Add Vehicle → Start click still creates one Draft Case
- Sync cursor passed to API and persisted after batch

Updated: `tests/test_wecom_slice.py`, `tests/test_wecom_active_case.py`, `tests/wecom_pipeline_test_db.py`, `tests/test_wecom_queued_pipeline.py`

---

## Related evidence

- Q0.9.7 phantom outbox: [`wecom_q0_final_phase2_2026-07-04.md`](evidence/wecom_q0_final_phase2_2026-07-04.md)
- Q0.9.4 original sync_msg batch pattern: [`wecom_q0_cloud_sql_smoke_2026-07-04.md`](evidence/wecom_q0_cloud_sql_smoke_2026-07-04.md)

---

*No live smoke or deploy performed in Q0.10 implementation step.*
