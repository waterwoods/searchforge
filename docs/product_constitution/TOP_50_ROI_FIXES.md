# Top 50 ROI Fixes — P15

**Version:** P15  
**Date:** 2026-05-31  
**Formula:** `ROI Score = (Business Impact × Trial Impact × Frequency) ÷ Effort`

**Scale (1–5 each dimension):**

| Dimension | 5 | 3 | 1 |
|-----------|---|---|---|
| Business Impact | Direct payment / Day 1 survival | Workflow improvement | Polish |
| Trial Impact | Chen Kui Day 0–7 blocker | Important but not blocking | Nice-to-have |
| Frequency | Every session / every broker | Weekly / kickoff | Rare edge |
| Effort | Hours (denominator) | — | — |

Higher score = higher priority. Constitution-locked items (Stripe, sync, CRM) **excluded**.

---

## Top 10

| Rank | Fix | Cap | BI | TI | F | Effort (h) | ROI | Priority |
|------|-----|-----|----|----|---|------------|-----|----------|
| 1 | Default trial URL to 办公室工作台 (`?tab=broker`) | 1 | 5 | 5 | 5 | 2 | **62.5** | P0 |
| 2 | Hide PG mirror tags in product_only | 1 | 5 | 5 | 5 | 2 | **62.5** | P0 |
| 3 | Hide API endpoint / 数据接口 in product_only | 1 | 5 | 5 | 5 | 2 | **62.5** | P0 |
| 4 | One-line wayfinding banner | 1 | 5 | 5 | 5 | 1 | **125.0** | P0 |
| 5 | Hide 路由/指标 debug tag in product_only | 1 | 5 | 5 | 4 | 1 | **100.0** | P0 |
| 6 | Add $49/$99 to BROKER_ONE_PAGER | 6 | 5 | 5 | 3 | 1 | **75.0** | P0 |
| 7 | Auto-open cancellation after demo queue load | 1 | 5 | 5 | 4 | 2 | **50.0** | P1 |
| 8 | First-request loading: "首次分析约30秒" | 2/4 | 5 | 5 | 4 | 2 | **50.0** | P1 |
| 9 | validate + deploy prod + `/readyz` green | 7 | 5 | 5 | 3 | 4 | **18.8** | P0 |
| 10 | 30-min founder kickoff before Day 1 alone | 6 | 5 | 5 | 2 | 0.5 | **100.0** | P0 |

---

## Top 11–20

| Rank | Fix | Cap | BI | TI | F | Effort (h) | ROI | Priority |
|------|-----|-----|----|----|---|------------|-----|----------|
| 11 | Demo queue progress indicator (3/13…) | 1 | 4 | 5 | 4 | 3 | **26.7** | P1 |
| 12 | Paste copy: "原样粘贴微信/通知文字，不用整理" | 4 | 4 | 5 | 5 | 1 | **100.0** | P1 |
| 13 | Formal broker UX launch checklist (two-gate) | 7 | 5 | 5 | 2 | 3 | **16.7** | P0 |
| 14 | 1-page pilot terms (Chinese) | 6 | 5 | 5 | 2 | 4 | **12.5** | P0 |
| 15 | Invoice template (WeChat/PDF) | 6 | 5 | 4 | 2 | 2 | **20.0** | P0 |
| 16 | Inline 3 practice scenarios (replace Simulation) | 1 | 4 | 5 | 3 | 8 | **7.5** | P1 |
| 17 | Update playbook — remove Simulation dependency | 6/7 | 4 | 5 | 3 | 1 | **60.0** | P1 |
| 18 | Remove SIM1–SIM3 from broker-facing materials | 7 | 4 | 4 | 3 | 1 | **48.0** | P1 |
| 19 | Explicit manual-paste expectation (anti–WeChat-sync) | 4 | 4 | 5 | 4 | 1 | **80.0** | P1 |
| 20 | Founder dry-run with observation log | 7 | 4 | 5 | 2 | 2 | **20.0** | P1 |

---

## Top 21–30

| Rank | Fix | Cap | BI | TI | F | Effort (h) | ROI | Priority |
|------|-----|-----|----|----|---|------------|-----|----------|
| 21 | Observation log "minutes saved" field | 6 | 4 | 5 | 3 | 1 | **60.0** | P1 |
| 22 | Simplify queue filters (broker-facing) | 5 | 3 | 4 | 4 | 4 | **12.0** | P1 |
| 23 | Reconcile Add-Car banner → cancellation-first trial | 1/4 | 4 | 4 | 4 | 2 | **32.0** | P1 |
| 24 | Graceful 503/warming message on first paste | 2/7 | 4 | 5 | 3 | 3 | **20.0** | P1 |
| 25 | Highlight 更新客户新消息 on case detail | 4/5 | 3 | 4 | 4 | 2 | **24.0** | P1 |
| 26 | Collapse pilot intro alert by default | 1 | 3 | 4 | 4 | 2 | **24.0** | P2 |
| 27 | Draft copy button: 复制到微信（请先修改） | 3 | 3 | 4 | 4 | 1 | **48.0** | P2 |
| 28 | Promote 复制案例快照 in support materials | 3/7 | 3 | 3 | 3 | 1 | **27.0** | P2 |
| 29 | Replace "case" with 服务记录 in broker strings | 1/3 | 3 | 3 | 5 | 4 | **11.3** | P2 |
| 30 | 15-min assistant training script | 5/6 | 3 | 4 | 2 | 2 | **12.0** | P2 |

