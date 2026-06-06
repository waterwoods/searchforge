# P16-C Phase 2 — Before vs After Comparison

**Date:** 2026-05-31  
**Before baseline:** Production `https://ui-smoky-beta.vercel.app/workbench/unified-intake` (pre-Sprint A, no `VITE_UNIFIED_INTAKE_PRODUCT_ONLY`)  
**After baseline:** Local Sprint A `c2e3dff` + `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` @ `http://127.0.0.1:4174/workbench/unified-intake`  
**North Star test:** Can a broker understand and trust the product in under 5 minutes?

---

## Broker Front Door — Dimension Comparison

### Default tab

| | Before Sprint A | After Sprint A |
|--|-----------------|----------------|
| First selected tab | **客户报送** (Add-Car portal) | **办公室工作台** (broker paste) |
| Document title on load | 加车报价 · 客户统一报送 | 加车报价试点 · 办公室工作台 |
| Broker sees paste/triage first? | **No** — must discover 4th tab | **Yes** — immediate |
| Score | **15 / 100** | **92 / 100** |
| Δ | | **+77** |

**Why:** P10/P11 #1 Day-1 failure was wrong-tab landing. Sprint A A1 fixes the primary abandonment vector.

---

### Navigation clarity

| | Before | After |
|--|--------|-------|
| Tab count | 4 (客户报送, 我的办理, 办公室工作台, 场景仿真) | 2 (客户报送, 办公室工作台) |
| Sidebar lab routes | May appear without product_only env | Hidden |
| Primary path obvious? | Add-Car buttons dominate first screen | Paste + wayfinding dominate broker tab |
| Residual confusion | Simulation tab referenced in playbook but usable | Inline practice replaces Simulation |
| Score | **25 / 100** | **78 / 100** |
| Δ | | **+53** |

**Why:** Hiding 我的办理 + 场景仿真 removes dead-end tabs. Residual −22 points: tab labels and header still say 加车优先 / 加车旗舰路径.

---

### First action clarity

| | Before | After |
|--|--------|-------|
| Obvious first action | 「办理加车报价 推荐主路径」 on wrong tab | 「粘贴客户消息」 + 「开始整理」 on default tab |
| Wayfinding one-liner | Absent | 「经纪人：请在本页粘贴客户消息」 |
| Paste expectation | Add-Car structured form | 「原样粘贴微信/通知文字，不用整理」 |
| Training without founder | Requires Simulation tab (hidden in prod product_only) | Inline 3 practice scenarios |
| Score | **20 / 100** | **85 / 100** |
| Δ | | **+65** |

**Why:** Broker archetype (Chen Kui) cares about urgent paste, not Add-Car portal. After Sprint A the first action matches constitution wedge.

---

### Demo discoverability

| | Before | After |
|--|--------|-------|
| Demo queue button | On workbench tab (must find tab first) | Visible on default tab |
| Progress feedback | Silent 15–30s load | 「0/12 条示例已就绪」+ progress copy in UI |
| Auto-open cancellation | No | Designed — auto-open after load |
| E2E verified this session | N/A on prod default tab | ⚠️ CORS blocked on local preview |
| Score | **30 / 100** | **55 / 100** |
| Δ | | **+25** |

**Why:** UX affordances improved in code; score capped because demo queue not proven end-to-end on deployed Preview URL.

---

### Trust

| | Before | After |
|--|--------|-------|
| Engineer labels (PG 镜像, API URL) | Visible on production workbench | **Zero** in product_only |
| English next-step on cards | Present on prod | Not observed on empty local queue |
| "Beta / unfinished" signal | Strong | Greatly reduced |
| Network/CORS error on first load | Not observed on prod alias | **Risk** if Preview origin not allowlisted |
| Score | **35 / 100** | **80 / 100** |
| Δ | | **+45** |

**Why:** A2 chrome purge is the highest-trust ROI item. Deploy misconfiguration (CORS, missing env) can still destroy trust instantly.

---

### Noise level

| | Before | After |
|--|--------|-------|
| Engineer filters | 镜像异常, 旧识别, 测试, 正式 | Broker-only: 全部 / 需今天处理 / 24小时内 (when queue populated) |
| Extra tabs | 4 | 2 |
| Pilot intro | Expanded Add-Car wall | Collapsed; cancellation-first when expanded |
| Header Add-Car tagline | Prominent | **Still prominent** — residual noise |
| Score | **30 / 100** (high noise) | **75 / 100** |
| Δ | | **+45** |

**Why:** Tab and chrome noise cut dramatically. Brand copy still Add-Car-first costs ~25 points.

---

## Composite Broker Front Door Score

| Dimension | Weight | Before | After | Weighted Δ |
|-----------|--------|--------|-------|------------|
| Default tab | 25% | 15 | 92 | +19.3 |
| Navigation clarity | 15% | 25 | 78 | +8.0 |
| First action clarity | 20% | 20 | 85 | +13.0 |
| Demo discoverability | 15% | 30 | 55 | +3.8 |
| Trust | 15% | 35 | 80 | +6.8 |
| Noise level | 10% | 30 | 75 | +4.5 |
| **Weighted total** | 100% | **~24** | **~79** | **+55** |

**Constitution Cap 1 score (conservative, deploy-discounted):**

| | Score |
|--|-------|
| **Before Sprint A** | **35 / 100** (matches CAPABILITY_SCORECARD + contract §7) |
| **After Sprint A (local product_only, code verified)** | **68 / 100** |
| **After Sprint A (if Preview E2E PASS)** | **72–75 / 100** (projected) |
| **Net change (evidence-based)** | **+33** |

**Why 68 not 79:** Constitution scoring requires **deployed** broker-visible proof for demo queue, filters-with-data, and founder dry-run. Local-only + CORS block caps score at **Conditional**, not Target (75).

---

## Score Change Explanation (every delta)

1. **+33 overall Cap 1:** Default broker tab, chrome purge, wayfinding, paste copy, inline practice, tab reduction — all verified live.
2. **Not +40 to 75:** Demo queue E2E not verified on Preview; Add-Car copy remains in tab suffix + header; empty queue hides simplified filters.
3. **Trust +45 dimensionally but capped:** One visible Network Error on misconfigured origin would revert Day-1 trust — seen locally.
4. **Demo +25 only:** Progress UI exists; auto-open cancellation not observed this session.
5. **Navigation +53 not +70:** 客户报送 tab still invites wrong-tab click for unsupervised brokers.

---

## Before / After Snapshot Table

| Element | Before (Production) | After (Sprint A product_only) |
|---------|---------------------|-------------------------------|
| Default tab | 客户报送 | 办公室工作台 ✅ |
| Tab count | 4 | 2 ✅ |
| Simulation | Visible tab | Hidden; inline practice ✅ |
| Wayfinding | None | Broker banner ✅ |
| PG/API/debug | On workbench | Hidden ✅ |
| First paste CTA | Hidden behind tab | Immediate ✅ |
| Add-Car story | Dominant | Secondary but still in labels ⚠️ |
| Unsupervised Day 1 (P11) | ~28/100 | ~71 simulated (see P16C_SIMULATION_REPORT.md) |

---

*End of P16-C Phase 2 — Before vs After Comparison*
