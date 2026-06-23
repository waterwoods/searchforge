# P16 PDF VIN Fix — Deploy + Production Validation Report

**Date:** 2026-06-21  
**Backend revision:** `fiqa-api-00102-fbp`  
**Deploy entry:** `bash scripts/deploy_paid_pilot.sh`

---

## Executive Summary

Backend PDF text-layer VIN fix deployed to Cloud Run. Production validation on stable QA URL: **all cases pass**. Case A reaches **READY** with checksum-valid PDF (`pa_007`). PDF VIN regression: **4/4** exact ground-truth match (previously 0/3 on vision-only).

---

## Priority 1 — Deploy

| Check | Status |
|-------|--------|
| `extractor.py` fix included | ✅ `try_pdf_text_layer_vin` + `_apply_pdf_text_vin_preference` in revision |
| Requirements complete | ✅ Deploy succeeded (PyMuPDF, pillow-heif, etc.) |
| Cloud Run revision healthy | ✅ `fiqa-api-00102-fbp` serving 100% traffic |
| `/health/live` | ✅ `{"ok":true}` |
| `/readyz` | ✅ OK |
| Frontend stable QA URL | ✅ HTTP 200 — **no frontend redeploy needed** (backend-only change) |
| Frontend → backend | ✅ Bundle targets `fiqa-api-1013093472160.us-west1.run.app` |
| CORS from `ui-smoky-beta.vercel.app` | ✅ HTTP 200 + `access-control-allow-origin: https://ui-smoky-beta.vercel.app` |

**Frontend:** skipped (no UI changes)  
**Backend:** deployed `fiqa-api-00102-fbp`

---

## Priority 2 — Production Validation

**API tested:** `https://fiqa-api-1013093472160.us-west1.run.app`  
**Origin header:** `https://ui-smoky-beta.vercel.app`  
**Model:** `gpt-4o` (real extraction, `mock_mode: false`)

### Case A — READY PDF

| Field | Result |
|-------|--------|
| Document | `pa_007_hyundai_elantra.pdf` (checksum-valid VIN) |
| Readiness | **ready** ✅ |
| VIN | `KMHD84LF8KU123456` |
| VIN source | `pa_007_hyundai_elantra.pdf` |
| Checksum | ✅ valid |
| YMM | 2019 Hyundai Elantra |
| case_id | `case_2443b8598545` |
| Postgres | ✅ `case_id` returned; `postgres_case_persistence_primary: true` on `/health` |
| Screenshot | `artifacts/p16_deploy_validation/screenshots/CASE_A_READY.png` |

### Case B — NEED_INFO

| Field | Result |
|-------|--------|
| Documents | Grocery receipt PNG + utility bill PDF |
| Readiness | **needs_info** ✅ |
| VIN | *(empty — no fake VIN)* ✅ |
| document_guidance | Bilingual "couldn't find vehicle information" ✅ |
| case_id | `case_39d757405a17` |
| Postgres | ✅ persisted |
| Screenshot | `artifacts/p16_deploy_validation/screenshots/CASE_B_NEED_INFO.png` |

*Auto Follow-Up: would display in UI (`needs_info` + missing VIN/YMM keys).*

### Case C — BROKER_REVIEW

| Field | Result |
|-------|--------|
| Documents | `pa_001_toyota_camry.pdf` + `pa_002_honda_civic.pdf` |
| Readiness | **broker_review** ✅ |
| VIN | `4T1BF1FK5CU512345` (17-char, **not corrupted**) |
| Checksum | ❌ invalid (expected — synthetic corpus) |
| Warnings | 6 (VIN checksum + multiple VINs + field conflicts) ✅ |
| Silent READY | ❌ none — correct |
| case_id | `case_7f99fdd549ef` |
| Screenshot | `artifacts/p16_deploy_validation/screenshots/CASE_C_BROKER_REVIEW.png` |

### PDF VIN Regression

| File | Ground Truth | Extracted | Len | Match | Pass |
|------|--------------|-----------|-----|-------|------|
| `pa_001_toyota_camry.pdf` | 4T1BF1FK5CU512345 | 4T1BF1FK5CU512345 | 17 | ✅ | ✅ |
| `pa_002_honda_civic.pdf` | 2HGFC2F69MH123456 | 2HGFC2F69MH123456 | 17 | ✅ | ✅ |
| `pa_003_bmw_x5.pdf` | 5UXCR6C06L9B12345 | 5UXCR6C06L9B12345 | 17 | ✅ | ✅ |
| `pa_007_hyundai_elantra.pdf` | KMHD84LF8KU123456 | KMHD84LF8KU123456 | 17 | ✅ | ✅ |

**Before fix (prior production):** `pa_001` → `1B1F1FK5CU512345` (16 chars, corrupted)

---

## Priority 3 — Pilot Prep

See **`docs/p16/P16_PILOT_VALIDATION_PREP.md`**:
- A. Wu Xiaojie Test Plan (7 steps + 3 questions)
- B. Chen Kui 5-minute Demo Plan
- C. 5 broker outreach archetypes (prepared, not sent)

---

## Final Report Block

```
DEPLOY_STATUS: PASS — backend fiqa-api-00102-fbp deployed; frontend unchanged; alias OK

PRODUCTION_VALIDATION_STATUS: PASS — Case A/B/C all match expected readiness

PDF_VIN_FIX_STATUS: PASS — 4/4 PDF regression exact GT match; pa_001 no longer corrupted

CASE_A_STATUS: PASS — READY, checksum-valid VIN, case_id case_2443b8598545

CASE_B_STATUS: PASS — NEED_INFO, no fake VIN, document_guidance present

CASE_C_STATUS: PASS — BROKER_REVIEW, warnings visible, 17-char VIN from text layer

POSTGRES_STATUS: PASS — case_id returned on all extracts; PG primary writes confirmed on /health

QA_URL: https://ui-smoky-beta.vercel.app/add-car

REMAINING_RISKS:
  1. Synthetic demo PDFs (pa_001–pa_005) fail NHTSA checksum → BROKER_REVIEW even with correct VIN
  2. Scanned/image-only PDFs still rely on Vision OCR (no text layer)
  3. Direct case read via GET /api/inbox/cases/{id} requires API key — persistence inferred from case_id return

NEXT_3_ACTIONS:
  1. Run Wu Xiaojie real-case test per P16_PILOT_VALIDATION_PREP.md
  2. Regenerate demo corpus with checksum-valid VINs for Chen Kui READY demo on pa_001
  3. Schedule Chen Kui 5-min demo + ask for 10-case pilot

RECOMMENDATION: SHIP
```

---

## Rollback

```bash
# Revert traffic to prior revision if needed
gcloud run services update-traffic fiqa-api \
  --region us-west1 --project optimal-disk-472305-e2 \
  --to-revisions fiqa-api-00101-wdw=100
```

No DB migration. No UI change.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Validation JSON | `artifacts/p16_deploy_validation/production_validation.json` |
| Screenshots | `artifacts/p16_deploy_validation/screenshots/` |
| Pilot prep | `docs/p16/P16_PILOT_VALIDATION_PREP.md` |

---

*QA URL: https://ui-smoky-beta.vercel.app/add-car*
