# P19H-3d — Deploy + WeCom Image Binding Smoke

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Fix QA gate `Argument list too long`, deploy P19H-3d WeCom Claim image binding + C1 multi-channel copy, and validate Tier A/B/C + Add Vehicle behavior on QA Cloud SQL + Cloud Run.

---

## 2. QA gate hotfix summary

| Field | Value |
|-------|-------|
| Root cause | `check_chen_kui_demo_environment.sh` passed full `/api/inbox/cases` JSON as `sys.argv[1]` to Python — exceeded OS argv limit on large payloads |
| Fix | Write curl response to `mktemp` file; pass **file path** to Python (`open(path)`) |
| Commit | `dc711ee` — fix: make QA gate handle large cases payload |
| Before | **FAIL** — `/usr/bin/python3: Argument list too long` |
| After | **PASS** (pre- and post-deploy) |

---

## 3. Deployed commits

| Commit | Message |
|--------|---------|
| `45ae0fc` | feat: bind WeCom claim images to pending evidence |
| `dc711ee` | fix: make QA gate handle large cases payload |

---

## 4. Backend revision / GIT_SHA

| Field | Value |
|-------|-------|
| Revision | **`fiqa-api-00177-45n`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`dc711ee9b`** (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Prior revision | `fiqa-api-00176-njk` |

---

## 5. Frontend deployment / stable alias

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` (from `ui/`) |
| Deployment URL | `https://ui-etm0c2nuh-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Bundle check | `assets/index-CFMNkgoW.js` contains `待分类微信照片` |
| `/workbench/document-intake` | **HTTP 200** |

---

## 6. Health / ready

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"dc711ee9b",...}` |

---

## 7. Tests and regressions

| Suite | Result |
|-------|--------|
| `test_p19h3d_wecom_claim_image_binding.py` | **PASS** (9/9) |
| `test_p19h3c_r3_claim_identity_resolver_foundation.py` | **PASS** |
| `test_p19h3c3c_h5_claim_slot_persistence.py` | **PASS** |
| `test_p19h3c3a_claim_evidence_summary_backend.py` | **PASS** |
| `test_p19h3c3ab_get_case_enrichment_parity.py` | **PASS** |
| `test_p19h3c2_claim_c1_h5_button.py` | **PASS** |
| `test_p19h2_claim_wecom_basics.py` | **PASS** |
| `test_p19h21_claim_interrupt_lane_switch.py` | **PASS** |
| `pytest -k claim` | **PASS** |
| `pytest -k h5` | **PASS** |
| `npm run build` | **PASS** |

---

## 8. QA gate before/after

| When | Result |
|------|--------|
| Pre-deploy (after hotfix) | **PASS** |
| Post-deploy | **PASS** |

---

## 9. Smoke A/B/C/D results

**Method:** QA Cloud SQL ingest via same `ingest_wecom_media_message()` + Claim Identity Resolver as deployed revision. Ephemeral `workbench_test` cases; unique `external_userid` prefix `wm_p19h3d_smoke_*`. Cloud Run API readback for Tier A.

**Smoke suffix:** `164807`

### Smoke A — Tier A: one recent open Claim → bind

| Check | Result |
|-------|--------|
| Case | `case_6a3e108f1815` |
| Outcome | `media_attached_to_case` |
| Reply | **Yes** — `照片已收到` |
| `identity_tier` / `identity_action` | **A** / **append_existing** |
| Attachment `source` | **wecom** |
| `slot_assignment` | **unassigned** |
| `eligible_for_ocr` | **false** |
| Slots marked received | **None** |
| API `unassigned_wecom_photos.count` | **1** |
| API `broker_next_action` | `有 1 张微信照片待陈总人工归类。` |

### Smoke B — Tier C: no open Claim + image only

| Check | Result |
|-------|--------|
| Outcome | `media_unassigned` |
| Claim cases created | **0** |
| Reply | **Yes** — asks user to say `我要理赔` |
| `identity_action` | `create_new` |

### Smoke C — Tier B: multiple open Claims

| Check | Result |
|-------|--------|
| Setup | 2 open Claim cases, same user |
| Outcome | `media_unassigned` |
| Silent bind to newest | **No** — `bound_claim_ids=[]` |
| Reply | **Yes** — `混在一起` / Chen will confirm |
| `identity_action` | **broker_confirm** |

### Smoke D — Add Vehicle unaffected

| Check | Result |
|-------|--------|
| Case | `case_c12641fb820c` |
| Outcome | `media_attached_to_case` |
| `service_lane` | **add_car** |
| Claim cases for user | **0** |

**Note:** Live WeCom phone image send on new revision **HUMAN-PENDING** — QA Cloud SQL + API simulator confirms binding path.

---

## 10. Workbench visual result

| Check | Result |
|-------|--------|
| Deployed bundle contains `待分类微信照片` | **Yes** |
| Cloud API enrichment on smoke case A | **Yes** — `unassigned_wecom_photos.count=1` |
| Drawer visual on `case_6a3e108f1815` | **HUMAN-PENDING** — operator can open on https://ui-smoky-beta.vercel.app/workbench/document-intake |

---

## 11. Log check

Scanned Cloud Run logs (`fiqa-api-00177-45n`, limit 50):

| Finding | Result |
|---------|--------|
| `claim_identity` / media binding errors | **None** |
| Workbench 500s | **None** |
| Qdrant embedding warmup gRPC errors | Expected optional warnings |
| Import / traceback on claim path | **None** |

---

## 12. Constraints

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No AI image classification | ✅ |
| No OCR | ✅ |
| No auto slot assignment | ✅ |
| No image-only Claim creation | ✅ |
| No merge UI | ✅ |

---

## 13. Known limitations

- Broker cannot assign pending WeCom photo to slot yet (P19H-3d-2)
- No image dedup / AI classify
- Live phone WeCom image smoke pending
- API attachment response may omit `flow` / `needs_broker_review` (sanitized); enrichment uses `slot_assignment=unassigned` + `source=wecom`

---

## 14. Next recommended sprint

- **P19H-3d-2 Broker Manual Slot Assignment** — assign unassigned WeCom photos to checklist slots
- Or polish pending WeCom photos UX (thumbnails, broker copy)

---

## 15. GO / HOLD

**GO** — QA gate fixed, P19H-3d deployed, Tier A/B/C + Add Vehicle smoke PASS on QA Cloud SQL + API readback.

**STOP**
