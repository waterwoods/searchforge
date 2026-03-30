# A/B Scenario Pack Spec

## Battery Artifact
- `docs/sprints/LONG_TAIL_GENERIC_REPLY_EXTERNALIZATION_SPRINT/long_tail_ab_scenario_battery.json`
- Runner: `scripts/run_long_tail_generic_reply_ab_scenarios.py`

## Coverage Goals
- One client A + one client B scenario for each new phrase family.
- At least one negative leak assertion for client B.
- At least one omitted-key/fallback sanity check (industry fallback when client override not present).
- At least one flagship add-car sanity check for non-regression.

## Scenario Groups
- Family checks:
  - `missing_signature` (A/B zh)
  - `underwriting_followup` (A/B en)
  - `renewal_reminder` (A/B zh)
  - `informational` (B negative leak en)
- Fallback sanity:
  - renewal reminder fallback behavior still coherent.
- Flagship sanity:
  - add-car still handoff-ready with existing tone path.

## Assertions
- `expected_handoff_ready`
- language checks
- must-contain phrases for intended client tone
- must-not-contain phrases to prevent cross-client leakage
