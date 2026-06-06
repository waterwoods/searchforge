# Recommended document index — Unified Intake

**Purpose:** Reduce doc sprawl without deleting anything. Use this as the **navigation layer**.  
**Policy:** No files deleted here — only **grouping** and **archive candidates**.

---

## READ_FIRST (onboarding ≤ 1 hour)

| Document | Notes |
|----------|--------|
| `docs/SYSTEM_ONE_PAGE_MAP.md` | ~3 minutes; diagram + facts. |
| `docs/archive/platform/UNIFIED_INTAKE_MASTER_BLUEPRINT.md` | Full module table + invariants (**archived** — cross-check `CURRENT_PRODUCT_SHAPE.md`). |
| `docs/PRODUCT_TRUTH_DOCUMENT.md` | Product principles, field strategy, broker completion. |
| `docs/PG_TRUTH_PIPELINE_CONTRACT.md` | API ↔ PG vehicle identity contract. |
| `docs/AMBIGUITY_CLARIFY_CONTRACT.md` | Clarify vs guess for multi-vehicle. |

---

## MODULE_CONTRACTS (behavioral truth)

| Document | Notes |
|----------|--------|
| `docs/PILOT_CONTRACT_ADD_CAR_V1.md` | Pilot scope for add-car. |
| `docs/VEHICLE_ENTITY_MEMORY_MVP.md` | Entity store MVP (replaces missing `PG_MULTIVEHICLE_ENTITY_PLAN.md` reference). |
| `docs/CASE_CONTRACT_V1.md` | Case shape expectations. |
| `docs/ENTITY_TRIAGE_INTEGRATION_PLAN.md` | Entity + triage integration notes. |
| `configs/common/add_car_field_strategy.json` | Executable field strategy (paired with `field_strategy.py`). |

---

## RUNBOOKS

| Document | Notes |
|----------|--------|
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Deploy steps. |
| `docs/runbooks/RELEASE_CHECKLIST.md` | Release gates. |
| `docs/runbooks/UNIFIED_INTAKE_DB_OBSERVABILITY_SIGNALS.md` | DB/obs signals. |
| `docs/runbooks/KNOWN_DEPLOYMENT_GOTCHAS.md` | Ops pitfalls. |
| `docs/CLOUD_RUN_DEPLOYMENT.md` | Cloud Run specifics. |

---

## REPORTS (time-bounded sprints / evaluations)

| Path pattern | Notes |
|--------------|--------|
| `results/*REPORT*.md` | Lock-in, takeover, evaluation — **check date**; may describe target state ahead of branch tip. |
| `results/SIMPLIFICATION_AND_PLUGIN_AUDIT.md` | Plug-in audit (aligns with `docs/archive/platform/PLUGIN_ARCHITECTURE_MAP.md`). |
| `docs/sprints/**/03_FINAL_REPORT.md` | Historical sprint outputs. |

---

## ARCHIVE_CANDIDATES (do not delete; move or label when ready)

**Criterion:** Superseded by master blueprint + contracts, or **time-slice** reports that contradict current code without a banner.

| Candidate | Reason |
|-----------|--------|
| `results/RESOLVER_PATHS.md` | Describes `USE_RESOLVER_ONLY`-era dual paths; takeover report says flag removed — keep for history, not for “how it works today” without cross-check. |
| `results/FINAL_LOCKIN_REPORT.md` | Valuable metrics; **REMOVE_LATER** items may be stale vs branch — cite alongside `DEPRECATED_PATHS.md`. |
| `results/FINAL_SYSTEM_REPORT.md` | May assert resolver wiring that **branch tip** does not show — archive mentally as “sprint snapshot.” |
| Older `docs/sprints/**/01_BLUEPRINT.md` files | Useful archaeology; not READ_FIRST. |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | **Potential overlap** with archived master blueprint — prefer `CURRENT_PRODUCT_SHAPE.md` for runtime truth. |

**Missing doc placeholder:** `docs/PG_MULTIVEHICLE_ENTITY_PLAN.md` — referenced in sprint audit but **not in repo**; use `VEHICLE_ENTITY_MEMORY_MVP.md` instead.

---

## New in this audit sprint

- `docs/archive/platform/UNIFIED_INTAKE_MASTER_BLUEPRINT.md` (archived P6)
- `docs/DEPRECATED_PATHS.md`
- `docs/archive/platform/PLUGIN_ARCHITECTURE_MAP.md` (archived P6)
- `docs/SYSTEM_ONE_PAGE_MAP.md`
- `docs/DOC_INDEX_RECOMMENDED.md` (this file)
- `results/MASTER_BLUEPRINT_AUDIT_REPORT.md`
- `docs/archive/sprint_reports/` — 71 historical sprint reports (archived P6)
