# P16 Runtime Resolution Report

**Date:** 2026-06-06  
**Mission:** P16-PUSH-PRESERVE-AND-RUNTIME-GATE — Phase 4  
**Commit:** `b3c8ec369fa9f9232e3f663be23cd4f093c985d3`  
**Message:** `chore(repo): resolve reviewed runtime bundles`

---

## Committed Files (35 KEEP)

### UI (10)

- `ui/src/App.tsx`
- `ui/src/routes/labPages.tsx`
- `ui/src/components/intake/CustomerIntakeProgressSummary.tsx`
- `ui/src/components/intake/UserCaseListProgressPanel.tsx`
- `ui/src/components/intake/customerPortalPresentation.tsx`
- `ui/src/components/layout/AppSider.tsx`
- `ui/src/components/layout/LabDevBanner.tsx`
- `ui/src/features/intake/constants/index.ts`
- `ui/src/features/intake/types/index.ts`
- `ui/src/vite-env.d.ts`

### Scripts (19)

- `scripts/run_demo_local.sh`
- `scripts/demo_pre_checklist.sh`
- `scripts/demo_quick_validate.sh`
- `scripts/check_unified_intake_prod_posture.sh`
- `scripts/dev_local.sh`
- `scripts/founder_pre_trial_checklist.sh`
- `scripts/health_check.sh`
- `scripts/import_smoke_check.py`
- `scripts/restore_8001_readiness.sh`
- `scripts/run_append_boundary_ab_scenarios.py`
- `scripts/run_cross_client_ab_scenarios.py`
- `scripts/run_residual_copy_ab_scenarios.py`
- `scripts/run_small_batch_phrase_map_ab_scenarios.py`
- `scripts/start_all.sh`
- `scripts/start_demo_app.sh`
- `scripts/stop_all.sh`
- `scripts/summarize_readiness_posture.sh`
- `scripts/trial_launch_check.sh`
- `scripts/trial_readiness_check.sh`

### API (3)

- `services/fiqa_api/app_main.py`
- `services/fiqa_api/deployment_profile.py`
- `services/fiqa_api/health/ready.py`

### Tests (3)

- `tests/test_active_vehicle_resolver.py` (deleted)
- `tests/test_deployment_profile.py`
- `tests/test_operator_surface_collapse.py`

**Diff stats:** 35 files changed, 926 insertions(+), 422 deletions(-)

---

## Reverted Files (1 REVERT)

| Path | Action |
|------|--------|
| `ui/src/features/intake/prototypes/p16z21/` | Removed from disk (3 files: `PathTimelineFirstBanner.tsx`, `PathGuidedRail.tsx`, `evolutionPaths.ts`) |

Never tracked in git — experimental prototype discarded.

---

## Remaining Files (17 UNSURE + 2 DO_NOT_COMMIT)

### UNSURE — founder review required (17)

| Path | Bundle |
|------|--------|
| `ui/src/api/clientConfig.ts` | A |
| `ui/src/api/inboxTriage.ts` | A |
| `ui/src/api/request.ts` | A |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | A |
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | A |
| `ui/src/features/intake/components/MyRequestsTab.tsx` | A |
| `ui/src/features/intake/components/WorkbenchSummary.tsx` | A |
| `ui/src/features/intake/utils/intakePure.ts` | A |
| `ui/src/pages/UnifiedIntakePage.tsx` | A |
| `scripts/deploy_paid_pilot.sh` | B |
| `scripts/validate_pilot_deploy_env.py` | B |
| `triage.sh` (deleted locally) | B |
| `configs/clients/chen_kui/ui_copy.json` | C |
| `configs/industries/insurance/markers.json` | D |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` (deleted locally) | D |
| `services/fiqa_api/inbox_triage/case_store.py` | E |
| `services/fiqa_api/db/service_record_repository.py` | E |

### DO_NOT_COMMIT (2)

| Path | Reason |
|------|--------|
| `configs/demo.env.example` | Local template |
| `demo_brain_report.html` (deleted locally) | Generated artifact |

---

## Note on Partial Consistency

`tests/test_active_vehicle_resolver.py` deletion was committed (KEEP), but `active_vehicle_resolver.py` module deletion remains UNSURE/unstaged. HEAD still contains the resolver module. Founder should resolve Bundle D as a unit in a future session.

---

*Phase 4 complete. One commit created. UNSURE paths untouched.*
