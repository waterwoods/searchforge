# Execution Outline — Sellable Standard Scenario Package Sprint

**Purpose:** Describe workstreams, implementation order, test plan, loop plan.

---

## 1. Workstreams

| Workstream | Owner | Focus |
|------------|-------|-------|
| **Package definition** | Planner / architect | Package name, target, scenarios, in-scope vs deferred |
| **Scenario coherence** | Scenario package designer | Which scenarios belong together; matrix spec |
| **Office-side packaging** | Workbench / office-side worker | Workbench as part of offer; handoff clarity |
| **Product packaging / positioning** | Product packaging worker | Founder demo / sales clarity |
| **QA / simulation** | QA / simulation worker | run_inbox_triage, run_multi_turn, guardrail |

---

## 2. Implementation Order

| Phase | Work |
|-------|------|
| **Phase A** | Create all 7 control docs |

| Phase B | Baseline audit |
| **Phase C** | Loop 1: Define and tighten core package |
| **Phase D** | Loop 2: Strengthen office / handoff side |
| **Phase E** | Loop 3: Final sellability hardening |
| **Phase F** | Optional Loop 4 |

---

## 3. Test Plan

| Test | Command |
|------|---------|
| Inbox triage scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| Multi-turn simulations | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` |
| State field accuracy | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| Smoke check | `bash scripts/unified_intake_smoke_check.sh` |
| UI build | `cd ui && npm run build` |

---

## 4. Loop Plan

| Loop | Target | Validation |
|------|--------|------------|
| **Loop 1** | Define package; tighten scenario set; improve naming/framing | All tests above |
| **Loop 2** | Office-side value; handoff packaging; workbench clarity | Rerun affected tests |
| **Loop 3** | Package explanation; founder demo path; guardrail | Rerun affected tests |
| **Loop 4** | One optional refinement | Only if clearly valuable |

---

*End of Execution Outline*
