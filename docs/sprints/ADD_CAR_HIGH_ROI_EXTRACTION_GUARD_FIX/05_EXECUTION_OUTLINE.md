# Execution Outline

## Loop 1 — Audit

- Read `triage.py`: `_extract_add_car_fields`, `_derive_follow_up_type`, `_is_fast_path_candidate`, add-car acknowledgements.
- Confirm root causes: `\b` ZIP, driver substring gaps, `发你` in questions.

## Loop 2 — Implement

- Add `_CA_ZIP_STRICT_RE`, `_text_has_ca_zip_signal`, `_extract_ca_zip_from_message`.
- Add `_ADD_CAR_DRIVER_MARKERS` + `_text_has_add_car_driver_signal`.
- Add `_is_prospective_send_offer_message` + reorder `_derive_follow_up_type`.
- Wire acknowledgements to shared zip extractor.

## Loop 3 — Regression pack

- Author `regression_scenarios.json` and `run_add_car_high_roi_regression.py`.

## Loop 4 — Validate

- Guardrail + multi-turn + edge + scenario battery + new regression runner.

## Loop 5 — Document & ship judgment

- Sprint specs + final report; state backend redeploy if runtime Python changed.

## Time budget

Target 45–75 minutes wall clock for a single engineer; automation should finish in minutes once env is ready.
