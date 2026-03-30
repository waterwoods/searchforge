# REALISTIC ADD-CAR SIMULATION + POSTGRES DUAL-WRITE VALIDATION — Final report

## What was simulated

Ten scenarios (B1–B10): direct Add-Car, 微信已发, VIN未就绪, spouse/second driver, same-turn date correction, re-shop/太贵, “还缺什么”, minimal “想加车”, multi-turn merged history, and two-turn **append** (first message saved, second via `triage_for_append` + `append_follow_up_message`). Client pack: `chen_kui`. Engine: **rule-based** (`LLM_GENERATION_ENABLED=0`) for reproducibility.

## What persisted correctly

- **JSON path** (via `save_case` / `append_follow_up_message`): all scenarios produced cases with coherent `issue_category`, Add-Car collections, and messages as designed.
- **Postgres dual-write** (disposable `postgres:16-alpine` on port 54333, schema from `stage1_service_record.sql`): after the full battery, counts were **10** `service_records`, **10** `structured_record_data`, **14** `record_messages`, **11** `state_history` (extra event on append). Row content matched first-case spot check (`quote_readiness`, JSON `still_needed_fields`).

## What failed or was weak

1. **B7 (“还想加那台Camry的quote，现在还缺什么…”)** — Routed to `missing_document` with **empty** `collected_fields` / `still_needed_fields`. Poor Stage 1 and Stage 2 signal for a clear Add-Car continuation ask.
2. **B6 (太贵 / 换公司 / coverage)** — Only **zip** and weak `insurance_status_new_customer` surfaced; vehicle and pickup context under-extracted. Office would need to re-ask most slots.
3. **B2 (微信发过了)** — Structurally strong (`customer_says_materials_sent`, VIN collected) but **`handoff_ready: false`** in rule path. In the **real API**, `persist_case` would **not** write JSON or Postgres until handoff — correct product guardrail, but operators should know “strong structured state” can still be **in-session only**.
4. **`missing_fields_summary`** was always **NULL** in Postgres until a small repository fix (see below).

## What was improved

- **`services/fiqa_api/db/service_record_repository.py`**: populate `structured_record_data.missing_fields_summary` from `still_needed_fields` (comma-separated) on insert and upsert, for easier SQL/office skim without replacing JSONB authority.

## Re-validation

- Truncated pilot tables; saved a single Add-Car case with dual-write on; confirmed `missing_fields_summary` = `name, phone` matching JSON.
- `bash scripts/guardrail_inbox_triage.sh` — **PASS**.

## Next most valuable sprint

1. **Triage rule tweak** for B7-style “还缺什么 / 加那台车” Add-Car follow-up (keep narrow; avoid broad `missing_document` bleed).
2. **Stronger slot extraction** for price-shopping utterances that still mention dealer/zip (B6-class).
3. **Integration test** with disposable Postgres in CI (foundation sprint already suggested this).
4. **Dual-write** for `update_case_status` / notes when those become pilot-critical.

## Environment note

Repo host had **no `psql` client**; schema was applied with **psycopg** executing the SQL file. Dual-write validation is still “real Postgres,” not a mock.
