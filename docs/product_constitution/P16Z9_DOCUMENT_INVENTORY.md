# P16-Z9 Phase 1 — Document Inventory

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Constraint:** Documentation only — no production code changes.  
**Core question:** If a new engineer joined tomorrow, what is the minimum required reading?

---

## Classification legend

| Class | Meaning | Action for readers |
|-------|---------|-------------------|
| **SSOT** | Permanent truth — update when reality changes | Read first; cite in PRs |
| **Reference** | Deep dive, sprint artifact, or runbook — authoritative for its topic | Read when working that topic |
| **Historical** | Point-in-time discovery; superseded by later sprint | Read for context only |
| **Obsolete** | Wrong, duplicated, or blocked (P17, platform fantasy) | Do not implement from |

---

## Minimum reading set (new engineer — ≤12 docs)

| Order | Document | Class | Why required |
|-------|----------|-------|--------------|
| 1 | `AGENTS.md` | SSOT | Entry point, scripts, scope |
| 2 | `docs/CURRENT_PRODUCT_SHAPE.md` | SSOT | Runtime/deploy truth beats all blueprints |
| 3 | `docs/goals/insurance_paid_pilot_goal.md` | SSOT | In/out of scope |
| 4 | `docs/product_constitution/CASE_INTELLIGENCE_MASTER_OUTLINE.md` | SSOT | Product architecture layers |
| 5 | `docs/product_constitution/CASE_INTELLIGENCE_MATURITY_MODEL.md` | SSOT | L1–L7 commercial ladder |
| 6 | `docs/product_constitution/P16Z9_SSOT_PROPOSAL.md` | SSOT | Which doc wins conflicts |
| 7 | `docs/product_constitution/P16Z9_FOUNDER_SUMMARY.md` | SSOT | Consolidated discoveries + 90-day OS |
| 8 | `docs/FOUNDER_ONE_PATH.md` | SSOT | Founder execution path |
| 9 | `docs/runbooks/OPERATOR_SURFACE.md` | SSOT | 10 scripts, 5 endpoints |
| 10 | `docs/runbooks/OPERATOR_IGNORE_LIST.md` | Reference | Cognitive load filter |
| 11 | `docs/PROJECT_DOC_SYSTEM_MAP.md` | Reference | Full doc hierarchy |
| 12 | `docs/BROKER_ONE_PAGER.md` | Reference | Customer-facing language |

**Optional day-2:** `docs/ANDY_QUICK_START.md`, `docs/trial/INDEX.md`, `P16Z9_VALIDATION_OS.md`

---

## Tier A — Runtime & operator (SSOT)

| Document | Class | Notes |
|----------|-------|-------|
| `AGENTS.md` | SSOT | Agent entry |
| `docs/CURRENT_PRODUCT_SHAPE.md` | SSOT | Wins over sprint docs |
| `docs/goals/insurance_paid_pilot_goal.md` | SSOT | Pilot boundary |
| `docs/FOUNDER_ONE_PATH.md` | SSOT | Single founder path |
| `docs/runbooks/OPERATOR_SURFACE.md` | SSOT | Target operator surface |
| `docs/runbooks/RUNTIME_PATH_STANDARD.md` | SSOT | Ports 8001/8000 |
| `docs/runbooks/OPERATOR_IGNORE_LIST.md` | Reference | Safe to ignore |
| `docs/runbooks/DEPLOY_TRUTH_MAP.md` | Reference | Which deploy script |
| `docs/trial/INDEX.md` | Reference | Real broker trial pack |

---

## Tier B — Product constitution (SSOT + reference)

| Document | Class | Notes |
|----------|-------|-------|
| `CASE_INTELLIGENCE_MASTER_OUTLINE.md` | **SSOT** | Strategic product layers |
| `CASE_INTELLIGENCE_MATURITY_MODEL.md` | **SSOT** | Maturity L1–L7 |
| `P16Z9_SSOT_PROPOSAL.md` | **SSOT** | Doc hierarchy after Z9 |
| `P16Z9_DEVELOPMENT_OS.md` | **SSOT** | Sprint loop |
| `P16Z9_VALIDATION_OS.md` | **SSOT** | Batteries + observation log |
| `P16Z9_FOUNDER_SUMMARY.md` | **SSOT** | Consolidated verdict |
| `P16Z25_NORTH_STAR.md` | SSOT | One-sentence north star (canonical) |
| `P16Z25_PRODUCT_SOUL.md` | SSOT | Product soul sentence |
| `P16Z25_CAPACITY_RANKING.md` | Reference | Seven capacities — superseded ranking in `P16Z9_CAPACITY_REVIEW.md` |

---

## Tier C — P16 sprint chain (reference / historical)

### P16-Y — Case Intelligence Hardening

| Document | Class |
|----------|-------|
| `P16Y_FINAL_VERDICT.md` | Reference — battery baseline 88.6 |
| `P16Y_RUBRIC.md`, `P16Y_SCORECARD.md` | Reference |
| `P16Y_50_CASES.md`, `P16Y_FAILURE_ANALYSIS.md` | Historical |
| `configs/p16y_50_cases.json` | Reference (battery input) |

### P16-Z0 — Capability Archaeology

