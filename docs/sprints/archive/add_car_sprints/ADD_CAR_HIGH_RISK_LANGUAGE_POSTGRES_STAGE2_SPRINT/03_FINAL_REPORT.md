# ADD-CAR HIGH-RISK LANGUAGE + POSTGRES + STAGE-2 — Final report

## What was simulated

- **16-case battery** (`scripts/run_high_risk_add_car_pg_stage2_sprint_battery.py`): direct Add-Car, weak follow-ups (还缺什么 / 材料已发 / registration 又发), spouse + household second vehicle, re-shop, multi-turn, append+VIN, almost-ready, minimal opener.
- **Engine:** rule triage, `LLM_GENERATION_ENABLED=0`, client `chen_kui`.
- **Postgres:** disposable `postgres:16-alpine`, port **54338**, schema via psycopg executing `services/fiqa_api/db/schema/stage1_service_record.sql`; dual-write env per `PROJECT_TRUTH_SWITCH`.

## What improved

1. **Priority 1 — “材料/微信已发 + 还缺什么”** — Classify as **`customer_question`** before generic `missing_document`; extend **`_is_add_vehicle_request`** so thin turns still get **add-car structured fields** (`still_needed_fields`, `quote_ready_status`, materials-sent flags).
2. **Priority 1 — registration / doc resend “收到吗”** — New guardrail branch → **`missing_document`** with **`_extract_missing_doc_status`** extended for **registration** (+ email channel) so **`verify_carrier_received`** appears in `still_needed_fields`.
3. **Priority 2 — spouse vehicle (“老婆…塞纳…报一下价”)** — **`_is_add_vehicle_request`**: **报+价** + spouse terms + vehicle context / **那台** pattern.
4. **Priority 2 — household second vehicle (“家里还有一台…一起报”)** — Same function: **家里还有 / 也要一起报** + vehicle markers + **报/报价/quote/价**.
5. **Multi-driver quote question** — **`都会开`** added alongside **也会开** for spouse/household driving phrasing.
6. **Markers** — **`报一下价`**, **`报个价`** in `configs/industries/insurance/markers.json` for substring gaps vs **报价**.
7. **Postgres re-validation** — After fixes, full battery dual-write: **16** service_records, **16** structured_record_data, **19** record_messages, **17** state_history; **`unclear` row count 0**.

## What persisted well

- **Dual-write** mirrored JSON cases; **`missing_fields_summary`** denormalized from `still_needed_fields` (existing repository behavior).
- **Append scenario (H14)** produced extra **message** + **state_history** row vs single-message cases (consistent with prior sprint reports).

## What remained weak

- **Re-shop (H11/H12)** — Still **thin on delivery / vehicle** when the customer omits pickup language; acceptable but **Stage-2 automation would still need another turn**.
- **Thin “材料还缺什么”** — Structured **`still_needed`** is a **generic add-car checklist**, not thread-specific (no CRM memory in rule-only single turn).
- **Read path** — Still **JSON-authoritative**; no Postgres read API in this sprint.

## Stage-2 gaps (honest)

- No automatic **quote-ready scoring** beyond current **`quote_ready_status`** and slots.
- No **carrier** or **rater** integration.
- **Context-free** follow-ups remain dependent on **case/thread** in product (UI/API), not fixed entirely in triage rules.

## Recommended next sprint

1. **Triage + optional case context** for material-only follow-ups when `case_id` / history exists (S12-class from NA sprint).
2. **Narrow slot carry** for re-shop utterances that mention **model year** in one clause but omit delivery.
3. **CI integration test** with disposable Postgres for dual-write regression.
4. **Dual-write** for additional mutations (status/notes) when pilot-critical (per foundation report).

## Timing (authoritative in chat §14)

Recorded in the sprint chat output.
