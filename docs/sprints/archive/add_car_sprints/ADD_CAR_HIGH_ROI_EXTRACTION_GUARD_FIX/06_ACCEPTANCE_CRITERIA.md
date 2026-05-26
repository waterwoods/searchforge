# Acceptance Criteria

## Functional

- [ ] `邮编95131` (no space) sets add-car **zip** collected signal in realistic multi-turn context.
- [ ] `我自己开` sets **primary_driver** collected signal when zip + vehicle context exists.
- [ ] `要不要发你`, `要不要先发给你`, `要不我发你微信` → **`follow_up_type` ≠ `already_sent`** (expected: `new_info` with current rules).
- [ ] `材料发你微信了`, `我已经发你微信了` → **`follow_up_type` == `already_sent`**.

## Non-regression

- [ ] `scripts/audit_state_field_accuracy.py` cases unchanged in expected outcomes (run manually if part of workflow).
- [ ] `scripts/guardrail_inbox_triage.sh` passes.
- [ ] `run_multi_turn_simulations.py`, `run_add_car_edge_case_simulations.py`, `run_add_car_scenario_battery.py` pass with `LLM_GENERATION_ENABLED=false` unless project standard says otherwise.

## Documentation

- [ ] All sprint docs under `docs/sprints/ADD_CAR_HIGH_ROI_EXTRACTION_GUARD_FIX/`.
- [ ] Final report section 8 states redeploy needs clearly.
