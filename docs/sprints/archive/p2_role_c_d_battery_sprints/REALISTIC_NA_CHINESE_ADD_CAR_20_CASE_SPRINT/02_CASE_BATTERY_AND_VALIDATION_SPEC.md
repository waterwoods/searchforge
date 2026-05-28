# Case battery & validation spec

## Battery overview

**18 scenarios** (`S01`–`S18`), `client_id=chen_kui`, engine **rule-based** (`LLM_GENERATION_ENABLED=0`). Harness: `scripts/run_na_chinese_20_case_sprint_battery.py`.

| ID | Category | Example thrust | Turn shape | Tests |
|----|----------|----------------|------------|--------|
| S01 | Direct happy-path Add-Car | Full vehicle + zip + pickup + driver | single | intent, slots, quote_ready, handoff, PG row |
| S02 | Incomplete Add-Car | No zip | single | missing zip, need_more, handoff gating |
| S03 | 微信 / already sent | Camry + VIN 微信发过了 | single | materials flags, VIN, broker verify WeChat |
| S04 | VIN not ready | Dealer delay phrasing | single | VIN guard, quote_ready vs delivery |
| S05 | Spouse / second driver | 老婆也会开 + quote怎么报 | single | multi-driver routing, slots |
| S06 | 改口 / pickup correction | 不是明天是这个周五 | single | date correction, extraction stability |
| S07 | 太贵 / re-shop / coverage | 换company + coverage + zip | single | add-car vs premium_review, slot depth |
| S08 | “还缺什么” Add-Car | Camry quote 还缺什么 | single | **must not** be unclear/missing_document; still_needed clarity |
| S09 | One-line minimal | 想加车 | single | need_more, progressive collection |
| S10 | Mixed ZH/EN | Model Y + zip + Friday | single | mixed language, markers |
| S11 | Append same record | Prius first → VIN append | append | `triage_for_append`, PG messages + state_history |
| S12 | Material follow-up | registration 又发邮箱 | single | continuation / unclear risk |
| S13 | Borderline quote-readiness | VIN没拿到可以先报吗 | single | almost_ready / need_more semantics |
| S14 | Multi-turn clarification | 我想加车 → full details | multi | merged context, slot fill |
| S15 | Almost-ready + phone | Lexus + phone in same bubble | single | identity slots, handoff |
| S16 | Dealer finance / lien hint | F-150 dealer finance | single | lienholder signal if any |
| S17 | Policyholder spouse vehicle | 老婆塞纳 + zip | single | routing / extraction edge |
| S18 | Polite office check | 要不要先发行驶证 | single | prospective send + slots |

## Structured-data success criteria

- `issue_category` appropriate for Add-Car wedge (typically `customer_question` on rule add-car path).
- `collected_fields` / `still_needed_fields` non-empty when message has extractable signal; **S08-class** must surface missing vehicle/delivery/identity fields, not empty structured shells.
- `quote_ready_status` in `quote_ready` | `almost_ready` | `need_more` when add-car pipeline applies.
- `broker_next_step` references concrete next office actions where possible.

## Postgres validation criteria

With `SERVICE_RECORD_DATABASE_URL` set and `UNIFIED_INTAKE_PG_DUAL_WRITE=1`:

- One `service_records` row per saved case; matching `structured_record_data` row.
- `record_messages` count ≥ customer messages (append + optional system line increases count).
- `state_history` has baseline events; append cases show extra history where implemented.
- `missing_fields_summary` populated when `still_needed_fields` non-empty (repository behavior).

## State / flow review criteria

- `handoff_ready` aligns with `collection_stage` / `lifecycle_status` semantics.
- Append path moves `lifecycle_status` toward office follow-up (`office_followup` in case store).
- Customer vs office “next step” readable from `client_reply_draft` + `broker_next_step` (no redesign—readability only).

## Stage-2 (quote-prep) readiness criteria

- Enough structured fields to know **whether quote can start** (vehicle + garage + delivery + driver + identity).
- `still_needed_fields` lists blockers clearly for automation handoff.
- Weak: price objection without vehicle context (S07-class) — expect office re-ask; document honestly.

## Acceptance criteria

- Battery executed; results recorded in `03_FINAL_REPORT.md`.
- `bash scripts/guardrail_inbox_triage.sh` **PASS** after any triage/config change.
- Postgres: either **verified** with real instance or explicitly **not run**.
