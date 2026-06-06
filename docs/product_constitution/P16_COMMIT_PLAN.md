# P16 Commit Plan

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 2  
**Status:** PLAN ONLY — **do not commit yet**

---

## Safety Summary

| Classification | Count | % | Action |
|----------------|------:|--:|--------|
| SAFE_TO_COMMIT | 1672 | 94.5% | Stage in hygiene commits A–C |
| REVIEW_REQUIRED | 94 | 5.3% | Founder review before staging |
| DO_NOT_COMMIT | 3 | 0.2% | Exclude from all commits |
| **Total** | **1769** | **100%** | |

---

## DO_NOT_COMMIT (3 paths)

These must never enter a commit without explicit founder override.

| Status | Path | Reason |
|--------|------|--------|
| ` M` | `configs/demo.env.example` | env template / local artifact |
| ` D` | `demo_brain_report.html` | local generated HTML report |
| `??` | `docs/archive/root_archaeology/demo_brain_report.html` | local generated HTML report |

---

## REVIEW_REQUIRED (94 paths)

Configs, scripts, and source changes require line-by-line review before staging.

### Configs & infrastructure (23)

| Status | Path |
|--------|------|
| ` M` | `Dockerfile.ecommerce` |
| ` M` | `Dockerfile.jobhunter` |
| ` M` | `Makefile` |
| ` M` | `README.md` |
| `??` | `agents/README.md` |
| ` M` | `configs/clients/chen_kui/ui_copy.json` |
| ` M` | `configs/industries/insurance/markers.json` |
| `??` | `configs/p16y_50_cases.json` |
| `??` | `configs/p16z20_add_car_customers.json` |
| `??` | `configs/p16z235_add_car_customers.json` |
| `??` | `configs/p16z24_add_car_customers.json` |
| `??` | `configs/role_d_claims_battery.json` |
| `??` | `configs/role_d_journeys.json` |
| `??` | `docker-compose.product.yml` |
| ` M` | `docker-compose.yml` |
| `??` | `engines/README.md` |
| `??` | `experiments/README.md` |
| ` M` | `jobhunter-clipper/README.md` |
| ` M` | `k8s/README.md` |
| `??` | `mcp/README.md` |
| `??` | `ml_models/README.md` |
| `??` | `modules/autotuner/README.md` |
| `??` | `orchestrators/README.md` |

### Scripts (40)

| Status | Path |
|--------|------|
| `??` | `scripts/DEEP_SCRIPT_TIER_MAP.md` |
| `??` | `scripts/LAB_SCRIPT_INDEX.md` |
| ` M` | `scripts/README.md` |
| ` M` | `scripts/README_OPERATOR.md` |
| `??` | `scripts/archive/` |
| ` M` | `scripts/check_unified_intake_prod_posture.sh` |
| ` M` | `scripts/demo_pre_checklist.sh` |
| ` M` | `scripts/demo_quick_validate.sh` |
| `??` | `scripts/deploy/` |
| ` M` | `scripts/deploy_paid_pilot.sh` |
| ` M` | `scripts/dev_local.sh` |
| `??` | `scripts/founder/` |
| ` M` | `scripts/founder_pre_trial_checklist.sh` |
| ` M` | `scripts/health_check.sh` |
| ` M` | `scripts/import_smoke_check.py` |
| `??` | `scripts/lab/` |
| `??` | `scripts/operator/` |
| `??` | `scripts/p16z11_founder_output.sh` |
| `??` | `scripts/post_sprint_check.sh` |
| ` M` | `scripts/restore_8001_readiness.sh` |
| ` M` | `scripts/run_append_boundary_ab_scenarios.py` |
| ` M` | `scripts/run_cross_client_ab_scenarios.py` |
| ` M` | `scripts/run_demo_local.sh` |
| `??` | `scripts/run_p16y_case_battery.py` |
| `??` | `scripts/run_p16z20_add_car_simulation.py` |
| `??` | `scripts/run_p16z21_tournament_simulation.py` |
| `??` | `scripts/run_p16z235_founder_reality_sprint.py` |
| `??` | `scripts/run_p16z24_add_car_sprint.py` |
| ` M` | `scripts/run_residual_copy_ab_scenarios.py` |
| `??` | `scripts/run_role_d_memory_battery.py` |
| ` M` | `scripts/run_small_batch_phrase_map_ab_scenarios.py` |
| ` M` | `scripts/start_all.sh` |
| ` M` | `scripts/start_demo_app.sh` |
| ` M` | `scripts/stop_all.sh` |
| ` M` | `scripts/summarize_readiness_posture.sh` |
| `??` | `scripts/summarize_support_posture.sh` |
| ` M` | `scripts/trial_launch_check.sh` |
| ` M` | `scripts/trial_readiness_check.sh` |
| ` M` | `scripts/validate_pilot_deploy_env.py` |
| ` D` | `triage.sh` |

### Source code & tests (27)

