# P16-C Phase 3 — AI Simulation Review

**Date:** 2026-05-31  
**Input:** Sprint A code (`c2e3dff`), local product_only visual review, Cloud Run triage smoke, P15 Founder Review blockers  
**Method:** Structured persona simulation (5-minute first session each)

---

## Persona 1 — Chen Kui (Broker Owner)

**Profile:** Busy broker owner; cares about time saved, not technical labels; evaluates whether to pay $49–99 after 7 days.

### First 5 Minutes (simulated journey)

1. **0:00** — Opens trial URL. **Before Sprint A:** lands on 客户报送, confused. **After Sprint A (product_only):** lands on 办公室工作台 — immediate orientation win.
2. **0:30** — Sees wayfinding banner + paste box. Understands: paste WeChat text here. Trust improves vs hidden Simulation tab.
3. **1:00** — Clicks「加载演示队列」. **Risk:** if API/CORS fails, sees empty queue → feels broken (Day 1 killer if deploy misconfigured).
4. **3:00** — If demo loads: cancellation case opens, sees 下一步 + draft → **first value moment** (constitution wedge).
5. **5:00** — Can paste real message or use inline「取消/付款风险」practice. Still sees Add-Car tab suffix — minor cognitive dissonance.

### Scores (0–5 each → ×20 for /100)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Clarity | 4 | Tab + banner clear; tab suffix still Add-Car flavored |
| Trust | 3.5 | Engineer chrome gone; API errors/CORS would destroy trust |
| Speed to value | 3.5 | Demo path designed well; not proven on Vercel |
| Confusion | 2 (lower better → invert: 3/5 clarity inverse) | |
| Likelihood to continue | 4 | Much better than 28/100 unsupervised baseline |

**Chen Kui composite: 71 / 100** (up from ~28 unsupervised pre-Sprint A)

---

## Persona 2 — Office Assistant

**Profile:** Processes 50+ messages/day; needs queue, next action, fewer repeated questions.

### First 5 Minutes

1. **0:00** — Same entry as broker (workbench default) — good for shared workflow.
2. **1:00** — Queue filters (全部 / 需今天处理 / 24小时内) match assistant mental model **when queue populated**.
3. **2:00** — Opens case → broker_next_step preview on cards helps scan queue.
4. **4:00** — Missing: prominent「更新客户新消息」 (Sprint C / P1 item) — still buried.
5. **5:00** — Would use paste + 开始整理 for new messages; loading copy helps patience on first triage.

### Scores

| Dimension | Score (/5) |
|-----------|------------|
| Clarity | 4 |
| Trust | 3.5 |
| Speed to value | 3 |
| Confusion | 3.5 (moderate) |
| Likelihood to continue | 3.5 |

**Assistant composite: 68 / 100**

---

## Persona 3 — End Customer (Indirect)

**Profile:** Sends messy WeChat messages; does not use workbench — experiences broker replies only.

### First 5 Minutes (customer does not see UI)

Customer sends cancellation notice → broker uses workbench → customer receives improved draft.

| Dimension | Score (/5) | Notes |
|-----------|------------|-------|
| Clarity (of broker reply) | 4 | Cancellation draft in Chinese is usable (API smoke) |
| Trust | 4 | Broker responds faster with structure |
| Speed to value | 4 | If broker finds tool in 5 min |
| Confusion | 4 | Customer unaware of tool — depends on broker |
| Likelihood to continue | 4 | Indirect |

**Customer indirect composite: 80 / 100** (tool impact on customer experience, assuming broker adopts)

---

## Aggregate AI Simulation Score

| Persona | Weight | Score |
|---------|--------|-------|
| Chen Kui | 50% | 71 |
| Assistant | 30% | 68 |
| Customer (indirect) | 20% | 80 |
| **Weighted average** | | **72 / 100** |

**Threshold for GO:** ≥70 — **met on simulation**, contingent on deployed Preview with working API.

---

## TOP_20_CONFUSIONS_REMAINING

1. Tab suffix still mentions 加车旗舰路径
2. Header tagline Add-Car-first (`portal_brand_tagline`)
3. 客户报送 tab still visible — may click wrong tab
4. Empty queue on first load — no visible filters until cases exist
5. Demo queue fails silently if CORS/API misconfigured
6.「case」/ English in some API draft paths (payment failed → English draft)
7. Address change triage returns `unclear` category
8. Add-car misclassified as `customer_question` sometimes
9. No visible pricing / trial terms (Sprint B)
10. No persistence disclaimer if not on Postgres prod
11. 服务记录编号 monospace noise on cards
12. Follow-up actions buried in case detail scroll
13.「管理」hidden in product_only — good, but no admin path documented for founder
14. Multiple tabs still say「加车优先」in customer tab label
15. Product intro when expanded still mixed messaging
16. First paste 30s wait without backend warm — needs live `/readyz` gate
17. No mobile-optimized paste UX called out in terms
18. WeChat sync still implied by some archived docs (not UI)
19. Queue pagination — filters only on current page
20. No time-saved measurement in UI (observation log external)

---

## TOP_20_IMPROVEMENTS_AFTER_SPRINT_A

1. ✅ Default broker tab
2. ✅ Hide Simulation + 我的办理 in product_only
3. ✅ Engineer chrome hidden (PG, API, 路由/指标, engineer filters)
4. ✅ Wayfinding banner
5. ✅ Paste expectation copy
6. ✅ Loading / warmup messaging
7. ✅ Inline 3 practice scenarios
8. ✅ Demo queue progress UI (code)
9. ✅ Cancellation auto-open logic (code)
10. ✅ Simplified filter options (when queue loaded)
11. ✅ Pilot intro collapsed default + cancellation-first intro text
12. ⏳ Vercel Preview with product_only env
13. ⏳ Tab suffix / brand copy alignment (cancellation wedge)
14. ⏳ E2E demo queue on deployed Preview
15. ⏳ CORS allowlist for Preview URLs
16. — Sprint B pricing on one-pager
17. — Sprint B pilot terms
18. — Prod Postgres validation
19. — Draft quality fix-now from trial
20. — 更新客户新消息 prominence (Sprint C)

---

## TOP_10_BLOCKERS_BEFORE_CHEN_KUI

| # | Blocker | Sprint A addressed? |
|---|---------|---------------------|
| 1 | No deployed Preview with Sprint A + product_only | **NO** — P0 |
| 2 | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not on Vercel | **NO** — P0 |
| 3 | Demo queue E2E not verified on remote URL | **NO** — P0 |
| 4 | No proven time savings (7-day trial) | NO — execution |
| 5 | Production not validated (Postgres, `/readyz`) | NO — Cap 7 parallel |
| 6 | Pricing / terms / invoice missing | NO — Sprint B |
| 7 | Draft quality on real messages (payment English draft) | Partial — engine |
| 8 | Add-Car vs cancellation copy split in tab labels | Partial |
| 9 | CORS may block Preview origins | **Risk** — P0 deploy |
| 10 | Founder dry-run not yet executed on Preview | **NO** — Andy gate |

---

*End of P16-C Phase 3 — AI Simulation Review*
