# WeCom Q0.11 — sync_msg Watermark Final Phase 2 Smoke

**Date:** 2026-07-04  
**Task:** Q0.11 — Deploy Q0.10 sync_msg watermark fix and run final clean Phase 2 smoke  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com  
**Final verdict:** **PARTIAL** — pipeline/watermark **PASS**; product behavior **FAIL** on first run (generic smoke merged into open Draft). **Q0.11.1 re-smoke PASS** (SQL) — see [`wecom_q0_11_1_resmoke_2026-07-04.md`](wecom_q0_11_1_resmoke_2026-07-04.md).

---

## 1. Pre-check

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Commit (HEAD) | `cb4940b` |
| Q0.10 deploy | Working tree image `gcr.io/optimal-disk-472305-e2/fiqa-api:q0.11` (uncommitted Q0.10 changes) |
| Q0.10 files | `message_processed.py`, `sync_cursor.py`, schema SQL, `docs/wecom_q0_sync_msg_watermark.md` |
| Tests (pre-deploy) | Q0.10-focused suite 57 passed |
| Live smoke before deploy | None |

---

## 2. Schema applied (Cloud SQL `caseiq`)

Applied via operator public-IP path (secret `fiqa-service-record-database-url-cloudsql` v1):

```bash
psql -f services/fiqa_api/db/schema/wecom_message_processed.sql
psql -f services/fiqa_api/db/schema/wecom_sync_cursors.sql
# also re-applied wecom_inbox_events.sql, wecom_reply_outbox.sql
```

Tables verified:

| Table | Present |
|-------|---------|
| `wecom_message_processed` | ✓ |
| `wecom_sync_cursors` | ✓ |
| `wecom_inbox_events` | ✓ |
| `wecom_reply_outbox` | ✓ |

Neon untouched.

---

## 3. Queue cleanup (pre-smoke)

Truncated smoke queue + Q0.10 state tables only:

- `wecom_inbox_events`, `wecom_reply_outbox`, `wecom_message_processed`, `wecom_sync_cursors`

**Not touched:** `service_records=1`, `wecom_reply_dedup=34`, `record_messages`, business tables.

Post-cleanup: all four queue/watermark tables **0 rows**.

---

