# REALISTIC NA-CHINESE ADD-CAR 20-CASE + POSTGRES + STAGE-2 READINESS — Blueprint

## Sprint goal

Prove, with realistic North-American-Chinese Add-Car phrasing (single- and multi-turn), that Stage-1 intake produces **operationally useful structured service records**, **optional Postgres dual-write rows** that cohere with JSON, and signals that are **honest about quote-prep / Stage-2 readiness**—without broadening into CRM, full workflow engines, or carrier pricing.

## Why now

Master outline and `PROJECT_TRUTH_SWITCH` already state: Add-Car is the wedge, JSON is authoritative until read cutover, Postgres is the Stage-1 record direction. The open question is **real language under pressure**: extraction quality, persistence coherence, and whether `still_needed` / `quote_ready` / broker next steps support both office handoff and future quote-prep automation.

## Read-first docs (mandatory alignment)

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md`
3. `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md`
4. `docs/sprints/STAGE_1_SERVICE_RECORD_POSTGRES_FOUNDATION_SPRINT/03_FINAL_REPORT.md`
5. `docs/sprints/REALISTIC_ADD_CAR_SIMULATION_POSTGRES_DUAL_WRITE_VALIDATION_SPRINT/03_FINAL_REPORT.md`
6. Recent Add-Car realism audits (e.g. `ADD_CAR_REALISTIC_NA_CHINESE_SIMULATION_AUDIT_SPRINT`) as context only

## Scope

- 10–20 realistic NA-Chinese / mixed Add-Car cases (rule path, `LLM_GENERATION_ENABLED=0`)
- Structured field / quote-readiness / handoff signal review
- Postgres dual-write when a real DB + env are available
- Small, justified routing fix for a known weak pattern (“还缺什么” on Add-Car continuation)
- Re-run guardrail + spot-check Postgres counts

## Non-scope

- Full CRM, full Stage-2 implementation, carrier APIs, large UI redesign, schema expansion beyond what already exists

## Target outcome

- Documented case battery + validation criteria (`02_…`)
- Executed simulation + honest Postgres note (`03_…`)
- Clear founder answers: Stage-1 strength, Stage-2 gaps, DB dual-write certainty, next sprint recommendation
