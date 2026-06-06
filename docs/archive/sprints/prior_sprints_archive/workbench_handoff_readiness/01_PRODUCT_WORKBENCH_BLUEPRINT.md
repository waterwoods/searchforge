# Product / Workbench Blueprint — Workbench Handoff Readiness Sprint

**Sprint:** Workbench Handoff Readiness  
**Date:** 2026-03-17  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Broker Workbench office-side view

---

## 1. Why Workbench Handoff Readiness Matters Now

The product has evolved:
- Stronger multi-turn continuity
- Stronger workflow_state
- Lifecycle visibility
- In-progress persistence
- Stronger top scenarios
- Better later-turn behavior

**But the founder's business goal is not just better chat.** It is:
> **Help the broker/assistant take over faster with less manual follow-up**

If the office side still feels thin, even a good conversation engine will not convert into real merchant value.

---

## 2. Why This Is the Correct Move After Backbone + Scenario Deepening

| Prior work | What it delivered |
|------------|-------------------|
| Minimal Production Backbone | lifecycle_status coherence, case_messages, origin_session_id |
| Structured Workbench Expansion | collected/still_needed for add-car, renewal, claim, missing-doc |
| Broker Workbench Structured Intake UI | Chips for Collected/Still needed in case card |

**Gap:** The broker still must re-read raw text to understand "what did the customer actually say?" and "what should I do next?" The handoff surface feels like a debug screen, not a working tool.

---

## 3. What This Sprint Will Strengthen

1. **Recent customer messages** — Broker sees last 2–3 original customer messages without parsing source_text
2. **Collected / still needed** — Already present; make more prominent and above-the-fold
3. **Lifecycle / handoff stage** — Clearer "Handed off" vs "Office follow-up"
4. **Next best action** — Clearer "Your next move" and correction/context hints
5. **Handoff quality** — Correction badge, "Customer says already sent" when applicable

---

## 4. What This Sprint Intentionally Will NOT Do

- Full CRM redesign
- Random admin features
- Enterprise assignment/routing
- Inbox sync / email/WeChat integration
- Overbuilding

---

## 5. Core Principle

**Do NOT redesign the whole UI.**  
**Do NOT add random admin features.**  
**Do NOT overbuild enterprise CRM features.**  
This sprint makes the handoff layer much more operationally useful for a broker/assistant.

---

*End of blueprint*
