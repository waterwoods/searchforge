# Scenario Pack / Validation Spec

## Primary battery (extended)

- `docs/sprints/ADD_CAR_DRIVER_ZIP_MATERIALS_STRESS_BATTERY/scenario_battery.json`  
  - Existing: ADZM-M01, M02, X02, X04 (prospective vs `already_sent`).  
  - **Added**: ADZM-M05 (要不我发你微信你看下行不行), ADZM-M06 (我先发给你看看行吗 after vague opener), ADZM-X05 (incomplete + 要不要先发给你行驶证).

## Runners (LLM off)

```bash
bash scripts/guardrail_inbox_triage.sh
PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py
PYTHONPATH=. python3 scripts/run_add_car_driver_zip_materials_stress_battery.py
PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py
```

## Manual checks

- Single-bubble quote-ready + 要不要发你行驶证截图 → lead mentions 截图, then handoff.  
- `材料发你微信了` → still `already_sent`, warmer verify line, **no** prospective lead.
