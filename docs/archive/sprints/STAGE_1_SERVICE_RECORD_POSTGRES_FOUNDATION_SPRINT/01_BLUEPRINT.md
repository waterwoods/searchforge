# STAGE 1 SERVICE RECORD POSTGRES FOUNDATION SPRINT — Blueprint

## Sprint goal

Establish the **minimum real Postgres foundation** for Stage 1 Unified Intake service records: canonical DDL, env wiring, and **opt-in** dual-write from the existing JSON case store—without replacing pilot persistence or building CRM scope.

## Why now

- `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md` names Postgres as the primary Stage 1 direction and recommends schema-first, then dual-write, then gradual read cutover.
- `docs/PROJECT_TRUTH_SWITCH.md` still described JSON-only truth; the product needs an explicit, low-risk path to a relational backbone before multi-instance or formal ops requirements harden.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — product boundaries, state-driven intake, not CRM.
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical paths and persistence truth (updated when this sprint lands).
3. `docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md` — objects, hybrid JSONB strategy, gentle migration.

## Scope

- DDL for core Stage 1 tables aligned with the blueprint.
- Python settings + repository + dual-write hooks after successful JSON writes.
- Apply script and sprint documentation (`01`–`03`).

## Non-scope

- Full CRM schema, customers as first-class multi-record CRM, auth, billing, multi-tenant platform.
- Removing JSON persistence or changing read paths.
- Session store in Postgres, attachment blobs in Postgres, vector/graph stores.

## Target outcome

A **concrete** Postgres schema and an **off-by-default** dual-write path so the next sprint can extend schema, wire more events, or begin read experiments without a big-bang migration.
