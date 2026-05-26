# Execution Outline — Add-Car Battery Re-Run + Mutation Stress

**Target time:** 45–75 minutes (document-driven loops).

## Loop A — Baseline re-run

1. Run `scripts/run_add_car_scenario_battery.py` → capture pass narrative.
2. Run `scripts/run_add_car_edge_case_simulations.py` → expect 18/18 strong.
3. Run `scripts/run_multi_turn_simulations.py` → expect 0 weak.
4. Run `scripts/guardrail_inbox_triage.sh` → expect `Guardrail: PASS`.

## Loop B — Mutation design

1. Confirm three attack surfaces (ZIP, driver, already-sent intent).
2. Author `mutation_scenario_pack.json` (10 scenarios).
3. Add runner `scripts/run_add_car_mutation_battery.py`.

## Loop C — Mutation execute + grade

1. `PYTHONPATH=. python3 scripts/run_add_car_mutation_battery.py`
2. Grade each scenario (Strong / Acceptable / Weak / Trust-breaking) using `EVALUATION_CRITERIA.md`.
3. Update `FIX_PRIORITY_SPEC.md` if any Weak or Trust-breaking.

## Loop D — Summarize

1. Write `FINAL_REPORT.md` (English + 中文总结 + founder block).
2. Write `FOUNDER_INSPECTION_NOTES.md` (1-page skim).

## Artifacts

| Artifact | Path |
|----------|------|
| Mutation pack | `mutation_scenario_pack.json` |
| Runner | `scripts/run_add_car_mutation_battery.py` |
| Reports | `FINAL_REPORT.md`, `FOUNDER_INSPECTION_NOTES.md` |
