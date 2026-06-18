# P16 Runtime Gate Review

**Date:** 2026-06-06  
**Mission:** P16-PUSH-PRESERVE-AND-RUNTIME-GATE — Phase 3  
**Branch:** `sprint-a/broker-front-door` @ `d870ccc` (pre-resolution)  
**Source:** `P16_RUNTIME_BUNDLE_REVIEW.md` + verification pass  
**Status:** Classification only — resolution in Phase 4

---

## Bundle Summary

| Bundle | Size | KEEP | REVERT | UNSURE | Recommendation | Risk | Expected Impact |
|--------|-----:|-----:|-------:|-------:|----------------|:----:|-----------------|
| **A — UI** | 20 | 10 | 1 | 9 | Commit KEEP subset; defer UNSURE to founder demo review | Medium | Product-only UI gate lands; demo-critical tabs pending |
| **B — Product Surface** | 25 | 22 | 0 | 3 | Commit as unit (KEEP only); defer deploy scripts | High | Default demo posture shifts to product-only |
| **C — Config** | 1 | 0 | 0 | 1 | Defer — broker copy review required | Medium | Customer-facing Chinese copy |
| **D — Triage** | 2 | 0 | 0 | 2 | Defer — run guardrail before any commit | High | Classification marker changes |
| **E — Persistence** | 2 | 0 | 0 | 2 | Defer — verify DB replay compatibility | Medium | Office title/step fields |
| **F — Misc** | 3 | 3 | 0 | 0 | Commit with paired bundles | Low | Test coverage for committed bundles |
| **Total** | **53** | **35** | **1** | **17** | — | — | — |

---

## Bundle A — UI (20 files)

**Theme:** Product-only UI gate, lazy lab routes, intake presentation.

| Path | Class | Rationale |
|------|:-----:|-----------|
| `ui/src/App.tsx` | KEEP | Lazy-loads lab pages; product routes default to workbench |
| `ui/src/routes/labPages.tsx` | KEEP | Pairs with App.tsx lab/product split |
| `ui/src/components/intake/CustomerIntakeProgressSummary.tsx` | KEEP | New progress summary component |
| `ui/src/components/intake/UserCaseListProgressPanel.tsx` | KEEP | Progress panel updates |
| `ui/src/components/intake/customerPortalPresentation.tsx` | KEEP | Portal presentation layer |
| `ui/src/components/layout/AppSider.tsx` | KEEP | Sidebar layout for product-only nav |
| `ui/src/components/layout/LabDevBanner.tsx` | KEEP | Lab mode indicator banner |
| `ui/src/features/intake/constants/index.ts` | KEEP | Constants only |
| `ui/src/features/intake/types/index.ts` | KEEP | Type definitions |
| `ui/src/vite-env.d.ts` | KEEP | Vite env type for product-only flag |
| `ui/src/features/intake/prototypes/p16z21/` | REVERT | Experimental prototype — not pilot surface |
| `ui/src/api/clientConfig.ts` | UNSURE | Client config API — verify no breaking contract |
| `ui/src/api/inboxTriage.ts` | UNSURE | Intake API client — check field additions |
| `ui/src/api/request.ts` | UNSURE | Request layer — verify error handling |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | UNSURE | Demo-critical workbench tab |
| `ui/src/features/intake/components/CustomerEntryTab.tsx` | UNSURE | Demo-critical customer entry |
| `ui/src/features/intake/components/MyRequestsTab.tsx` | UNSURE | User-facing my requests |
| `ui/src/features/intake/components/WorkbenchSummary.tsx` | UNSURE | Workbench summary display |
| `ui/src/features/intake/utils/intakePure.ts` | UNSURE | Pure utilities — verify no triage logic change |
| `ui/src/pages/UnifiedIntakePage.tsx` | UNSURE | Main intake page — demo-critical |

**Risk:** Medium — demo-visible; does not touch AC03/AC05/AC07.

---

## Bundle B — Product Surface (25 files)

**Theme:** Product-only default in launcher, operator scripts, deployment profile.

| Path | Class | Rationale |
|------|:-----:|-----------|
| 19 operator scripts (see bundle review) | KEEP | Product-only posture alignment |
| `services/fiqa_api/app_main.py` | KEEP | Display name + product-only banner |
| `services/fiqa_api/deployment_profile.py` | KEEP | Runtime display name, operator warnings |
| `services/fiqa_api/health/ready.py` | KEEP | Readiness messaging for product-only mode |
| `scripts/deploy_paid_pilot.sh` | UNSURE | Deploy entry — verify prod parity |
| `scripts/validate_pilot_deploy_env.py` | UNSURE | Deploy env validation |
| `triage.sh` | UNSURE | Root shim deletion — confirm no operator dependency |

**Risk:** High — changes default demo posture.

---

## Bundle C — Config (1 file)

| Path | Class | Rationale |
|------|:-----:|-----------|
| `configs/clients/chen_kui/ui_copy.json` | UNSURE | Portal trust line + history CTA — broker review |

**Risk:** Medium — visible in Chen Kui demo.

---

## Bundle D — Triage (2 files)

| Path | Class | Rationale |
|------|:-----:|-----------|
| `configs/industries/insurance/markers.json` | UNSURE | Marker expansions affect classification |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` | UNSURE | Deprecated module removal — verify no imports |

**Risk:** High — marker changes affect live triage. Does not touch AC03/AC05/AC07.

---

## Bundle E — Persistence (2 files)

| Path | Class | Rationale |
|------|:-----:|-----------|
| `services/fiqa_api/inbox_triage/case_store.py` | UNSURE | New office title/step fields |
| `services/fiqa_api/db/service_record_repository.py` | UNSURE | PG persistence for office fields |

**Risk:** Medium — persistence contract change.

---

## Bundle F — Misc (3 files)

| Path | Class | Rationale |
|------|:-----:|-----------|
| `tests/test_active_vehicle_resolver.py` | KEEP | Paired deletion (Bundle D context) |
| `tests/test_deployment_profile.py` | KEEP | Tests for deployment profile |
| `tests/test_operator_surface_collapse.py` | KEEP | Operator surface regression tests |

**Risk:** Low.

---

## Excluded (DO_NOT_COMMIT)

| Path | Reason |
|------|--------|
| `configs/demo.env.example` | Local template |
| `demo_brain_report.html` | Generated artifact |

---

## Grand Totals

| Classification | Count |
|----------------|------:|
| KEEP | 35 |
| REVERT | 1 |
| UNSURE | 17 |
| DO_NOT_COMMIT | 2 |
| **Total runtime scope** | **55** |

*Note: 53 classified runtime paths + 2 DO_NOT_COMMIT = 55 dirty paths at sprint start.*

---

*Phase 3 complete. Classification carried forward to Phase 4 resolution.*
