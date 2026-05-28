# REALISTIC ADD-CAR SIMULATION + POSTGRES DUAL-WRITE VALIDATION — Blueprint

## Sprint goal

Prove, with realistic North-American-Chinese Add-Car language (including mixed Chinese/English and multi-turn patterns), that the current stack can: classify and structure intake, persist a coherent JSON case, and—when enabled—dual-write the same intent into Postgres (`service_records`, `record_messages`, `structured_record_data`, `state_history`) without claiming CRM or full workflow scope.

## Why now

The Postgres foundation and opt-in dual-write path exist, but value is only real when **messy customer text** produces **useful structured payloads** and **queryable rows**. This sprint grounds the DB direction in broker-realistic phrasing and closes the loop: simulation → structured fields → row inspection.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Stage 1 = intake + structuring + handoff; Add-Car wedge; state-driven flow; no full CRM.
2. `docs/PROJECT_TRUTH_SWITCH.md` — Canonical path; JSON authority; dual-write env contract.
3. `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md` — Record-first, state-first, structured data as asset.
4. `docs/sprints/STAGE_1_SERVICE_RECORD_POSTGRES_FOUNDATION_SPRINT/03_FINAL_REPORT.md` — What was built, what was explicitly not built (no read path from Postgres yet).

## Scope

- Realistic Add-Car simulation battery (rule-based, `LLM_GENERATION_ENABLED=0` for reproducibility).
- Structured field and quote-readiness review.
- Postgres dual-write validation when a real DB is available (disposable local Postgres acceptable).
- Small persistence or state-adjacent fixes only when clearly justified.

## Non-scope

- Full CRM, carrier APIs, Stage 2 automation product, broad UI redesign, Alembic chains, read-path cutover from Postgres.

## Target outcome

- Documented battery and acceptance criteria.
- Honest report: what persisted well, what failed, one small improvement if warranted.
- Clear answer whether the line **realistic text → structured record → Postgres** is proven for the pilot path when env flags are set.
