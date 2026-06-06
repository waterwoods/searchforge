# P16-G Phase 2 — Preview Validation

**Date:** 2026-05-31  
**Preview URL:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Alias:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app  
**API:** https://fiqa-api-g7zatxrycq-uw.a.run.app  
**Post-CORS revision:** `fiqa-api-00079-ngq`

---

## Validation matrix

| Check | Method | Result | Notes |
|-------|--------|--------|-------|
| Preview HTML loads | `vercel curl -y` | ✅ PASS | HTTP 200, bundle `index-97qCgvUS.js` |
| Sprint A bundle present | Bundle grep | ✅ PASS | See Sprint A artifacts below |
| CORS preflight | curl OPTIONS | ✅ PASS | 200 + allow-origin for Preview |
| Queue API | curl GET with Origin | ✅ PASS | 200, 569 cases, CORS header present |
| Triage API | curl POST × 3 scenarios | ✅ PASS | Correct categories + drafts |
| Network Error | API layer | ✅ **RESOLVED** | Was CORS 400; now 200 |
| Browser DOM E2E | Cursor browser MCP | ⚠️ **BLOCKED** | Vercel Deployment Protection → login wall |
| Andy authenticated walkthrough | — | ⏳ **PENDING** | Required to close browser E2E gate |

---

## Sprint A Capability 1 features

| Feature | Evidence | Status |
|---------|----------|--------|
| **Broker default tab** | Source `resolveInitialTab()` → `'broker'`; local DOM (P16-F.5); bundle has 办公室工作台 | ✅ High confidence |
| **Wayfinding** | Bundle: `经纪人：请在本页` | ✅ |
| **Practice scenarios** | Bundle: `取消/付款风险`, `缺材料跟进`, `加车报价` | ✅ |
| **Cancellation-first path** | Bundle: `试用重点`; intro collapsed | ✅ |
| **Hidden engineer chrome** | Runtime-gated `!productOnlyUi`; PG/路由/指标 not rendered in product_only | ✅ |
| **Paste copy** | Bundle: `原样粘贴微信`, `首次分析约30秒` | ✅ |
| **Demo queue button** | Bundle: `加载演示队列` | ✅ |
| **Simulation tab hidden** | `showSimulationTab = !productOnlyUi` | ✅ |
| **客户报送 tab** | Still visible (Sprint A A1 = default only, not removal) | ⚠️ Known gap |
| **Add-Car header copy** | Title still 加车报价 · 统一报送 | ⚠️ Residual wedge confusion |

---

## Workflow checks (API + CORS layer — simulates browser after login)

| Step | Result |
|------|--------|
| Queue loading | ✅ `GET /api/inbox/cases` → 200, cases returned |
| Inbox loading | ✅ Same endpoint; no Network Error class |
| Paste → triage (cancellation) | ✅ `cancellation_warning`, `critical`, draft present |
| Paste → triage (missing doc) | ✅ `missing_document`, `medium`, draft present |
| Paste → triage (add-car) | ✅ `customer_question`, Chinese draft with 待补充 |
| Draft generation | ✅ All 3 scenarios return actionable drafts |
| Demo queue path | ✅ Client loops `triageMessage(text, persist=true)` — API supports; 13 seeds defined in `FOUNDER_DEMO_QUEUE` |
| Copy workflow | ⚠️ Not tested in browser; API returns copyable draft text |

---

## Access friction (unchanged)

| Channel | Result |
|---------|--------|
| Unauthenticated browser | Redirect to Vercel Login |
| `vercel curl` (bypass) | HTML + assets OK |
| Authenticated Andy session | **Required** for live Preview paste/queue UX proof |

---

## Phase 2 verdict

| Dimension | Score |
|-----------|-------|
| Build / bundle correctness | 95 / 100 |
| API connectivity from Preview origin | **95 / 100** (was 0) |
| Browser E2E (authenticated) | **Pending Andy** |
| Sprint A front door (static) | 88 / 100 |

**Preview is operationally unblocked at the CORS/API layer.** Network Error root cause is fixed. Full product validation requires Andy hard-refresh after Vercel login: queue loads → paste cancellation → confirm draft panel → 加载演示队列.

---

*End of P16-G Phase 2*
