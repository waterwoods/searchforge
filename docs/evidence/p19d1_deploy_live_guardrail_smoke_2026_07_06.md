# P19D-1 Deploy + Live Guardrail Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Deploy commit:** `566422a` (`feat: add strict WeCom upload guardrail`)  
**Verdict:** **PASS (deploy + live guardrail smoke + Workbench UI)**

---

## 1. Pre-check

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Commit `566422a` | present (pushed to origin) |
| QA gate (`--cloud-api`) pre-deploy | **PASS** — revision `fiqa-api-00150-f6h` |
| Cloud SQL | `gcp-cloud-sql` @ `10.73.0.3` db=`caseiq` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` |
| Neon | not QA truth |

---

## 2. Push

| Item | Value |
|------|-------|
| Remote | `origin/sprint/p16-trust-layer` |
| Range pushed | `9231fda..566422a` |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00151-hxh`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Runtime `GIT_SHA` | `566422a58` (`GET /version`) |
| DB secret | unchanged (`fiqa-service-record-database-url-cloudsql-private`) |
| `/health/live` | OK |
| `/readyz` | OK (`intake_core_readiness: true`) |
| QA gate post-deploy | **PASS** |

**Not changed:** Cloud SQL instance, VPC/NAT/static IP, WeCom callback URL, schema, Neon.

---

## 4. Frontend deploy (Workbench quarantine badges)

| Field | Value |
|-------|-------|
| Command | `vercel deploy --yes` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Preview deployment | `https://ui-nvcs2kdbh-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Target page | `/workbench/document-intake` (attachment drawer) |
| Build | PASS |

Live bundle contains P19D-1 strings: `Quarantined Uploads`, `Needs Review`, `Eligible for OCR later`.

---

## 5. Live guardrail smoke (3 images → 1 promote + 2 quarantine)

**Method:** QA Cloud SQL ingest path (same `ingest_wecom_media_message` + guardrail code as deployed revision), then Cloud Run API readback + Workbench UI verification.  
**Smoke case:** tagged `demo_name=p19d1_guardrail_smoke`, `workbench_test=true` — does not touch `chen_kui_p18` seed rows.

| Item | Value |
|------|-------|
| **Case** | `case_65e8f926cb90` |
| **Customer label** | `P19D1 Guardrail Smoke` |
| **Lane** | `add_car` |
| **external_userid tail** | `…83351883` (masked in UI/logs) |
| **Images sent** | 3 within rolling window |
| **Promoted** | 1 (`att_8f6b487bc447`, `guardrail_status=accepted`, `eligible_for_ocr=true`) |
| **Quarantined** | 2 (`att_817cc9c9ed58`, `att_0243ce225acd`, `guardrail_status=bulk_confirm_needed`, `eligible_for_ocr=false`) |
| **Customer reply (last)** | Contains `确认` + `第一张` — no OCR language |
| **Inbox paperclip count** | **1** (quarantined excluded from queue count) |

### API sanitization (live)

`GET /api/inbox/cases/case_65e8f926cb90` returns guardrail fields on attachments.  
Absent: `storage_uri`, `external_userid`, public/signed URL.

---

## 6. Live UI smoke — Workbench drawer

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake  
**Case opened:** `case_65e8f926cb90` · P19D1 Guardrail Smoke · Add Car

| Check | Result |
|-------|--------|
| **Uploaded Documents / Attachments (1)** | ✅ promoted section only |
| Promoted badges | ✅ `Accepted` · `Eligible for OCR later` |
| **Quarantined Uploads (2)** | ✅ separate yellow subsection |
| Quarantined badges | ✅ `Needs Review` · `Bulk confirm needed` · `Not eligible for OCR` |
| Preview proxy | ✅ available on all 3 (no public GCS URL in UI) |
| Full external_userid in UI | ❌ not visible |
| P19A holding case (`case_82092cc39bae`) | ✅ still in queue |
| Chen Kui demo 5 (`chen_kui_p18`) | ✅ QA gate still PASS |

---

## 7. Regression checks

| Check | Result |
|-------|--------|
| `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` post-smoke | **PASS** |
| Text lanes (Add Car / Premium / Claim / Coverage) | unchanged — QA gate lane tags OK |
| OCR / LLM / vision | not introduced |
| Schema migration | none |
| H5 / 小程序 / slot editor / broker confirm | not started |

---

## 8. Scope guardrails (confirmed)

| Item | Status |
|------|--------|
| OCR / LLM / vision extraction | ❌ Not introduced |
| Schema migration | ❌ None |
| Cloud SQL / VPC / NAT / Secret / callback | ❌ Unchanged |
| Public GCS URL | ❌ Not exposed |
| Neon as QA truth | ❌ Not used |
| P19D-2 / H5 | ❌ Not started |

---

## 9. Known limitations / notes

1. Live smoke used **operator-scripted triple ingest** on QA Cloud SQL (not a live WeCom album pick from phone). Callback/crypto path unchanged; guardrail logic exercised on deployed revision `566422a`.
2. A partial failed pre-smoke row (`case_ae9908e48f76`) may exist from an aborted run — left in QA DB per no-delete policy.
3. Rolling-window ordering within the same second may be unstable (documented in P19D-1 MVP evidence).

---

## 10. Recommendation

**GO — P19D-1 strict upload guardrail is live on QA.**  
Workbench shows promote vs quarantine split; multi-image bulk does **not** surface all images as normal evidence.

**STOP** before P19D-2 / H5 / OCR.

---

*P19D-1 deploy + live guardrail smoke complete.*
