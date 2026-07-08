# P19H-3c-3C — H5 Claim Slot Persistence / Skip Reason

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Status:** GO (local + tests; no deploy)

---

## 1. Goal

Persist explicit `claim_attachment_slots` status on H5 Claim Evidence Pack **upload** and **skip**, so Workbench checklist reflects received / skipped / missing accurately without inferring only from `case_attachments[]` and `h5_photo_flow_state`.

---

## 2. Why this matters

P19H-3c-3A summary logic already reads `claim_attachment_slots` when present, but H5 upload/skip did not write it. Skips had no `skip_reason`; Workbench could not show “已跳过 · 原因”. Upload did not record `source_channel` or attachment ids at slot level.

---

## 3. Upload persistence behavior

On successful H5 Claim Evidence Pack upload (`lane=claim`, `flow=claim_evidence_pack`):

- Append attachment to `case_attachments[]` (unchanged)
- Update `claim_attachment_slots[slot_key]`:
  - `status = received`
  - `source_channel = h5_task`
  - `attachment_ids` append id
  - `latest_attachment_id = attachment_id`
  - `updated_at = now`
  - Clears prior `skip_reason` / `needs_retake` (full slot replace)
- `eligible_for_ocr` remains `false`
- Add Vehicle H5 uploads **do not** write `claim_attachment_slots`

**Code:** `ingest_h5_slot_upload()` → `record_claim_evidence_slot_received()` via `claim_evidence_slots.patch_claim_slot_received()`.

---

## 4. Skip persistence behavior

`POST /api/h5/tasks/{token}/skip` accepts optional `skip_reason` form field.

On Claim Evidence Pack skip:

- Validates token lane/flow
- Validates slot is skippable (`other_party_vehicle_photo`, `scene_photo`)
- Validates `skip_reason` against allowed list (defaults to `not_available`)
- Updates `h5_photo_flow_state.skipped_slots` (existing)
- Updates `claim_attachment_slots[slot_key]`:
  - `status = skipped`
  - `skip_reason = <reason>`
  - `source_channel = h5_task`
  - `updated_at = now`
- No fake attachment created
- Returns `next_slot` when flow continues

**Frontend:** Skip button sends first metadata `skip_reason` key (typically `no_other_party` for other-party, `not_available` for scene) — minimal, no reason picker UI.

---

## 5. Required vs soft-required vs optional skip policy

| Slot | Level | Customer skip? |
|------|-------|----------------|
| `customer_damage_photo` | required | **No** → `400 slot_not_skippable` |
| `other_party_vehicle_photo` | soft_required | Yes — reasons: `no_other_party`, `not_available`, `hit_and_run`, `customer_not_safe_to_collect` |
| `scene_photo` | optional | Yes — reasons: `not_available`, `not_needed`, `customer_not_safe_to_collect` |

Broker override for required-slot skip: **deferred** (not in this sprint).

---

## 6. JSONB shape

Stored on case document (no schema migration):

```json
{
  "claim_attachment_slots": {
    "customer_damage_photo": {
      "status": "received",
      "source_channel": "h5_task",
      "attachment_ids": ["att_abc123"],
      "latest_attachment_id": "att_abc123",
      "updated_at": "2026-07-09T20:15:00+00:00"
    },
    "other_party_vehicle_photo": {
      "status": "skipped",
      "source_channel": "h5_task",
      "skip_reason": "not_available",
      "updated_at": "2026-07-09T20:16:00+00:00"
    }
  }
}
```

---

## 7. Summary compatibility

`build_claim_evidence_summary()` priority unchanged:

1. `needs_retake` (explicit)
2. `skipped` (explicit or legacy `h5_photo_flow_state`)
3. `received` (explicit or attachments)
4. `missing`

Enhanced: explicit `received` / `skipped` now honor `source_channel` from slot record when set.

---

## 8. Tests

**New:** `tests/test_p19h3c3c_h5_claim_slot_persistence.py` (8 cases)

| # | Scenario |
|---|----------|
| 7.1 | Upload marks slot received + summary |
| 7.2 | Upload clears prior skipped status |
| 7.3 | Skip other-party soft-required |
| 7.4 | Customer damage skip rejected |
| 7.5 | Scene optional skip → complete |
| 7.6 | Invalid skip reason rejected |
| 7.7 | Add Vehicle unaffected |
| 7.8 | Workbench summary review_ready |

---

## 9. Regression results

```
PYTHONPATH=. python3 -m pytest tests/test_p19h3c3c_h5_claim_slot_persistence.py -q
# 8 passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3c3a_claim_evidence_summary_backend.py -q
# passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3c3ab_get_case_enrichment_parity.py -q
# passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3c1_claim_h5_evidence_foundation.py -q
# passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3c2_claim_c1_h5_button.py -q
# passed

PYTHONPATH=. python3 -m pytest tests/test_p19h3a_claim_workbench_visibility.py -q
# passed

PYTHONPATH=. python3 -m pytest tests -q -k "h5"
# 86 passed
```

---

## 10. Frontend build / test

- `ui/package.json` has no `npm test` script — **not run**
- `cd ui && npm run build` — **PASS**

**Changed frontend:**

- `ui/src/api/h5TaskUpload.ts` — optional `skip_reason` on skip API
- `ui/src/pages/H5SingleSlotUploadPage.tsx` — default skip reason from metadata

---

## 11. QA gate result

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS
```

Cloud revision unchanged (`fiqa-api-00173-n7k`) — **no deploy**.

---

## 12. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ |
| No schema / new tables | ✅ |
| No Workbench UI redesign | ✅ |
| No WeCom direct image binding | ✅ |
| No identity resolver | ✅ |
| No OCR | ✅ |
| No carrier filing | ✅ |

---

## 13. Known limitations

- Skip reason UI is minimal (default from metadata first key, not a picker)
- Broker override for required customer damage skip deferred
- WeCom images still not bound to claim slots
- Identity resolver deferred
- Phone summary deferred
- Re-upload after skip in H5 flow order is not supported in UI (persistence layer clears skip if broker/tools call receive directly)

---

## 14. Next recommended prompts

1. **P19H-3c-3C Deploy + H5/Workbench Smoke**
2. **P19H-3c-R3 Claim Identity Resolver Foundation**
3. **P19H-3d WeCom Direct Image Binding**

---

## 15. GO / HOLD

**GO** — slot persistence + skip reason implemented, tests and QA gate pass, ready for deploy prompt.

---

## Files changed

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/claim_evidence_slots.py` | **New** — pure slot mutation + skip reason validation |
| `services/fiqa_api/inbox_triage/case_store.py` | `record_claim_evidence_slot_received/skip` |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | Wire upload/skip persistence; scene skip reasons |
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | Explicit received/skipped source_channel |
| `services/fiqa_api/routes/h5_task_upload.py` | `skip_reason` form param |
| `ui/src/api/h5TaskUpload.ts` | Skip reason payload |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | Default skip reason |
| `tests/test_p19h3c3c_h5_claim_slot_persistence.py` | **New** |
