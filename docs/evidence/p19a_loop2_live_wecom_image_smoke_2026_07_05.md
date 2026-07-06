# P19A Loop 2 — Live WeCom Image Smoke Evidence

**Date:** 2026-07-05  
**Branch:** `sprint/p16-trust-layer`  
**Deploy commit:** `605c652` (`feat: add WeCom media intake foundation`)  
**Verdict:** **PASS (deploy + live smoke)**

---

## 1. Pre-check (before deploy)

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Working tree | clean |
| Commit `605c652` | present |
| QA gate (`--cloud-api`) | **PASS** |
| Cloud SQL | `gcp-cloud-sql` @ `10.73.0.3` db=`caseiq` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` |
| Neon | not QA truth |
| GCS bucket | `caseiq-wecom-media-qa` |

---

## 2. Dependency check

| Item | Result |
|------|--------|
| `requirements.txt:46` | `google-cloud-storage>=2.14.0` |
| Cloud Build install | `google-cloud-storage-3.12.0` |
| Dockerfile | `services/fiqa_api/Dockerfile.cloudrun` → root `requirements.txt` |

---

## 3. Focused tests (pre-deploy)

| Suite | Result |
|-------|--------|
| `tests/test_wecom_media_intake.py` | 26 passed |
| WeCom regression bundle (7 files) | 129 passed |

---

## 4. Deploy

| Item | Value |
|------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| Project | `optimal-disk-472305-e2` |
| **Revision** | `fiqa-api-00149-jj4` |
| **URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA (runtime) | `605c652d1` |
| DB secret (unchanged) | `fiqa-service-record-database-url-cloudsql-private` |
| `WECOM_MEDIA_GCS_BUCKET` | unset → default `caseiq-wecom-media-qa` |
| `/health/live` | OK |
| `/readyz` | OK |
| QA gate post-deploy | **PASS** |

**Not changed this loop:** Cloud SQL instance, VPC/NAT/static IP, WeCom callback URL, Vercel/frontend, Neon, schema.

---

## 5. Baseline (before live image)

| Metric | Value |
|--------|-------|
| `service_records` total | 14 |
| `wecom_media_intake` holding cases | 0 |
| Records with `case_attachments` | 0 |
| GCS `wecom/` prefix | empty |

---

## 6. Live image smoke

| Item | Value |
|------|-------|
| **Send time (operator)** | ~2026-07-05 20:50 PDT |
| **Cloud Run receive (UTC)** | `2026-07-06T03:50:47Z` |
| **msgtype** | `image` |
| **msg_id (partial)** | `Ajm6RvwvCwa8…` |
| **Customer label** | `企业微信客户（尾号 mxcw）` |
| **external_userid tail** | `…mxcw` (masked in reports) |

### 6.1 Cloud Run log chain (fiqa-api-00149-jj4)

1. `POST /api/wecom/kf/callback` → 200
2. `wecom_sync_msg_pulled_v1` — `media_message_count: 1`
3. `wecom_media_event_normalized_v1` — `msgtype: image`, `msg_id` present
4. `wecom_media_download_ok_v1` — `size_bytes: 237473`, `content_type: image/jpeg`
5. `wecom_media_gcs_upload_ok_v1` — bucket `caseiq-wecom-media-qa`, object under `wecom/…/2026/07/<msg_id>.jpg`
6. `wecom_media_intake_ok_v1` — `case_id: case_82092cc39bae`, `attachment_id: att_92f722de864d`, `active_case_outcome: media_unassigned`
7. `wecom_slice_reply_sent_v1` — `sent: true`
8. Follow-up duplicate callbacks at same timestamp — `message_count: 0` (cursor advanced, no re-processing)

No error stack traces. No OCR/vision log lines.

---

## 7. GCS verification

| Check | Result |
|-------|--------|
| Bucket | `caseiq-wecom-media-qa` (not `smartsearchx-bucket`) |
| Object path pattern | `wecom/<external_userid>/2026/07/<msg_id>.jpg` |
| Object exists | **yes** |
| Size | `237473` bytes (> 0) |
| MIME (from download) | `image/jpeg` |
| Public URL generated | **no** (`gs://` private URI only) |

---

## 8. DB / API verification

### Case (unassigned holding path)

| Field | Value |
|-------|-------|
| `case_id` | `case_82092cc39bae` |
| `service_lane` | `wecom_media_intake` |
| `workbench_tags` | `WeCom`, `Media Intake`, `Unassigned` |
| `active_case_outcome` | `media_unassigned` |
| `case_created` | `true` |

### Attachment metadata (`case_attachments[0]`)

| Field | Value |
|-------|-------|
| `attachment_id` | `att_92f722de864d` |
| `source` | `wecom` |
| `msgtype` | `image` |
| `msg_id` | `Ajm6RvwvCwa8hXAX6oZWiCThJV` |
| `storage_uri` | `gs://caseiq-wecom-media-qa/wecom/…/Ajm6RvwvCwa8hXAX6oZWiCThJV.jpg` |
| `mime_type` | `image/jpeg` |
| `size_bytes` | `237473` |
| `ocr_status` | `not_started` |
| `broker_confirmed` | `false` |
| `binding_confidence` | `unknown` |
| `intake_status` | `unassigned` |
| `bound_case_id` | `null` |
| `public_url` | absent |

API `GET /api/inbox/cases` returns case with attachment visible (`total_count` 14 → 15).

---

## 9. Customer reply (safe, unassigned)

Expected template (`build_media_intake_reply`, unassigned):

> 收到图片。为了放到正确的服务事项里，请问这是加车资料、保单/续保资料、理赔照片，还是 DMV/停保通知？

Log: `wecom_slice_reply_sent_v1` `sent: true`. Reply does **not** mention OCR, VIN, coverage, driving, or claim filing advice.

---

## 10. Dedup evidence

| Guard | Count for `msg_id` |
|-------|-------------------|
| `wecom_message_processed` | 1 |
| `wecom_reply_dedup` | 1 |
| `case_attachments` with same `msg_id` | 1 |

Duplicate WeCom callback pings after cursor save returned zero new messages.

---

## 11. Text lane regression (post-deploy)

| Check | Result |
|-------|--------|
| QA gate `--cloud-api` after smoke | **PASS** |
| Live text WeCom messages | not sent (avoid QA pollution) |
| Demo workbench cases (5 seeded) | still present and aligned |

---

## 12. Scope guardrails (confirmed)

| Item | Status |
|------|--------|
| OCR / LLM / vision extraction | **not introduced** |
| Schema migration | **none** |
| Cloud SQL / VPC / NAT / Secret / callback | **unchanged** |
| Frontend / Vercel deploy | **none** |
| Neon | **not used** |
| Public GCS access | **none** |
| P19B UI / guided upload buttons | **not started** |

---

## 13. Remaining risks

1. **Workbench UI** does not yet render attachment preview (expected — P19B scope).
2. **`service_lane` in Postgres `extra` JSON** may be sparse at row level; API projection exposes `wecom_media_intake` correctly.
3. **httpx may log WeCom API URLs** containing access tokens in Cloud Run logs — treat logs as sensitive; redact in future hardening (out of P19A scope).
4. **GCS object `contentType`** not set at upload time (size/MIME captured in attachment metadata from download).

---

## 14. Recommendation

**GO for P19B — Workbench Attachment UI** (broker preview, confirm/bind, no OCR).

P19A Loop 2 acceptance: **all 19 criteria met**. STOP before P19B implementation.
