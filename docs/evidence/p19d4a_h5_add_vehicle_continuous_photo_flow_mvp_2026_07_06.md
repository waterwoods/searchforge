# P19D-4A — H5 Add Vehicle Continuous Photo Flow MVP

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Local dev + tests + evidence only — **no deploy**

---

## Summary

Implemented continuous H5 Add Vehicle photo flow: one WeCom entry → H5 session completes VIN → registration → optional insurance card (or skip) → return to WeChat for text fields.

Aligned with P19D-3.5 recon: do not bounce user between WeChat and H5 on every step.

---

## Prior doc commit

- `66c6500` — `docs: add P19D guided workflow best practice recon`

---

## Changed files

| Area | Files |
|------|-------|
| Token | `services/fiqa_api/inbox_triage/h5_task_token.py` |
| Upload logic | `services/fiqa_api/inbox_triage/h5_task_upload.py` |
| Routes | `services/fiqa_api/routes/h5_task_upload.py` |
| Link minting | `services/fiqa_api/inbox_triage/h5_task_link.py` |
| Case skip state | `services/fiqa_api/inbox_triage/case_store.py` |
| WeCom | `services/fiqa_api/wecom/slice.py`, `services/fiqa_api/wecom/reply.py` |
| H5 UI | `ui/src/pages/H5SingleSlotUploadPage.tsx`, `ui/src/api/h5TaskUpload.ts` |
| Workbench labels | `ui/src/features/intake/utils/attachmentDisplay.ts`, `CaseAttachmentsPanel.tsx` |
| Script | `scripts/generate_h5_task_link.py` (`--flow`) |
| Tests | `tests/test_h5_add_vehicle_photo_flow.py`, updates to token/single-slot/WeCom tests |
| Static tests | `ui/src/pages/h5SingleSlotUpload.static.test.mjs`, `attachmentDisplay.test.ts` |

---

## Token design

**v2 flow token payload:**

```json
{
  "v": 2,
  "case_id": "...",
  "lane": "add_car",
  "flow": "add_vehicle_photo_flow",
  "slots": ["vin_photo", "registration_photo", "insurance_card_photo"],
  "iat": "...",
  "exp": "...",
  "nonce": "...",
  "user_ref": "8-char"
}
```

- Signed with `H5_TASK_TOKEN_SECRET` (HMAC)
- No full `external_userid` in token or URL
- **v1 single-slot tokens unchanged** — P19D-2 backward compatible

---

## API changes

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/api/h5/tasks/{task_token}` | v1: single slot info; v2: `flow`, `steps[]`, `current_step`, `flow_complete` |
| POST | `/api/h5/tasks/{task_token}/upload` | v2 requires `slot` form field matching current step; one image, max 5MB |
| POST | `/api/h5/tasks/{task_token}/skip` | v2 only; optional `insurance_card_photo` skip |

Skip state stored in case JSON `h5_photo_flow_state.skipped_slots` — **no schema migration**.

---

## Attachment metadata (per upload)

```json
{
  "source": "h5_task",
  "slot_assignment": "<slot>",
  "document_type": "<slot>",
  "document_type_confidence": "user_selected_step",
  "intake_status": "promoted",
  "guardrail_status": "accepted",
  "eligible_for_ocr": true,
  "ocr_status": "not_started",
  "broker_confirmed": false,
  "binding_confidence": "high",
  "flow": "add_vehicle_photo_flow"
}
```

No `storage_uri` or public URL in API responses.

---

## H5 UI flow

1. Step 1/3: VIN photo — preview → confirm → submit  
2. Step 2/3: Registration photo  
3. Step 3/3: Insurance card (optional skip)  
4. Final: 「照片资料已收到」+ 请回微信补充提车日期、停车 ZIP、联系电话  
5. `multiple=false`, `capture="environment"`, no OCR language

Route unchanged: `/task/upload/:taskToken`

---

## WeCom Start Card

Add Vehicle text → flow link via `mint_h5_add_vehicle_photo_flow_link`.

Copy updated:
- 按顺序完成 VIN、行驶证、保险卡照片
- Button: **开始补资料**
- No “upload all”, no OCR, no quote/coverage claims

Premium / Claim / Coverage / hello — no flow link (regression tests pass).

---

## Workbench display

| Slot | Label |
|------|-------|
| `vin_photo` | VIN photo |
| `registration_photo` | Registration photo |
| `insurance_card_photo` | Insurance card photo |

Source label: **H5 Task / Guided Upload**  
Preview via broker-authenticated proxy — no public GCS URL.

---

## Tests / build

```text
PYTHONPATH=. python3 -m pytest tests/test_h5_task_token.py tests/test_h5_single_slot_upload.py -q  → PASS
PYTHONPATH=. python3 -m pytest tests/test_h5_add_vehicle_photo_flow.py -q                          → PASS (12)
Regression P19A/B/D-1 + WeCom lanes                                                               → PASS
cd ui && npm run build                                                                            → PASS
node ui/src/pages/h5SingleSlotUpload.static.test.mjs                                                → PASS
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts                                    → PASS
bash scripts/check_chen_kui_demo_environment.sh --cloud-api                                       → PASS
```

---

## Local smoke (API-level)

Covered by `test_h5_add_vehicle_photo_flow.py`:
- Full VIN → registration → insurance upload path
- Skip insurance path
- Wrong slot order rejected
- v1 single-slot still works

Manual phone smoke: **not run** (no deploy this loop).

---

## Explicit non-goals (confirmed)

| Item | Status |
|------|--------|
| OCR / LLM / vision | ❌ Not introduced |
| 小程序 | ❌ |
| Text field H5 form | ❌ |
| Schema migration | ❌ |
| Public GCS URL | ❌ |
| Neon as QA truth | ❌ |
| Deploy | ❌ |

---

## Known limitations

- Skip metadata on case JSON only; Workbench has no “skipped slot” UI yet
- v1 single-slot tokens still work but WeCom Add Vehicle now mints v2 flow tokens
- Re-upload / replace slot not supported (one attachment per slot per flow)
- Text fields (delivery date, ZIP, phone) remain WeCom chat lane

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local dev + tests | **GO** |
| Deploy + live phone smoke | **HOLD** — deploy backend + frontend + verify H5_TASK_TOKEN_SECRET on Cloud Run before phone test |

---

*No token secrets, full tokens, external_userid, or image content recorded in this doc.*
