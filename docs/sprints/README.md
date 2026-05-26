# Sprint docs — historical reference only

**Do not treat files in this directory as current runtime truth.**

Sprint documents capture discovery, execution notes, and acceptance criteria from focused work sessions. Product shape, deployment posture, and env requirements evolve; many sprint files were accurate **at write time** but are now superseded.

## Classification

| Class | Read this |
|-------|-----------|
| **Runtime truth** | [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) |
| **Active reduction** | [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../SIMPLIFICATION_MASTER_PLAN.md), [`docs/SIMPLIFICATION_EXECUTION_PLAN.md`](../SIMPLIFICATION_EXECUTION_PLAN.md) |
| **Historical** | [`docs/sprints/archive/`](./archive/README.md) |
| **Speculative** | Archived `FUTURE_SAAS_*`, `LONG_HORIZON_SAAS_*`, `TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT` — investor/historical only |
| **Deprecated** | Old deploy reports — do not copy env tuples |

## How to use sprint docs

- **OK:** Understand why a decision was made, find grep targets, audit history
- **Not OK:** Copy env tuples, assume wiring state, skip `validate_pilot_deploy_env.py`

When implementing changes, update `docs/CURRENT_PRODUCT_SHAPE.md` and runbooks — not a new sprint doc unless explicitly requested.

## Archive (`docs/sprints/archive/`)

**Batch 2 (2026-05-26):** ~90 root sprint docs + 16 historical directories → [`archive/`](./archive/README.md).

**P0 batch 2 (2026-05-26):** Turn-1 / focus-mode / stress-test packages + `workbench_handoff_readiness/` → archive. **Not deleted.**

**P1 batch 3 (2026-05-26):** ~41 `ADD_CAR_*` / `add_car_*` sprint dirs → `archive/add_car_sprints/`; stale deploy reports; convergence docs → `docs/archive/convergence_reports/`. **Not deleted.**

## Active at repo root (recent / convergence)

- [`COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md`](./COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md)
- [`PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md`](./PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md)
- [`SAFE_REDUCTION_BASELINE_CHECKPOINT.md`](./SAFE_REDUCTION_BASELINE_CHECKPOINT.md)
- [`PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md`](./PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md)
- [`STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md`](./STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md)
- [`FOUNDER_TRIAL_CHECKLIST.md`](./FOUNDER_TRIAL_CHECKLIST.md)

Continue batch-archiving stale sprints per [`docs/SIMPLIFICATION_EXECUTION_PLAN.md`](../SIMPLIFICATION_EXECUTION_PLAN.md).
