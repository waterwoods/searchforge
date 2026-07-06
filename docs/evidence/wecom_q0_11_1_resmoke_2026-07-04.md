# WeCom Q0.11.1 — Re-smoke (Draft Merge Fix)

**Date:** 2026-07-04  
**Task:** Deploy Q0.11.1 open-Draft merge fix and controlled Phase 2 re-smoke  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com  
**Final verdict:** **PASS** (pipeline + product SQL checks) — operator phone/Workbench confirmation pending

---

## 1. Deploy Q0.11.1

| Item | Value |
|------|-------|
| Image | `gcr.io/optimal-disk-472305-e2/fiqa-api:q0.11.1` |
| GIT_SHA | `cb4940b14-q0.11.1` |
| Deploy revision (flags OFF) | **`fiqa-api-00141-vj8`** |
| Phase 2 revision | **`fiqa-api-00142-kwq`** |
| Rollback revision | **`fiqa-api-00143-zwh`** |
| DB secret | `fiqa-service-record-database-url-cloudsql-private:latest` |
| Cloud SQL connector | absent |
| VPC egress | `all-traffic` |
| Fix | `slice.py` — skip open-Draft merge for guide-menu text without collection fields |

---

## 2. Pre-smoke cleanup

Truncated (smoke queue tables only):

- `wecom_inbox_events`, `wecom_reply_outbox`, `wecom_message_processed`, `wecom_sync_cursors` → **0**

**Not touched:** `service_records=1`, `record_messages=1`, existing Draft `case_7d366e317c3d`

---

## 3. Preflight (flags OFF)

| Check | Result |
|-------|--------|
| No/wrong token | **401** |
| Status ×3 | **200**, `db_preflight.ok=true` |
| Empty drain ×2 | claimed=0, failed=0 |

---

## 4. Phase 2 enabled

| Flag | Value |
|------|-------|
| `WECOM_INBOX_QUEUE` | `1` |
| `WECOM_REPLY_OUTBOX` | `1` |
| `WECOM_SLICE_SEND_REPLY` | `1` |

Pre-message: inbox pending=0, outbox pending=0, watermark tables=0.

---

## 5. Operator test message

**Text:** `smoke test q0.11.1 generic guide menu final`  
**msg_id:** `AZBf9ZFYC4dkQXzMj3skxGBh5F`  
**Operator confirmed:** sent

Post-message status: inbox **pending=1**, outbox pending=0.

---

## 6. Drain limit=1 (single drain only)

| Field | Value |
|-------|-------|
| HTTP | **200** |
| `inbox.claimed` | 1 |
| `inbox.processed` | 1 |
| `inbox.failed` | 0 |
| `outbox.claimed` | 1 |
| `outbox.sent` | 1 |
| `outbox.failed` | 0 |
| Post-drain outbox pending | **0** |
| `memory_degraded` | absent |

No extra drains run (per protocol).

---

## 7. Q0.11.1 product verification (SQL)

| Check | Before | After | Result |
|-------|--------|-------|--------|
| `service_records` count | 1 | **1** | **PASS** — no new Draft |
| Existing Draft | `case_7d366e317c3d` | same | **PASS** |
| Smoke text in `service_records` | — | **not found** | **PASS** |
| Smoke text in `record_messages` | — | **not found** | **PASS** |
| Smoke `msg_id` outcome | — | `intent_not_actionable`, `case_id=None` | **PASS** |
| `wecom_reply_outbox` pending | 0 | **0** | **PASS** |
| `wecom_reply_outbox` sent | 0 | **1** | **PASS** |
| Historical sync_msg replay phantom outbox | — | **0 pending** (38 msgs deduped) | **PASS** |

**`record_messages` after drain:** only `WeCom: Start / 开始` on existing case — smoke text **not** merged.

**Note:** sync_msg replay still re-processed 38 historical `msg_id`s (including 7× `start_add_car_click` attaching to existing `case_7d366e317c3d`). Watermark prevented duplicate outbox rows; Q0.11.1 prevented smoke text merge into Draft.

---

## 8. Rollback

| Flag | Value |
|------|-------|
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |

Post-rollback status: HTTP **200**, `db_preflight.ok=true`, outbox pending=0, sent=1.

---

## 9. Operator verification (pending)

| Question | Operator answer |
|----------|-----------------|
| Phone received exactly one guide-menu reply? | _pending_ |
| More than one reply? | _pending_ |
| Workbench — no smoke text on Add Car Draft? | _pending_ |
| No new unintended Draft Case? | _pending_ (SQL: no new case) |

---

## 10. Acceptance scorecard

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Q0.11.1 deployed | **PASS** |
| 2 | Empty drains before message | **PASS** |
| 3 | One inbox processed | **PASS** |
| 4 | One outbox sent, pending=0 | **PASS** |
| 5 | No phantom pending outbox | **PASS** |
| 6 | No new Draft Case (SQL) | **PASS** |
| 7 | No smoke text merge into Draft (SQL) | **PASS** |
| 8 | Phone exactly one reply | **PENDING** |
| 9 | Workbench clean | **PENDING** |
| 10 | Flags rolled back | **PASS** |
| 11 | No extra drains/messages | **PASS** |

---

## Revision summary

| Stage | Revision |
|-------|----------|
| Q0.11.1 deploy | `fiqa-api-00141-vj8` |
| Phase 2 ON | `fiqa-api-00142-kwq` |
| Rollback OFF | `fiqa-api-00143-zwh` (live) |

---

*Prior run: [`wecom_q0_11_sync_cursor_final_2026-07-04.md`](wecom_q0_11_sync_cursor_final_2026-07-04.md)*
