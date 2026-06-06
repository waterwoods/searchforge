# Execution Outline

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Document set | Planner | 7 control docs |
| Config boundary | Config worker | category_templates.json, workflow_defaults.json |
| Config loader | Backend worker | get_category_templates(), get_workflow_fallbacks() |
| Triage integration | Backend worker | _get_category_templates reads from config |
| Verification | QA | Guardrail, build, scenario pass |

---

## 2. Implementation Order

1. **Baseline audit** — Document current state
2. **Loop 1** — Extract broker_next_step + client_prep to category_templates.json; wire config_loader; triage reads config
3. **Loop 2** — Extract common workflow_defaults.json; wire config_loader
4. **Loop 3** — Tighten consistency; add client ui_copy.json if feasible
5. **Validation** — Guardrail, build, compare before/after

---

## 3. Test Plan

| Phase | Test |
|-------|------|
| After Loop 1 | run_inbox_triage_scenarios, run_multi_turn_simulations, guardrail_inbox_triage |
| After Loop 2 | Same + verify fallbacks when category missing |
| After Loop 3 | Same + UI build if UI touched |

---

## 4. Loop Plan

- **Loop 1:** Highest value — category_templates (broker_next_step, client_prep)
- **Loop 2:** Common layer — workflow_defaults
- **Loop 3:** Client UI copy or consistency pass
- **Loop 4:** Only if clearly valuable, low-risk refinement remains

---

*See also: 06_ACCEPTANCE_REUSABILITY_CRITERIA.md*