| Status | Path |
|--------|------|
| ` D` | `"docs/\347\224\265\345\225\206\345\224\256\345\220\216Agent_\344\273\243\347\240\201\350\265\204\344\272\247\345\213\230\346\237\245\346\212\245\345\221\212.md"` |
| `??` | `pipelines/` |
| ` M` | `services/fiqa_api/app_main.py` |
| ` M` | `services/fiqa_api/db/service_record_repository.py` |
| ` M` | `services/fiqa_api/deployment_profile.py` |
| ` M` | `services/fiqa_api/health/ready.py` |
| ` D` | `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` |
| ` M` | `services/fiqa_api/inbox_triage/case_store.py` |
| ` D` | `tests/test_active_vehicle_resolver.py` |
| ` M` | `tests/test_deployment_profile.py` |
| ` M` | `tests/test_operator_surface_collapse.py` |
| ` M` | `ui/src/App.tsx` |
| ` M` | `ui/src/api/clientConfig.ts` |
| ` M` | `ui/src/api/inboxTriage.ts` |
| ` M` | `ui/src/api/request.ts` |
| `??` | `ui/src/components/intake/CustomerIntakeProgressSummary.tsx` |
| ` M` | `ui/src/components/intake/UserCaseListProgressPanel.tsx` |
| `??` | `ui/src/components/intake/customerPortalPresentation.tsx` |
| ` M` | `ui/src/components/layout/AppSider.tsx` |
| `??` | `ui/src/components/layout/LabDevBanner.tsx` |
| ` M` | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` |
| ` M` | `ui/src/features/intake/components/CustomerEntryTab.tsx` |
| ` M` | `ui/src/features/intake/components/MyRequestsTab.tsx` |
| ` M` | `ui/src/features/intake/components/WorkbenchSummary.tsx` |
| ` M` | `ui/src/features/intake/constants/index.ts` |
| `??` | `ui/src/features/intake/prototypes/` |
| ` M` | `ui/src/features/intake/types/index.ts` |
| ` M` | `ui/src/features/intake/utils/intakePure.ts` |
| ` M` | `ui/src/pages/UnifiedIntakePage.tsx` |
| `??` | `ui/src/routes/` |
| ` M` | `ui/src/vite-env.d.ts` |

---

## SAFE_TO_COMMIT (1672 paths)

All documentation, sprint reports, product constitution artifacts, and archival moves.

**Breakdown by category:**

| Category | Count |
|----------|------:|
| docs | 1321 |
| reports | 209 |
| sprint artifacts | 115 |
| archived content | 27 |

---

## Exclusion Rules

1. Never commit `demo_brain_report.html` or `.p16z24_results/*.json` without explicit review.
2. Never commit `.env`, credentials, or IDE caches (none currently dirty).
3. Script changes (`scripts/*.sh`) require operator-path validation before Commit C.
4. `configs/demo.env.example` is REVIEW_REQUIRED — verify no secrets before any commit.

---

## Commit Strategy (Phase 3 — DO NOT EXECUTE YET)

### Commit A — `chore(repo): archive sprint reports and governance documents`

**Scope (~841 paths):**

- `docs/product_constitution/P16_*.md` and all governance artifacts
- New operator docs: `docs/15_MINUTE_ENGINEER_ONBOARDING.md`, `docs/FOUNDER_ONE_PATH.md`, etc.
- Modified operator runbooks: `docs/ANDY_QUICK_START.md`, `docs/runbooks/*`
- Root-level doc updates: `AGENTS.md`, `README.md` (after review)

**Excludes:** scripts, configs, source code, generated HTML

### Commit B — `chore(repo): preserve release manifests and deployment records`

**Scope (~82 paths):**

- Deployment and release documentation under `docs/runbooks/DEPLOYMENT_*`
- Trial docs: `docs/trial/*`
- Release verification and deploy alignment reports in `docs/product_constitution/`
- Any `release/` manifest files

**Excludes:** sprint archive bulk, script changes

### Commit C — `chore(repo): repository cleanup and archival structure`

**Scope (~749 paths + reviewed scripts/configs):**

- 1,228 deleted root-level `docs/*_SPRINT_REPORT.md` paths
- 471 new untracked paths under `docs/sprints/archive/` and `docs/archive/`
- Reviewed script changes (`scripts/*.sh`, `scripts/*.py`) after operator validation
- Reviewed config changes (`configs/`, `docker-compose.yml`, Dockerfiles)
- Reviewed source changes (`ui/src/*`, `services/fiqa_api/*`)

**Excludes:** DO_NOT_COMMIT paths, unreviewed configs

### Post-commit validation

```bash
bash scripts/demo_pre_checklist.sh
bash scripts/guardrail_inbox_triage.sh
git status --porcelain  # target: ≤10 paths (IDE/local only)
```

---

## Why These Boundaries

| Boundary | Rationale |
|----------|-----------|
| **A before B** | Governance docs define how release artifacts are interpreted; commit context first |
| **B separate from C** | Release/deploy records are audit-critical; isolate from bulk archival noise |
| **C last** | Largest diff (1,228 deletions + 471 additions); includes code/scripts needing review |
| **Three commits, not one** | Single 1,769-path commit is unreviewable; bisect and rollback become impossible |
| **Scripts in C, not A** | Script changes affect demo runtime; must not ride along with doc-only commits |

**Estimated post-commit dirty paths:** 3 (DO_NOT_COMMIT) + any REVIEW_REQUIRED items deferred by founder.

