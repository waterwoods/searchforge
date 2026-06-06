# Mature Skeleton / Commercial Intake Backbone Report

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Date:** 2026-03-20  
**Budget:** 30–70 minutes (document-driven strategy)

---

## 1. Sprint Theme

**What was chosen:** Define a mature commercial intake backbone by borrowing the strongest proven structural patterns from Stripe, Amazon-style, Intercom/Shopify Inbox, and Zendesk — then adapting them to vertical insurance broker workflows.

**Why now:** The product has Add-Car flagship, Workbench, quote-ready visibility, identity/contact-lite, attachment-ready-lite, simulations/guardrails, and a clearer vertical direction. But future progress will become messy without a stable backbone. The founder needs to answer: what skeleton are we building on? which mature products should we borrow from? how should page, flow, state, and handoff be structured? what rules should guide future professionalization?

---

## 2. Document Set Created

| # | Document | Purpose |
|---|----------|---------|
| 1 | `01_MATURE_SKELETON_BACKBONE_BLUEPRINT.md` | Why backbone needed; what sprint defines; what it will not do |
| 2 | `02_REFERENCE_PATTERN_ANALYSIS_SPEC.md` | Stripe, Amazon, Intercom, Zendesk analysis; borrow map |
| 3 | `03_PAGE_FLOW_STATE_HANDOFF_BACKBONE_SPEC.md` | Core spec: page, flow, state, handoff backbones |
| 4 | `04_BORROW_VS_BUILD_DECISION_SPEC.md` | Borrow directly, adapt, build vertical-specific, defer |
| 5 | `05_EXECUTION_OUTLINE.md` | Workstreams, loop plan, how future teams use backbone |
| 6 | `06_ACCEPTANCE_BACKBONE_CRITERIA.md` | Clarity, usefulness, realism, commercial relevance, reusability |
| 7 | `07_FOUNDER_MAINLINE_NOTES.md` | What Andy should remember; mainline reference; alignment |

---

## 3. Baseline Product Position Audit

### Strongest Current Assets

| Asset | Status |
|-------|--------|
| **Unified Intake** | One paste → structured triage; multi-turn collection; handoff to Workbench |
| **Broker Workbench** | Queue, case card, Collected/Still needed chips, broker_next_step, follow-up memory, reopen context |
| **Add-Car flagship** | Multi-turn year/model/zip; quote-ready visibility; concrete vehicle in broker_next_step |
| **Quote-ready visibility** | quote_ready / almost_ready / need_more; separated from attachment |
| **Identity/contact layer** | customer_name, customer_phone extraction; Contact block visible |
| **Attachment-ready lite** | case_attachments, upload API, Workbench visible; optional, non-blocking |
| **Scenario Logic Center** | Rules in config; detect → ask → enough? → handoff; 5-layer architecture |
| **Simulation / guardrail** | 64/64 guardrail, 41/41 multi-turn, 12/12 handoff timing; founder demo queue |

### Biggest Structural Gap

**No single mature backbone reference.** Page structure (hero, primary actions, free input) exists in UI professionalization sprint but is not yet the canonical backbone. Flow is defined in MATURE_INTAKE_SKELETON and LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT but not synthesized into one flow backbone. State and handoff are spread across multiple docs. Future sprints have no single place to check alignment.

### Biggest Commercialization Gap

**UI/product polish and "paid-product feel."** The page can still feel like a demo or internal tool (workbench URL, fragmented styling). Trust/hero above fold is not yet canonical. Commercial product framework overview exists but backbone rules for trust, clarity, and reduced broker rework are not codified in one spec.

### Biggest Likely Mistake Without a Backbone

**Drift toward enterprise-heavy or chatbot-centric choices.** Without explicit "do not copy" and "defer" lists, the team could: (1) add real-time chat because Intercom has it; (2) add multi-channel inbox because Zendesk has it; (3) over-build ticketing (SLA, macros) because Zendesk has it; (4) make the product feel like a generic chatbot instead of a vertical intake + handoff tool. The backbone prevents this.

---

## 4. 10–20 Point Breakdown

