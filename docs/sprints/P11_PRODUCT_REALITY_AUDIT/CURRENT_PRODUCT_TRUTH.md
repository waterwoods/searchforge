# Current Product Truth — P11 Product Reality Audit

**Authority:** Customer-facing truth distilled from README, CURRENT_PRODUCT_SHAPE, broker docs, trial path, and P10 audit.  
**Audience:** Broker, office manager, founder, customer — not engineers.  
**Date:** 2026-05-30

---

## 1. What is the product?

**Unified Intake** is a California auto insurance broker assistant that turns messy customer messages into **one structured service record** you can act on.

**What you do:** Paste a message as you received it (WeChat text, carrier notice, follow-up).  
**What you get:**

| Output | What it means for your office |
|--------|-------------------------------|
| **Case focus** | What this message is about (cancellation, missing doc, add-car, etc.) |
| **Urgency** | Whether you need to handle it today |
| **Your next move** | One operational sentence — what to do next |
| **Collected / Still needed** | What you already have vs what to ask the customer |
| **Draft reply** | Editable text to copy to WeChat — **you send, not the system** |

**Where you use it:** Broker Workbench at `/workbench/unified-intake` — case queue, triage, notes, drafts.

**How you try it:** 7-day free trial → optional paid pilot (~$99/month manual invoice).

**One sentence (Chinese):**

> 试用一周：帮你把客户发来的 messy 消息整理成结构化 case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## 2. What is NOT the product?

| Not included | What that means |
|--------------|-----------------|
| **WeChat or email inbox sync** | You still copy-paste messages manually |
| **Automatic sending** | Nothing goes to your customer without you |
| **Screenshot/PDF reading** | Paste text; don't upload images expecting OCR |
| **Full CRM** | No client profiles, policies, or carrier portals |
| **Multi-office billing portal** | Single broker pilot; no self-serve accounts |
| **SearchForge RAG lab** | `/demo` Q&A page is separate research — not the workbench |
| **Platform / workflow engine** | Not a general operating system for insurance offices |
| **Perfect every edge case** | Mixed language, unusual notices — you still verify |

**If someone promises these today, they are over-promising.**

---

## 3. Who pays?

**Primary payer:** The **broker owner** (e.g., Chen Kui) — California auto insurance broker serving Chinese-speaking clients.

**Secondary beneficiary (doesn't pay directly):** Office assistant who handles WeChat follow-ups daily.

**Who does NOT pay in v1:** End customers, carriers, CRM vendors, or multi-office franchises.

**Payment model today:** Manual invoice (Zelle/Venmo/WeChat) after 7-day trial. No Stripe, no billing portal.

---

## 4. Why would they pay?

| Pain today | What Unified Intake offers |
|------------|----------------------------|
| Urgent cancellation notices buried in WeChat | Same-day action cases surface first |
| Re-asking for info the customer already sent | **Collected / Still needed** chips at a glance |
| Starting over on every follow-up | Reopen case; paste new message; resume context |
| Writing similar replies from scratch every day | Editable draft ready to copy |
| Mental load of "what was this about?" | **Case focus** + **Your next move** in one view |
| Losing track of who needs a reply today | Queue: Work now vs waiting |

**They pay when:** At least one real workflow (usually cancellation or missing document) clearly saves time across a week of use — not because the demo looked impressive.

**They do NOT pay when:** It feels like extra steps (paste again) without faster triage, or the first screen confuses them before they see value.

---

## 5. What outcome are they buying?

**Not buying:** AI, vectors, Postgres, or "a platform."

**Buying this outcome:**

> **Fewer minutes lost on urgent customer messages, with less re-reading and less re-typing — while staying in control of what gets sent.**

**Concrete success looks like:**

1. Monday morning: broker opens workbench, sees what needs same-day action
2. On a cancellation notice: knows next move in one sentence, not after scrolling WeChat
3. On missing document follow-up: sees what was collected, stops re-asking
4. On follow-up message: reopens case, pastes update, draft updates in context
5. Day 7: broker can say "yes, this saved time on [specific scenario]" or "not yet because [specific friction]"

**Failure outcome (what they're trying to avoid):** Paying for a tool that adds paste steps, shows engineer labels, loses cases, or produces drafts they wouldn't use.

---

## Product truth summary

| Question | Answer |
|----------|--------|
| Product | Paste → structured case → draft → you send |
| Not product | Sync, auto-send, CRM, lab, platform |
| Who pays | Broker owner |
| Why pay | Time saved on urgent triage + reply drafting |
| Outcome bought | Faster, clearer handling of messy inbound messages |

---

*End of current product truth*
