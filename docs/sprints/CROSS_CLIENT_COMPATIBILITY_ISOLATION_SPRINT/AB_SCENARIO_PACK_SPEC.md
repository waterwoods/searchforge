# A/B Scenario Pack Spec

## Artifact

- **Battery:** `cross_client_ab_scenario_battery.json` (this folder)
- **Runner:** `scripts/run_cross_client_ab_scenarios.py`  
  Uses `triage_conversation` / `triage_for_append` with explicit `client_id` and `LLM_GENERATION_ENABLED=0`.

## Scenarios (12)

| ID | Client | Intent |
|----|--------|--------|
| ab_01–02 | A / B | Add-car clean path, first-turn handoff |
| ab_03–04 | A / B | Add-car + second turn “发你微信了” (materials-sent stitched path) |
| ab_05–06 | A / B | Add-car + prospective send (“declaration page 要不要先发你”) |
| ab_07–08 | A / B | Add-car correction second turn |
| ab_09–10 | A / B | Append same-case thread → new-issue billing (boundary copy) |
| ab_11–12 | A / B | Talk-to-agent handoff |

## Pass criteria (per scenario)

- `expected_handoff_ready` when specified.
- `draft_must_contain_any` / `draft_must_not_contain_any` for isolation signals (e.g. B must not see 陈奎 on talk-to-agent; materials-sent B must not see 办公室 after externalization).

## Known documented leak

- **ab_10** (B, append): still expects **办公室** in Chinese boundary copy — engine-shared; called out in battery `note` and audit.

## Why this matters

Same logic may stay shared; **customer-visible** stitched lines must not imply the wrong office brand on high-traffic Add-Car paths.
