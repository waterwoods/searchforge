# P16-Z0 Role Simulation Archaeology

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 3  
**Search terms:** Role A/B/C, Role C+, Chen Kui, Assistant, Skeptical Broker  
**Evidence:** `docs/product_constitution/P16{L,Q,X,Y}_*`, `ui/src/components/simulation/`, `services/fiqa_api/inbox_triage/role_c_*`

---

## Persona map (canonical vs confusing)

| Persona | Also called | Primary artifacts | Deployed score (representative) |
|---------|-------------|-------------------|--------------------------------|
| **Founder (Andy)** | Role A | `P16L_ROLE_SIMULATION.md`, `P16Q_FOUNDER_JOURNEY.md` | Local continues; external URL blocked |
| **Chen Kui (broker owner)** | Role B | `P16X_CHENKUI_SIMULATION.md`, `P16Q_CHEN_KUI_SIMULATION.md`, `configs/clients/chen_kui/` | **47/100** deploy → **83/100** post P16-Y paste types |
| **Role C — cold user** | End customer on broker URL | `P16X_ROLEC_SIMULATION.md`, `P16Q_ROLE_C_SIMULATION.md` | **43/100** deploy |
| **Office Assistant** | — | `P16X_ASSISTANT_SIMULATION.md`, `P16Q_ASSISTANT_SIMULATION.md` | **44/100** deploy |
| **Skeptical Broker** | Role D (P16-L) | `P16Q_SKEPTICAL_BROKER.md` | **32/100** — Day 1 fail |
| **Role C+** | Add-car expansion personas | `run_add_car_cplus_scenario_library.py` | Lab batteries |

**Critical naming drift:** In `P16L_ROLE_SIMULATION.md`, **"Role C" = Office Assistant** — while P16-X/Q/Y use **Role C = cold end-user**. Same label, different archetype.

---

## 1. Which simulation frameworks were most effective?

Ranked by **actionable signal per hour** (from sprint verdicts, not nostalgia).

| Rank | Framework | Why effective | Evidence |
|------|-----------|---------------|----------|
| 1 | **Timed broker paste (Chen Kui)** | Maps to paid pilot wedge; found English copy, queue friction, draft quality | `P16X_CHENKUI_SIMULATION.md`, P16-Y post-fix 83 |
| 2 | **P16-Y 50-case battery** | Objective rubric; regression-safe; 0 regressions on engine sprint | `run_p16y_case_battery.py`, `P16Y_SCORECARD.md` |
| 3 | **Reality validation checklist (Q13–27)** | Cross-sprint comparable; ties to Cap contracts | `REALITY_VALIDATION_CHECKLIST.md` |
| 4 | **Failure Pattern Library mapping** | Explains *why* sims fail (FP-004 SSO, FP-009 invoice) | `FAILURE_PATTERN_LIBRARY.md`, P16-S/U |
| 5 | **Cold URL walkthrough (Role C)** | Exposes deploy vs local gap brutally | P16-Q/X — failed step 1 on Preview |
| 6 | **Office Assistant day-in-life** | Surfaces append discoverability, duplicate-case paste | `P16X_ASSISTANT_SIMULATION.md` |
| 7 | **Skeptical Broker** | Stress-tests trust / payment story | 32/100 — useful as **kill switch**, not tuning |
| 8 | **Role C LLM replay (simulation tab)** | Good for add-car depth when API key present | `ScenarioReplayTab.tsx` — hidden on trial |
| 9 | **Founder journey** | Catches operator gaps | Doesn't substitute broker proof |
| 10 | **Add-car mutation batteries** | High engineering cost; lab-only | Many `run_add_car_*` scripts |

**Least effective for trial GO:** Localhost-only guardrail PASS without Preview proof (anti-pattern in `CONSTITUTION_ENFORCEMENT.md`).

---

## 2. Which are still usable?

### Usable today (with caveats)

