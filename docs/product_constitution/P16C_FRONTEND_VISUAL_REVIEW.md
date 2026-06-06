# P16-C Phase 2 — Frontend Visual Review

**Date:** 2026-05-31  
**Commit tested:** `c2e3dff`  
**Method:** Local `vite preview` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` + browser accessibility snapshot/CDP  
**URL:** `http://127.0.0.1:4173/workbench/unified-intake`  
**Production baseline compared:** `https://ui-smoky-beta.vercel.app/workbench/unified-intake` (pre-Sprint A)

---

## Checklist Results

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Default tab = 办公室工作台 | ✅ PASS | Tab `办公室工作台` has `[selected]`; `document.title` = 加车报价试点 · 办公室工作台 |
| 2 | 客户报送 not first experience | ✅ PASS | User lands on broker tab without click; 客户报送 tab exists but not selected |
| 3 | 我的办理 hidden | ✅ PASS | `tabCount: 2` (客户报送 + 办公室工作台 only); no 我的办理 in DOM text |
| 4 | Simulation hidden | ✅ PASS | No 场景仿真 tab or button |
| 5 | Engineer chrome hidden | ✅ PASS | CDP: no PG, 镜像异常, 数据接口, 路由/指标 in body text |
| 6 | Wayfinding banner visible | ✅ PASS | `hasWayfinding: true` — 「经纪人：请在本页粘贴客户消息」 |
| 7 | Paste copy (raw WeChat/notice) | ✅ PASS | Placeholder: 原样粘贴微信/通知文字，不用整理 |
| 8 | First-request loading copy | ⚠️ CODE ONLY | String present in source; not triggered in static review (no paste submitted) |
| 9 | Inline 3 practice scenarios | ✅ PASS | Buttons: 取消/付款风险, 缺材料跟进, 加车报价 |
| 10 | Demo queue progress | ⚠️ NOT E2E | Button visible; progress string not observed (API/CORS blocked from localhost preview) |
| 11 | Demo queue auto-open cancellation | ⚠️ NOT E2E | Not verified live — queue load did not complete from preview origin |
| 12 | Simplified filters | ⚠️ CONDITIONAL | Implemented in code; Segmented renders only when queue has cases (`recentCases.length > 0`) — empty queue on first load |

**Pass: 8/12 fully verified | 4/12 code-only or blocked by empty queue / CORS**

---

## Residual Visual Issues (non-blocking but visible)

| Issue | Severity | Notes |
|-------|----------|-------|
| Tab suffix still says「加车旗舰路径 · 与客户报送同一服务记录」 | Medium | Constitution wedge is cancellation-first; copy lag |
| Header tagline still Add-Car oriented (`portal_brand_tagline`) | Medium | ui_copy not updated |
| 客户报送 tab still visible | Low | Acceptable per Sprint A spec (optional hide later) |
| Product intro collapsed by default | ✅ Good | 「显示产品说明」button present |
| Sidebar may still show lab routes if product_only not set | N/A locally | Verified product_only build hides simulation |

---

## Before / After (Production vs Sprint A local)

| Element | Before (Production) | After (Sprint A product_only) |
|---------|---------------------|-------------------------------|
| First tab | 客户报送 selected | 办公室工作台 selected |
| Tab count | 4 (含我的办理、场景仿真) | 2 |
| Paste area | Customer Add-Car entry | Broker paste + wayfinding |
| Engineer labels | Present on prod workbench (historical) | Absent in product_only build |
| Practice path | Simulation tab (hidden in prod product_only anyway — but prod lacks env) | Inline 3 scenarios |

---

## Broker Front Door Preview Score

**Method:** Weighted checklist (12 Sprint A contract items) + residual copy penalty

| Category | Score |
|----------|-------|
| Tab / navigation | 90 |
| Engineer chrome purge | 95 |
| Wayfinding + paste UX | 85 |
| Demo queue E2E | 40 (not verified remote) |
| Copy alignment (cancellation wedge) | 65 |
| **Overall Preview Score** | **72 / 100** |

**Interpretation:** Sprint A **likely moved** Front Door from ~35 toward ~70 target for **static product_only UX**, but **not proven** on Vercel Preview/Production. E2E demo queue and filter visibility need live API + populated queue.

**Target for GO:** ≥70 on **deployed Preview** with correct env — **not yet achieved on remote URL**.

---

*End of P16-C Phase 2 — Frontend Visual Review*
