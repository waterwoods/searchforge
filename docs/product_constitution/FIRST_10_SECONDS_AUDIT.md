# P16-H Phase 3 — First 10 Seconds Audit

**Date:** 2026-05-31  
**Persona:** Cold arrival — no training, no founder, no documentation  
**URL:** `/workbench/unified-intake` (product_only)  
**Method:** DOM/copy audit + P16-C snapshot evidence + founder walkthrough synthesis

---

## Within 10 Seconds — Can They Know?

| Question | Answer | Confidence |
|----------|--------|------------|
| **What this product is?** | ⚠️ Partial — sees「金盾保险 · 陈魁团队」and insurance branding, but tagline says「加车报价为当前旗舰流程」— sounds like Add-Car portal, not intake triage | Low |
| **Who it is for?** | ⚠️ Ambiguous — avatar says Chen Kui team; could be customer or broker. Tab「客户报送」suggests customer; tab「办公室工作台」suggests broker | Low |
| **What button to click?** | ❌ No — two tabs of equal weight; no single hero CTA. If broker tab selected: paste area is below fold after 3 cards | Fail |
| **What success looks like?** | ❌ No — no visual of "paste → draft → copy to WeChat" in first viewport. Demo queue button exists but purpose unclear without label context | Fail |

**10-second pass rate: 1 / 4** (partial product identity only)

---

## First Viewport Inventory (Broker Tab, 1440×900)

What a cold user sees without scrolling:

1. Dark app header:「金盾·陈魁团队 · 客户统一受理」+ **返回工作台** link (dead end in product_only)
2. White card: Chen Kui avatar +「加车报价为当前旗舰流程」
3. Two large tabs with long suffix subtitles
4. Left column: **快速体验** card with **加载演示队列**
5. Right column top: **办公室工作台** title + 2 subtitle lines
6. Blue info alert: wayfinding (good — but 4th block)
7. **练习场景** card (partially visible)
8. Paste textarea — **below fold**

**First actionable control above fold:** 加载演示队列 OR tab switch — not paste.

---

## TOP 30 First Impression Problems

Ranked by impact on cold-user comprehension and conversion.

| # | Problem | Severity | Screen |
|---|---------|----------|--------|
| 1 | **Two equal-weight tabs** — no clear "start here" | Critical | Global |
| 2 | **Add-Car tagline** on header contradicts product purpose | Critical | Global |
| 3 | **Paste area below fold** — primary action not visible in 10s | Critical | Workbench |
| 4 | **No hero sentence** explaining paste → draft → send loop | Critical | Workbench |
| 5 | **「加车报价 · 客户统一报送」** document title on customer tab leaks via tab label | High | Global |
| 6 | **返回工作台** link visible but routes nowhere useful in product_only | High | Header |
| 7 | Tab suffix text** — 加车优先 / 加车旗舰路径** — noise in peripheral vision | High | Global |
| 8 | **Three onboarding cards** before paste (demo, wayfinding, practice) | High | Workbench |
| 9 | **客户报送 tab visible** — cold user may click wrong door | High | Global |
| 10 | **No screenshot/mock** of success state (draft card) | High | Workbench |
| 11 | **English "Unified Intake"** in sidebar when sidebar visible (dev builds) | Medium | Chrome |
| 12 | **Dark header + light island** — feels like dev shell wrapping product | Medium | Global |
| 13 | **Chen Kui avatar** — implies logged-in/account; no login exists | Medium | Global |
| 14 | **加载演示队列** without "or paste real message" equal prominence | Medium | Workbench |
| 15 | **练习场景** sounds like training software, not production tool | Medium | Workbench |
| 16 | **显示产品说明** link — implies product needs explanation | Medium | Global |
| 17 | Customer tab hero: **6 category buttons** — instant overwhelm if mis-clicked | High | Customer |
| 18 | Customer tab: **IntakeFlowStepTrack** before any input | High | Customer |
| 19 | Customer tab: **structured form** visible in collapse label | Medium | Customer |
| 20 | **Empty queue** left column — large dead space on first visit | Medium | Workbench |
| 21 | **No pricing/value** hint — "why am I here?" | Medium | Global |
| 22 | **No "不自动发送"** trust line above fold on workbench (only in collapsed intro) | Medium | Workbench |
| 23 | **Font size hierarchy weak** — everything 12–14px secondary gray | Low | Workbench |
| 24 | **Sticky left queue** steals horizontal space on laptop | Medium | Workbench |
| 25 | **服务记录队列** jargon — not "inbox" or "待处理" | Medium | Queue |
| 26 | **Case ID monospace** visible early — engineer signal | Low | Detail |
| 27 | **双 copy buttons** — decision paralysis when case open | Medium | Detail |
| 28 | **Status radio** looks like required action | Medium | Detail |
| 29 | **Mobile: paste area** even further below fold | High | Workbench |
| 30 | **Vercel SSO** on preview URL — product never loads for cold user | Critical | Deploy |

---

## 10-Second Fix Cluster (Not building — identification only)

If only 3 things could change for first impression:

1. **Single sentence hero** above paste: 「粘贴客户微信消息 → 系统整理 → 您复制草稿发出」
2. **Hide 客户报送 tab** in trial product_only
3. **Move paste textarea to top** of workbench — queue below

---

## Cold User Personas

| Persona | 10s outcome | Likely action |
|---------|-------------|---------------|
| Chen Kui (broker) | Confused by Add-Car branding | Clicks 客户报送 or closes tab |
| Office assistant | Finds paste eventually | Needs Andy to point |
| End customer (wrong URL) | Overwhelmed by categories | Abandons |
| Investor/demo guest | Thinks it's Add-Car SaaS | Wrong pitch |

---

*End of P16-H Phase 3 — First 10 Seconds Audit*
