# Rule-Map Summary Spec

The **filled rule map** for this sprint is in **`09_FINAL_REPORT.md` §8**. This spec lists **what the summary must contain**.

## Required sections

1. **Main backend modules** — triage engine, config loader, API surface, case persistence touchpoints.
2. **Add-Car entry points** — functions that decide add-car vs other flows and build replies.
3. **Extraction** — ZIP regex, driver markers, vehicle concrete / correction, field dict shape.
4. **State / handoff** — quote readiness, `follow_up_type`, collection stage, materials-sent branches.
5. **Configurable copy** — `add_car_rules.json` keys and defaults.
6. **Validation assets** — scenario JSON paths + runner scripts.

## Minimum files to cite (concrete)

- `services/fiqa_api/inbox_triage/triage.py`
- `services/fiqa_api/inbox_triage/config_loader.py` (`get_add_car_rules`, defaults)
- `configs/industries/insurance/add_car_rules.json`
- `services/fiqa_api/routes/inbox_triage.py` (HTTP entry)
- `services/fiqa_api/inbox_triage/case_store.py` (contact / attachments notes)
- `scripts/run_add_car_*.py`, `scripts/guardrail_inbox_triage.sh`, `scripts/test_inbox_triage_api.py`
- Scenario batteries: this sprint, ACB, ADZM, `configs/customer_entry_multi_turn_simulations.json` (Add-Car sections)

## Diagram (logical)

`conversation turns` → `triage_conversation` → `_rule_based_triage` (when LLM off) → add-car branch → `_extract_add_car_fields` / `_get_next_ask_for_add_car` / `_get_add_car_acknowledgement` → handoff + `broker_next_step` assembly.
