# High-Value Question Realism — Execution Outline

**Sprint:** High-Value Question Realism + Product Polish  
**Created:** 2026-03-14

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Control docs | Planner | Blueprint, Outline, SLA |
| 2 | Polish target selection | Planner | 5–8 question types chosen |
| 3 | Scenario realism | Scenario worker | inbox_triage, simulation_assistant, multi_turn configs |
| 4 | FAQ corpus + matrix | Routing worker | realistic_phrasing, handling examples |
| 5 | Frontend sync | UX worker | ui/src/config synced; build |
| 6 | Validation | QA worker | run_inbox_triage, run_multi_turn, guardrail, smoke |
| 7 | Product critic | Reviewer | Loop evaluation, founder showcase |

---

## Sequence

1. **Phase A:** Control docs (Blueprint, Outline, SLA)
2. **Phase B:** Select 5–8 polish targets; assess current realism
3. **Phase C — Loop 1:** Realism polish → validate → evaluate
4. **Phase D — Loop 2:** Product polish → validate → evaluate
5. **Phase E:** Frontend redeploy (npm build, vercel --prod)
6. **Phase F:** Post-deploy inspection
7. **Phase G:** Founder showcase + final report

---

## Simulation / Review Plan

| Script | When |
|--------|------|
| `run_inbox_triage_scenarios.py` | After Loop 1, Loop 2 |
| `run_multi_turn_simulations.py` | After Loop 1, Loop 2 |
| `audit_state_field_accuracy.py` | After Loop 1 |
| `verify_speed_routing.py` | After Loop 1 |
| `guardrail_inbox_triage.sh` | After Loop 1, Loop 2 |
| `unified_intake_smoke_check.sh` | After Loop 1, Loop 2 |
| `cd ui && npm run build` | After Loop 2, before deploy |

---

## Likely Loop Count

**Target: 2 loops.** Loop 1 = realism polish. Loop 2 = product polish. Stop if Loop 2 gains are marginal.

---

*See: Sprint Blueprint, Acceptance/SLA Criteria*
