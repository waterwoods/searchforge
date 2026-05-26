# Sprint archive — historical reference only

Files here were moved from `docs/sprints/` during reduction batches. They remain in git history and are **not deleted**.

**Do not treat archived content as current runtime truth.**

## Classification

| Class | Where to read | Use archived sprints for |
|-------|----------------|---------------------------|
| **Runtime truth** | [`docs/CURRENT_PRODUCT_SHAPE.md`](../../CURRENT_PRODUCT_SHAPE.md) | Never — copy env or wiring from here |
| **Active reduction** | [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../../SIMPLIFICATION_MASTER_PLAN.md), [`docs/SIMPLIFICATION_EXECUTION_PLAN.md`](../../SIMPLIFICATION_EXECUTION_PLAN.md) | Context on what to delete/hide next |
| **Historical** | This directory | Why a decision was made, grep targets, audits |
| **Speculative** | `FUTURE_SAAS_*`, `HUNDRED_OFFICES_*`, multi-tenant narratives | Inspiration only — not build lists |
| **Deprecated** | Superseded deploy reports, old backbone specs | Do not implement |

## Read instead (current truth)

| Doc | Purpose |
|-----|---------|
| [`docs/CURRENT_PRODUCT_SHAPE.md`](../../CURRENT_PRODUCT_SHAPE.md) | Product + deploy + paid-pilot requirements |
| [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../../SIMPLIFICATION_MASTER_PLAN.md) | Reduction roadmap |
| [`docs/SIMPLIFICATION_EXECUTION_PLAN.md`](../../SIMPLIFICATION_EXECUTION_PLAN.md) | Batch execution status |
| [`docs/sprints/README.md`](../README.md) | How to use sprint docs |

## Why archived

- Completed deploy / redeploy execution reports
- Platform-future narratives (multi-tenant, hundred-offices, future SaaS OS)
- Turn-1 / focus-mode / stress-test sprint packages superseded by code + CURRENT_PRODUCT_SHAPE
- Workbench handoff readiness specs merged into product shape
- **P1 batch 3:** Add-Car sprint packages (`add_car_sprints/`) — product behavior lives in code + `STANDARD_SCENARIO_PACKAGE.md`; scenario JSON kept for regression scripts
- **P1 batch 3:** Stale deploy/redeploy reports (`stale_deploy_reports/`)
- **P1 batch 3:** Convergence/deploy audit reports → `docs/archive/convergence_reports/`
- **P1 batch 3:** `MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md` — superseded by `SIMPLIFICATION_*` docs

## Active at `docs/sprints/` (not archived)

- [`COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md`](../COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md) — convergence authority
- [`PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md`](../PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md)
- [`SAFE_REDUCTION_BASELINE_CHECKPOINT.md`](../SAFE_REDUCTION_BASELINE_CHECKPOINT.md)
- [`PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md`](../PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md)
- [`STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md`](../STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md)
- [`FOUNDER_TRIAL_CHECKLIST.md`](../FOUNDER_TRIAL_CHECKLIST.md)

## Subdirectories

| Path | Contents |
|------|----------|
| `add_car_sprints/` | Historical Add-Car sprint dirs; scenario JSON used by `scripts/run_add_car_*.py` |
| `stale_deploy_reports/` | One-off redeploy / UX bugfix reports |

## Batch log

| Batch | Date | Approx. moved |
|-------|------|----------------|
| safe-batch-loops | 2026-05-26 | ~90 root `.md` + 16 dirs |
| p0-hardening-loops | 2026-05-26 | 26 root `.md` + `workbench_handoff_readiness/` |
| p1-simplification-loops | 2026-05-26 | ~41 Add-Car dirs + 6 root convergence reports + MINIMAL_PAID sprint |
