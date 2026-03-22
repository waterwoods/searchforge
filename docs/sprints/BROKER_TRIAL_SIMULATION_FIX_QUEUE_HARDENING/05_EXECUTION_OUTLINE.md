# Execution Outline

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. Workstreams

| # | Workstream | Owner | Output |
|---|------------|-------|--------|
| 1 | Control doc set | Planner | Blueprint, Simulation Pack, Evaluation, Fix Queue, Execution, Acceptance, Founder Notes |
| 2 | Baseline audit | Evaluator | Current strong/weak; biggest trial-risk; broker rework source; trust-breaking risk |
| 3 | Loop 1: Core simulation | Broker sim worker | Run 8–15 flows; record pass/fail; what stayed strong; what failed |
| 4 | Loop 2: Root-cause + queue | Root-cause analyst | Group issues; fix-now/fix-next/defer; decide if tiny fixes justified |
| 5 | Loop 3: Small fixes | Small-fix worker | Apply 1–2 fixes; retest |
| 6 | Validation | QA | guardrail; multi-turn; adversarial; build |
| 7 | Final report | Release reviewer | Report; founder block; cross-window summary |

---

## 2. Implementation Order

1. **Phase A** — Create all 7 control docs
2. **Phase B** — Baseline audit; run guardrail + simulations
3. **Loop 1** — Run core broker-style simulation pack
4. **Loop 2** — Root-cause; fix queue hardening
5. **Loop 3** — Apply 1–2 small fixes (if justified)
6. **Optional Loop 4** — Only if one clearly valuable refinement remains
7. **Deployment judgment** — Backend/frontend redeploy if changed
8. **Founder verification** — What to inspect when back

---

## 3. Loop Plan

| Loop | Focus | Exit condition |
|------|-------|----------------|
| 1 | Run simulations; record issues | Issues classified; strong/weak identified |
| 2 | Root-cause; fix queue | fix-now/fix-next/defer clear; fix decision made |
| 3 | Apply small fixes | 1–2 fixes applied; retested |
| 4 | Optional refinement | Only if low-risk, high-value |

---

## 4. Validation Approach

- `bash scripts/guardrail_inbox_triage.sh` — must PASS
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — run
- `PYTHONPATH=. python3 scripts/run_simulation_assistant_scenarios.py` — run
- `PYTHONPATH=. python3 scripts/run_follow_up_append_simulations.py` — run
- `cd ui && npm run build` — only if frontend touched

---

*End of Execution Outline*
