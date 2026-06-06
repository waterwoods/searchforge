# P16-Z18 Product Soul

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Sources:** P16-Z3 · P16-Z6 · P16-Z9 · P16-Z16 · P16-Z17 founder summaries · P16-Z2.5 soul

---

## What problem are we actually solving?

### One sentence

> **We stop insurance requests from getting lost in WeChat chaos by turning each customer message into a draft case the office can confirm, continue, and close — across days, on the same record.**

---

## What we are NOT solving

| Not this | Why |
|----------|-----|
| **CRM** | Offices have AMS; we don't replace contact management |
| **Chatbot** | Customer gets a case, not a conversation partner |
| **Insurance software** | Not policy admin, rating, or carrier portal |
| **AI platform** | Rules-first triage in `triage.py`, not a model showcase |
| **Document scanner product** | OCR exists; text/message wedge first |

---

## Soul synthesis (Z3 → Z17)

### From Z3 — maturity truth

You built an **L4.5 engine** deployed as **L3.5 experience** with **L2.5 access**. The gap is **wire + deploy + teach**, not architecture. Highest waste: rebuilding what exists in `inbox_triage/`.

### From Z6 — memory truth

Backend remembers; brokers couldn't **see** it until thread UI shipped. **Turn 1 feels smart; Turn 2+ failed on corrections** until Y44/Y45 merge. Soul implication: **continuity beats smarter Turn 1**.

### From Z9 — operating truth

48 `inbox_triage` modules = complete engine. Next 90 days = **deploy + wire + Role D proof + get paid** — not rediscover append. Documentation redundancy was the enemy; SSOT stops re-archaeology.

### From Z16 — Customer Builder truth

**Customer Builder already exists** as `CustomerEntryTab` (~72–76%). Create + broker review work. Return-later breaks on refresh after formal submit — **wiring gap, not missing product**.

### From Z17 — live proof

Case `case_98f4ac099d15`: formal submit → append Day 2/Day 3 → broker sees 11 messages without reopening customer chat. **Data layer complete; customer UX incomplete.**

---

## Who pays and why

### Broker (Chen Kui)

Brokers pay for **time back**, not software.

| Pain | Soul answer |
|------|-------------|
| 50 unread WeChat messages | One customer message → draft case ready to confirm |
| Re-read paste for deadline | Timeline + next action on the case |
| Lose context when client replies | Same `case_id`, append, merged fields |
| "Why open a webpage?" | Beat「直接回微信」on first closed loop |

**Payment trigger:** Chen Kui handles a real 3-day customer case **without Andy on the phone** — customer used link or broker pasted, case stayed unified, client responded positively.

### Customer (via broker or link)

Customers pay for **the office handling their thing** — not an app.

| Need | Soul answer |
|------|-------------|
| "帮我加车" without forms | Message-first Case Builder |
| Know what's still needed | Plain Chinese gap list |
| Know it was received | Submit to office + case reference |
| Return with VIN later | Same case append (after Z18 wiring) |

**Pilot reality:** Weeks 1–2, broker may still paste from WeChat. Customer tab is **real** and **primary product story** — not week-3 fantasy.

---

## The product should feel like

**Customer loop:**

> **发消息 → 草稿案件 → 提交办公室 → 稍后回来 → 补充 → 办完了**

**Broker loop (subordinate):**

> **看草稿 → 确认/修改 → 复制回复 → 客户再发 → 同案更新 → 再复制 → 结案**

**Combined (canonical):**

```
Customer Message → AI Draft Case → Broker Confirm → Timeline → Return Later → Close
```

---

## Three soul elements (updated)

### 1. Draft, not chat

AI produces a **structured draft case** — fields, gaps, next step — that a human confirms. Not open-ended conversation. Not generic reply text.

### 2. Same case, same ID

Turn 1 is not the product. **The loop is the product.** `case_id` + `case_messages` + append = office working memory (Linear-style context, insurance WeChat).

### 3. Confirm, don't re-type

Broker **confirms, corrects, executes**. AI converts and merges. Human owns carrier calls, judgment, and client relationship.

---

## Soul test (every feature idea)

Ask:

> *Does this help a customer send a messy message, get a draft case, let the broker confirm it, and continue the same case days later — without starting over?*

- **Yes** → Wire, tune, or repackage existing code.
- **No** → Reject or defer (see `P16Z18_NEVER_BUILD.md`).

---

## Competitive alignment (unchanged insight, reframed)

Zendesk, Intercom, Linear, HubSpot all implement:

```
Chaos → Understanding → Case → Next Action → Outcome
```

We built this pipeline. Z16–Z17 proved the **customer-facing half exists**. Z18 soul: **finish the customer return path**, don't build a parallel product.

---

*End of P16-Z18 Phase 2 — Product Soul*