| Framework | How to run | Caveat |
|-----------|------------|--------|
| Chen Kui proxy cases | `configs/chen_kui_proxy_calibration_cases.json` + guardrail | Needs working Preview URL (FP-004) |
| P16-Y battery | `PYTHONPATH=. python3 scripts/run_p16y_case_battery.py` | Scores engine, not deploy UX |
| Role C API line | `POST /api/inbox/simulation-role-c-customer` | **503** without `OPENAI_API_KEY` |
| Scenario replay UI | Dev mode: `RUN_DEMO_LAB=1` or `product_only=0` | Hidden on trial build |
| Reality checklist | Manual on Preview URL | SSO blocks Q13–14 until fixed |
| Skeptical / Assistant scripts | Read P16-Q/X docs; manual walkthrough | Same SSO blocker |
| `run_follow_up_append_simulations.py` | Local guardrail | Validates append engine |
| `run_simulation_assistant_scenarios.py` | Config `simulation_assistant_scenarios.json` | Legacy path; UI orphan |

### Not usable without founder action

| Blocker | Affects |
|---------|---------|
| Vercel Preview SSO (FP-004) | All cold-URL personas |
| Empty invoice IDs (FP-009) | Day 7 payment sim |
| Zero observation log rows | Commercial evidence sim |

---

## 3. Which were abandoned?

| Item | Status | Evidence |
|------|--------|----------|
| **SimulationAssistant.tsx** | Orphan component | Zero imports; superseded by `ScenarioReplayTab` |
| **Visual Simulation Assistant** sprints | Archived | `docs/archive/sprint_reports/VISUAL_SIMULATION_ASSISTANT_*` |
| **P16-F.5 / P16-G** role revalidation | Evaluation closed | No ongoing automation |
| **External URL drop** (Role A) | Abandoned for trial day | `P16L` — *"Abandon external URL drop today"* |
| **Skeptical Broker as tuning target** | Effectively abandoned | 32/100 — use as veto, not roadmap |
| **Role C on deployed trial URL** | N/A | Customer tab absent; cold user hits broker-only surface |
| **P17 simulation platform** | Frozen | Multiple `Do not start P17` verdicts |

---

## Implementation inventory

### Backend

```
services/fiqa_api/inbox_triage/role_c_simulation_service.py  → next_role_c_customer_line()
services/fiqa_api/inbox_triage/role_c_customer_llm.py        → generate_role_c_customer_turn()
routes/inbox_triage.py                                       → POST .../simulation-role-c-customer
```

Env: `OPENAI_API_KEY` / `LLM_API_KEY`, `ROLE_C_SIMULATION_MODEL`, `ROLE_C_SIMULATION_MAX_TURNS`

### Frontend

```
ui/src/components/simulation/ScenarioReplayTab.tsx   ← ACTIVE (lab)
ui/src/components/simulation/roleCReplay.ts
ui/src/components/simulation/SimulationAssistant.tsx ← DEAD
ui/src/pages/UnifiedIntakePage.tsx                   ← hides sim tab if product_only
```

### Scripts (lab-heavy)

- `run_role_c_add_car_battery.py`
- `run_simulation_assistant_scenarios.py`
- `run_adversarial_simulation.py`, `run_complex_adversarial_simulation.py`
- `run_daily_use_simulation.py`
- `run_broker_trial_stress_simulations.py`

---

## Scorecard summary (deployed vs local)

| Persona | P16-X Deploy | P16-Y Post-engine | Interpretation |
|---------|--------------|-------------------|----------------|
| Role C cold | 43 | — | UX/URL failure dominates |
| Chen Kui | 47 | 83 (paste types) | Engine fix helped; deploy UX still weak |
| Assistant | 44 | — | Append path undiscoverable |
| Skeptical | 32 (P16-Q) | — | Payment/trust not credible |

---

## Recommendations

| Do | Don't |
|----|-------|
| Re-run **Chen Kui timed paste** after SSO fix | Rebuild Role C LLM service |
| Gate releases on **P16-Y battery** avg ≥88 | Invent new persona letters |
| Use **Skeptical** as payment veto only | Optimize UI for Skeptical score |
| Wire **ScenarioReplayTab** only in lab | Ship SimulationAssistant again |
| Fix **Role C naming** in future docs | Merge Role C cold + Role C assistant labels |

---

## Evidence index

| Doc | Path |
|-----|------|
| P16-L roles | `P16L_ROLE_SIMULATION.md` |
| P16-Q pack | `P16Q_*_SIMULATION.md` |
| P16-X pack | `P16X_*_SIMULATION.md` |
| P16-Y roles | `P16Y_ROLE_SIMULATION.md` |

---

*End of P16-Z0 Role Simulation Archaeology*
