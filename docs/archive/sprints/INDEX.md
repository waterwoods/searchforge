# Archived Sprint Directories — Historical Reference Only

> **HISTORICAL / ARCHIVE** — Not current runtime truth.  
> **Authority:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../../CURRENT_PRODUCT_SHAPE.md) always wins.

**P8 batch (2026-05-28):** 38 sprint subdirectories moved from `docs/sprints/` → `docs/archive/sprints/` to reduce visible sprint archaeology.

---

## What remains visible at `docs/sprints/`

Live convergence and reduction plans only:

| File | Purpose |
|------|---------|
| [`README.md`](../../sprints/README.md) | Sprint doc classification |
| `COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md` | Runtime path reduction |
| `PRODUCT_SIMPLIFICATION_SAAS_REDUCTION_SPRINT.md` | SaaS reduction |
| `SAFE_REDUCTION_BASELINE_CHECKPOINT.md` | Reduction baseline |
| `PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md` | Pilot hardening |
| `STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md` | Product-only wiring |
| `FOUNDER_TRIAL_CHECKLIST.md` | Founder trial checklist |

---

## Archived here (P8)

| Directory | Note |
|-----------|------|
| `BROKER_TRIAL_HANDOFF_TIMING_AUDIT/` | Execution record |
| `CASE_*`, `CLIENT_*`, `CONFIGURATION_*` | Client/case wiring sprints |
| `CROSS_CLIENT_*`, `FLOW_*`, `MATURE_*` | Product hardening archaeology |
| `NARROW_POSITIONING_*`, `PRODUCT_*`, `SALES_*` | Readiness/value sprints |
| `SECOND_BROKER_*`, `SELLABLE_*`, `STANDARD_*` | Scenario package sprints |
| `SIMULATION_*`, `SMALL_BATCH_*`, `STAGE_1_*` | Feature execution notes |
| `TOP_*`, `TRUTH_*`, `UNIFIED_INTAKE_UI_*` | Hardening/polish sprints |
| `WEB_INFORMED_*`, `WORKBENCH_*` | Workbench sprints |
| `customer_entry_*`, `human_*`, `hybrid_*`, `in_progress_*` | Entry-flow discovery |
| `prior_sprints_archive/` | Earlier P0–P2 batch archive (from `docs/sprints/archive/`) |

**Total archived sprint dirs (P8):** 38 top-level + `prior_sprints_archive/` subtree.

---

## How to use

- **OK:** Understand why a decision was made, grep for historical context
- **Not OK:** Copy env tuples, assume current wiring, skip `validate_pilot_deploy_env.py`

When implementing changes, update `CURRENT_PRODUCT_SHAPE.md` and runbooks — not archived sprint docs.

---

## Rollback

```bash
# Restore one sprint dir to visible surface
git mv docs/archive/sprints/BROKER_TRIAL_HANDOFF_TIMING_AUDIT docs/sprints/

# Full P8 sprint archive rollback (if single commit)
git checkout HEAD~1 -- docs/sprints/ docs/archive/sprints/
```
