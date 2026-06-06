# Battery spec — long-thread Role C

## Command surface

```bash
export ROLE_C_SIMULATION_MAX_TURNS=8   # align client request with server le=8
PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py \
  --base-url http://127.0.0.1:8001 \
  --client-id chen_kui \
  --persona <persona> --difficulty <difficulty> \
  --max-turns 7 --truth-chain \
  --optional-note "<scenario note>" \
  --jsonl
```

## Cases (this sprint)

| ID | Persona           | Difficulty | Outer loops | Note |
|----|-------------------|------------|------------|------|
| C1 | price_sensitive   | tough      | 7          | 比价 / 正式提交 / 材料与时间线 |
| C2 | elderly           | tough      | 7          | 收到确认 / 是否算报上去 |
| C3 | family_vehicle    | realistic  | 7          | 家庭用车 / 承保细节 / 下一步 |
| C4 | materials_first   | realistic  | 7          | 材料已发 / 是否再提交 / 进度 |
| C5 | fragmented        | tough      | 7          | 碎片信息 / 状态挑战 |

## What `--truth-chain` does

When triage returns `handoff_ready` and there is not yet a `case_id`, the runner injects one persisted `formal_submit` customer line so later triage calls pass `case_id` and **`reply_truth_context` from case store** (strongest practical post-submit path for this battery).

## Oracle reference

`scripts/role_c_battery_oracles.py` — truth/reply/intent/state heuristics (e.g. `REPLY_REPEATED_BLOCK`, `STATE_POST_SUBMIT_LIFECYCLE_COLLECTING`, `INTENT_LATE_GENERIC` when `add_car_turn_intent` is present).
