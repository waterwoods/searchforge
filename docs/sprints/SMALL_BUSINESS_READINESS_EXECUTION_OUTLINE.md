# Small-Business Readiness Stress Test — Execution Outline

**Sprint:** Small-Business Readiness Stress Test  
**Date:** 2026-03-14

---

## Workstreams

| # | Workstream | Role | Focus |
|---|------------|------|-------|
| 1 | Control docs | Planner | Blueprint, Outline, SLA Criteria |
| 2 | Baseline audit | Architect | Speed, language, case report, trust, pilot maturity |
| 3 | Speed / latency | Speed evaluator | Turn 1 vs Turn 2+, cold vs warm, perceived wait |
| 4 | Language / realism | Language evaluator | Naturalness, system-like tone, small-business feel |
| 5 | Case accuracy | Case evaluator | Collected/Still needed, broker_next_step, handoff correctness |
| 6 | Small-business critic | Buyer critic | Would they try? Pay? Worry? |
| 7 | Simulation runner | Demo runner | Inbox triage, multi-turn, state audit, speed routing, guardrail |
| 8 | Product reviewer | Summary writer | Final judgment, strengths, weaknesses, next step |

---

## Sequence of Testing / Simulation

1. **Control docs** — Blueprint, Outline, SLA Criteria
2. **Baseline audit** — Code + config review; classify each dimension
3. **Scripts (rule-based, no LLM):**
   - `run_inbox_triage_scenarios.py`
   - `run_multi_turn_simulations.py`
   - `audit_state_field_accuracy.py`
   - `verify_speed_routing.py`
   - `guardrail_inbox_triage.sh`
   - `unified_intake_smoke_check.sh`
4. **UI build** — `cd ui && npm run build`
5. **Targeted scenario evaluation** — R1/R2/R3, SIM1/SIM2/SIM3, SIM15, mixed-intent
6. **Small-business readiness judgment**
7. **Optional re-check** — If one critical uncertainty remains
8. **Final product decision**

---

## Likely Loop Count

- **Loop 1:** Baseline + script pass
- **Loop 2:** Targeted scenario evaluation
- **Loop 3:** Optional re-check (if needed)
- **Loop 4:** Final judgment + report

---

*See: Evaluation/SLA Criteria*
