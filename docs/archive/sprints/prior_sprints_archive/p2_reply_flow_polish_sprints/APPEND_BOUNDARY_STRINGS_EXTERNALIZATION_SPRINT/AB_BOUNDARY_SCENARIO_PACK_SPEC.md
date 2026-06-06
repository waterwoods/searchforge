# A/B Boundary Scenario Pack Spec

## Artifact

- **Battery:** `docs/sprints/APPEND_BOUNDARY_STRINGS_EXTERNALIZATION_SPRINT/append_boundary_ab_scenario_battery.json`
- **Runner:** `scripts/run_append_boundary_ab_scenarios.py`

## Runner contract

- Calls `triage_for_append(existing_source_text, latest_text, client_id=...)`.
- Asserts `expected_case_boundary`: `same_case` (no `case_boundary`), `new_issue`, or `borderline`.
- For `borderline`, requires `human_confirmation_required`.
- Optional: `draft_must_contain_any` / `draft_must_not_contain_any`, `expected_draft_language` (`zh` / `en`).

## Scenarios (12)

| ID | Intent |
|----|--------|
| abb_01–02 | Add-car handoff → **same_case** (materials follow-up) A vs B |
| abb_03–04 | Add-car → **billing new_issue** A vs B |
| abb_05–06 | **Borderline** (“还有一个问题”) A vs B |
| abb_07–08 | **EN billing** new_issue A vs B |
| abb_09–10 | **Premium thread** → add-car pivot A vs B |
| abb_11 | Known leak path: add-car → **claim** new_issue, Client B |
| abb_12 | **demo_broker**: no `append_boundary` → defaults still sane |

## Why it matters

- Proves **classification** unchanged while **wording** switches by client.
- Locks **A/B isolation**: B must not show Chen-specific strings; A must not show B-only tokens where asserted.

## Guardrail

`bash scripts/guardrail_inbox_triage.sh` includes step **`[12b]`** running this battery.

## Related

- Cross-client stitched pack (updated `ab_10`): `docs/sprints/CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT/cross_client_ab_scenario_battery.json`
- Logic-only pack: `configs/case_boundary_append_scenarios.json` + `scripts/run_case_boundary_battery.py`
