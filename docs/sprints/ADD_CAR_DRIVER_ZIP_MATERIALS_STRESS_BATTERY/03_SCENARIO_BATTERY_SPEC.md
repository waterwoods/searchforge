# Scenario Battery Spec (machine + human)

## Source of truth

- **JSON:** `scenario_battery.json` (19 scenarios).
- **Runner:** `scripts/run_add_car_driver_zip_materials_stress_battery.py`

## Runner behavior

1. Sets `LLM_GENERATION_ENABLED=false` unless overridden in environment.
2. For each customer message in order: calls `triage_conversation(latest_text, conversation_so_far)`.
3. Appends customer + `client_reply_draft` as system turn to the conversation list.
4. Emits per-turn: `issue_category`, `handoff_ready`, `triage_path`, `quote_ready_status`, `follow_up_type`, `collected_fields`, `still_needed_fields`, `broker_next_step`, `client_reply_draft`.

## Commands

```bash
cd /path/to/searchforge
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py --json > /tmp/adzm.json
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_driver_zip_materials_stress_battery.py --single ADZM-D04 -v
```

## Scenario index (abbreviated)

| ID | Focus |
|----|--------|
| ADZM-Z01–Z06 | ZIP variants (incl. `zip 95131` + `zip95131`) + one two-turn ZIP completion |
| ADZM-D01–D05 | Driver micro-phrases incl. 主要驾驶人是我老婆 |
| ADZM-M01–M04 | 要不要… vs 已发 / registration |
| ADZM-X01–X04 | Mixed density + two-turn materials |

## Change control

When triage rules change, re-run the runner and update `FINAL_REPORT.md` and `FOUNDER_INSPECTION_NOTES.md`.
