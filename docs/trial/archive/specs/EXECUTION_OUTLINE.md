# Real Broker Trial Package — Execution Outline

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Trial package definition | Planner | Blueprint, Scope, Scenario Pack, Metrics |
| Broker workflow | Product | Workflow Spec, Day 1 checklist |
| Acceptance criteria | QA | Trial Readiness Criteria |
| Founder materials | Product | Founder Trial Notes |
| Implementation | Dev | Small product improvements if needed |

---

## 2. Implementation Order

1. **Phase A** — Create full control-doc stack (8 docs)
2. **Step 1** — Baseline audit
3. **Loop 1** — Define and tighten core trial package
4. **Loop 2** — Strengthen trial workflow + metrics
5. **Loop 3** — Final trial readiness hardening
6. **Optional Loop 4** — One more refinement if clearly valuable
7. **Validation** — Run guardrail, smoke, build
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

---

## 4. Loop Plan

| Loop | Focus | Expected outcome |
|------|-------|------------------|
| 1 | Define and tighten core trial package | Clear trial definition; coherent scenario set |
| 2 | Strengthen trial workflow + metrics | Broker workflow doc; metrics template |
| 3 | Final trial readiness hardening | Founder script; broker checklist |
| 4 | Optional | One high-value, low-risk refinement |

---

*End of Execution Outline*
