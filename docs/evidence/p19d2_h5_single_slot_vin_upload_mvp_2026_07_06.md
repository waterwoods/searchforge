# P19D-2 — H5 Single-Slot VIN Upload MVP

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Implementation evidence — H5 guided single-slot upload (VIN photo only)

---

## Implemented scope

| Item | Status |
|------|--------|
| H5 route `/task/upload/:taskToken` | ✅ |
| Single slot: `vin_photo` only | ✅ |
| One image, preview confirm, submit | ✅ |
| HMAC task token (case + lane + slot, 24h TTL) | ✅ |
| POST upload → GCS → attachment metadata | ✅ |
| Workbench shows H5 attachment + preview path | ✅ |
| Link generator script | ✅ |
| Registration / insurance / OCR / mini program | ❌ (deferred) |
| Deploy | ❌ |

**Doctrine confirmed:** P19D-2 is single-slot H5 upload — not bulk upload, not multi-image page.

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/h5_task_token.py` | HMAC signed task token |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | Upload handler + metadata |
| `services/fiqa_api/routes/h5_task_upload.py` | GET task / POST upload API |
| `services/fiqa_api/inbox_triage/case_store.py` | `append_h5_gcs_attachment_metadata` |
| `services/fiqa_api/inbox_triage/case_attachment_api.py` | H5 GCS preview support |
| `services/fiqa_api/wecom/media_storage.py` | HEIC mime mapping |
| `services/fiqa_api/app_main.py` | Mount H5 router |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | Mobile H5 page |
| `ui/src/api/h5TaskUpload.ts` | Frontend API client |
| `ui/src/App.tsx` | Route registration |
| `ui/src/features/intake/components/CaseAttachmentsPanel.tsx` | `H5 Task` source label |
| `ui/src/pages/h5SingleSlotUpload.static.test.mjs` | Static UI contract test |
| `scripts/generate_h5_task_link.py` | Dev link generator |
| `tests/test_h5_task_token.py` | Token tests |
| `tests/test_h5_single_slot_upload.py` | Upload API tests |

---

## Token design

- **Prefix:** `h5t1.`
- **Payload:** `case_id`, `lane` (`add_car`), `slot` (`vin_photo`), `iat`, `exp`, `nonce`, optional `user_ref` (8-char HMAC ref — not full `external_userid`)
- **Secret:** `H5_TASK_TOKEN_SECRET` → `UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET` → `WECHAT_BINDING_STATE_SECRET` (dev fallback only)
- **TTL:** 24h default
- **Validation:** signature + expiry + supported lane/slot only

---

## Route / page

| Surface | Path |
|---------|------|
| H5 page | `/task/upload/:taskToken` |
| Task info API | `GET /api/h5/tasks/{task_token}` |
| Upload API | `POST /api/h5/tasks/{task_token}/upload` |

---

## Metadata shape (written on success)

```json
{
  "source": "h5_task",
  "slot_assignment": "vin_photo",
  "document_type": "vin_photo",
  "document_type_confidence": "user_selected_step",
  "intake_status": "promoted",
  "guardrail_status": "accepted",
  "eligible_for_ocr": true,
  "ocr_status": "not_started",
  "broker_confirmed": false,
  "binding_confidence": "high",
  "bound_case_id": "<case_id>",
  "task_token_nonce": "<nonce>",
  "h5_upload_id": "h5_..."
}
```

Response sanitized: no `storage_uri`, no `external_userid`, no public URL.

---

## One-image enforcement

| Layer | Enforcement |
|-------|-------------|
| H5 UI | `<input multiple={false}>`; preview required before submit |
| API | Single `UploadFile` parameter; empty / non-image / >5MB rejected |
| Metadata | Slot copy `max_images: 1` |

---

## Local / manual smoke

```
case_id case_048e2a5f0eb8 (ephemeral JSON fixture)
GET /api/h5/tasks/{token} → 200, task_label=请拍 VIN 照片
POST upload (1 JPEG) → 200, slot_assignment=vin_photo
Case JSON: source=h5_task, intake_status=promoted, eligible_for_ocr=true
```

Link generator:

```bash
PYTHONPATH=. python3 scripts/generate_h5_task_link.py --case-id <case_id> --slot vin_photo
```

---

## Tests / build

| Command | Result |
|---------|--------|
| `pytest tests/test_h5_task_token.py tests/test_h5_single_slot_upload.py` | PASS (14) |
| `pytest tests/test_wecom_upload_guardrail.py tests/test_wecom_media_intake.py tests/test_workbench_attachment_api.py` | PASS (56) |
| `pytest tests/test_wecom_minimal_lanes.py … test_wecom_identity_b0_extractors.py` | PASS (103) |
| `node ui/src/pages/h5SingleSlotUpload.static.test.mjs` | PASS |
| `cd ui && npm run build` | PASS |
| `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` | PASS |

---

## Constraints verified

| Constraint | Status |
|------------|--------|
| No OCR / LLM / vision | ✅ |
| No schema migration | ✅ |
| No Neon | ✅ |
| No public GCS URL | ✅ |
| No deploy | ✅ |
| P19A / P19B / P19D-1 not broken | ✅ (regression tests) |

---

## Known limitations

- Only `vin_photo` slot implemented; registration deferred in UI copy
- WeCom Start Card → H5 link not wired (script-only for MVP)
- Skip button shown disabled
- HEIC accepted in validation; preview in older browsers may vary
- Token secret must be set in production (`H5_TASK_TOKEN_SECRET`)

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local MVP acceptance | **GO** |
| Deploy / live demo | **HOLD** — needs Vercel + Cloud Run deploy + `H5_TASK_TOKEN_SECRET` on Cloud Run + manual phone smoke on deployed URL |

---

*No token secrets, full external_userid, public URLs, or sensitive images in this document.*
