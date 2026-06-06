# Battery spec — C1–C6

## Endpoints

- `POST {BASE}/api/inbox/simulation-role-c-customer`
- `POST {BASE}/api/inbox/triage` with `soft_route: add_car`, `persist_case: false` during the loop (matches `scripts/run_role_c_add_car_battery.py`).

## Cases (minimum)

| ID | Persona | Difficulty | Max turns | Optional note (zh) |
|----|---------|------------|-----------|-------------------|
| C1 | `price_sensitive` | `realistic` | 7 | 加车报价；关心保费与自付额；追问正式提交与消息时间 |
| C2 | `price_sensitive` | `tough` | 8 | 刁钻比价；对办公室接手/正式提交敏感 |
| C3 | `elderly` | `tough` | 8 | 年长口语；担心办公室是否收到 |
| C4 | `family_vehicle` | `realistic` | 7 | 家庭多车/主驾；承保与下一步 |
| C5 | `materials_first` | `realistic` | 7 | 微信已发驾照/dec；是否再提交 |
| C6 | `fragmented` | `tough` | 8 | 信息很碎；纠错与状态跟随 |

## Extra probe (this sprint)

After each variant, if `handoff_ready` or handoff-ish lifecycle on last turn: one `POST /api/inbox/triage` with `persist_case: true`, `formal_submit: true` (same `session_id`, prior turns only in `conversation_turns`) to observe `case_id`, `formal_submitted_at`, `updated_at`.

## Follow-up timestamp check (spot)

`POST /api/inbox/cases/{case_id}/append-message` on one created case to confirm `formal_submitted_at` stable and `updated_at` advances.

## Client

`client_id: chen_kui` (client pack).
