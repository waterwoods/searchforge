# P16 Dirty Tree Final

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 2  
**Branch:** `sprint-a/broker-front-door` @ `4d5bf46`

---

## Before / After

| Metric | Before | After |
|--------|-------:|------:|
| **Total dirty paths** | **107** | **55** |
| REVIEW_REQUIRED (unresolved) | 93 | 53 |
| KEEP_AND_COMMIT (resolved) | 40 | 0 |
| DO_NOT_COMMIT | 2 | 2 |
| MISSED_ARCHIVE | 5 | 0 |
| Prior sprint reports (uncommitted) | 7 | 0 |
| AGENTS.md (extra doc) | 1 | 0 |

**Reduction:** 52 paths resolved (−48.6%)

---

## Actions Executed (Phase 2)

### Committed — `4d5bf46`

```
chore(repo): commit safe hygiene paths and complete missed archive
```

| Action | Paths | Details |
|--------|------:|---------|
| Archive missed lab docs | 4 | Deleted `docs/vitals_*.md` (3) + Chinese ecommerce doc (1); copies exist under `docs/archive/lab/` |
| Script tier organization | 35+ | `operator/`, `founder/`, `lab/`, `deploy/`, `archive/` wrappers + indexes |
| Simulation fixtures | 6 | `configs/p16*.json`, `configs/role_d_*.json` |
| Lab README stubs | 8 | `agents/`, `engines/`, `pipelines/`, etc. |
| Infra documentation | 6 | `docker-compose.product.yml`, Makefile/docker-compose comments, Dockerfiles |
| Prior preservation reports | 7 | `P16_COMMIT_*`, `P16_PUSH_PLAN`, etc. |
| AGENTS.md | 1 | Operator doc table update |

**88 files changed** in commit `4d5bf46`.

### Not executed (per mission guardrails)

| Action | Reason |
|--------|--------|
| Commit API/UI/runtime scripts | NEEDS_FOUNDER_REVIEW — changes product behavior |
| Revert any path | REVERT count = 0 |
| Commit `demo.env.example` | DO_NOT_COMMIT |
| Commit `demo_brain_report.html` | DO_NOT_COMMIT (generated) |
| Push to origin | Phase 4 — plan only |
| Merge to main | Out of scope |

---

## Remaining Dirty Tree — 55 paths

```
 M configs/clients/chen_kui/ui_copy.json
 M configs/demo.env.example                    # DO_NOT_COMMIT
 M configs/industries/insurance/markers.json
 D demo_brain_report.html                     # DO_NOT_COMMIT
 M scripts/check_unified_intake_prod_posture.sh
 M scripts/demo_pre_checklist.sh
 M scripts/demo_quick_validate.sh
 M scripts/deploy_paid_pilot.sh
 M scripts/dev_local.sh
 M scripts/founder_pre_trial_checklist.sh
 M scripts/health_check.sh
 M scripts/import_smoke_check.py
 M scripts/restore_8001_readiness.sh
 M scripts/run_append_boundary_ab_scenarios.py
 M scripts/run_cross_client_ab_scenarios.py
 M scripts/run_demo_local.sh
 M scripts/run_residual_copy_ab_scenarios.py
 M scripts/run_small_batch_phrase_map_ab_scenarios.py
 M scripts/start_all.sh
 M scripts/start_demo_app.sh
 M scripts/stop_all.sh
 M scripts/summarize_readiness_posture.sh
 M scripts/trial_launch_check.sh
 M scripts/trial_readiness_check.sh
 M scripts/validate_pilot_deploy_env.py
 M services/fiqa_api/app_main.py
 M services/fiqa_api/db/service_record_repository.py
 M services/fiqa_api/deployment_profile.py
 M services/fiqa_api/health/ready.py
 D services/fiqa_api/inbox_triage/active_vehicle_resolver.py
 M services/fiqa_api/inbox_triage/case_store.py
 D tests/test_active_vehicle_resolver.py
 M tests/test_deployment_profile.py
 M tests/test_operator_surface_collapse.py
 D triage.sh
 M ui/src/App.tsx
 M ui/src/api/clientConfig.ts
 M ui/src/api/inboxTriage.ts
 M ui/src/api/request.ts
 M ui/src/components/intake/UserCaseListProgressPanel.tsx
 M ui/src/components/layout/AppSider.tsx
 M ui/src/features/intake/components/BrokerWorkbenchTab.tsx
 M ui/src/features/intake/components/CustomerEntryTab.tsx
 M ui/src/features/intake/components/MyRequestsTab.tsx
 M ui/src/features/intake/components/WorkbenchSummary.tsx
 M ui/src/features/intake/constants/index.ts
 M ui/src/features/intake/types/index.ts
 M ui/src/features/intake/utils/intakePure.ts
 M ui/src/pages/UnifiedIntakePage.tsx
 M ui/src/vite-env.d.ts
?? ui/src/components/intake/CustomerIntakeProgressSummary.tsx
?? ui/src/components/intake/customerPortalPresentation.tsx
?? ui/src/components/layout/LabDevBanner.tsx
?? ui/src/features/intake/prototypes/
?? ui/src/routes/
```

### Breakdown

| Category | Count |
|----------|------:|
| NEEDS_FOUNDER_REVIEW | 53 |
| DO_NOT_COMMIT | 2 |

---

## Tree Health

| Check | Status |
|-------|--------|
| HEAD commit clean? | ✅ `git diff --stat HEAD` shows only 55 paths |
| Demo SHA unchanged? | ✅ `release/p16-demo-ready-v1` still `517f728` |
| Archive migration complete? | ✅ MISSED_ARCHIVE resolved |
| Promotion-safe? | ⚠️ 53 runtime paths remain unstaged |

---

*See `P16_RUNTIME_REVIEW_REPORT.md` for per-path classification.*
