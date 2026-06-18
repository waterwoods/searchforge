# P16 Runtime Bundle Review

**Date:** 2026-06-06  
**Mission:** P16-GOVERNANCE-FINALIZATION-SPRINT — Phase 3  
**Branch:** `sprint-a/broker-front-door` @ `d870ccc`  
**Scope:** Classify 53 NEEDS_FOUNDER_REVIEW paths — **no commit, no revert**

---

## Summary

| Bundle | Files | Risk | Founder recommendation |
|--------|------:|:----:|------------------------|
| **A — UI** | 20 | Medium | Review as one unit with Bundle B product-only gate |
| **B — Product Surface** | 25 | High | Commit together or revert together |
| **C — Config** | 1 | Medium | Chen Kui demo copy — validate with broker before commit |
| **D — Triage** | 2 | High | Markers + deprecations affect classification paths |
| **E — Persistence / Case Store** | 2 | Medium | Office title/step fields — verify DB replay compatibility |
| **F — Misc** | 3 | Low | Tests follow bundles D and B decisions |
| **Total** | **53** | — | Defer to P16-RUNTIME-COMMIT-GATE |

*Note: `triage.sh` deletion is in Bundle B scripts; `tests/test_active_vehicle_resolver.py` is in Bundle F.*

---

## Classification Key

| Label | Meaning |
|-------|---------|
| **KEEP** | Diff appears intentional, self-consistent, aligned with P16 product-only direction |
| **REVERT** | Diff appears accidental, experimental junk, or contradictory |
| **UNSURE** | Requires founder business judgment before commit |

---

## Bundle A — UI (20 files)

**Theme:** Product-only UI gate, lazy lab routes, intake presentation, Chen Kui portal UX.

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `ui/src/App.tsx` | M | KEEP | Lazy-loads lab pages; product routes default to workbench |
| `ui/src/routes/labPages.tsx` | ?? | KEEP | Pairs with App.tsx lab/product split |
| `ui/src/api/clientConfig.ts` | M | UNSURE | Client config API changes — verify no breaking contract |
| `ui/src/api/inboxTriage.ts` | M | UNSURE | Intake API client — check field additions |
| `ui/src/api/request.ts` | M | UNSURE | Request layer — minor; verify error handling unchanged |
| `ui/src/components/intake/CustomerIntakeProgressSummary.tsx` | ?? | KEEP | New progress summary component |
| `ui/src/components/intake/UserCaseListProgressPanel.tsx` | M | KEEP | Progress panel updates |
| `ui/src/components/intake/customerPortalPresentation.tsx` | ?? | KEEP | Portal presentation layer |
| `ui/src/components/layout/AppSider.tsx` | M | KEEP | Sidebar layout for product-only nav |
| `ui/src/components/layout/LabDevBanner.tsx` | ?? | KEEP | Lab mode indicator banner |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | M | UNSURE | Workbench tab — verify demo flow |
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | M | UNSURE | Customer entry — demo-critical path |
| `ui/src/features/intake/components/MyRequestsTab.tsx` | M | UNSURE | My requests — user-facing |
| `ui/src/features/intake/components/WorkbenchSummary.tsx` | M | UNSURE | Workbench summary display |
| `ui/src/features/intake/constants/index.ts` | M | KEEP | Constants only |
| `ui/src/features/intake/prototypes/p16z21/` | ?? | REVERT | Experimental prototype — not pilot surface |
| `ui/src/features/intake/types/index.ts` | M | KEEP | Type definitions |
| `ui/src/features/intake/utils/intakePure.ts` | M | UNSURE | Pure utilities — verify no triage logic change |
| `ui/src/pages/UnifiedIntakePage.tsx` | M | UNSURE | Main intake page — demo-critical |
| `ui/src/vite-env.d.ts` | M | KEEP | Vite env type for `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` |

**Bundle A counts:** KEEP 10 · REVERT 1 · UNSURE 9  
**Risk:** Medium — UI changes are demo-visible but do not touch `triage.py` or AC03/AC05/AC07.  
**Founder recommendation:** Commit A minus `prototypes/` if approving product-only UI gate. Review UNSURE paths in live demo before commit.

---

## Bundle B — Product Surface (25 files)

**Theme:** Product-only default in launcher, operator scripts, deployment profile, health endpoints.