1. **Why we need a mature backbone now** — Product has strong assets but no single structural reference; future progress will become messy without it.
2. **Why we should not reinvent the whole product** — Mature products have proven skeletons; we borrow and adapt, not invent from scratch.
3. **What Stripe-like patterns are best for** — Page hierarchy, trust/hero, card containment, visual productization, form/card structure.
4. **What Amazon-like patterns are best for** — Service entry by need, operational flows, customer support pathing, "what do you need?" routing.
5. **What Intercom/Shopify-like patterns are best for** — Handoff context, quick actions, conversation-first framing, "assign to human" clarity.
6. **What Zendesk-like patterns are best for** — Ticket structure, priority/urgency, status workflow, agent next action.
7. **What the page backbone should look like** — Trust/hero above fold; primary action area (7 scenarios); free input subordinate; supporting/helper tertiary.
8. **What the flow backbone should look like** — Entry → triage/routing → information collection → confirmation → handoff → broker follow-up.
9. **What the state backbone should include** — need_more, almost_ready, quote_ready, attachment_received, contact_missing, escalation/urgent, closed, follow_up_pending; status; due-state; follow_up_type.
10. **What the handoff backbone should include** — Case focus, your next move, collected, still needed, urgency, human confirmation; correction/already_sent visibility; attachment visibility.
11. **What should be copied directly** — Page hierarchy, card containment, service entry by need, ticket structure, priority/urgency, handoff context.
12. **What should be adapted** — Trust messaging, primary actions, flow shape, status workflow, quick actions, collection logic.
13. **What must be vertical-specific** — Add-car multi-turn, quote-ready, cancellation urgency, missing doc + already_sent, Chen Kui tone, handoff phrases, follow_up_type, human confirmation.
14. **What should remain deferred** — Real-time chat, multi-channel inbox, full ticketing, team assignment, carrier API, OCR, Stripe, multi-tenant.
15. **What most improves trust** — Trust/hero above fold; "office will follow up" messaging; professional card containment; no lab/workbench framing on customer entry.
16. **What most reduces broker rework** — One broker_next_step per case; collected chips (avoid re-asking); still needed chips (next ask clarity); correction/already_sent visibility.
17. **What most improves paid-product feel** — Mature page hierarchy; clear service entry points; structured handoff; vertical specialization (add-car, quote-ready, cancellation).
18. **What should guide all future sprints** — The four backbones (Page, Flow, State, Handoff); Borrow-vs-Build; Defer list; Founder Mainline Notes.

---

## 5. Iteration Loop 1

### References Analyzed

- **Stripe** — Page clarity, visual productization, form/card hierarchy, trust signals
- **Amazon / Amazon-style** — Service entry structure, operational flows, customer support pathing
- **Intercom / Shopify Inbox** — Messaging entry, quick actions, handoff friendliness, customer-service framing
- **Zendesk** — Structured support/ticket thinking, priority/urgency, status workflow, agent view

### What Each Is Good For

| Reference | Best For |
|-----------|----------|
| Stripe | Page hierarchy, trust/hero, card containment, professional feel |
| Amazon-style | Service entry by need, operational flows, routing by issue type |
| Intercom/Shopify Inbox | Handoff context, quick actions, conversation-first, assign-to-human |
| Zendesk | Ticket structure, priority/urgency, status workflow, agent next action |

### What Should NOT Be Copied

| Reference | Do NOT Copy |
|-----------|-------------|
| Stripe | Payment flows, dashboard density, API-first productization |
| Amazon | Scale, automation, multi-department routing, marketplace |
| Intercom/Shopify | Real-time chat, team assignment, marketing automation, chatbot-first |
| Zendesk | Full ticketing, multi-channel, SLA, macros, triggers |

### First Borrow Map

| Reference | Borrow | Adapt | Skip |
|-----------|--------|-------|------|
| Stripe | Page hierarchy, card containment | Trust messaging ("office will follow up") | Dashboard density, payment |
| Amazon | Service entry by need | Our 7 scenarios as entry points | Scale, automation |
| Intercom | Handoff context, quick actions | Draft editable, no auto-send | Real-time chat, team assignment |
| Zendesk | Ticket structure, urgency, status | Simpler status (new, reviewing, waiting_client, done) | Full ticketing, SLA |

### Whether Loop 1 Was Worth It

**Yes.** Without explicit analysis, the team could have defaulted to "copy Intercom" (chatbot-heavy) or "copy Zendesk" (enterprise-heavy). The borrow map forces synthesis: we take page from Stripe, flow from Amazon + our skeleton, state from Zendesk + our field progress, handoff from Intercom + our structure. No single product is the template.

---

## 6. Iteration Loop 2

### Backbone Synthesis

**Page Backbone:** Trust/hero (Layer 1) → Primary action area (Layer 2) → Free input (Layer 3) → Supporting/helper (Layer 4). Card containment, 24–32px gaps, max width 720–800px.

