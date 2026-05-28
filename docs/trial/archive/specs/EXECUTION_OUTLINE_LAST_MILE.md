# Trial Execution Readiness — Execution Outline

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Workstreams, implementation order, test plan, loop plan.

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Control docs | Planner | Blueprint, Last-Mile Risk Spec, Runbook, Handoff Spec, Observation-to-Iteration Spec |
| Trial execution path | Trial workflow worker | Founder pre-trial checklist; broker Day 1 flow; one product/workbench improvement |
| Handoff / office | Office handoff worker | Next-action visibility; correction/context badges |
| Observation bridge | Product critic | Observation template; friction classification; fix now/next/defer |
| QA / validation | QA worker | Guardrail, smoke, build; loop comparison |

---

## 2. Implementation Order

1. **Phase A** — Create full control-doc stack (8 docs)
2. **Step 1** — Baseline audit from real-execution perspective
3. **Loop 1** — Strengthen trial execution path (founder flow, broker clarity, 1–2 product improvements)
4. **Loop 2** — Strengthen handoff / office next action
5. **Loop 3** — Tighten observation → iteration bridge
6. **Optional Loop 4** — One high-value, low-risk refinement
7. **Validation** — Run all checks; compare loops
8. **Report** — Full sprint report

---

## 3. Test Plan

| Check | Script | When |
|-------|--------|------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | After each loop |
| Smoke | `bash scripts/unified_intake_smoke_check.sh` | After loop 1, 2, 3 |
| Inbox triage | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Each loop |
| Multi-turn | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | Each loop |
| State audit | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | Each loop |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | Each loop |
| UI build | `cd ui && npm run build` | After frontend changes |
| Trial readiness | `bash scripts/trial_readiness_check.sh` | Before and after sprint |

---

## 4. Loop Plan

| Loop | Focus | Expected outcome |
|------|-------|-------------------|
| 1 | Trial execution path | Founder pre-trial clearer; broker Day 1 clearer; 1–2 product improvements |
| 2 | Handoff / office | Next action more visible; correction/context stand out |
| 3 | Observation → iteration | Log template; friction classification; fix now/next/defer |
| 4 | Optional | One high-value, low-risk refinement |

---

*End of Execution Outline*
