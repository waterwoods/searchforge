# INTENT LAYER IMPLEMENTATION + REPLY ROUTING BINDING — Final report

## What was implemented

- New module `services/fiqa_api/inbox_triage/add_car_intent.py`: `resolve_add_car_turn_intent`, `ResolvedAddCarIntent`, named intent constants.
- `triage.py`: Add-Car handoff phrase key selection uses the resolver (merged truth includes `still_needed_fields`); triage response includes `add_car_turn_intent`.
- `configs/clients/chen_kui/handoff_phrases.json`: `add_car_office_receipt`, `add_car_office_receipt_submitted`.
- Engine fallbacks for missing pack keys: pre-submit office-receipt lines in `triage.py`; post-submit fallback line for `add_car_office_receipt` in `_POST_SUBMIT_ADD_CAR_FALLBACK_ZH_EN`.
- `tests/test_add_car_intent.py` regression tests.

## What improved

- Explicit intent families and routing keys instead of only `_classify_add_car_post_handoff_family` heuristics inline in `triage.py`.
- **Office receipt** questions get a dedicated routing path and pre-submit safe defaults.
- **Materials** on turn ≥2 route to `add_car_supplement` (reduces repeated flagship `add_car` default before stitched overrides).
- Observable `truth_notes` for pre-submit office-receipt and materials-claim cases.

## What remains weak

- Still rule-based markers (not ML); edge overlaps possible (e.g. short English messages).
- Non-Add-Car lanes unchanged.
- `use_alt` rotation on `add_car` only — late-turn variety still depends on pack + stitched blocks.

## Recommended next sprint

- Thread `add_car_turn_intent` into UI / workbench for operator visibility; optional Role-C battery oracles keyed on `intent_family`.
