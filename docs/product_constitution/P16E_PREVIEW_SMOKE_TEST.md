# P16-E Phase 4 — Preview Smoke Test

**Date:** 2026-05-31  
**Preview URL:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Method:** `vercel curl` (protection bypass) + JS bundle static analysis (`index-97qCgvUS.js`)  
**Limitation:** No authenticated browser DOM/CDP (Vercel SSO wall for raw browser)

---

## Checklist

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Page loads | ✅ PASS | `vercel curl` → HTTP 200 HTML, title「加车报价 · 统一报送」 |
| 2 | Product-only UI active | ✅ PASS | Bundle: wayfinding, product intro collapse, `!i&&` guards (productOnlyUi minified as `i`), no env var name in bundle |
| 3 | Default tab = 办公室工作台 | ⚠️ INFERRED | Source + P16-C local CDP; not DOM-verified on Preview |
| 4 | 客户报送 not first experience | ⚠️ INFERRED | product_only `resolveInitialTab` → `broker`; needs Andy browser |
| 5 | 我的办理 hidden | ⚠️ INFERRED | Tab render gated `showMyRequestsTab = !productOnlyUi`; string still in bundle (dead routes) |
| 6 | Simulation hidden | ⚠️ INFERRED | `showSimulationTab = !productOnlyUi` |
| 7 | PG/API/debug chrome hidden | ⚠️ INFERRED | `!productOnlyUi` guards; PG strings remain in bundle but gated |
| 8 | Wayfinding banner visible | ✅ PASS | Bundle: `经纪人：请在本页` |
| 9 | Paste copy improved | ✅ PASS | Bundle: `原样粘贴微信/通知文字，不用整理` |
| 10 | First-request loading copy | ✅ PASS | Bundle: `首次分析约30秒，请稍候…` |
| 11 | Inline 3 practice scenarios | ✅ PASS | Bundle: `取消/付款风险`, `缺材料跟进`, `加车报价` |
| 12 | Demo queue progress | ⚠️ PARTIAL | Bundle: `加载演示队列`; progress E2E not run on Preview |
| 13 | Simplified filters | ⚠️ PARTIAL | Bundle: `需今天处理`, `24小时内`; visible only when queue has cases |
| 14 | API base URL correct | ✅ PASS | Bundle: `fiqa-api-g7zatxrycq-uw.a.run.app` |
| 15 | No obvious build error | ✅ PASS | Vercel build Ready; no runtime bundle parse errors |

**Fully verified: 7/15 | Inferred from product_only build: 6/15 | Partial: 2/15**

---

## Comparison: Production vs this Preview

| Element | Production (`ui-smoky-beta`) | P16-E Preview |
|---------|------------------------------|---------------|
| Sprint A code | NO | YES (local Sprint A tree) |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | Not set | `1` (build flag) |
| Deployment Protection | Public (200) | SSO required (401 without auth) |
| Default tab | 客户报送 | Expected 办公室工作台 |

---

## Preview Front Door Score

| Category | Score |
|----------|-------|
| Deployed with correct build env | 95 |
| Bundle UX strings (wayfinding, paste, practice, loading) | 90 |
| Live DOM / tab default | 50 (blocked by SSO; inferred) |
| Demo queue E2E on Preview origin | 40 |
| Deploy purity (uncommitted `ui/` dirt) | 75 |
| Andy access friction (Vercel login) | 60 |

### **Preview Front Door Score: 76 / 100**

Up from P16-C local-only **72** (deployed + env baked), down from ideal **85** until Andy completes authenticated 5-minute walkthrough and demo queue loads against Cloud Run from Preview origin (CORS).

---

*End of P16-E Phase 4*
