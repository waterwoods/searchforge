# Acceptance Criteria

## Must pass

1. **No false “already sent”** on prospective-send phrases containing 截图 / 发你 / VIN permission (see `retest_scenarios.json` forbidden substrings).
2. **True completed send** still yields verify / office handoff tone (`WTR-S05`, `WTR-M01`, guardrail **HT13**).
3. **`scripts/run_wirc_trust_breaking_15_retest.py`**: **15/15** with `LLM_GENERATION_ENABLED=false`.
4. **`bash scripts/guardrail_inbox_triage.sh`**: **PASS** (all sections).
5. **`LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`**: **64/64** passed.
6. **Web-informed battery** completes without new regressions in add-car handoff behavior (10 scenarios, script default).

## Should pass (add-car regression batteries)

- `run_add_car_edge_case_simulations.py` — edge pack remains all **Strong** (18/18 at time of sprint).
- `run_add_car_scenario_battery.py` — completes successfully.
- `run_add_car_driver_zip_materials_stress_battery.py` — completes successfully.

## Explicit non-requirements

- No guarantee that every screenshot-permission line without any vehicle anchor is classified as `customer_question` (may remain `unclear` but must not claim “sent”).
- No OCR / carrier automation.
