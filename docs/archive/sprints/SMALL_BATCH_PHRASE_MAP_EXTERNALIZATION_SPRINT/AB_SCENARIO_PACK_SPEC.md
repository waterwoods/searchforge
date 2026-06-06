# A/B Scenario Pack Spec

## Battery artifact

- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/small_batch_ab_scenario_battery.json`
- Runner: `scripts/run_small_batch_phrase_map_ab_scenarios.py`

## Coverage matrix

1. **Client A vs B per new family**
   - doc-clarification suffix (add-car handoff-ready)
   - add-car coverage overlay (answer + suffix)
   - payment correction urgency overlay
2. **Negative leak assertions**
   - Client B must not contain Chen Kui office voice markers
3. **Fallback scenario**
   - `demo_broker` omitted-key path verifies engine default remains sane
4. **Flagship regression**
   - Add-car handoff baseline still passes for Client A

## Why this pack matters

- Verifies same logic with differentiated wording
- Verifies no cross-client leakage
- Verifies fallback safety when keys are absent
