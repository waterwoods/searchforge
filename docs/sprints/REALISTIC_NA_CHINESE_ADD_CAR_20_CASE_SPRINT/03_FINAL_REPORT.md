# REALISTIC NA-CHINESE ADD-CAR 20-CASE — Final report

## Loop 1 — Alignment

- **Stage 1** (master outline + blueprint): intake → structured service record → explicit missing items → office handoff; state-first migration; not CRM.
- **DB blueprint**: Postgres stores record, messages, structured payload, state history; JSON remains authoritative until read cutover (`PROJECT_TRUTH_SWITCH`).
- **Why this sprint**: Prior foundation + prior dual-write sprint validated mechanics; this sprint stress-tests **real NA-Chinese phrasing**, **Stage-2 signal honesty**, and **live dual-write** on a disposable DB.

## Loop 2 — Case battery

See `02_CASE_BATTERY_AND_VALIDATION_SPEC.md` — **18 scenarios** covering happy path, incomplete, 微信已发, VIN delay, spouse driver, correction, re-shop, “还缺什么”, minimal, mixed language, append+VIN, material follow-up, borderline readiness, multi-turn, almost-ready+phone, lien hint, spouse vehicle, polite doc offer.

## Loop 3 — Simulation run

- **Command**: `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_na_chinese_20_case_sprint_battery.py` (optional `--persist-pg` + env for Postgres).
- **Engine**: Rule triage, `chen_kui`.
- **Directly executed**: All 18 scenarios; outputs captured (JSON snapshots: category, quote_ready, collected/still_needed, handoff, collection_stage, broker_next_step prefix).

## Loop 4 — Postgres validation

- **Real Postgres**: Yes — disposable `postgres:16-alpine`, port **54337**, DB `sf_sprint`; schema applied via **psycopg** executing `services/fiqa_api/db/schema/stage1_service_record.sql` (no `psql` client required).
- **Env**: `SERVICE_RECORD_DATABASE_URL=postgresql://postgres:sprint@127.0.0.1:54337/sf_sprint`, `UNIFIED_INTAKE_PG_DUAL_WRITE=1`, `UNIFIED_INTAKE_CASES_PATH=/tmp/sprint_na_cases.json`.
- **Counts after full battery**: `service_records` **18**, `structured_record_data` **18**, `record_messages` **21**, `state_history` **19** (append scenario adds an extra message/state event vs single-message cases).
- **Coherence spot-check**: S08-class row is `issue_category=customer_question`, `quote_readiness=need_more`, `missing_fields_summary` lists missing slots (not empty structured shell).

## Loop 5 — Structured data + state/flow + Stage-2

**Strong**

- Direct Add-Car (S01), mixed EN (S10), multi-turn fill (S14): solid slots and `need_more` / `quote_ready` progression.
- S03 微信已发: materials flags + VIN + broker step to verify WeChat.
- S08 after fix: **customer_question** with explicit `still_needed_fields` (year, zip, delivery, driver, etc.) — usable Stage-1 and Stage-2-prep signal vs prior `unclear` / empty extraction.

**Weak / honest gaps**

- **S07** (太贵 + 换公司 + coverage): still thin vehicle/delivery extraction — office must re-ask; Stage-2 automation would stall without another turn.
- **S05** (RAV4 spouse): `need_more` on year/delivery — acceptable but operator must follow up.
- **S06** (correction bubble): year/make_model sometimes split across correction — **fragile** slot reconciliation.
- **S12** (registration 又发邮箱): routed **unclear** — continuation/material echo not anchored to an open case in this harness.
- **S17** (老婆塞纳): **unclear** — spouse-as-policyholder vehicle add not reliably captured as Add-Car in rule path.

**State / flow**

- `handoff_ready` / `lifecycle_status` / `collection_stage` generally align on rule path; append (S11) exercises `triage_for_append` + `office_followup` lifecycle in case store.

**Stage-2 readiness**

- Begins to be visible where slots + `still_needed_fields` are populated (S01, S08, S13, S15 patterns).
- Blocked where category is **unclear** (S12, S17) or vehicle context too thin (S07).

## Loop 6 — Micro-fixes applied

1. **`triage.py`**: Before generic `missing_document`, classify **Add-Car “还缺什么”** continuations as `customer_question` when `_is_add_vehicle_request` **or** (vehicle_context + quote/报价/加).
2. **`markers.json`**: Add **`还想加`** to `add_vehicle` markers so `_is_add_vehicle_request` matches common NA-Chinese phrasing.

## Loop 7 — Re-validation

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (full suite after changes).
- Postgres battery re-run: counts stable (18 / 18 / 21 / 19).

## Recommended next sprint

1. **Add-Car continuation copy** for material-only follow-ups (S12-class) when `case_id` / thread context exists — likely API/UI + narrow triage context, not broad CRM.
2. **Spouse / secondary-policyholder vehicle** routing (S17) — small marker + rule guard.
3. **Re-shop utterance** slot carry (S07) — narrow extraction improvement for zip + “last quote” context.
4. **CI integration test** with disposable Postgres (per foundation sprint) so dual-write does not rely on manual Docker.

## Timing (authoritative in chat output)

Recorded in the sprint chat section **§14**.
