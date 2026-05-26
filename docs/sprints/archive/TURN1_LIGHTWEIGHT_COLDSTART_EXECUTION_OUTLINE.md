# Turn 1 Lightweight + Cold-Start — Execution Outline

**Theme:** Turn 1 Lightweight First-Pass + Cold-Start Mitigation

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Lightweight Turn 1 first-pass | Backend | `_is_turn1_lightweight_candidate()` + routing in triage_conversation |
| 2 | Cold-start mitigation | Runtime | Warmup script improvement + runbook clarity |
| 3 | Validation | QA | Guardrail, scenarios, speed routing, state audit |

---

## Sequence

1. **Control docs** — Blueprint, Outline, Acceptance Criteria
2. **Baseline audit** — Warm/cold latency, simple vs complex Turn 1
3. **Strategy A** — Implement lightweight Turn 1 routing
4. **Strategy B** — Strengthen warmup + runbook
5. **Loop 1** — Implement, test, evaluate
6. **Loop 2** — Refine if worthwhile
7. **Final** — Cost/ROI, recommendation

---

## Role Assignment

- **Planner:** Control docs, baseline
- **Backend:** triage.py changes
- **Runtime:** warmup_for_demo.sh, runbook
- **QA:** guardrail_inbox_triage.sh, run_inbox_triage_scenarios.py, run_multi_turn_simulations.py, audit_state_field_accuracy.py, verify_speed_routing.py, unified_intake_smoke_check.sh

---

## What Will Be Tested

- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py`
- `PYTHONPATH=. python3 scripts/verify_speed_routing.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`
- Targeted Turn 1 checks: cancellation, missing-doc, add-car, mixed-intent

---

## Likely Loop Count

2–3 loops. Loop 3 only if clearly fixable, low-risk, high-value issue remains.
