# Client Pack Drill Scenario Pack

Machine source: [`drill_scenarios.json`](./drill_scenarios.json)  
Runner: `PYTHONPATH=. python3 scripts/run_second_broker_drill.py` (uses `LLM_GENERATION_ENABLED=0` by default)

## Scenarios (8)

| ID | Intent |
|----|--------|
| `drill_client_config_surfaces` | `get_ui_copy` / `get_handoff_phrases` load; no 陈奎 in pack-owned JSON |
| `drill_add_car_clean_handoff` | Add-car clean path, one shot → handoff uses **本所 / 营业日** |
| `drill_add_car_partial_then_complete` | Partial → completion |
| `drill_add_car_correction` | Correction follow-up after quote-ready handoff |
| `drill_talk_to_agent` | Free-text **转接人工** → `customer_requested_human` + client phrase |
| `drill_add_car_first_turn_template` | Vague premium ask — documents where **reply_overrides** may be skipped |
| `drill_materials_sent_note` | Materials-sent branch — **expects 办公室** in draft to prove core hardcoding leak |

## What “pass” means

- Assertions use **direct** `triage_conversation(..., client_id="socal_precision")` (verified).
- One scenario **intentionally** asserts presence of **办公室** to lock the known leak (verified failure of pure client-voice in that branch).

## Not covered in JSON (manual / founder)

- Full browser pass with `?client=socal_precision` (visual quick-start + closure card) — recommended once with API running.
- LLM-enabled triage — **not** asserted here (inferred: wording may drift).
