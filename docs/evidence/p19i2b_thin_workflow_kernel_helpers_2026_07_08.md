# P19I-2b — Thin Workflow Kernel Helpers Evidence

**Date:** 2026-07-08  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Thin workflow kernel — pure Python helpers + unit tests  
**Verdict:** **LOCAL PASS** · **REGRESSION PASS** · **QA GATE PASS** · **NO DEPLOY**

---

## 1. Goal

Implement P19I-2b: the first minimal, framework-agnostic workflow kernel skeleton validated in P19I-1 and P19I-2. Pure helpers only — no routing, schema, deploy, or orchestration framework.

---

## 2. Source docs

| Doc | Role |
|-----|------|
| `docs/p19i1_workflow_kernel_breakthrough_recon.md` | Kernel semantics, gate model, Claim simplification |
| `docs/p19i2_workflow_kernel_core_validation_recon.md` | Andy 4-question validation, minimal kernel API |
| `docs/p19i0_generic_workflow_kernel_recon.md` | Generic vs lane-specific split |
| `docs/p19h0_claim_case_builder_state_machine_recon.md` | Claim field/slot model |
| `docs/evidence/p19h1_claim_state_machine_foundation_2026_07_08.md` | `claim_state.py` foundation parity reference |

---

## 3. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/workflow_kernel.py` | **NEW** — dataclasses + pure helper functions |
| `services/fiqa_api/workflow_definitions.py` | **NEW** — Add Vehicle + Claim simplified example definitions |
| `tests/test_p19i2b_workflow_kernel.py` | **NEW** — 17 acceptance tests |
| `docs/evidence/p19i2b_thin_workflow_kernel_helpers_2026_07_08.md` | **NEW** — this doc |

**Not changed:** `slice.py`, `reply.py`, `claim_state.py`, `add_vehicle_*`, H5, Workbench, schema, cloud config.

---

## 4. Kernel concepts implemented

| Concept | Module |
|---------|--------|
| `SlotDefinition` | `workflow_kernel.py` |
| `WorkflowDefinition` | `workflow_kernel.py` |
| `MissingItem` | `workflow_kernel.py` |
| `GateResult` | `workflow_kernel.py` |
| `CurrentStep` | `workflow_kernel.py` |
| `WorkflowRuntimeSnapshot` | `workflow_kernel.py` |
| `HumanHandoffDecision` | `workflow_kernel.py` |

---

## 5. Andy 4-question mapping

| Andy's Q | Function |
|----------|----------|
| 1. What does this task need? | `what_does_task_need(defn)` |
| 2. What has customer provided? | `what_is_collected(defn, snapshot)` |
| 3. What is still missing? | `what_is_missing(defn, snapshot)` |
| 4. Can this be handed off? | `evaluate_human_gate(defn, snapshot)` |

Aggregate view: `evaluate_workflow_snapshot(defn, snapshot)`.

---

## 6. Gates implemented

| Gate | Function | Behavior |
|------|----------|----------|
| **Safety** | `evaluate_safety_gate()` | Fails when `snapshot.safety_flags` non-empty |
| **Required** | `evaluate_required_gate()` | Binary pass only when all required slots collected |
| **Human** | `evaluate_human_gate()` | Safety fail → manual handle + handoff; required pass → ready for review; else blocked |

Completion score is separate: `compute_completion_score()` — never gates handoff.

---

## 7. Current step behavior

`get_current_step(defn, snapshot)`:

- Safety flags → `action=manual_handle`, hint「需要人工优先处理」
- Else first missing required slot by `current_step_order` (or required_slots order)
- Returns **one phase focus** — missing items filtered to that phase only
- All required satisfied → `phase=human_review_phase`, `action=ready_for_human_review`

---

## 8. Completion score behavior

- `0–100` = collected slots / (required + optional) × 100
- Optional slots increase score but do not affect `evaluate_required_gate`
- High score with one required missing still fails required gate (test #12)

---

## 9. Example definitions

### A. `ADD_VEHICLE_MINIMAL_DEFINITION`

- Phases: `photos` → `phase2_text` → `broker_review`
- Required: `vin_photo` (composite + `vin`), `registration_photo`, `delivery_date`, `parking_zip`, `contact_phone`
- Optional: `insurance_card_photo`
- Human review: `ready_for_broker_review`
- Done: `broker_done`

### B. `CLAIM_SIMPLIFIED_DEFINITION`

- Phases: `accident_basics` → `evidence_pack` → `risk_confirmation`
- Required: 3 basics + `customer_damage_photo` + `other_party_vehicle_or_plate` (composite) + injury/police yes_no
- Optional: 6 evidence/risk enrichment slots
- Human review: **`intake_ready_for_broker`** (not `claim_summary_ready`)
- Done: `broker_done`
- Safety rules listed in definition; runtime uses `snapshot.safety_flags`

---

## 10. Tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19i2b_workflow_kernel.py -q
# 17 passed
```

Coverage includes: definitions, empty/partial/complete snapshots, composite slots, safety manual handle, score vs gate separation, focused current step, stable `evaluate_workflow_snapshot` keys, no forbidden framework imports.

---

## 11. Regression

| Suite | Result |
|-------|--------|
| `tests/test_p19h1_claim_state_machine_foundation.py` | 25 passed |
| `tests/test_p19g32_phase2_field_validation.py` | 15 passed |
| `tests/test_p19e2_add_vehicle_progress_card.py` | 26 passed |
| `tests/test_wecom_*.py` (5 files) | 86 passed |

---

## 12. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
# Result: PASS — QA UI + Cloud Run API + Cloud SQL aligned
```

---

## 13. Constraints honored

| Constraint | Status |
|------------|--------|
| No routing changes | ✅ |
| No schema changes | ✅ |
| No deploy | ✅ |
| No framework migration | ✅ |
| No Claim WeCom implementation | ✅ |
| No LLM state control | ✅ |
| Deterministic pure Python only | ✅ |

---

## 14. Known limitations

- Not wired into production routing yet
- Event Log concept not implemented beyond design
- Human Task represented only via `HumanHandoffDecision` / `human_task_status` field
- `SafetyPolicy` minimal — uses `snapshot.safety_flags` only
- No workflow version persistence in case JSONB yet
- No YAML/config runtime engine
- Claim simplified definition is example only; `claim_state.py` unchanged

---

## 15. GO/HOLD for next step

**GO** for P19H-2' / P19I-3 when Andy approves:

1. Refactor `claim_state.py` internals to call kernel (parity tests)
2. Wire `build_progress_snapshot` from lane adapters
3. Resume simplified Claim WeCom path on `intake_ready_for_broker` model

**HOLD** on Temporal/Camunda, schema migration, routing changes until explicit sprint approval.

---

## STOP

| Item | Value |
|------|-------|
| Kernel module | `services/fiqa_api/workflow_kernel.py` |
| Definitions | `services/fiqa_api/workflow_definitions.py` |
| Tests | `tests/test_p19i2b_workflow_kernel.py` — 17/17 PASS |
| Deploy | **No** |
| Routing | **Unchanged** |
