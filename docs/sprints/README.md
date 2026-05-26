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

## Archive candidates (historical — do not delete blindly)

Move to `docs/sprints/archive/` when convenient (see `COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md` § Phase 2D):

- `KILL_LEGACY_DEFAULT_PATHS_SPRINT.md`
- `PILOT_TO_REAL_SAAS_TRANSITION_SPRINT.md`
- `LONG_HORIZON_SAAS_OPERATING_SYSTEM_SPRINT.md`
- `backend_redeploy_*` execution report directories
- `ROLE_C_BACKEND_DEPLOY_SMOKE_CHECK_SPRINT/`
- `REMOTE_DEMO_ENV_REBASELINE_PRECHECK_SPRINT/`

Active convergence sprint: [`COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md`](./COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md).
