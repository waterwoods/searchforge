# P16-H Final Verdict

**Date:** 2026-05-31  
**Sprint:** P16-H — Founder Real Usage + UI Simplicity Review  
**Constraint:** No features built. No Constitution changes. No Capability 8.  
**Evidence:** Phases 1–7 in this sprint; P16-G deployment validation; local API + product_only UI audit

---

## 1. Is the UI too complicated?

**Yes.**

Not because the triage engine is complex — it isn't. The UI is too complicated because **two products share one URL**, **Add-Car copy dominates a cancellation-first trial**, and **case detail exposes CRM/lab surfaces** that Chen Kui will never use in Week 1.

Sprint A fixed the **front door mechanism** (correct tab, hidden engineer chrome, wayfinding). It did **not** fix the **front door story** or **information architecture**.

| Lens | Score |
|------|-------|
| Engine / triage | 85–90 |
| Front door mechanism (Sprint A) | 72 |
| **UI simplicity (this sprint)** | **58** |
| Professional SaaS benchmark | 44 |

**Brutal truth:** Andy can demo this. Chen Kui cannot adopt it alone yet.

---

## 2. What percentage can be removed?

| Surface | Removable without losing trial value |
|---------|--------------------------------------|
| Customer tab (trial mode) | 100% of tab (hide) |
| Customer empty state chrome | ~70% of elements |
| Workbench landing | ~40% (merge cards, dedupe copy) |
| Case detail | ~50% (CRM, collapses, second copy button) |
| Global chrome | ~30% (suffixes, intro tags, wrong tagline) |
| **Overall visible UI** | **~35–40%** |

This is **not** repo cleanup or lab deletion — it is **conditional hide/collapse in product_only** plus **ui_copy.json alignment**.

Removing 35% would raise simplicity score from **58 → ~75** (estimated).

---

## 3. What should happen BEFORE Chen Kui trial?

| Priority | Action | Owner | Blocks |
|----------|--------|-------|--------|
| P0 | Ship **Top 8 deletions** (tab suffixes, Add-Car tagline, hide 客户报送 tab, single copy button, collapse case detail) | Eng | Day 1 confusion |
| P0 | **ui_copy.json** cancellation-first pass (header, titles, empty states) | Eng + Founder | Story trust |
| P0 | **Andy authenticated browser E2E** on preview/production URL | Founder | P16-G open gate |
| P0 | **Commercial pack** ($49/$99, terms, invoice) | Founder | Payment |
| P1 | Promote **追加客户补充** adjacent to draft | Eng | Follow-up friction |
| P1 | Paste **above fold** (reorder workbench layout) | Eng | 10-second fail |
| P1 | Production deploy Sprint A bundle (stable URL, no Vercel SSO for broker) | Founder/Eng | Access |
| P1 | Ratify **Contract Simplicity Amendments** (Cap 1 + 4 §6) | Founder | Sprint closure |
| P2 | Supervised **Day 0 kickoff** scheduled with observation log | Founder | Trial proof |

**Do not start Chen Kui unsupervised trial until P0 complete.**

---

## 4. What should happen AFTER Chen Kui trial?

| Timing | Action |
|--------|--------|
| Week 1 trial | Fix-now queue from observation log only — no feature expansion |
| If payment yes | Customer portal hybrid (message-first) for end-customer GTM |
| If payment no | Kill or continue based on **minutes saved** evidence — not UI polish for its own sake |
| Week 2+ | Re-enable CRM fields (status, waiting_on) if assistant adopts |
| Deferred | Attachment upload, WeChat identity strip, record summary rail simplification |
| Never (v1) | New tabs, Stripe, inbox sync, Capability 8 |

---

## 5. What is the highest ROI simplification?

**Hide 客户报送 tab + replace Add-Car tagline with one cancellation-first sentence.**

Cost: ~2 hours. Risk: Low. Impact: Fixes 10-second test, dual-product confusion, and Chen Kui wrong-door abandonment — the #1, #2, and #9 problems in the First 10 Seconds Audit.

Second highest ROI: **One copy button (draft only) + collapse Case 整理明细** — makes the payoff obvious after paste.

---

## TOP 20 Simplification Actions

Ranked. Deletions only. No new features.

| # | Action | ROI | Risk | Est. |
|---|--------|-----|------|------|
| 1 | Hide **客户报送** tab in product_only trial | Critical | Low | 1h |
| 2 | Replace **portal_brand_tagline** + hero titles with cancellation-first copy | Critical | Low | 2h |
| 3 | Remove **tab suffix subtitles** | Critical | Low | 30m |
| 4 | Move **paste textarea above fold** (before demo/practice cards) | Critical | Medium | 3h |
| 5 | Merge **练习场景** into **加载演示队列** card | High | Low | 2h |
| 6 | Hide **返回工作台** in product_only header | High | Low | 30m |
| 7 | Hide **复制摘要**; keep **复制客户草稿** only | High | Low | 1h |
| 8 | Collapse **Case 整理明细** by default; rename English "Case" | High | Low | 2h |
| 9 | Hide **status radio** from default case view | High | Medium | 2h |
| 10 | Dedupe trust lines to **one**「不自动发送 · 手动粘贴」 | High | Low | 1h |
| 11 | Hide **IntakeFlowStepTrack** on customer empty state | High | Medium | 2h |
| 12 | Hide **6 category buttons** until after first message (if tab kept) | High | Medium | 4h |
| 13 | Promote **追加客户补充** next to draft block | High | Medium | 3h |
| 14 | Simplify queue cards to **urgency + one-line preview** | High | Medium | 4h |
| 15 | Hide **follow-up CRM** fields in product_only | High | Medium | 2h |
| 16 | Remove pilot intro **tag wall**; one trust line | Medium | Low | 1h |
| 17 | Hide **founderQueue N/13** tag after load | Low | Low | 30m |
| 18 | Collapse **conversation thread** by default on case detail | Medium | Low | 1h |
| 19 | Align **document.title** to 办公室工作台 (remove Add-Car) | Medium | Low | 30m |
| 20 | Add Cap 1/4 **simplicity acceptance criteria** to contracts | High | Low | 1h doc |

**Total engineering (items 1–19):** ~30 hours (~4 days) — fits Week 1 deletion sprint, not feature sprint.

---

## Capability Impact (Post-Simplification Estimate)

| Capability | P16-G | After Top 20 deletions | Notes |
|------------|-------|------------------------|-------|
| 1 Broker Front Door | 70 | **78** | Story + density |
| 4 Customer Intake | 62 | **72** | Hidden or message-first |
| 3 Case Record | 72 | **78** | Draft prominence |
| 5 Case Lifecycle | 55 | **62** | Simpler queue |
| **Overall product** | 68 | **~74** | Still below 80 until trial proof |

---

## What P16-H Did NOT Do

- Did not change Constitution  
- Did not create Capability 8  
- Did not build features  
- Did not run authenticated Preview browser (localhost isolation) — relied on API + code + P16-C/P16-G  

---

## ONE LINE VERDICT

**The engine is trial-ready; the UI still sells Add-Car while Chen Kui buys cancellation — delete 35% of what brokers see, hide the customer tab, and paste becomes a product.**

---

*End of P16-H Final Verdict*
