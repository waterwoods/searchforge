# Trial Launch — Execution Outline

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Workstreams, implementation order, test plan, loop plan.

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Launch path | Planner | trial_launch_check.sh, one-page checklist |
| Evidence + fix-now | Evidence worker | FIX_NOW_QUEUE_TEMPLATE, results/trial_logs structure |
| Product friction | UX worker | Copy case snapshot, optional paste hint |
| QA / validation | QA worker | Run guardrail, smoke, build |

---

## 2. Implementation Order

1. **Loop 1:** Strengthen trial launch path — single entry, checklist
2. **Loop 2:** Evidence capture + fix-now queue structure
3. **Loop 3:** Small product friction reduction (Copy case snapshot)
4. **Optional Loop 4:** Paste hint or other refinement

---

## 3. Test Plan

| After loop | Commands |
|------------|----------|
| Loop 1 | trial_launch_check.sh, guardrail_inbox_triage.sh, unified_intake_smoke_check.sh, run_inbox_triage_scenarios.py, run_multi_turn_simulations.py, audit_state_field_accuracy.py, verify_speed_routing.py, npm run build |
| Loop 2 | Same + verify FIX_NOW_QUEUE_TEMPLATE exists, results/trial_logs writable |
| Loop 3 | Same + verify Copy case snapshot works in UI |

---

## 4. Loop Plan

- **Loop 1:** Launch path — fix founder confusion, single entry
- **Loop 2:** Evidence + queue — fix post-trial iteration gap
- **Loop 3:** Friction — fix one product friction point
- **Loop 4:** Only if one clearly valuable, low-risk refinement remains

---

*End of Execution Outline*
