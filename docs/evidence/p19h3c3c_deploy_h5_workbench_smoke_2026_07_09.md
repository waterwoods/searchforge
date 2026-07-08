# P19H-3c-3C — Deploy + H5/Workbench Smoke

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO** (API smoke PASS after PG extra hotfix)

---

## 1. Goal

Deploy P19H-3c-3C (Claim H5 slot persistence / skip reason) and verify Cloud Run + Vercel + Workbench checklist behavior after H5 upload/skip.

---

## 2. Commits deployed

| Commit | Message | Layer |
|--------|---------|-------|
| `959057f` | feat: persist Claim H5 evidence slot status | H5 upload/skip + summary (initial deploy) |
| `1ee6090` | fix: persist claim_attachment_slots in Postgres extra bag | **Hotfix** — Cloud SQL `extra` whitelist + hydrate |

**Note:** First deploy (`fiqa-api-00174-p9n`, `959057f`) wrote attachments + `h5_photo_flow_state` but **did not** persist `claim_attachment_slots` to Postgres because `_build_extra()` omitted the field. Hotfix redeploy required for production parity with JSON/local tests.

---

## 3. Backend deploy

| Field | Initial | **Final (accepted)** |
|-------|---------|----------------------|
| Revision | `fiqa-api-00174-p9n` | **`fiqa-api-00175-4p6`** |
| GIT_SHA | `959057f12` | **`1ee609080`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | same |
| Script | `bash scripts/deploy_paid_pilot.sh` | redeploy after hotfix |

### Health

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"1ee609080",...}` |

---

## 4. Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` (from `ui/`) |
| Build env | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| Deployment URL | `https://ui-btf4j0yjj-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Changed files | `h5TaskUpload.ts` (skip_reason), `H5SingleSlotUploadPage.tsx` (default reason) |
| `/workbench/document-intake` | **HTTP 200** |

No frontend redeploy needed for PG hotfix (backend-only).

---

## 5. Pre-deploy tests

| Suite | Result |
|-------|--------|
| `test_p19h3c3c_h5_claim_slot_persistence.py` | PASS (8/8) |
| `test_p19h3c3a_claim_evidence_summary_backend.py` | PASS |
| `test_p19h3c3ab_get_case_enrichment_parity.py` | PASS |
| `test_p19h3c1_claim_h5_evidence_foundation.py` | PASS |
| `test_p19h3c2_claim_c1_h5_button.py` | PASS |
| `pytest -k h5` | PASS (86) |
| `npm run build` | PASS |
| Pre-deploy QA gate (`--cloud-api`) | PASS |

---

## 6. Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS** — revision `fiqa-api-00175-4p6`, Cloud SQL aligned.

---

## 7. Cloud API smoke (automated)

Token minted with Cloud Run `H5_TASK_TOKEN_SECRET` (value not recorded). Ephemeral `workbench_test` cases on QA Cloud SQL.

**Smoke case:** `case_093aad6280fc` (tagged `demo_name=p19h3c3c_deploy_smoke`)

### Smoke A — H5 upload persists received

| Check | Result |
|-------|--------|
| Upload `customer_damage_photo` | **200** |
| PG `claim_attachment_slots.customer_damage_photo.status` | **received** |
| `source_channel` | **h5_task** |
| `latest_attachment_id` | **att_93ff93e86973** |
| Workbench GET `claim_evidence_summary` slot status | **received** ✅ |

### Smoke B — skip other-party persists reason

| Check | Result |
|-------|--------|
| Skip `other_party_vehicle_photo` + `not_available` | **200** |
| PG slot `status` | **skipped** |
| PG `skip_reason` | **not_available** |
| Workbench summary other-party | **skipped** · reason **not_available** |
| `missing_soft_required_slots` | **[]** |
| `completion_level` | **review_ready** |

### Smoke C — required slot cannot skip

| Check | Result |
|-------|--------|
| Skip `customer_damage_photo` | **400** |
| `detail` | **slot_not_skippable** |

### Smoke D — Add Vehicle unaffected

| Check | Result |
|-------|--------|
| Add-car VIN upload | **200** |
| `claim_attachment_slots` written | **No** |

---

## 8. Logs

Scanned Cloud Run logs post-hotfix (`fiqa-api-00175-4p6`):

| Finding | Result |
|---------|--------|
| `h5_task_upload_ok` claim_evidence_pack | **Present** |
| `claim_attachment_slots` / skip errors | **None** |
| Workbench summary 500s | **None** |
| Qdrant / Redis / embedding warmup | Expected optional warnings only |

---

## 9. Manual / browser checks

| Check | Status |
|-------|--------|
| Workbench drawer visual: ✅ 自己车损 / — 已跳过 | **HUMAN-PENDING** |
| Live WeCom → H5 → upload/skip phone flow | **HUMAN-PENDING** |

API + PG JSON confirm checklist data; operator can open `case_093aad6280fc` on https://ui-smoky-beta.vercel.app/workbench/document-intake for visual confirmation.

---

## 10. Constraints

| Constraint | Status |
|------------|--------|
| No schema migration | ✅ |
| No WeCom image binding | ✅ |
| No identity resolver | ✅ |
| No OCR / carrier filing | ✅ |

---

## 11. Known limitations

- Skip reason UI remains minimal (default from metadata first key)
- Broker override for required customer damage skip deferred
- First deploy revision `00174` lacked PG slot persistence until hotfix `1ee6090`

---

## 12. GO / HOLD

**GO** — after hotfix `1ee6090`, Cloud API smoke PASS, QA gate PASS, Workbench enrichment shows received/skipped with skip reason.

---

## 13. Next recommended prompt

**P19H-3c-R3 Claim Identity Resolver Foundation**
