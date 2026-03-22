# Scenario / Regression Pack Spec

## Artifact

- **Data**: `regression_scenarios.json` in this folder.
- **Runner**: `scripts/run_add_car_high_roi_regression.py`

## Case types

1. **`follow_up_cases`** — direct `_derive_follow_up_type(message)` assertions (deterministic, no LLM).
2. **`add_car_field_cases`** — multi-turn `triage_conversation` with `expect_collected_contains` on `collected_fields`.

## Minimum list (sprint requirement)

Covered in JSON + runner:

1. 邮编95131  
2. 邮编 95131  
3. zip 95131  
4. 我自己开  
5. 我一个人开  
6. 我老婆开  
7. 儿子开  
8. 女儿开 (extra)  
9. 要不要发你  
10. 要不要先发给你  
11. 材料发你微信了  
12. 我已经发你微信了  
13. 要不我发你微信  

## Broader regression (repo scripts)

After code changes, always run:

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py`
- `PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py`
- `PYTHONPATH=. python3 scripts/run_add_car_high_roi_regression.py`