### Scripts (22)

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `scripts/run_demo_local.sh` | M | KEEP | Primary demo launcher — `RUN_DEMO_LAB=1` opt-in |
| `scripts/demo_pre_checklist.sh` | M | KEEP | Workbench-first checklist |
| `scripts/demo_quick_validate.sh` | M | KEEP | Intake guardrail default; lab via `RUN_DEMO_LAB=1` |
| `scripts/check_unified_intake_prod_posture.sh` | M | KEEP | Humanized operator warnings |
| `scripts/deploy_paid_pilot.sh` | M | UNSURE | Deploy entry — verify prod parity |
| `scripts/dev_local.sh` | M | KEEP | Local dev launcher alignment |
| `scripts/founder_pre_trial_checklist.sh` | M | KEEP | Trial checklist updates |
| `scripts/health_check.sh` | M | KEEP | Health probe alignment |
| `scripts/import_smoke_check.py` | M | KEEP | Import smoke |
| `scripts/restore_8001_readiness.sh` | M | KEEP | Recovery script |
| `scripts/run_append_boundary_ab_scenarios.py` | M | KEEP | AB runner — no triage.py |
| `scripts/run_cross_client_ab_scenarios.py` | M | KEEP | AB runner |
| `scripts/run_residual_copy_ab_scenarios.py` | M | KEEP | AB runner |
| `scripts/run_small_batch_phrase_map_ab_scenarios.py` | M | KEEP | AB runner |
| `scripts/start_all.sh` | M | KEEP | Lab stack starter |
| `scripts/start_demo_app.sh` | M | KEEP | Demo app starter |
| `scripts/stop_all.sh` | M | KEEP | Lab stack stopper |
| `scripts/summarize_readiness_posture.sh` | M | KEEP | Readiness summary |
| `scripts/trial_launch_check.sh` | M | KEEP | Trial launch gate |
| `scripts/trial_readiness_check.sh` | M | KEEP | Trial readiness gate |
| `scripts/validate_pilot_deploy_env.py` | M | UNSURE | Deploy env validation |
| `triage.sh` | D | UNSURE | Root shim deletion — confirm no operator dependency |

### API (3)

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `services/fiqa_api/app_main.py` | M | KEEP | Display name + product-only banner |
| `services/fiqa_api/deployment_profile.py` | M | KEEP | `runtime_service_display_name`, operator warnings |
| `services/fiqa_api/health/ready.py` | M | KEEP | Readiness messaging for product-only mode |

**Bundle B counts:** KEEP 22 · REVERT 0 · UNSURE 3  
**Risk:** High — changes default demo posture and operator paths.  
**Founder recommendation:** Commit as a single bundle if product-only default is confirmed. Do not cherry-pick individual scripts.

---

## Bundle C — Config (1 file)

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `configs/clients/chen_kui/ui_copy.json` | M | UNSURE | Portal trust line + history CTA — customer-facing Chinese copy |

**Bundle C counts:** KEEP 0 · REVERT 0 · UNSURE 1  
**Risk:** Medium — visible in Chen Kui demo; no code logic.  
**Founder recommendation:** Review copy with broker before commit. Pair with Bundle A portal presentation files.

---

## Bundle D — Triage (2 files)

**Theme:** Marker expansions and deprecated module removal. Does **not** touch `triage.py` or AC03/AC05/AC07.

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `configs/industries/insurance/markers.json` | M | UNSURE | Payment/lapse/remove-vehicle marker expansions — affects classification |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` | D | UNSURE | Deprecated module removal — verify no import references remain |

**Bundle D counts:** KEEP 0 · REVERT 0 · UNSURE 2  
**Risk:** High — marker changes affect live triage classification.  
**Founder recommendation:** Run `guardrail_inbox_triage.sh` and scenario battery before commit. Deprecation bundle must commit or revert together.

---

## Bundle E — Persistence / Case Store (2 files)

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `services/fiqa_api/inbox_triage/case_store.py` | M | UNSURE | New `office_case_title` / `office_broker_next_step` fields |
| `services/fiqa_api/db/service_record_repository.py` | M | UNSURE | PG persistence for office fields; `current_next_action` precedence |

**Bundle E counts:** KEEP 0 · REVERT 0 · UNSURE 2  
**Risk:** Medium — persistence contract change; no DDL migration in diff.  
**Founder recommendation:** Verify read compatibility with existing cases. Commit paired with any UI that displays office title/step.

---

## Bundle F — Misc (2 files)

| Path | Status | Class | Rationale |
|------|--------|:-----:|-----------|
| `tests/test_active_vehicle_resolver.py` | D | KEEP | Paired deletion with Bundle D resolver removal |
| `tests/test_deployment_profile.py` | M | KEEP | Tests for new deployment profile functions |
| `tests/test_operator_surface_collapse.py` | M | KEEP | Operator surface regression tests |

**Bundle F counts:** KEEP 3 · REVERT 0 · UNSURE 0  
**Risk:** Low — tests follow bundle decisions.  
**Founder recommendation:** Commit with whichever bundles they test (B for deployment profile; D for resolver deletion).

---

## Grand Totals

| Classification | Count |
|----------------|------:|
| KEEP | 35 |
| REVERT | 1 |
| UNSURE | 17 |
| **Total** | **53** |

---

## Excluded (DO_NOT_COMMIT — not in 53)

| Path | Reason |
|------|--------|
| `configs/demo.env.example` | Local template; verify secrets before any commit |
| `demo_brain_report.html` | Generated artifact |

---

*Phase 3 complete. Classification only — no files modified.*
