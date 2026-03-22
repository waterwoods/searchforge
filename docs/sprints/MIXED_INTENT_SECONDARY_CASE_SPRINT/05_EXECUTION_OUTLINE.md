# Execution Outline

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Workstreams, implementation order, loop plan, validation.

---

## 1. Workstreams

| # | Workstream | Scope |
|---|------------|-------|
| 1 | **Doc set** | Blueprint, Primary/Secondary Spec, Case Split Spec, Broker Handoff Spec, Acceptance, Founder Notes |
| 2 | **Baseline audit** | Current mixed-intent gaps; case pollution risk; broker confusion risk |
| 3 | **Detection** | Side-question markers; secondary intent detection; flow_count already exists |
| 4 | **Summary + handoff** | Add secondary_issue_note to conversation_summary; optional broker_next_step append |
| 5 | **Case schema** | Optional secondary_issue_note in case_store |
| 6 | **Simulation** | Extend mixed_intent_scenarios; add secondary-addressed checks |
| 7 | **Guardrail** | Run guardrail_inbox_triage; run complex adversarial |

---

## 2. Implementation Order

1. **Phase A:** Doc set + baseline audit (this sprint start)
2. **Loop 1:** Define V1 strategy; add secondary_issue_note to summary; add 2–3 simulation cases
3. **Loop 2:** Implement secondary detection in triage; improve draft for mixed-intent; reduce case pollution
4. **Loop 3:** Final hardening; one more broker clarity improvement; guardrail pass

---

## 3. Loop Plan

| Loop | Focus | Deliverable |
|------|-------|-------------|
| 1 | Strategy + simulations | Doc set; secondary in summary; simulation cases |
| 2 | Triage + draft | Secondary detection; draft improvement; case schema |
| 3 | Hardening | Broker clarity; guardrail pass; founder notes |

---

## 4. Validation Approach

| Check | Command / Method |
|-------|------------------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| Mixed-intent sim | `PYTHONPATH=. python3 scripts/run_complex_adversarial_simulation.py --pack mixed_intent` |
| Inbox triage API | `python3 scripts/test_inbox_triage_api.py` (server on 8001) |
| Build | `cd ui && npm run build` |

---

*End of Outline*
