# WeCom Q0.9.7 — Final Phase 2 Live Smoke (Cloud SQL Private IP)

**Date:** 2026-07-04  
**Task:** Q0.9.7 — One controlled Phase 2 live smoke on Cloud SQL private IP path  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com  
**Final verdict:** **PASS** (core Phase 2 live smoke) — phone confirmed exactly one reply; Workbench Draft check pending operator; sync_msg history batch cleaned post-smoke

---

## 1. Pre-check

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Pre-smoke revision | `fiqa-api-00135-8zw` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private:latest` |
| Cloud SQL connector | absent |
| VPC egress | `all-traffic` (Direct VPC) |
| Cloud NAT / WeCom IP | `8.235.43.132` |
| Pre-enable flags | `INBOX=0`, `OUTBOX=0`, `SEND_REPLY=1` |
| Admin token | set (not logged) |

**Pre-check admin status:** HTTP **200**, `db_preflight.ok=true`, all queue counts **0**.

---

## 2. Phase 2 flags enabled

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-env-vars=WECOM_INBOX_QUEUE=1,WECOM_REPLY_OUTBOX=1,WECOM_SLICE_SEND_REPLY=1
```

| Item | Value |
|------|-------|
| Phase 2 revision | **`fiqa-api-00136-6sk`** |
| `WECOM_INBOX_QUEUE` | `1` |
| `WECOM_REPLY_OUTBOX` | `1` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| DB secret | unchanged (`cloudsql-private`) |
| VPC / NAT | unchanged |

---

## 3. Pre-message status

HTTP **200**, `db_preflight.ok=true`

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | 0 | 0 | 0 | 0 |
| outbox | 0 | 0 | 0 | 0 |

---

## 4. Operator test message

**Text sent:** `smoke test q0.9.7 final cloud sql private ip`  
**Phone reply before drain:** **0** (operator confirmed)

Log confirmation:

```text
wecom_event_normalized_v1 … "text": "smoke test q0.9.7 final cloud sql private ip" … "msg_id": "ANmkYqGtKEBRFtY68XAGz7bsGv"
```

---

## 5. Post-message status

HTTP **200**, `db_preflight.ok=true`

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | **1** | 0 | 0 | 0 |
| outbox | 0 | 0 | 0 | 0 |

Exactly one inbox row enqueued from callback — **PASS**.

---

## 6. Drain limit=1 (Cloud Run admin)

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
| Drain duration | ~6.1s |

**Cloud Run logs:** `wecom_queue_db_preflight_ok_v1` throughout; `wecom_reply_outbox_batch_v1` sent=1; outbox row **14** marked sent. No HTTP 500.

**Known side effect (Q0.9.4 pattern):** inbox worker `sync_msg` replayed **historical session messages** during processing, enqueuing **19 outbox rows** total (1 sent + 18 pending). Same root cause as Q0.9.4 — one user send, many synced msgs from WeCom session history.

---

## 7. Post-drain status

HTTP **200**, `db_preflight.ok=true`

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | 0 | 0 | **1** | 0 |
| outbox | **18** | 0 | **1** | 0 |

No stuck processing/sending rows. Inbox clean. **18 pending outbox rows** from sync_msg history batch — not from duplicate callbacks.

---

## 8. Operator verification

| Question | Operator answer |
|----------|-----------------|
| Phone reply before drain | **0** |
| Phone reply after drain | **1** |
| Exactly one reply? | **Yes** — topic selection / guide menu message |
| More than one reply? | **No** |
| Broker Workbench Draft Case count | _pending operator check_ |
| Duplicate Draft Case? | _pending operator check_ |

---

## 9. No-op drain check

**Skipped** — 18 pending outbox rows remain. Draining would trigger additional `send_msg` calls. Per stop conditions: do not drain blindly.

---

## 10. Rollback / final state

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-env-vars=WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

