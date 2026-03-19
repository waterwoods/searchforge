# Turn 1 Experience Optimization — Sprint Blueprint

**Sprint:** Controlled Multi-Agent Iteration Sprint  
**Theme:** Turn 1 Experience / First Impression  
**Scope:** Chen Kui Insurance Unified Entry (Unified Intake)  
**Created:** 2026-03-14

---

## 1. Why This Sprint Matters

The strongest blocker to small-client confidence is **first-impression latency and clarity**. When Chen Kui (or any prospect) pastes a message and waits 5+ seconds with no clear feedback, they may think the system is slow or broken. Trust erodes before the first response appears.

---

## 2. Current Problem

| Surface | Turn 1 Flow | Current Loading Feedback | Gap |
|---------|-------------|--------------------------|-----|
| **Customer Entry** | User pastes → submits → triage → system reply | Button shows `loading`; no inline feedback in conversation | User sees their message, then blank gap for 1.5–5+ s. Feels like "did it work?" |
| **Broker Workbench** | User pastes → Triage → case card | "正在整理 case..." + Spin in separate card | Adequate but could be more prominent; no skeleton preview |
| **Demo Page (RAG)** | User clicks question or submits | "Searching..." on button; latency shown after | Acceptable; out of scope for this sprint |

**Focus:** Customer Entry and Broker Workbench only. Demo page is out of scope.

---

## 3. Target Improvement

1. **Customer Entry:** Inline "typing" or "正在整理" placeholder in the conversation area while waiting for Turn 1 response. User should never see a blank gap after sending.
2. **Broker Workbench:** Ensure loading state is visible and reassuring; optionally add a brief "what we're doing" hint (e.g. "正在分析消息并生成 case 卡片...").
3. **Latency perception:** No new backend work. Frontend-only improvements to make wait feel shorter and more predictable.

---

## 4. What "Good Enough" Looks Like

- Customer Entry: User sends first message → immediately sees an inline "正在整理 case..." (or similar) in the conversation, styled like a system placeholder, until real reply arrives.
- Broker Workbench: Loading card remains clear; wording is broker-friendly and consistent with Customer Entry.
- No regression: Existing validation (guardrail, scenario pack, demo_quick_validate) still passes.
- Trust preserved: Loading states do not over-promise; they simply confirm "we're working on it."

---

## 5. Out of Scope

- Backend latency optimization
- Skeleton UI / progressive loading
- Demo page (/demo) changes
- CRM, auth, multi-tenant
- Broad redesign

---

*See also: `docs/WEEKEND_FINAL_PRODUCT_HEALTH_CHECK_REPORT.md` §4–5, `docs/CHEN_KUI_TRIAL_PACK.md`*
