# ADD-CAR HIGH-RISK LANGUAGE + POSTGRES + STAGE-2 — Blueprint

## Sprint goal

Strengthen three linked areas for Unified Intake (Add-Car flagship path):

1. **High-risk realistic North-American Chinese phrasing** — isolated follow-ups, already-sent + “还缺什么”, spouse/household vehicles, re-shop/coverage language.
2. **Postgres-persisted data quality** — dual-write rows remain coherent and skimmable (`missing_fields_summary`, `quote_readiness`, structured payload).
3. **Stage-2 quote-prep readiness signals** — clearer `still_needed` / `quote_readiness` / broker next steps without building full Stage 2.

## Why now

Prior foundation and NA-Chinese sprint reports showed: mechanics of dual-write work; remaining value is **narrow triage and slot behavior** on realistic broker-facing utterances. Broad UI or CRM work would not move the data asset as much as fixing these families.

## Read-first docs (mandatory alignment)

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md`
3. `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md`
4. `docs/sprints/STAGE_1_SERVICE_RECORD_POSTGRES_FOUNDATION_SPRINT/03_FINAL_REPORT.md`
5. `docs/sprints/REALISTIC_ADD_CAR_SIMULATION_POSTGRES_DUAL_WRITE_VALIDATION_SPRINT/03_FINAL_REPORT.md`
6. `docs/sprints/REALISTIC_NA_CHINESE_ADD_CAR_20_CASE_SPRINT/03_FINAL_REPORT.md`

## Scope

**In scope:** Rule-path simulation, small `triage.py` / `markers.json` / missing-doc extraction tweaks, disposable Postgres validation, battery script, honest gap notes.

**Out of scope:** Full Stage 2, carrier APIs, CRM expansion, read-path cutover from JSON, large schema changes, frontend redesign.

## Target outcome

- Fewer **unclear** / wrong **`missing_document`** routes on Priority 1–3 Add-Car families.
- **Postgres** row counts and spot-checks show useful `issue_category`, `quote_readiness`, `missing_fields_summary`.
- **Stage-1** handoff and **Stage-2-prep** signals improve where slots are thin but intent is clear.
