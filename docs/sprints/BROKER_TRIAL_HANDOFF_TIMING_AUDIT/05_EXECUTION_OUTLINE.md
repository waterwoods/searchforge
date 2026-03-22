# Execution Outline

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Purpose:** Workstreams, loop plan, validation.

---

## Workstreams

1. **Document stack** — Blueprint, Simulation Spec, Evaluation Criteria, Fix Queue, Acceptance, Founder Notes
2. **Handoff timing simulation pack** — Config + runner script
3. **Baseline audit** — Inspect current handoff logic; classify strong/weak
4. **Loop 1** — Run handoff-timing simulation; identify failures
5. **Loop 2** — Root-cause; fix queue
6. **Loop 3** — Apply 1–2 small fixes if justified
7. **Validation** — Rerun guardrail; compare
8. **Report** — Full sprint report

---

## Implementation Order

1. Create 7 control docs
2. Create handoff_timing_simulations.json + run_handoff_timing_simulations.py
3. Run baseline: guardrail, multi-turn, broker stress
4. Run handoff timing pack
5. Classify; build fix queue
6. Apply fixes if justified
7. Rerun; summarize

---

## Loop Plan

| Loop | Focus | Exit condition |
|------|-------|----------------|
| 1 | Run handoff-timing pack; identify too-early/too-late | Clear failure list |
| 2 | Root-cause; fix-now/fix-next/acceptable | Fix queue populated |
| 3 | Apply 1–2 small fixes | Evidence-based; low-risk |
| 4 | Optional refinement | Only if clearly valuable |

---

## Validation Approach

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py`

---

*End of Outline*