| Document | Class |
|----------|-------|
| `P16Z0_FINAL_VERDICT.md` | Reference — "revive not rebuild" |
| `P16Z0_CAPABILITY_INVENTORY.md`, `P16Z0_CAPABILITY_MAP_V2.md` | Reference |
| `P16Z0_DUPLICATION_AUDIT.md` | Reference — merged into `P16Z9_DUPLICATE_AUDIT.md` |
| `P16Z0_*_ARCHAEOLOGY.md` (6 files) | Historical |

### P16-Z2 / Z2.5 — Strategic reverse engineering & soul

| Document | Class |
|----------|-------|
| `P16Z2_FINAL_VERDICT.md` | Reference |
| `P16Z2_TOP100_IDEAS.md`, `P16Z2_TOP50_DO_NOT_COPY.md` | Reference |
| `P16Z2_COMPANY_TEARDOWN.md`, `P16Z2_*_RESEARCH.md` | Historical |
| `P16Z25_FINAL_VERDICT.md`, `P16Z25_TOP20_*.md` | Reference — soul synthesis |

### P16-Z3 — Maturity model sprint

| Document | Class |
|----------|-------|
| `P16Z3_FINAL_VERDICT.md` | Reference — L4.5 engine / L3.5 deployed |
| `P16Z3_30_DAY_PLAN.md`, `P16Z3_90_DAY_PLAN.md` | Historical — use `P16Z9_90_DAY_FILTER.md` |
| `P16Z3_*` (10 phase docs) | Historical |

### P16-Z4 — Case continuity

| Document | Class |
|----------|-------|
| `P16Z4_EXECUTION_PLAN.md` | Reference — 7-day continuity ship list |
| `P16Z4_*` (8 files) | Historical |

### P16-Z5 — Case memory

| Document | Class |
|----------|-------|
| `P16Z5_FINAL_VERDICT.md` | Reference — memory UX vs backend |
| (single mega verdict) | Historical detail embedded in Z5 |

### P16-Z6 — Memory activation (ship sprint)

| Document | Class |
|----------|-------|
| `P16Z6_*` (8 files) | Reference — what shipped / thread UI |
| `P16Z6_CLAIMS_VALIDATION.md` | Reference |

### P16-Z7 — Reality memory validation (Role D)

| Document | Class |
|----------|-------|
| `ROLE_D_*.md` (10 files) | Reference — multi-day battery |
| `ROLE_D_FOUNDER_SUMMARY.md` | Reference — Z7 verdict |
| `configs/role_d_*.json` | Reference |
| `scripts/run_role_d_memory_battery.py` | SSOT (executable) |

### P16-Z8 — Memory hardening archaeology

| Document | Class |
|----------|-------|
| `P16Z8_EXECUTION_PLAN.md` | Reference — 3-day engine slice |
| `P16Z8_*` (9 files) | Reference — payment/remove/merge/waiting |

### P16-Z9 — This sprint

| Document | Class |
|----------|-------|
| `P16Z9_*.md` (10 files) | **SSOT** — operating system |

---

## Tier D — Pre-Z archaeology (historical)

| Document | Class | Notes |
|----------|-------|-------|
| `P16X_*`, `P16M_*`, `P16N_*`, `P16K_*`, `P16L_*`, `P16O_*`, `P16Q_*`, `P16T_*`, `P16W_*` | Historical | Friction lists; themes merged in Z0–Z9 |
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Reference | Macro blueprint — not daily ops |
| `docs/archive/platform/*` | Obsolete | Platform fantasy |
| `docs/sprints/archive/*` | Obsolete | Future SaaS OS speculation |

---

## Tier E — Executable validation (SSOT for ops)

| Asset | Class |
|-------|-------|
| `scripts/operator/guardrail_inbox_triage.sh` | SSOT |
| `scripts/trial_launch_check.sh` | SSOT |
| `scripts/run_p16y_case_battery.py` | SSOT |
| `scripts/run_role_d_memory_battery.py` | SSOT |
| `scripts/demo_pre_checklist.sh` | Reference |
| `scripts/run_demo_local.sh` | SSOT |

---

## Tier F — Lab / auto-evolution (obsolete for pilot)

| Pattern | Class |
|---------|-------|
| `scripts/run_add_car_*_battery.py` (10+) | Obsolete for operator path |
| `scripts/lab/*` | Obsolete unless `RUN_DEMO_LAB=1` |
| `auto-evolution/*` branches | Historical branches |

---

## Conflict resolution rule

When two documents disagree:

1. `docs/CURRENT_PRODUCT_SHAPE.md` (runtime)
2. `CASE_INTELLIGENCE_MASTER_OUTLINE.md` (product)
3. `P16Z9_SSOT_PROPOSAL.md` (doc hierarchy)
4. Latest P16-Z* **verdict** for discovery claims
5. Sprint phase docs (lowest)

---

## Inventory statistics

| Class | Approx. count (`docs/product_constitution/`) |
|-------|-----------------------------------------------|
| SSOT (post-Z9) | ~15 |
| Reference | ~120 |
| Historical | ~170 |
| Obsolete (for pilot) | ~30+ lab scripts, platform archives |

**Recommendation:** Archive P16-M/N/X friction megadocs to `docs/archive/product_constitution/` after Z9 — keep verdicts only.

---

*End of P16-Z9 Phase 1 — Document Inventory*
