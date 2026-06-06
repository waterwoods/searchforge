# CASE-CONTEXT CONTINUATION + RE-SHOP SLOT-CARRY + CI POSTGRES — Blueprint

## Sprint goal

Strengthen Unified Intake **Add-Car** so that (1) follow-up turns use existing case/thread context, (2) re-shop / price-pushback phrasing preserves vehicle and zip signals when present, and (3) **Postgres dual-write** validation becomes a **repeatable, disposable-DB regression** path instead of a one-off manual exercise.

## Why now

Prior sprints hardened direct Add-Car, high-risk NA-Chinese families, and disposable Postgres dual-write mechanics. The remaining leverage is narrow: **append / merged-thread behavior** (especially boundary false positives), **re-shop utterances** that omit explicit “上次报价”, and **automation** so every meaningful triage change can re-verify DB writes cheaply.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md`
3. `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md`
4. `docs/sprints/REALISTIC_NA_CHINESE_ADD_CAR_20_CASE_SPRINT/03_FINAL_REPORT.md`
5. `docs/sprints/ADD_CAR_HIGH_RISK_LANGUAGE_POSTGRES_STAGE2_SPRINT/03_FINAL_REPORT.md`

## Scope

- Continuation / thin follow-ups that should stay on the **same** Add-Car record when prior context exists.
- Re-shop / 太贵 / 换公司 / 再报 / coverage language with **slot carry** from merged customer text.
- Append **case boundary** logic: avoid treating quote price pushback as a **new issue** vs an open add-car thread.
- Disposable Postgres: schema apply + dual-write battery + **row-count / coherence** checks via one script.

## Non-scope

- CRM, full Stage 2 execution, carrier pricing, broad UI redesign, schema expansion beyond Stage 1 pilot tables, read-path cutover from JSON.

## Target outcome

- Measurable triage/boundary improvements on representative append + re-shop turns.
- `scripts/run_disposable_pg_dual_write_regression.py` as the default **local / CI-style** dual-write smoke.
- Honest report of what remains weak (e.g. single-turn material echo without any case context).
