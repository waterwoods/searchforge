# Sprint docs — historical reference only

**Do not treat files in this directory as current runtime truth.**

Sprint documents capture discovery, execution notes, and acceptance criteria from focused work sessions. Product shape, deployment posture, and env requirements evolve; many sprint files were accurate **at write time** but are now superseded.

## Current truth (read these instead)

| Doc | Purpose |
|-----|---------|
| [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) | **Current** product, deployment, paid-pilot requirements |
| [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../SIMPLIFICATION_MASTER_PLAN.md) | **Reduction roadmap** — hide/archive/delete priorities |
| [`docs/PROJECT_DOC_SYSTEM_MAP.md`](../PROJECT_DOC_SYSTEM_MAP.md) | Full doc index |
| [`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`](../UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md) | Macro north star |

## How to use sprint docs

- **OK:** Understand why a decision was made, find grep targets, audit history
- **Not OK:** Copy env tuples, assume wiring state, skip `validate_pilot_deploy_env.py`

When implementing changes, update `docs/CURRENT_PRODUCT_SHAPE.md` and runbooks — not a new sprint doc unless explicitly requested.

## Archive (`docs/sprints/archive/`)

**Batch 2 (2026-05-26):** ~90 root sprint docs + 16 historical directories moved to [`archive/`](./archive/README.md) — platform-future narratives, completed redeploy reports, superseded backbone specs. **Not deleted**; see [`archive/README.md`](./archive/README.md).

Still at repo root (active / recent):

- [`COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md`](./COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md) — convergence authority
- [`PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md`](./PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md)
- [`SAFE_REDUCTION_BASELINE_CHECKPOINT.md`](./SAFE_REDUCTION_BASELINE_CHECKPOINT.md)
- [`MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md`](./MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md)
- [`PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md`](./PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md)

Continue batch-archiving stale sprints per [`docs/SIMPLIFICATION_EXECUTION_PLAN.md`](../SIMPLIFICATION_EXECUTION_PLAN.md).