**Flow Backbone:** Entry → Triage/routing → Information collection → Confirmation → Handoff → Broker follow-up. detect → ask → enough? → hand off at core.

**State Backbone:** need_more, almost_ready, quote_ready, attachment_received, contact_missing, escalation/urgent, closed, follow_up_pending. Status: new, reviewing, waiting_client, done. Due-state: Overdue, Due today, Due tomorrow, No due date.

**Handoff Backbone:** Case focus, your next move, collected, still needed, urgency, human confirmation. Context: correction, already_sent, attachment, secondary issue.

### What Was Adapted for Vertical Insurance

- **Trust messaging** — "Office will follow up" instead of Stripe's "secure payment"
- **Primary actions** — 获取报价, 保单变更, 报事故, 上传材料, 联系人工 (our 7 scenarios)
- **Flow** — Our detect→ask→enough?→handoff; not Amazon's self-service resolution
- **State** — quote_ready, almost_ready (add-car specific); human_confirmation_recommended
- **Handoff** — broker_next_step operational style; "Verify receipt" for already_sent

### What Was Challenged

- **Does it fit a small CA broker office?** Yes — single broker; no team assignment; lightweight status.
- **Does it fit Chinese-speaking?** Yes — primary actions in Chinese; handoff phrases; Chen Kui tone.
- **Does it fit lightweight commercial SaaS?** Yes — no enterprise workflows; defer list protects scope.
- **Is it too chatbot-centric?** No — intake-first; AI collects, human confirms; no auto-send.
- **Is it too engineering-tool-like?** No — broker-facing; operational next step; draft editable.

### Whether Loop 2 Was Worth It

**Yes.** The challenge step caught potential drift: we explicitly rejected chatbot-centric and engineering-tool-like choices. The backbone is broker-centric, vertical-specific, and commercially oriented.

---

## 7. Iteration Loop 3

### Final Backbone Guidance

- **Page:** Trust/hero above fold; primary actions dominate; free input subordinate; no lab framing.
- **Flow:** Entry → triage → collect → confirm → handoff → follow-up.
- **State:** need_more, almost_ready, quote_ready, escalation, etc.; status; due-state; follow_up_type.
- **Handoff:** Case focus, next move, collected, still needed, urgency; correction/already_sent visible.

### What Future Sprints Should Align To

- Before starting: Read relevant backbone(s).
- During: Check alignment at milestones.
- After: If backbone refined, document why.
- Never: Build deferred items without explicit backbone update and founder approval.

### What Remains Intentionally Deferred

Real-time chat, multi-channel inbox, full ticketing, team assignment, carrier API, OCR, Stripe billing, multi-tenant auth.

### Whether Loop 3 Was Worth It

**Yes.** Founder-usable and sprint-usable guidance is now explicit. Tradeoffs are documented. Next vs later is clear.

---

## 8. Final Backbone Summary Table

| Backbone | Current Target Structure | Mature Reference Source | Vertical Adaptation Needed | Implementation Priority |
|----------|--------------------------|-------------------------|----------------------------|--------------------------|
| **Page** | Trust/hero → Primary actions → Free input → Supporting | Stripe | "Office will follow up"; 7 scenarios as entry points | High — UI professionalization |
| **Flow** | Entry → Triage → Collect → Confirm → Handoff → Follow-up | Amazon + our skeleton | detect→ask→enough?→handoff; per-category thresholds | Medium — already largely implemented |
| **State** | need_more, almost_ready, quote_ready, escalation, etc. | Zendesk + our field progress | quote_ready, almost_ready; human_confirmation | Medium — align naming and visibility |
| **Handoff** | Case focus, next move, collected, still needed, urgency | Intercom + our structure | broker_next_step; correction/already_sent; "Verify receipt" | High — trial hardening |

---

## 9. Founder Guidance

### What Andy Should Hold in Mind as the Mainline Axis

- We are building a **mature commercial intake backbone** — borrow, adapt, do not reinvent.
- **Four backbones:** Page, Flow, State, Handoff. Every future sprint aligns to them.
- **Borrow from:** Stripe (page), Amazon (flow), Intercom (handoff), Zendesk (state).
- **Build vertical-specific:** Add-car, quote-ready, cancellation, missing doc, Chen Kui tone.

### What Should Be Copied

Page hierarchy, card containment, service entry by need, ticket structure, priority/urgency, handoff context.

### What Should Be Adapted

Trust messaging, primary actions, flow shape, status workflow, quick actions, collection logic.

### What Should Be Avoided

