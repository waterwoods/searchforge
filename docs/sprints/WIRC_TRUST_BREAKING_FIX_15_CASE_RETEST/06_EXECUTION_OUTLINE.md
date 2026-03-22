# Execution Outline

## Preconditions

- Repo root: `searchforge`
- Triage tests use **rules only**: `export LLM_GENERATION_ENABLED=false` (runner scripts setdefault this).

## Loop executed

1. **Audit** — Read `triage.py` follow-up typing, unclear short path, summary hints, cancellation fields; reproduce with `triage_message` / `_derive_follow_up_type`.
2. **Implement** — `_is_prospective_send_offer_message`, `_message_claims_completed_material_send`, call-site rewires, add-car routing + slot fixes, `markers.json` tokens.
3. **Retest** — 15-case script + guardrail + WIRC battery + core add-car batteries.
4. **Classify** — Document remaining gaps (this folder `05_…`).
5. **Summarize** — Final report (`09_…`).

## Commands (copy-paste)

```bash
# 15-case sprint retest
PYTHONPATH=. python3 scripts/run_wirc_trust_breaking_15_retest.py

# Unified intake guardrail
bash scripts/guardrail_inbox_triage.sh

# Scenario pack (64 scenarios)
LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py

# Web-informed add-car battery
PYTHONPATH=. python3 scripts/run_web_informed_add_car_realistic_battery.py

# Add-car batteries (examples)
LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py
LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py
LLM_GENERATION_ENABLED=false PYTHONPATH=. python3 scripts/run_add_car_driver_zip_materials_stress_battery.py
```

## Files touched (implementation)

- `services/fiqa_api/inbox_triage/triage.py`
- `configs/industries/insurance/markers.json`
- `scripts/run_wirc_trust_breaking_15_retest.py` (new)
- `docs/sprints/WIRC_TRUST_BREAKING_FIX_15_CASE_RETEST/*` (new)
