# P16 Customer First Deployment Certification

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-DEPLOYMENT-RECOVERY-SPRINT  
**Date:** 2026-06-07  
**Status:** Preview UI **CERTIFIED** · End-to-end API flow **BLOCKED** (Cloud Run not promoted)

---

## 1. Root Cause

Git-triggered Vercel builds on commit `b3c8ec3` fail because `CustomerEntryTab.tsx` imports missing `p16z21` prototype files (`evolutionPaths`, `PathGuidedRail`, `PathTimelineFirstBanner`). Customer First implementation exists only in the **local working tree** (uncommitted) and was never included in git-connected deploys.

Details: `docs/trial/DEPLOY_FAILURE_ROOT_CAUSE.md`

---

## 2. Fix Applied

| Fix | Scope |
|-----|-------|
| Removed broken `p16z21` prototype imports (already in working tree) | Build blocker |
| CLI Preview deploy from `ui/` with Customer First source files | Ships uncommitted UI |
| Build env: `PRODUCT_ONLY=1` + `SUPERVISED_DEMO=1` | Restores **客户报送** tab in product-only mode |
| Build env: API URL + intake API key | Queue/API auth parity |
| Alias `ui-waterwoods` → new deployment | Founder-stable URL |

**Not changed:** Product design, Cloud Run backend (separate promotion needed for active-case API).

---

## 3. Deployment Record

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_CUZEuqipbcaLaUoby5owCLbhvLzx` |
| **Deployment URL** | `https://ui-y40mjm5ih-andys-projects-1f411b73.vercel.app` |
| **Alias (founder)** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Workbench path** | `/workbench/unified-intake?tab=customer` |
| **Status** | **Ready** |
| **Timestamp** | Sun Jun 07 2026 03:00:51 PDT |
| **Bundle hash** | `index-PbeYeKTS.js` |
| **Git-linked** | No — CLI upload of working tree @ repo HEAD `b3c8ec3` + uncommitted Customer First delta |

### Bundle markers (verified)

| Marker | Present |
|--------|---------|
| `Add-Car Request` | ✅ |
| `No account required` | ✅ |
| `Return anytime` | ✅ |
| `客户报送` | ✅ |

---

## 4. Customer First Code Audit

**IS_CUSTOMER_FIRST_IMPLEMENTED = YES** (local working tree)

| Requirement | File(s) | Status |
|-------------|---------|--------|
| Customer First entry screen | `ui/src/features/intake/components/CustomerFirstEntryScreen.tsx` | ✅ |
| Phone-first flow | `CustomerFirstEntryScreen.tsx` (phone required, name optional) | ✅ |
| Customer Never Logs In | No login/password/OAuth on entry screen; trust copy explicit | ✅ |
| Phone Is The Return Key | `lookupActiveCaseByPhone`, `CUSTOMER_PHONE_STORAGE_KEY`, return-key copy | ✅ |
| Customer Report tab (客户报送) | `ui/src/pages/UnifiedIntakePage.tsx` — tab renders with `SUPERVISED_DEMO=1` | ✅ |
| Gate before intake chat | `CustomerEntryTab.tsx` — `customerFirstUnlocked` gate | ✅ |
| Phone utilities | `ui/src/features/intake/utils/customerFirstEntry.ts` | ✅ |
| API client | `ui/src/api/inboxTriage.ts` — `lookupActiveCaseByPhone`, `startCustomerAddCarDraft` | ✅ |
| Backend (local only) | `active_case_lookup.py`, `phone_normalization.py`, routes in `inbox_triage.py` | ✅ local · ❌ Cloud Run |

---

## 5. Founder Verification Results

**Preview opened:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer`

### Scenario A — New customer, no active case

| Check | Result |
|-------|--------|
| **客户报送** tab visible | **PASS** |
| Phone field present | **PASS** |
| Continue button present | **PASS** |
| Trust lines (no account / no password / phone return) | **PASS** |
| After Continue → “Start New Add-Car Request” → intake | **FAIL** — `GET /api/inbox/customer/active-case` returns **404** on Cloud Run; UI shows phone validation error and stays on entry screen |

**Scenario A verdict: UI PASS · Flow FAIL (backend not on Cloud Run)**

### Scenario B — Phone with active case

| Check | Result |
|-------|--------|
| Active case detected | **FAIL** — same API 404; resume card cannot load |

**Scenario B verdict: FAIL (backend not on Cloud Run)**

### Tab / runtime

| Check | Result |
|-------|--------|
| Deployment Ready, no build error | **PASS** |
| No runtime crash (page loads) | **PASS** |
| 客户报送 tab renders Customer First screen | **PASS** |

---

## 6. Screenshots

Browser verification captured during sprint (Cursor browser tool):

- Customer First entry: Add-Car Request banner, phone field `(626) 555-0100`, Continue / 继续, trust bullets
- Three-tab layout: 客户报送 · 办公室工作台 · 场景仿真

---

## 7. Follow-Up (out of scope for this sprint)

1. **Commit** Customer First UI + remove `p16z21` imports so git-connected deploys build.
2. **Promote** `active_case_lookup` + `/customer/active-case` routes to Cloud Run (`deploy_paid_pilot.sh`) for Scenario A/B E2E on Preview.
3. **Persist** `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1` in Vercel Preview dashboard to prevent tab regression on future redeploys.

---

## FINAL URL FOR FOUNDER

**Open this URL now:**

https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

You will see the Customer First entry screen (phone + Continue). Full Continue → intake flow requires Cloud Run backend promotion (API returns 404 today).

---

*End of certification*
