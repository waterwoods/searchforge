# A/B Residual Copy Scenario Pack Spec

## Artifact

- **Battery:** `residual_copy_ab_scenario_battery.json`
- **Runner:** `scripts/run_residual_copy_ab_scenarios.py`

## Coverage

| Bucket | Count | Intent |
|--------|------:|--------|
| Client A (chen_kui) | 6 | Must show engine/industry **办公室 / 我这边** defaults where applicable |
| Client B (socal_precision) | 6 | Must show **本所 / desk** and **must not** show Client A caveat phrases |
| Engine default (demo_broker) | 1 | No stitched keys → **office** caveat default still sane |
| Flagship add-car handoff | 2 | Quote-ready message → **handoff** copy still correct per client |
| English add-car caveat | 2 | **desk** vs **office** substring isolation |

**Total:** 15 scenarios.

## Assertions

- `draft_must_contain_any` / `draft_must_not_contain_any` on `client_reply_draft`.
- `expected_handoff_ready` on flagship add-car rows.
- Language guard: Chinese vs English drafts.

## Why it matters

- Catches **cross-client leakage** on the exact strings that were hardcoded.
- Confirms **demo_broker** still reads acceptably when stitched keys are absent.
- Protects **flagship add-car** handoff phrases (unchanged business path).
