# Case Builder North Star — 2026-08-03

**Status:** Authoritative product promise for the six-day pilot release window  
**Date:** 2026-08-03  
**Scope:** Insurance Case Builder / Unified Claim intake (customer Mini Program + Broker Workbench)  
**Does not supersede:** `docs/product/p20_product_north_star.md` (P20 development law) or `docs/CURRENT_PRODUCT_SHAPE.md` (runtime deploy truth)  
**Companion plan:** `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md`

---

## Customer problem

Chinese-speaking insurance customers and small broker offices currently rely on:

- repeated phone calls
- scattered WeChat messages
- repeated document requests
- unclear ownership
- unclear next steps
- weak case continuity

---

## Product promise

SearchForge Case Builder helps an insurance office:

- recognize an existing customer
- reuse confirmed vehicle and policy context
- collect an accident story and evidence
- identify genuinely missing information
- request and receive supplements
- let the Broker confirm every important step
- preserve one Active Case and Timeline
- show one clear next action
- measure timing and AI quality

---

## Canonical workflow

Customer message / entry  
→ known-customer context  
→ accident story  
→ bounded AI proposal  
→ customer confirmation  
→ deterministic completeness check  
→ Broker review  
→ Request More when needed  
→ customer supplement  
→ office acceptance  
→ Timeline / metrics

---

## Frozen principles

- Server-side source of truth
- One Active Case
- Append-first, split-later
- Customer sees one current task
- Broker sees one canonical next action
- AI proposes; humans confirm
- AI never changes lifecycle state
- Timeline and evidence remain auditable
- Production safety over demo convenience

---

## Commercial promise

Do not sell “LangGraph”, “LangSmith” or “MCP”.  
Sell:

- fewer repeated calls
- fewer unnecessary uploads
- fewer supplement loops
- faster broker-ready cases
- clear case ownership and next action
- measurable workflow quality

---

## Explicit exclusions for this release

- quoting
- coverage or liability decisions
- autonomous claim filing
- general CRM
- open-ended chatbot
- large multi-agent system
- full legal/compliance certification

---

## Truthfulness bound for Sunday V1

Sunday target is a **demonstrable and truthful V1**:

- Founder-demonstrable on Cloud QA for 陈总 / Chen Camry scenarios
- Credible Forward Deployed Engineer / Applied AI portfolio package
- Understandable, explainable, and continuable by the Founder

Sunday V1 is **not**:

- Production readiness certification
- Real-customer paid-pilot validation
- Authorization to retarget waterwoods or Production
