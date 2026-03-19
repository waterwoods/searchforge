# Execution Outline

**Purpose:** Workstreams, implementation order, test plan, loop plan.

---

## Workstreams

1. **Control docs** — Blueprint, Pack Spec, Criteria, Fix-Now Spec
2. **Baseline audit** — Current strengths, biggest risks
3. **Loop 1** — Build + run realistic pack
4. **Loop 2** — Root-cause analysis + fix-now queue
5. **Loop 3** — Apply 1–2 small fixes (if justified)
6. **Final report** — All required sections

---

## Implementation Order

1. Create document set (Phase A)
2. Baseline audit (Step 1)
3. Build realistic pack JSON
4. Run pack via new runner script
5. Diagnose failures
6. Build fix-now queue
7. Optionally implement 1–2 fixes
8. Retest, summarize

---

## Test Plan

- `run_inbox_triage_scenarios.py` — must stay 64/64
- `run_multi_turn_simulations.py` — must stay 41 strong
- `run_adversarial_simulation.py` — must stay 27 strong
- `run_complex_adversarial_simulation.py` — must stay 23 strong
- New: `run_realistic_conversation_pack.py` — report pass/weak

---

## Loop Plan

- **Loop 1:** Run pack, identify failures
- **Loop 2:** Root-cause, fix-now queue
- **Loop 3:** Small fixes if justified
- **Loop 4:** Optional refinement

---

*End of Execution Outline*