## 4. Deploy Q0.10

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Deploy revision | **`fiqa-api-00138-t87`** |
| Image | `gcr.io/optimal-disk-472305-e2/fiqa-api:q0.11` |
| GIT_SHA | `cb4940b14-q0.11-uncommitted` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private:latest` |
| Cloud SQL connector | absent |
| VPC egress | `all-traffic` (Direct VPC) |
| Network | `default` / `default` |
| Cloud NAT / WeCom IP | preserved (`8.235.43.132`) |
| Initial flags | `INBOX=0`, `OUTBOX=0`, `SEND_REPLY=1` |

---

## 5. Admin / security / preflight

| Test | HTTP |
|------|------|
| No token | **401** |
| Wrong token | **401** |
| Correct token × 3 | **200**, `db_preflight.ok=true`, queues clean, no `memory_degraded` |

---

## 6. Empty drain (2× pre-message)

Both `POST /api/admin/wecom/queues/drain?limit=1`:

| Run | HTTP | inbox | outbox | failed | memory_degraded |
|-----|------|-------|--------|--------|-----------------|
| 1 | 200 | claimed=0 | claimed=0 | 0 | absent |
| 2 | 200 | claimed=0 | claimed=0 | 0 | absent |

---

## 7. Phase 2 flags enabled

| Item | Value |
|------|-------|
| Phase 2 revision | **`fiqa-api-00139-7hq`** |
| `WECOM_INBOX_QUEUE` | `1` |
| `WECOM_REPLY_OUTBOX` | `1` |
| `WECOM_SLICE_SEND_REPLY` | `1` |

---

## 8. Pre-message status

HTTP **200**, `db_preflight.ok=true`

| Queue / table | Count |
|---------------|-------|
| inbox pending | 0 |
| outbox pending | 0 |
| `wecom_message_processed` | 0 |
| `wecom_sync_cursors` | 0 rows |

---

## 9. Operator test message

**Text:** `smoke test q0.11 sync cursor final`  
**Operator confirmed:** sent

Log (callback 200 path):

```text
wecom_event_normalized_v1 … "text": "smoke test q0.11 sync cursor final" … "msg_id": "Avi9H6pjD9167TwifTHyKWw5cs"
```

---

## 10. Post-message status

HTTP **200**, `db_preflight.ok=true`

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | **1** | 0 | 0 | 0 |
| outbox | 0 | 0 | 0 | 0 |

Exactly one inbox row from callback — **PASS**.

---

## 11. Drain limit=1 (Cloud Run admin)

`POST /api/admin/wecom/queues/drain?limit=1`

| Field | Value |
|-------|-------|
| HTTP | **200** |
| `ok` | true |
| `inbox.claimed` | 1 |
| `inbox.processed` | 1 |
| `inbox.failed` | 0 |
| `outbox.claimed` | 1 |
| `outbox.sent` | 1 |
| `outbox.failed` | 0 |
| `memory_degraded` | absent |
| Cloud SQL `:3307` errors | none |
| Drain duration | ~6.7s |

**Post-drain status:** inbox processed=1, outbox **pending=0**, sent=1, failed=0.

**Contrast with Q0.9.7:** same sync_msg history replay occurred internally, but Q0.10 guard prevented phantom outbox rows (Q0.9.7 had 18 pending after one drain).

---

## 12. Q0.10 behavior verification

| Metric | Value | Expected | Result |
|--------|-------|----------|--------|
| `wecom_reply_outbox` pending after drain | **0** | 0 | **PASS** |
| `wecom_reply_outbox` sent | **1** | 1 | **PASS** |
| Phantom pending outbox (18+) | **0** | 0 | **PASS** |
| `wecom_message_processed` total | **35** | small batch, all deduped | **PASS** — historical msgs recorded, not re-enqueued |
| New smoke msg outcome | `intent_not_actionable` | guide menu path, no draft | **PASS** |
| New smoke `msg_id` | `Avi9H6pjD9167TwifTHyKWw5cs` | — | logged |
| `wecom_sync_cursors` | 1 row, cursor_len=19 | updated after batch | **PASS** |
| `open_kf_id` | `wktLevSgAAM9st2kyoeHS4KQtisH0bww` | — | — |
| `last_sync_at` | 2026-07-05T00:36:41Z | — | — |
| `service_records` count | **1** (unchanged) | no new Draft from generic text | **PASS** (SQL) |

**`wecom_message_processed` outcome breakdown (35 rows from sync_msg batch):**

| Outcome | Count |
|---------|-------|
| `intent_not_actionable` | 26 |
| `start_add_car_click` | 6 |
| `start_card_sent` | 3 |

Historical replay messages were **skipped for outbox enqueue** (Layer 1 guard). Only the new smoke message produced one outbound reply row.

---

## 13. Operator verification

| Question | Operator answer |
|----------|-----------------|
| Phone reply after drain — exactly one? | **Yes** |
| Phone reply — zero? | No |
| Phone reply — more than one? | No |
| Broker Workbench — unintended Add Vehicle Draft for generic smoke text? | **Yes — FAIL** |
| Duplicate Draft Case? | _not reported_ |

Expected: exactly one guide-menu reply; no unintended Draft Case.

**Root cause (product):** Generic/unclear text correctly skipped `ingest_wecom_text_to_active_case`, but when an open Draft was already bound to the same `external_userid` (from pre-existing case + historical `start_add_car_click` replay in the same sync_msg batch), the open-Draft merge path still called `ingest_wecom_text_to_draft_case` and appended the smoke text to the Draft.

**Fix (Q0.11.1):** In `slice.py`, hoist `guided_menu` before open-Draft lookup. Open-Draft merge runs only when the message is actionable: not a guide-menu turn, **or** the text carries Draft collection fields (VIN/ZIP/phone/date/driver). Generic unclear text (including smoke/small talk) falls through to guide-menu-only handling with no Draft side effects.

**Re-smoke:** Required after redeploy to confirm Workbench shows no smoke text on Draft.

---

## 13b. Post-smoke code fix (Q0.11.1)

| Change | File |
|--------|------|
| Skip `ingest_wecom_text_to_draft_case` when `guided_menu` | `services/fiqa_api/wecom/slice.py` |
| Regression test: open Draft + generic smoke → no merge | `tests/test_wecom_message_processed.py` |

---

## 14. No-op drain check

`POST /api/admin/wecom/queues/drain?limit=1`

| Field | Value |
|-------|-------|
| HTTP | 200 |
| inbox.claimed | 0 |
| outbox.claimed | 0 |
| outbox.pending after | 0 |
| sent after | 1 |

**PASS** — safe to run; no duplicate send triggered.

---

## 15. Rollback / final state

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-env-vars=WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

| Item | Value |
|------|-------|
| Rollback revision | **`fiqa-api-00140-hrf`** |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| DB secret | kept on Cloud SQL private IP (`cloudsql-private`) |
| VPC / NAT | unchanged |

Post-rollback status: HTTP **200**, `db_preflight.ok=true`, outbox pending=0, sent=1.

---

## 16. Acceptance criteria scorecard

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Q0.10 deployed | **PASS** |
| 2 | New schema/tables applied | **PASS** |
| 3 | Empty drains pass before live message | **PASS** |
| 4 | One test message → inbox.processed=1 | **PASS** |
| 5 | One outbox row sent | **PASS** |
| 6 | outbox.pending=0 after drain | **PASS** |
| 7 | No historical replay phantom outbox rows | **PASS** (35 msgs deduped; 0 pending) |
| 8 | Phone exactly one reply | **PASS** (operator: 1) |
| 9 | Generic smoke text → no unintended Draft | **FAIL** (merged into open Draft; fix in Q0.11.1) |
| 10 | Flags rolled back after test | **PASS** |
| 11 | Evidence updated | **PASS** (this doc) |
| 12 | No scheduler/cron/PubSub/UI/product changes | **PASS** |

---

## Revision summary

| Stage | Revision |
|-------|----------|
| Q0.10 deploy (flags OFF) | `fiqa-api-00138-t87` |
| Phase 2 enabled | `fiqa-api-00139-7hq` |
| Rollback (flags OFF) | `fiqa-api-00140-hrf` |

---

## Next action

1. Deploy Q0.11.1 fix (`slice.py` guided_menu + collection-field gate on open-Draft merge).
2. Re-run controlled Phase 2 smoke (one message + drain) and confirm Workbench shows **no** smoke text on Add Car Draft.
3. Commit uncommitted Q0.10 + Q0.11.1 code when ready for permanent deploy path.

---

*Related: [`wecom_q0_sync_msg_watermark.md`](../wecom_q0_sync_msg_watermark.md), Q0.9.7 phantom outbox [`wecom_q0_final_phase2_2026-07-04.md`](wecom_q0_final_phase2_2026-07-04.md)*
