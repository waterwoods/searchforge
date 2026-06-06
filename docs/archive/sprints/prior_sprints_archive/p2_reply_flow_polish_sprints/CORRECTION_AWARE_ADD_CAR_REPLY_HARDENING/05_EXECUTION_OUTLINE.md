# Execution Outline — Correction-Aware Add-Car Reply Hardening

## Step 1 — Audit (completed)

- **Detection**: `_derive_follow_up_type` already flagged generic corrections; add-car needed **vehicle-scoped** detection.
- **Effective vehicle**: `_extract_add_car_vehicle_concrete` used last year but **first matching** X5/X3 in merged text → wrong vehicle after correction + materials.
- **Reply quality**: `_get_add_car_acknowledgement` prioritized **year** and skipped model when both present; single-turn draft regex missed plain `Tesla`.

## Step 2 — Implement (completed)

- Added `_is_add_car_vehicle_correction_signal`.
- Split `_add_car_vehicle_concrete_from_scope` + correction-scoped resolution in `_extract_add_car_vehicle_concrete`.
- Reworked `_get_add_car_acknowledgement` (merged context, correction template, concrete-before-year-only).
- Wired `_build_client_reply_draft` add-car branches to the same acknowledgement helper.
- Passed `merged_text` into acknowledgement from `_get_next_ask_for_add_car`.
- Handoff: prefix when add-car + vehicle correction + concrete.

## Step 3 — Validate (completed)

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py`
- New scenarios: `ACE13`–`ACE16`.

## Step 4 — Deploy

- **Backend redeploy**: Yes, if production runs this Python service — triage logic changed in `triage.py`. No automatic deploy from this sprint.
