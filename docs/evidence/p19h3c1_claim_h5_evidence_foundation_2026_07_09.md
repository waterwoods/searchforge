# P19H-3c-1 — Claim H5 Evidence Pack Foundation

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Prerequisite:** P19H-3b recon (`e159f0f`) · P19H-3a workbench visibility (`29b57fe`)

---

## 1. Goal

Extend the existing Add Vehicle H5 guided upload system to support **Claim evidence pack** photo collection — token minting, slot metadata API, and minimal upload path — without WeCom C1 Start Card, Workbench checklist, deploy, or schema changes.

---

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| `lane=claim` H5 token (v2 flow) | WeCom C1 → H5 Start Card |
| `flow=claim_evidence_pack` | Workbench evidence checklist |
| Three slot metadata definitions | OCR / AI damage detection |
| H5 task API metadata + safety copy | Skip reason persistence (deferred) |
| Basic claim slot upload (`eligible_for_ocr=false`) | `claim_attachment_slots` explicit mutation |
| Frontend safety note display | Deploy |
| Regression tests | Schema migration |

---

## 3. What was implemented

### Backend

- **`h5_task_token.py`**: Added `lane=claim`, `flow=claim_evidence_pack`, `CLAIM_EVIDENCE_PACK_FLOW_SLOTS`. Add Vehicle tokens unchanged.
- **`h5_task_link.py`**: `mint_h5_claim_evidence_pack_link()` — mints v2 flow URL starting at `customer_damage_photo`.
- **`h5_task_upload.py`**:
  - Claim slot copy + `get_claim_evidence_slot_metadata()`
  - `OTHER_PARTY_SKIP_REASONS` (4 keys)
  - `task_info_for_token()` returns Claim-specific fields for H5 UI
  - Upload sets `eligible_for_ocr=false`, `flow=claim_evidence_pack`
  - Claim flow completion message (no Add Vehicle end card)
  - Skip allowed for `other_party_vehicle_photo` and `scene_photo` (persist via `h5_photo_flow_state`; skip **reason** not persisted yet)

### Frontend

- **`H5SingleSlotUploadPage.tsx`**: Renders `safety_copy` from API; skip button uses `skippable` flag (supports soft-required other-party slot).
- **`h5TaskUpload.ts`**: Extended types for Claim metadata fields.

---

## 4. Intentionally deferred

| Item | Next sprint |
|------|-------------|
| WeCom C1 Start Card → H5 link | P19H-3c-2 or parallel |
| Workbench evidence checklist | P19H-3c-2+ |
| Skip reason persistence (`claim_attachment_slots.skip_reason`) | P19H-3c-2 |
| Explicit `claim_attachment_slots` status mutation on upload | P19H-3c-2 (status inferred from attachments today) |
| Claim flow completion WeCom card | P19H-3c-2 |
| Deploy | After P19H-3c-2 integration |

---

## 5. H5 token support

| Field | Value |
|-------|-------|
| `lane` | `claim` |
| `flow` | `claim_evidence_pack` |
| `slots` | `customer_damage_photo` → `other_party_vehicle_photo` → `scene_photo` |
| Token version | v2 flow token (same pattern as Add Vehicle) |
| Mint helper | `mint_h5_claim_evidence_pack_link(case_id=...)` |

---

## 6. Slot contract

| # | `slot_key` | Label | `required_level` | Skippable |
|---|------------|-------|----------------|-----------|
| 1 | `customer_damage_photo` | 自己车损照片 | `required` | no |
| 2 | `other_party_vehicle_photo` | 对方车辆 / 车牌照片 | `soft_required` | yes |
| 3 | `scene_photo` | 现场照片 | `optional` | yes |

**Accepted media:** `image/jpeg`, `image/png`, `image/heic`, `image/heif`  
**Max files per slot:** 2 (MVP UI still 1 per step)

---

## 7. Skip reasons (`other_party_vehicle_photo`)

| Key | Label (ZH) |
|-----|------------|
| `no_other_party` | 没有对方车辆 / 单方事故 |
| `not_available` | 当时无法拍摄 |
| `hit_and_run` | 对方逃逸 |
| `customer_not_safe_to_collect` | 当时不安全未能拍摄 |

Returned in H5 task API `skip_reasons`; persistence deferred.

---

## 8. H5 task metadata examples

### First slot (`customer_damage_photo`)

```json
{
  "lane": "claim",
  "flow": "claim_evidence_pack",
  "case_id": "case_…",
  "slot_key": "customer_damage_photo",
  "slot_label": "自己车损照片",
  "title": "理赔资料 · 车损照片",
  "instruction": "请拍摄您车辆的损伤部位（远景 + 近景更清晰）",
  "required_level": "required",
  "skippable": false,
  "eligible_for_ocr": false,
  "safety_copy": "这只是资料收集，不代表 claim 已正式提交。",
  "next_slot": "other_party_vehicle_photo",
  "current_step": "customer_damage_photo",
  "step_index": 1,
  "step_total": 3
}
```

---

## 9. Upload mutation status

**Implemented (basic):**

- Claim H5 upload validates token + claim lane
- Appends `case_attachments` with `source=h5_task`, `slot_assignment`, `flow=claim_evidence_pack`, `eligible_for_ocr=false`
- Slot status inferred as `received` via `get_claim_attachment_slot_status()` (attachment-based)

**Deferred:**

- Explicit `claim_attachment_slots[slot].status=received` write
- Skip reason on `claim_attachment_slots`

---

## 10. Add Vehicle regression

| Suite | Result |
|-------|--------|
| `pytest tests -k h5` | PASS |
| `test_h5_task_token.py` | PASS |
| `test_h5_add_vehicle_photo_flow.py` | PASS |
| Add Vehicle token / flow unchanged | PASS |

---

## 11. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3c1_claim_h5_evidence_foundation.py -q
# 12 passed
```

Covers: token mint/validate, first-slot metadata, other-party/scene metadata, invalid lane, canonical slot names, upload attachment shape, slot status inference, link minting.

---

## 12. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# PASS (recorded at commit time)
```

---

## 13. Constraints honored

| Constraint | Status |
|------------|--------|
| No deploy | ✅ |
| No schema change | ✅ |
| No OCR | ✅ (`eligible_for_ocr=false`) |
| No WeCom C1 Start Card | ✅ |
| No Workbench checklist | ✅ |
| Add Vehicle H5 unchanged | ✅ |

---

## 14. Next recommended sprint

**P19H-3c-2 — Claim H5 Upload + Slot Status Mutation + WeCom C1 Start Card**

1. Wire `mint_h5_claim_evidence_pack_link()` into C1 stage-complete card  
2. Persist `claim_attachment_slots` + skip reasons  
3. Workbench evidence checklist (display-only)  
4. Deploy + smoke on `case_b8d15b3ca59a` pattern

---

## 15. GO / HOLD

**GO** for P19H-3c-2 — foundation token/metadata/upload path verified; no blockers.

---

*Evidence sprint P19H-3c-1 — foundation only, no production deploy.*
