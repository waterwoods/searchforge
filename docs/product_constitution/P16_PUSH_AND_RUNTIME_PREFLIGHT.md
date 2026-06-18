# P16 Push and Runtime Pre-Flight

**Date:** 2026-06-06  
**Mission:** P16-PUSH-PRESERVE-AND-RUNTIME-GATE — Phase 0  
**Status:** Read-only snapshot — no changes made

---

## Branch and Refs

| Item | Value |
|------|-------|
| **Current branch** | `sprint-a/broker-front-door` |
| **HEAD SHA** | `d870cccf9ccfbb0296a263e1ba1e85b444fe74cb` |
| **Release branch SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` (`release/p16-demo-ready-v1`) |
| **Tag SHA (commit)** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` (`p16-demo-ready-v1` → annotated tag object `5a2ab39`) |
| **Origin sprint-a SHA** | `d05e94da0855942c6143405720d65be35b3c5829` |

---

## Working Tree Metrics

| Metric | Count |
|--------|------:|
| **Dirty file count** (modified + deleted + untracked in status) | 62 |
| **Untracked file count** | 12 |
| **Ahead of origin** | 8 commits |
| **Behind origin** | 0 commits |

---

## Exact Git Status Summary

```
## sprint-a/broker-front-door...origin/sprint-a/broker-front-door [ahead 8]
 M configs/clients/chen_kui/ui_copy.json
 M configs/demo.env.example
 M configs/industries/insurance/markers.json
 D demo_brain_report.html
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
?? docs/product_constitution/P16_AUDIT_REPORT_COMMIT.md
?? docs/product_constitution/P16_GOVERNANCE_FINALIZATION_PRECHECK.md
?? docs/product_constitution/P16_GOVERNANCE_FINALIZATION_SUMMARY.md
?? docs/product_constitution/P16_MAIN_PROMOTION_FINAL_GATE.md
?? docs/product_constitution/P16_PUSH_EXECUTION_READINESS.md
?? docs/product_constitution/P16_RELEASE_PRESERVATION_VERIFICATION.md
?? docs/product_constitution/P16_RUNTIME_BUNDLE_REVIEW.md
?? ui/src/components/intake/CustomerIntakeProgressSummary.tsx
?? ui/src/components/intake/customerPortalPresentation.tsx
?? ui/src/components/layout/LabDevBanner.tsx
?? ui/src/features/intake/prototypes/
?? ui/src/routes/
```

---

## Remote Preservation Gap

| Ref | On origin? |
|-----|:----------:|
| `sprint-a/broker-front-door` @ `d870ccc` | ❌ (origin at `d05e94d`) |
| `release/p16-demo-ready-v1` @ `517f728` | ❌ |
| `p16-demo-ready-v1` tag @ `517f728` | ❌ |
| `archive/production-pre-p16-demo` @ `85bacc6` | ✅ |

---

*Phase 0 complete. No repository changes made.*
