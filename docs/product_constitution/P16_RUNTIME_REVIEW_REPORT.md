# P16 Runtime Review Report

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 1  
**Branch HEAD:** `4d5bf46` (`sprint-a/broker-front-door`)  
**Frozen demo SHA:** `517f728` (`release/p16-demo-ready-v1` / `p16-demo-ready-v1`)  
**Scope:** Classify 93 `REVIEW_REQUIRED` paths — **no modifications in this phase**

---

## Summary

| Classification | Count |
|----------------|------:|
| KEEP_AND_COMMIT | 40 |
| REVERT | 0 |
| NEEDS_FOUNDER_REVIEW | 53 |
| **Total** | **93** |

**Additional dirty paths outside the 93-path list:**

| Category | Count | Notes |
|----------|------:|-------|
| DO_NOT_COMMIT | 2 | `configs/demo.env.example`, `demo_brain_report.html` |
| AGENTS.md (committed in hygiene D) | 1 | Doc-only; was dirty alongside the 93 |

---

## Classification Rationale

| Bucket | Rule applied |
|--------|----------------|
| **KEEP_AND_COMMIT** | Documentation, script tier wrappers, simulation fixtures, lab README stubs, comment-only infra — zero product/API/UI behavior change |
| **REVERT** | Accidental or contradictory edits — **none found**; all remaining runtime diffs appear intentional P16 product-only surface work |
| **NEEDS_FOUNDER_REVIEW** | Touches demo launcher, operator scripts, API deployment profile, case persistence fields, UI routing/copy, triage markers, or deletions of runtime modules |

**Explicit exclusions honored:** `triage.py`, AC03/AC05/AC07, append bug, UI polish sprints, Cloud Run, Vercel — not in scope for auto-commit.

---

## KEEP_AND_COMMIT — 40 paths

| Path | Status at review | Reason |
|------|------------------|--------|
| `agents/README.md` | `??` | Legacy dir README stub |
| `configs/p16y_50_cases.json` | `??` | Simulation battery fixture |
| `configs/p16z20_add_car_customers.json` | `??` | Simulation battery fixture |
| `configs/p16z235_add_car_customers.json` | `??` | Simulation battery fixture |
| `configs/p16z24_add_car_customers.json` | `??` | Simulation battery fixture |
| `configs/role_d_claims_battery.json` | `??` | Simulation battery fixture |
| `configs/role_d_journeys.json` | `??` | Simulation battery fixture |
| `docker-compose.product.yml` | `??` | Product-only compose split (documentation) |
| `Dockerfile.ecommerce` | `M` | Lab-only banner comment |
| `Dockerfile.jobhunter` | `M` | Lab-only banner comment |
| `docker-compose.yml` | `M` | Comment-only header (points to product compose) |
| `engines/README.md` | `??` | Legacy dir README stub |
| `experiments/README.md` | `??` | Legacy dir README stub |
| `jobhunter-clipper/README.md` | `M` | Lab deprecation notice |
| `k8s/README.md` | `M` | Lab deprecation notice |
| `Makefile` | `M` | Help banner — lab vs product pointer |
| `mcp/README.md` | `??` | Legacy dir README stub |
| `ml_models/README.md` | `??` | Legacy dir README stub |
| `modules/autotuner/README.md` | `??` | Legacy dir README stub |
| `orchestrators/README.md` | `??` | Legacy dir README stub |
| `pipelines/` | `??` | Legacy pipeline README stub |
| `README.md` | `M` | Root product positioning (doc) |
| `scripts/archive/` | `??` | Script tier wrappers — historical stubs |
| `scripts/DEEP_SCRIPT_TIER_MAP.md` | `??` | Script inventory documentation |
| `scripts/deploy/` | `??` | Deploy wrapper shims → `deploy_paid_pilot.sh` |
| `scripts/founder/` | `??` | Founder rehearsal wrappers |
| `scripts/LAB_SCRIPT_INDEX.md` | `??` | Lab script index |
| `scripts/lab/` | `??` | Lab wrappers with LAB ONLY banner |
| `scripts/operator/` | `??` | Operator surface wrappers (10 scripts) |
| `scripts/p16z11_founder_output.sh` | `??` | Founder simulation tooling |
| `scripts/post_sprint_check.sh` | `??` | Post-sprint hygiene check |
| `scripts/README.md` | `M` | Script tier discoverability docs |
| `scripts/README_OPERATOR.md` | `M` | Operator doc path update |
| `scripts/run_p16y_case_battery.py` | `??` | Simulation battery runner |
| `scripts/run_p16z20_add_car_simulation.py` | `??` | Simulation runner |
| `scripts/run_p16z21_tournament_simulation.py` | `??` | Simulation runner |
| `scripts/run_p16z235_founder_reality_sprint.py` | `??` | Simulation runner |
| `scripts/run_p16z24_add_car_sprint.py` | `??` | Simulation runner |
| `scripts/run_role_d_memory_battery.py` | `??` | Simulation runner |
| `scripts/summarize_support_posture.sh` | `??` | Support posture summary (non-demo) |

**Disposition:** All 40 committed in `4d5bf46` (Phase 2 hygiene commit D).

---

## REVERT — 0 paths

No path classified as accidental. Deletions (`triage.sh`, `active_vehicle_resolver.py`) and marker expansions appear intentional but require founder confirmation before commit — classified under NEEDS_FOUNDER_REVIEW, not REVERT.

---

## NEEDS_FOUNDER_REVIEW — 53 paths

### Scripts — 22 paths

