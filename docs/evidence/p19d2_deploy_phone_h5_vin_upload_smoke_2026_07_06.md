# P19D-2 Deploy + Phone H5 VIN Upload Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **PASS (deploy + live phone smoke + Workbench preview)**

---

## 1. Deployed commits

| Commit | Message |
|--------|---------|
| `64df022` | docs: add pure WeCom chat vs H5 guided flow recon |
| `e8327bd` | feat: add H5 single-slot VIN upload page |
| `a50d04c` | chore: bind H5_TASK_TOKEN_SECRET from Secret Manager on deploy |

Pushed to `origin/sprint/p16-trust-layer` before backend deploy.

---

## 2. H5_TASK_TOKEN_SECRET

| Field | Value |
|-------|-------|
| Configured | **Yes** |
| Secret Manager name | `fiqa-h5-task-token-secret` |
| Cloud Run binding | `H5_TASK_TOKEN_SECRET=fiqa-h5-task-token-secret:latest` |
| Value | *(not recorded)* |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — **unchanged** |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00152-5vh`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `/health/live` | OK |
| `/readyz` | OK |
| Cloud SQL | `caseiq` @ `10.73.0.3` private VPC — unchanged |
| Neon | Not used |
| WeCom callback | Unchanged |
| VPC/NAT | Unchanged |

---

## 4. Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Production deployment | `https://ui-ltvrynjae-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| H5 route | `/task/upload/:taskToken` — HTTP 200 |
| Workbench | `/workbench/document-intake` — HTTP 200 |
| Build | PASS |

---

## 5. Demo case selected

| Field | Value |
|-------|-------|
| Customer | 陈女士 |
| case_id | `case_8d5da9724e7d` |
| service_lane | `add_car` |
| status | `reviewing` |
| Attachments before smoke | 0 |

---

## 6. H5 task link (masked)

| Field | Value |
|-------|-------|
| Method | HMAC token issued with Cloud Run–matched `H5_TASK_TOKEN_SECRET` |
| Token prefix | `h5t1.` |
| Token sample | `h5t1.eyJjYXNlX2lk…c9425fd` *(full token omitted)* |
| Page URL pattern | `https://ui-smoky-beta.vercel.app/task/upload/<token>` |
| Pre-smoke GET task | 200 — `slot=vin_photo`, `lane=add_car`, `task_label=请拍 VIN 照片` |

---

## 7. Phone smoke (Andy)

**Operator confirmation:** `D2 已提交`

| Step | Expected | Result |
|------|----------|--------|
| Open H5 link on phone | Page loads | ✅ (confirmed by operator) |
| Title | 加车资料补充 | ✅ |
| Progress | 第 1 步 / 共 4 步 | ✅ |
| Task | 请拍 VIN 照片 | ✅ |
| Upload | One non-sensitive test image | ✅ |
| Preview → submit | Required before upload | ✅ |
| Success copy | VIN received; registration deferred | ✅ |
| No OCR / VIN recognized / policy claims | Safe copy only | ✅ |

**Upload timestamp (UTC):** `2026-07-06T16:50:16Z` (Cloud Run log)

---

## 8. Upload / metadata result

| Field | Value |
|-------|-------|
| attachment_id | `att_c83d1d8aaf14` |
| source | `h5_task` |
| slot_assignment | `vin_photo` |
| document_type | `vin_photo` |
| intake_status | `promoted` |
| guardrail_status | `accepted` |
| eligible_for_ocr | `true` |
| ocr_status | `not_started` |
| broker_confirmed | `false` |
| binding_confidence | `high` |
| mime_type | `image/png` |
| size_bytes | 105180 |
| storage | Private GCS (`gs://` — URI not exposed in API) |
| API response | No `storage_uri`, no `external_userid`, no public URL |

Cloud Run log: `h5_task_upload_ok_v1` — `POST …/upload → 200` (771ms)

---

## 9. Workbench verification

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake  
**Case:** `case_8d5da9724e7d` (陈女士 · add_car)

| Check | Result |
|-------|--------|
| Attachment count | 1 (was 0) |
| Source label | H5 Task |
| Document type | VIN photo |
| Binding confidence | high |
| OCR | not started |
| Broker confirmed | no |
| Preview proxy | **200** — PNG 105180 bytes via `/api/inbox/cases/.../preview` |
| Public GCS URL | None |
| Full external_userid | Not exposed |

---

## 10. Negative coverage

Automated (pre/post deploy, local):

| Test | Result |
|------|--------|
| Expired token rejected | PASS (`test_h5_task_token.py`) |
| Tampered token rejected | PASS |
| Non-image rejected | PASS |
| Oversized image rejected | PASS |
| Response sanitized (no storage_uri) | PASS |
| H5 UI `multiple={false}` | PASS (static contract test) |

No multi-image phone upload attempted (by design).

---

## 11. Logs / security scan

Cloud Run logs (`fiqa-api-00152-5vh`, limit 500):

| Check | Result |
|-------|--------|
| `H5_TASK_TOKEN_SECRET` value printed | **No** |
| Access token printed | **No** |
| Image binary in logs | **No** (only `size_bytes`) |
| H5 upload 500 | **No** |
| DB secret leak | **No** |
| Public GCS URL | **No** |

---

## 12. Regression / QA gate

```text
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
Result: PASS — revision fiqa-api-00152-5vh, Cloud SQL aligned
```

P19A/P19B/P19D-1 paths unchanged. No extra WeCom messages sent.

---

## 13. Constraints verified

| Constraint | Status |
|------------|--------|
| No OCR / LLM | ✅ |
| No schema migration | ✅ |
| No public URL | ✅ |
| No full external_userid | ✅ |
| No Neon | ✅ |
| No Cloud SQL/VPC/NAT/callback changes | ✅ |
| No registration / insurance / mini program | ✅ |

---

## 14. Known limitations

- Link generation from local dev cannot reach private Cloud SQL; token issued via API-verified case_id + matching secret
- WeCom Start Card does not auto-send H5 link yet
- Only `vin_photo` slot live; registration step deferred in UI copy
- `generate_h5_task_link.py` needs VPC/Cloud SQL access or API-based case verify for full local path

---

## 15. GO / HOLD

| Gate | Verdict |
|------|---------|
| **P19D-2 deploy + phone smoke** | **GO** |
| P19D-2.5 registration H5 step | **HOLD** — next loop |
| WeCom Start Card → H5 link | **HOLD** — next loop |
| OCR | **HOLD** — out of scope |

---

*No token secrets, full task tokens, real image content, full external_userid, or public URLs in this document.*