| Item | Value |
|------|-------|
| Rollback revision | **`fiqa-api-00137-hll`** |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| DB secret | **kept** on Cloud SQL private IP (`cloudsql-private`) |

Post-rollback status: HTTP **200**, `db_preflight.ok=true`, flags OFF, 18 pending outbox rows remain (safe while flags OFF).

---

## 10b. Post-smoke pending outbox cleanup (operator-approved)

**Method:** SQL delete of pending rows only — **no drain**, no `send_msg`.

Target: Cloud SQL `caseiq` via operator public IP path (same DB as private IP `10.73.0.3`).

| Before | After |
|--------|-------|
| outbox pending=18, sent=1 | outbox pending=**0**, sent=**1** |
| inbox processed=1 | inbox processed=1 (unchanged) |

```sql
DELETE FROM wecom_reply_outbox WHERE status = 'pending';
-- 18 rows deleted
```

**Not touched:** `service_records`, `wecom_reply_dedup`, sent outbox row (id=14), processed inbox row.

**Post-cleanup admin status:** HTTP **200**, `db_preflight.ok=true`, outbox pending=0, sent=1, failed=0.

Business tables unchanged: `service_records=1`, `wecom_reply_dedup=34`.

---

## 11. Acceptance criteria scorecard

| # | Criterion | Result |
|---|-----------|--------|
| 1 | One test message through Cloud SQL private IP queue path | **PASS** |
| 2 | `inbox.processed=1` | **PASS** |
| 3 | `outbox.sent=1` | **PASS** |
| 4 | Phone receives exactly one reply | **PASS** (operator: 1 guide-menu reply) |
| 5 | No duplicate Draft | **PENDING** (Workbench check outstanding) |
| 6 | No failed/stuck rows | **PASS** (after pending cleanup; inbox processed=1, outbox sent=1) |
| 7 | Evidence updated | **PASS** (this doc) |
| 8 | Flags rolled back | **PASS** |
| 9 | No scheduler/cron/UI/product changes | **PASS** |

---

## 12. Final verdict and next actions

**Verdict: PASS** (core Phase 2 live smoke on Cloud SQL private IP)

| Area | Verdict |
|------|---------|
| Cloud SQL private IP path under live drain load | **PASS** |
| Callback → inbox → drain → worker → outbox → send_msg | **PASS** |
| Phone exactly one reply (guide menu) | **PASS** |
| Queue clean after pending cleanup | **PASS** |
| Broker Workbench Draft / duplicate check | **PENDING** (operator) |
| sync_msg history batch side effect | **NOTED** (18 phantom outbox rows; cleaned without drain) |

**Next actions:**

1. Operator checks Broker Workbench for at most one related Draft Case / no duplicate.
2. Product/ops note: limit `sync_msg` scope in future smokes so one test message does not replay full session history (Q0.9.4 carry-forward).
3. Cloud Run remains on Cloud SQL private IP with queue flags OFF — ready for production cutover decision or next controlled smoke.

**Q0.10 follow-up (2026-07-04):** Code added for `wecom_message_processed` guard + `wecom_sync_cursors` watermark to prevent sync_msg history replay phantom outbox rows. See [`docs/wecom_q0_sync_msg_watermark.md`](../wecom_q0_sync_msg_watermark.md). Deploy Q0.10 before next live smoke.

**Related evidence:**

- Q0.9.6.1 queue cleanup: [`wecom_q0_clean_queue_2026-07-04.md`](wecom_q0_clean_queue_2026-07-04.md)
- Q0.9.6 private IP networking: [`wecom_q0_private_ip_network_2026-07-04.md`](wecom_q0_private_ip_network_2026-07-04.md)
- Q0.9.4 sync_msg batch pattern: [`wecom_q0_cloud_sql_smoke_2026-07-04.md`](wecom_q0_cloud_sql_smoke_2026-07-04.md)

---

*No passwords, tokens, payload bodies, or WeCom secrets recorded.*