| Path | Status | Concern |
|------|--------|---------|
| `scripts/check_unified_intake_prod_posture.sh` | `M` | Prod posture validation logic |
| `scripts/demo_pre_checklist.sh` | `M` | Pre-demo operator path |
| `scripts/demo_quick_validate.sh` | `M` | Live validation |
| `scripts/deploy_paid_pilot.sh` | `M` | Deploy entry (parent; wrapper committed) |
| `scripts/dev_local.sh` | `M` | Local dev launcher |
| `scripts/founder_pre_trial_checklist.sh` | `M` | Trial checklist |
| `scripts/health_check.sh` | `M` | Health probe |
| `scripts/import_smoke_check.py` | `M` | Import smoke |
| `scripts/restore_8001_readiness.sh` | `M` | Recovery script |
| `scripts/run_append_boundary_ab_scenarios.py` | `M` | AB scenario runner |
| `scripts/run_cross_client_ab_scenarios.py` | `M` | AB scenario runner |
| `scripts/run_demo_local.sh` | `M` | **Primary demo launcher** — product-only default |
| `scripts/run_residual_copy_ab_scenarios.py` | `M` | AB scenario runner |
| `scripts/run_small_batch_phrase_map_ab_scenarios.py` | `M` | AB scenario runner |
| `scripts/start_all.sh` | `M` | Lab stack starter |
| `scripts/start_demo_app.sh` | `M` | Demo app starter |
| `scripts/stop_all.sh` | `M` | Lab stack stopper |
| `scripts/summarize_readiness_posture.sh` | `M` | Readiness summary |
| `scripts/trial_launch_check.sh` | `M` | Trial launch gate |
| `scripts/trial_readiness_check.sh` | `M` | Trial readiness gate |
| `scripts/validate_pilot_deploy_env.py` | `M` | Deploy env validation |
| `triage.sh` | `D` | Root triage shim deletion |

### API / services — 6 paths

| Path | Status | Concern |
|------|--------|---------|
| `services/fiqa_api/app_main.py` | `M` | Deployment profile display name, health/version payloads |
| `services/fiqa_api/db/service_record_repository.py` | `M` | DB layer changes |
| `services/fiqa_api/deployment_profile.py` | `M` | Product-only profile, operator warnings |
| `services/fiqa_api/health/ready.py` | `M` | Readiness endpoint behavior |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` | `D` | Deprecated module removal |
| `services/fiqa_api/inbox_triage/case_store.py` | `M` | New `office_case_title` / `office_broker_next_step` fields |

### UI — 20 paths

| Path | Status | Concern |
|------|--------|---------|
| `ui/src/App.tsx` | `M` | Product-only UI gate, lazy lab routes |
| `ui/src/api/clientConfig.ts` | `M` | Client config API |
| `ui/src/api/inboxTriage.ts` | `M` | Intake API client |
| `ui/src/api/request.ts` | `M` | Request layer |
| `ui/src/components/intake/CustomerIntakeProgressSummary.tsx` | `??` | New intake component |
| `ui/src/components/intake/UserCaseListProgressPanel.tsx` | `M` | Progress panel |
| `ui/src/components/intake/customerPortalPresentation.tsx` | `??` | Portal presentation |
| `ui/src/components/layout/AppSider.tsx` | `M` | Sidebar layout |
| `ui/src/components/layout/LabDevBanner.tsx` | `??` | Lab dev banner |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | `M` | Workbench tab |
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | `M` | Customer entry |
| `ui/src/features/intake/components/MyRequestsTab.tsx` | `M` | My requests |
| `ui/src/features/intake/components/WorkbenchSummary.tsx` | `M` | Workbench summary |
| `ui/src/features/intake/constants/index.ts` | `M` | Intake constants |
| `ui/src/features/intake/prototypes/` | `??` | UI prototype experiments |
| `ui/src/features/intake/types/index.ts` | `M` | Intake types |
| `ui/src/features/intake/utils/intakePure.ts` | `M` | Intake utilities |
| `ui/src/pages/UnifiedIntakePage.tsx` | `M` | Main intake page |
| `ui/src/routes/` | `??` | Lab route lazy-load split (`labPages.tsx`) |
| `ui/src/vite-env.d.ts` | `M` | Vite env types |

### Configs — 2 paths

| Path | Status | Concern |
|------|--------|---------|
| `configs/clients/chen_kui/ui_copy.json` | `M` | **Broker demo copy** — portal trust line, history CTA |
| `configs/industries/insurance/markers.json` | `M` | **Triage markers** — payment/lapse/remove-vehicle expansions |

### Tests — 3 paths

| Path | Status | Concern |
|------|--------|---------|
| `tests/test_active_vehicle_resolver.py` | `D` | Paired with resolver deletion |
| `tests/test_deployment_profile.py` | `M` | New deployment profile tests |
| `tests/test_operator_surface_collapse.py` | `M` | Operator surface tests |

---

## Founder Action Required

Before committing the 53 paths, founder should decide per bundle:

1. **Product-only surface bundle** — `App.tsx`, `routes/`, `app_main.py`, `deployment_profile.py`, `run_demo_local.sh` (commit together or revert together)
2. **Chen Kui copy bundle** — `ui_copy.json` + related UI presentation files
3. **Triage markers bundle** — `markers.json` (impacts classification, not `triage.py`)
4. **Deprecation bundle** — `active_vehicle_resolver.py` + test + `triage.sh` deletions
5. **Case store fields** — `case_store.py` office title/step persistence

---

*Phase 1 complete. No product files modified during classification.*
