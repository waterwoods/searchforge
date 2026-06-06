# P16-F.5 Phase 2 — Preview Environment Report

**Date:** 2026-05-31  
**Preview URL:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Deployment ID:** `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN`  
**Method:** `vercel curl` (protection bypass) + JS bundle static analysis + local product_only DOM walkthrough (`index-97qCgvUS.js` bundle parity)

---

## Environment checklist

| Variable / target | Expected | Actual | Status |
|-------------------|----------|--------|--------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `1` | Baked at deploy via `-b` flag; env name dead-code-eliminated in bundle | ✅ |
| `VITE_API_BASE_URL` | Cloud Run HTTPS URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` in bundle | ✅ |
| Cloud Run target | `fiqa-api-g7zatxrycq-uw.a.run.app` | Matches | ✅ |
| Workbench route | `/workbench/unified-intake` | HTML 200 via `vercel curl` | ✅ |
| Vercel dashboard env | Persisted Preview vars | **Not set** — build flags only at CLI deploy time | ⚠️ |
| Deployment Protection | — | SSO required for browser (401 without auth) | ⚠️ |
| Preview → API CORS | Origin allowlisted | **FAIL** — origin not in `ALLOWED_ORIGINS` | ❌ |

---

## Sprint A code presence (bundle evidence)

| Sprint A artifact | In Preview bundle? |
|-------------------|-------------------|
| `经纪人：请在本页` (wayfinding) | ✅ |
| `原样粘贴微信/通知文字，不用整理` | ✅ |
| `首次分析约30秒，请稍候…` | ✅ |
| `试用重点` (cancellation-first intro) | ✅ |
| `显示产品说明` (collapsed intro) | ✅ |
| Inline practice: `取消/付款风险`, `缺材料跟进`, `加车报价` | ✅ |
| `正在加载` (demo queue progress strings) | ✅ |
| `fiqa-api-g7zatxrycq-uw.a.run.app` | ✅ |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` string | ❌ absent (expected Vite DCE) |
| Dead-code strings (`场景仿真`, `我的办理`, `路由/指标`) | Present in bundle but **runtime-gated** by `productOnlyUi` |

**Verdict:** This **is** Sprint A product_only code on Preview — not Production stale deploy.

---

## Required answers

### 1. Is broker tab default?

**YES (high confidence).** Source: `resolveInitialTab()` returns `'broker'` when `productOnlyUi` is true. Local product_only build DOM confirms **办公室工作台** tab selected on load without click. Preview DOM not verified (Vercel SSO blocks automation); bundle + source align with P16-E/P16-C local CDP.

### 2. Are engineer tags hidden?

**YES at runtime in product_only.** `BrokerWorkbenchTab.tsx` gates PG mirror tags, 路由/指标, API URL, engineer filters behind `!productOnlyUi`. Bundle still contains engineer strings (tree-shaking does not remove all branches) — **hidden in UI, not removed from bundle**.

### 3. Is simulation hidden?

**YES.** `showSimulationTab = !productOnlyUi` — Simulation tab not rendered. Local DOM shows **2 tabs only** (客户报送, 办公室工作台). `场景仿真` string remains in bundle as dead code.

### 4. Is customer tab hidden?

**NO.** Customer tab (**客户报送**) remains visible in product_only. Sprint A A1 fixed **default tab**, not tab removal. Wrong-tab exploration risk persists (~P16-E confusion #4).

### 5. Does cancellation-first onboarding appear?

**YES.** `TRIAL_PILOT_INTRO` replaces Add-Car-first `PILOT_INTRO` when product_only: copy mentions 取消/付款风险, 缺材料, 加车报价. Intro collapsed by default with **显示产品说明** link. Residual: tab suffixes and header tagline still Add-Car flavored.

### 6. Is this really Sprint A code?

**YES.** Bundle contains Sprint A UX strings; deploy used P16-E flags; Production (`ui-smoky-beta`) unchanged and lacks these strings. Caveat: P16-E noted **5 uncommitted `ui/` files** in uploaded tree — small unknown delta vs git `c92cabf`.

---

## Access friction

| Channel | Result |
|---------|--------|
| Browser (unauthenticated) | Redirect to Vercel Login |
| `vercel curl` | HTML + assets OK |
| Cursor IDE browser MCP | Blocked at Vercel SSO |
| Andy authenticated session | Required for live Preview walkthrough |

---

## Preview vs local product_only parity

Local build (`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `index-97qCgvUS.js` equivalent) at `http://127.0.0.1:4174`:

- Document title: **加车报价试点 · 办公室工作台** ✅
- Default tab: 办公室工作台 ✅
- Paste placeholder: 原样粘贴微信… ✅
- Practice scenario buttons visible ✅
- API calls: **blocked** — localhost preview origin not in backend `ALLOWED_ORIGINS` (same class of failure as Preview)

---

## Phase 2 verdict

| Dimension | Score |
|-----------|-------|
| Build env correctness | 95 / 100 |
| Sprint A code deployed | 90 / 100 |
| Live Preview functional (API) | **0 / 100** (CORS) |
| Andy/broker access | 55 / 100 (SSO + CORS) |

**Preview environment is correctly configured at build time but operationally blocked at runtime by CORS.**

---

*End of P16-F.5 Phase 2*