---

## Top 31–40

| Rank | Fix | Cap | BI | TI | F | Effort (h) | ROI | Priority |
|------|-----|-----|----|----|---|------------|-----|----------|
| 31 | Hide 我的办理 tab in broker trial mode | 1/5 | 3 | 3 | 3 | 3 | **9.0** | P2 |
| 32 | State data retention in pilot terms | 6 | 3 | 4 | 2 | 0.5 | **48.0** | P2 |
| 33 | L1 support doc + 24h response in terms | 7 | 3 | 4 | 2 | 2 | **12.0** | P2 |
| 34 | Deprecate stale RAG goal doc for agents | 7 | 2 | 3 | 4 | 1 | **24.0** | P1 |
| 35 | Apply CUSTOMER_LANGUAGE_GUIDE in triage→UI mapping | 2 | 3 | 3 | 4 | 4 | **9.0** | P1 |
| 36 | Reduce queue card tags (max 3 + expand) | 5 | 3 | 3 | 4 | 4 | **9.0** | P2 |
| 37 | Empty queue 3-step onboarding | 4 | 3 | 4 | 3 | 4 | **9.0** | P2 |
| 38 | Footer: 支持微信 · 不自动发送 | 1 | 3 | 3 | 4 | 1 | **36.0** | P2 |
| 39 | Rename 高风险 → 需当天处理 | 2/5 | 2 | 3 | 4 | 1 | **24.0** | P2 |
| 40 | Hide 管理 → 标为测试 from non-founder | 5 | 2 | 3 | 2 | 2 | **6.0** | P2 |

---

## Top 41–50

| Rank | Fix | Cap | BI | TI | F | Effort (h) | ROI | Priority |
|------|-----|-----|----|----|---|------------|-----|----------|
| 41 | Load chen_kui ui_copy.json into UI | 3 | 3 | 3 | 3 | 6 | **4.5** | P2 |
| 42 | Short 服务记录编号 in list | 3 | 2 | 2 | 4 | 2 | **8.0** | P3 |
| 43 | Sticky 下一步 + draft on scroll | 3 | 3 | 3 | 3 | 4 | **6.8** | P3 |
| 44 | Weekly `/readyz` probe during trial month | 7 | 3 | 4 | 2 | 1 | **24.0** | P2 |
| 45 | Capture Day 7 testimonial quote field | 6 | 2 | 3 | 1 | 1 | **6.0** | P2 |
| 46 | Remove English "Unified Intake" from sidebar | 1 | 2 | 3 | 4 | 1 | **24.0** | P2 |
| 47 | Fix-now: top 3 draft failures from trial | 3 | 4 | 5 | 2 | 8 | **5.0** | P1 (post-trial) |
| 48 | Demo vs real paste visual separation | 4 | 2 | 3 | 3 | 2 | **9.0** | P2 |
| 49 | Human confirmation badge prominence | 3 | 2 | 3 | 3 | 2 | **9.0** | P2 |
| 50 | Mobile-friendly paste area | 4 | 2 | 2 | 3 | 8 | **1.5** | P3 |

---

## Deferred (Constitution Locked — Not Ranked)

| Item | Reason |
|------|--------|
| Stripe / billing portal | Anti-goal v1 |
| WeChat / email sync | Anti-goal v1 |
| CRM / carrier APIs | Anti-goal v1 |
| Multi-tenant / OAuth | Anti-goal v1 |
| OCR primary intake | Anti-goal v1 |
| $199 tier | Features don't exist |
| Repo cleanup / lab isolation | Anti-goal during trial |
| New issue categories | Fix-now from trial only |

---

## Execution Bundles (Score-Weighted)

| Bundle | Fixes (ranks) | Expected overall delta |
|--------|---------------|------------------------|
| **Day 1–2 Trust + Front Door** | 1–5, 12, 19 | +12–15 overall |
| **Day 3–4 First Value + Deploy** | 7–9, 11, 24 | +5–8 overall |
| **Day 5–6 Commercial + Playbook** | 6, 14–18, 21 | +8–10 overall |
| **Day 7–8 Dry Run** | 10, 13, 20 | Gate before Chen Kui |
| **Day 9–14 Trial** | Observation + payment conversation | Proof or kill |

---

*End of Top 50 ROI Fixes — P15*
