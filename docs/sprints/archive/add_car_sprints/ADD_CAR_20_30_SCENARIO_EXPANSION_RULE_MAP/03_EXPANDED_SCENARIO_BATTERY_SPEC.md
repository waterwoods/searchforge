# Expanded Scenario Battery — File Spec

## Canonical file

- **Path:** `docs/sprints/ADD_CAR_20_30_SCENARIO_EXPANSION_RULE_MAP/scenario_battery.json`
- **Format:** JSON, UTF-8, `version: "1"`, `sprint: "ADD_CAR_20_30_SCENARIO_EXPANSION_RULE_MAP"`.

## Runner contract

- **Script:** `scripts/run_add_car_expansion_rule_map_battery.py`
- **API under test:** `services.fiqa_api.inbox_triage.triage.triage_conversation`
- **Environment:** `LLM_GENERATION_ENABLED=false` (set by script unless overridden in shell).

## Output shape (per scenario, per turn)

The runner attaches:

- `issue_category`, `handoff_ready`, `triage_path`, `quote_ready_status`, `collection_stage`, `follow_up_type`
- `client_reply_draft`, `broker_next_step`, `next_best_question` (truncated)
- `collected_fields`, `still_needed_fields`, `manual_followup_needed`

## Optional regression bundles

```bash
PYTHONPATH=. python3 scripts/run_add_car_expansion_rule_map_battery.py --include-existing-batteries --json
```

Includes:

1. This sprint’s `scenario_battery.json`
2. `docs/sprints/ADD_CAR_SCENARIO_BATTERY_EVALUATION/scenario_battery.json`
3. `docs/sprints/ADD_CAR_DRIVER_ZIP_MATERIALS_STRESS_BATTERY/scenario_battery.json`

## Change control

When adding scenarios: preserve unique `id`, keep `coverage_category` aligned with A–G, and document rationale in `why_matters` / `expected_good_behavior`.
