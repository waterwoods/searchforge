# P19I-2c — Claim State Kernel Parity Refactor Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Parity refactor — wire `claim_state.py` to thin workflow kernel  
**Verdict:** **LOCAL PASS** · **P19H-1 PARITY PASS** · **NO DEPLOY**

---

## 1. Goal

Connect P19H-1 Claim State Foundation (`claim_state.py`) to P19I-2b Thin Workflow Kernel (`workflow_kernel.py` / `workflow_definitions.py`) **without changing external behavior**.

This sprint is **parity only** — not the simplified Claim WeCom path (P19H-2').

---

## 2. Source commits

| Sprint | Commit | Artifact |
|--------|--------|----------|
| P19H-1 | `d4a8d45` | `services/fiqa_api/wecom/claim_state.py` foundation |
| P19I-2b | `d7f8b0b` | `workflow_kernel.py`, `workflow_definitions.py` |

---

## 3. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/claim_state.py` | Internal kernel adapter + delegation for completion predicates |
| `services/fiqa_api/workflow_definitions.py` | Added `CLAIM_FOUNDATION_DEFINITION` (P19H-1 parity schema) |
| `tests/test_p19i2c_claim_state_kernel_parity.py` | **NEW** — adapter + parity acceptance tests |
| `docs/evidence/p19i2c_claim_state_kernel_parity_refactor_2026_07_08.md` | **NEW** — this doc |

**Not changed:** `reply.py`, `slice.py`, `claim_basics.py`, H5, Workbench, schema, cloud config.

---

## 4. Architecture

```text
case_extra (JSONB)
    │
    ▼
_claim_snapshot_from_case_extra()   ← P19I-2c adapter
    │
    ▼
WorkflowRuntimeSnapshot
    │
    ▼
workflow_kernel helpers
  · what_is_collected()
  · what_is_missing()
  · evaluate_required_gate()
    │
    ▼
claim_state public API (unchanged names/shapes)
  · is_accident_basics_complete()
  · are_claim_photos_complete()
  · is_other_party_info_complete()
  · is_injury_police_complete()
  · is_claim_summary_ready()
  · get_claim_missing_items()
  · get_claim_collected_fields()
  · derive_claim_phase()          ← kept P19H-1 granular logic
```

---

## 5. Phase naming compatibility

| Constant | Value | Status |
|----------|-------|--------|
| `CLAIM_PHASE_SUMMARY_READY` | `claim_summary_ready` | **Active** — `derive_claim_phase()` still returns this |
| `CLAIM_PHASE_INTAKE_READY_FOR_BROKER` | `intake_ready_for_broker` | **Added** — future P19H-2' simplified model |

`CLAIM_FOUNDATION_DEFINITION.human_review_phase` = `claim_summary_ready` (not `intake_ready_for_broker`).

`CLAIM_SIMPLIFIED_DEFINITION` (P19I-2b example) still uses `intake_ready_for_broker` for future migration reference.

---

## 6. CLAIM_FOUNDATION_DEFINITION

New definition mirrors P19H-1's 8 required + 5 optional slots:

| Required slot | Kernel type |
|---------------|-------------|
| `accident_datetime`, `accident_location`, `accident_description` | `field` |
| `customer_damage_photo` | `attachment` |
| `other_party_vehicle_or_plate` | `composite` (photo or plate text) |
| `other_party_info` | `composite` (≥1 other-party artifact) |
| `anyone_injured`, `police_involved` | `yes_no` |

Optional: `scene_photo`, `police_report_photo`, `tow_repair_info`, `witness_info`, `existing_claim_number`.

---

## 7. Adapter behavior

`_claim_snapshot_from_case_extra(case_extra)`:

- Maps `known_facts` + `collected_fields` → `snapshot.collected_fields` (with P19H-1 validation rules)
- Normalizes Chinese/English yes/no via `normalize_claim_yes_no()`
- Maps `case_attachments` / `claim_attachment_slots` → `snapshot.attachments` (`received`)
- Treats optional skipped photo slots as collected for completion score only
- Sets `safety_flags` for injury yes / manual_handle

Attachment slot helpers (`get_claim_attachment_slots`, etc.) remain claim-specific and unchanged.

---

## 8. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h1_claim_state_machine_foundation.py -q
# 25 passed

PYTHONPATH=. python3 -m pytest tests/test_p19i2c_claim_state_kernel_parity.py -q
# 14 passed

PYTHONPATH=. python3 -m pytest tests/test_p19i2b_workflow_kernel.py -q
# 17 passed
```

---

## 9. Regression

| Suite | Result |
|-------|--------|
| `test_p19h1_claim_state_machine_foundation.py` | 25/25 PASS |
| `test_p19i2c_claim_state_kernel_parity.py` | 14/14 PASS |
| `test_p19i2b_workflow_kernel.py` | 17/17 PASS |
| `test_p19h2_claim_wecom_basics.py` | PASS |
| `test_p19g32_phase2_field_validation.py` | PASS |
| `test_p19e2_add_vehicle_progress_card.py` | PASS |

---

## 10. Constraints honored

| Constraint | Status |
|------------|--------|
| No WeCom routing changes | ✅ |
| No schema changes | ✅ |
| No deploy | ✅ |
| P19H-1 public API preserved | ✅ |
| `claim_summary_ready` semantics unchanged | ✅ |
| No orchestration framework | ✅ |

---

## 11. Known limitations / next steps

- `derive_claim_phase()` still uses P19H-1 granular 14-phase model (not kernel `get_current_step`)
- `intake_ready_for_broker` is defined but not yet used in production phase derivation
- **P19H-2'** will migrate simplified Claim WeCom path to `CLAIM_SIMPLIFIED_DEFINITION` + `intake_ready_for_broker`

---

## STOP

| Item | Value |
|------|-------|
| Adapter | `_claim_snapshot_from_case_extra()` in `claim_state.py` |
| Definition | `CLAIM_FOUNDATION_DEFINITION` in `workflow_definitions.py` |
| Parity tests | `tests/test_p19i2c_claim_state_kernel_parity.py` |
| Deploy | **No** |
| Routing | **Unchanged** |
