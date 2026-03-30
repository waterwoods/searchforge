# High-Frequency Residual Customer Copy Externalization — Final Report

This file mirrors the sprint deliverable structure. For the full narrative (including 中文), see the chat **Final Report** section or merge this file into release notes.

## Summary

Four **high-traffic customer-visible** families were made **client-overridable**: add-car premium caveat, payment/premium “already sent materials” tail, add-driver reply, and bundling reply. **SoCal Precision** overrides were added; **Chen Kui** continues to use engine + industry defaults. **demo_broker** validates omitted stitched keys. **Guardrail** and **Add-Car battery** passed.

## Document set

- `RESIDUAL_COPY_EXTERNALIZATION_BLUEPRINT.md`
- `HIGH_FREQUENCY_RESIDUAL_COPY_AUDIT_SPEC.md`
- `EXTERNALIZATION_PRIORITY_SPEC.md`
- `AB_RESIDUAL_COPY_SCENARIO_PACK_SPEC.md`
- `EXECUTION_OUTLINE.md`
- `ACCEPTANCE_CRITERIA.md`
- `FOUNDER_INSPECTION_NOTES.md`
- `EXTERNALIZATION_TABLE_NOW_LATER_KEEP.md`
- `residual_copy_ab_scenario_battery.json`
- `FINAL_REPORT.md` (this file)

## Code / config touchpoints

- `services/fiqa_api/inbox_triage/triage.py` — helpers + wiring + next-ask parity
- `services/fiqa_api/inbox_triage/config_loader.py` — stitched schema doc
- `configs/industries/insurance/reply_templates.json` — `add_driver`, `bundling`
- `configs/clients/socal_precision/handoff_phrases.json` — new stitched keys
- `configs/clients/socal_precision/reply_overrides.json` — add_driver, bundling
- `scripts/run_residual_copy_ab_scenarios.py`, `scripts/guardrail_inbox_triage.sh`

## Validation run (this sprint)

- `bash scripts/guardrail_inbox_triage.sh` — **PASS**
- `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py` — **PASS**
