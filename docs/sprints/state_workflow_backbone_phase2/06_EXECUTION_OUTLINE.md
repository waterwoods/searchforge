# State / Workflow Backbone Phase 2 — Execution Outline

---

## Workstreams

| # | Workstream | Scope |
|---|------------|-------|
| 1 | Session continuity | session_id in API + frontend localStorage |
| 2 | Workflow state contract | next_best_question, lifecycle_status in triage/case |
| 3 | UI state visibility | Clearer collecting/handoff/lifecycle display |

---

## Implementation Order

1. **Loop 1**: Session continuity (API + frontend) + workflow_state contract (next_best_question, lifecycle_status)
2. **Loop 2**: UI visibility improvements
3. **Loop 3** (optional): One refinement (e.g. regression test, contract fix)

---

## Test Plan

- `run_inbox_triage_scenarios.py`
- `run_multi_turn_simulations.py`
- `audit_state_field_accuracy.py`
- `verify_speed_routing.py`
- `guardrail_inbox_triage.sh`
- `unified_intake_smoke_check.sh` (if exists)
- `test_state_workflow_backbone.py` (extend for new keys)

---

## Likely Loop Count

2–3 loops.