Blind copying of one product; enterprise-heavy; chatbot-centric; scope creep (defer list).

---

## 10. 中文宏观总结

### 为什么现在要定成熟骨架

产品已有 Add-Car 旗舰、Workbench、quote-ready、simulation/guardrail 等强资产，但缺少统一的成熟骨架参考。未来迭代会变乱：没有明确的产品结构、页面结构、流程结构、状态结构、handoff 结构。现在定骨架，是为了让后续 sprint 有稳定锚点。

### 哪些成熟骨架最值得借

- **Stripe** — 页面层级、信任/hero、卡片边界、视觉产品化
- **Amazon 风格** — 按需求的服务入口、运营流程、客服路径
- **Intercom/Shopify Inbox** — handoff 上下文、快捷操作、对话优先
- **Zendesk** — ticket 结构、优先级、状态流转、agent 下一步

不盲抄一家；按功能从各家取最强部分合成。

### 我们自己的垂直差异化在哪里

- Add-car 多轮收集、quote-ready 可见性
- 取消/付款 urgency、same-day action
- 缺材料 + already_sent、「Verify receipt」
- 陈奎 tone、handoff phrases
- follow_up_type、human_confirmation 边界

### 下一步该怎么按这份骨架推进

1. UI sprint 对齐 Page Backbone：trust/hero、primary actions、free input
2. Trial 加固对齐 Handoff Backbone：correction/already_sent、broker_next_step
3. State 命名和可见性对齐 State Backbone
4. 新功能先查 Borrow-vs-Build、Defer list，避免 scope creep

---

## 11. COPY/PASTE FOUNDER BLOCK

```
BEST MATURE REFERENCE MIX
- Stripe: page hierarchy, trust/hero, card containment
- Amazon-style: service entry by need, operational flows
- Intercom/Shopify Inbox: handoff context, quick actions
- Zendesk: ticket structure, priority/urgency, status

BIGGEST STRUCTURAL TAKEAWAY
Four backbones (Page, Flow, State, Handoff) are the stable reference.
Borrow from each; synthesize; do not copy one product blindly.

WHAT MUST REMAIN VERTICAL-SPECIFIC
Add-car multi-turn, quote-ready, cancellation urgency, missing doc + already_sent,
Chen Kui tone, handoff phrases, follow_up_type, human confirmation.

WHAT FUTURE PRODUCT WORK SHOULD ALIGN TO
- Page: trust/hero above fold; primary actions dominate; free input subordinate
- Flow: entry → triage → collect → confirm → handoff → follow-up
- State: need_more, almost_ready, quote_ready, escalation, etc.
- Handoff: case focus, next move, collected, still needed; correction/already_sent visible
- Defer: real-time chat, multi-channel, full ticketing, carrier API, OCR, Stripe, multi-tenant
```

---

## 12. REQUIRED SHORT OVERVIEW

### 为什么做这件事

产品已有强资产（Add-Car、Workbench、quote-ready、simulation），但缺统一成熟骨架。未来迭代会乱。需要定义：我们建在什么骨架上？从哪些成熟产品借？页面、流程、状态、handoff 怎么结构？什么规则指导商业化？

### 主要用了什么方法/技术

Document-driven strategy sprint。分析 Stripe、Amazon 风格、Intercom/Shopify Inbox、Zendesk 四类成熟产品的结构模式；按功能（页面、流程、状态、handoff）提取可借部分；合成 4 个 backbone；3 轮迭代：分析 → 合成 → 挑战 → 定稿。

### 这轮最大的结论

**不盲抄一家，按功能合成。** 页面借 Stripe，流程借 Amazon + 我们的 detect→ask→enough?→handoff，状态借 Zendesk + 我们的 field progress，handoff 借 Intercom + 我们的 broker_next_step/collected/still_needed。垂直保险必须自建：add-car、quote-ready、cancellation、missing doc、陈奎 tone。明确 defer：real-time chat、multi-channel、full ticketing、carrier API、OCR、Stripe、multi-tenant。

### 现在最该做什么

1. 用 Page Backbone 指导 UI professionalization（trust/hero、primary actions）
2. 用 Handoff Backbone 指导 trial 加固（correction/already_sent、broker_next_step）
3. 新功能先查 Borrow-vs-Build、Defer list
4. 把 `03_PAGE_FLOW_STATE_HANDOFF_BACKBONE_SPEC.md` 作为未来 sprint 的结构参考

---

*End of Mature Skeleton / Commercial Intake Backbone Report*
