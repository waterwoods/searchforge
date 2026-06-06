# P16-X Phase 7 — SaaS Continuity Benchmark

**Date:** 2026-06-01  
**Focus:** What happens **after the first action** — not feature parity  
**Subject:** Deployed Unified Intake Preview vs Stripe, Linear, Intercom, Zendesk  
**Method:** Pattern comparison against P16-H benchmark + live Preview behavior

---

## Benchmark question

> User completes the **first meaningful action**. What does the product do in the next 60 seconds to keep them in the loop?

---

## Summary table

| Product | First action | Next 60 seconds | Continuity grade |
|---------|--------------|-----------------|------------------|
| **Stripe** | Create test charge | Dashboard updates; clear status; suggested next step (「View payment」) | **A** |
| **Linear** | Create issue | Issue page opens; assignee, state, comment box ready; inbox points back | **A** |
| **Intercom** | Send first reply | Conversation thread; customer reply routes back; unread badge | **A** |
| **Zendesk** | Submit ticket | Ticket # assigned; status Open; macro suggestions; requester notified | **A-** |
| **Unified Intake (Preview)** | Paste → 开始整理 → copy draft | Static card; paste box still open; no thread; user exits to WeChat | **D** |

---

## 1. Stripe — after first payment

| Pattern | Unified Intake equivalent | Gap |
|---------|---------------------------|-----|
| Immediate status object | Case ID exists but not celebrated | No「payment succeeded」moment |
| Activity feed | `case_activity` in data, collapsed | No visible timeline |
| Suggested next step | None post-copy | **Missing** |
| Return trigger | Email / dashboard notification | None |

**Stripe continuity lesson:** First action creates a **durable object with visible state** — user knows where to look next.

---

## 2. Linear — after first issue

| Pattern | Unified Intake equivalent | Gap |
|---------|---------------------------|-----|
| Land on detail view | Detail below fold | Scroll required |
| State machine visible | Status in kebab | **Hidden** |
| Comment thread | Append exists on reopen only | **Not thread-shaped** |
| Inbox points to open items | Queue exists | No unread / bold since last visit |

**Linear continuity lesson:** **Stay on the artifact** after creation; inbox is for **return**, not **creation**.

---

## 3. Intercom — after first reply

| Pattern | Unified Intake equivalent | Gap |
|---------|---------------------------|-----|
| Conversation shape | One-shot report | Not conversational |
| Customer reply routes in | Append API | UI undiscoverable |
| Typing / waiting indicators | None | |
|「Waiting on customer」badge | Data field | Not in glance |

**Intercom continuity lesson:** **Channel of record** — product owns the thread even if send happens elsewhere.

---

## 4. Zendesk — after first ticket update

| Pattern | Unified Intake equivalent | Gap |
|---------|---------------------------|-----|
| Ticket number + Open status | Short case ID; status hidden | Weak |
| Internal vs public note split | Broker vs client draft | Good |
| Follow-up updates same ticket # | Backend yes | UX no |
| Solve / Close ceremony | Kebab status | **No ceremony** |

**Zendesk continuity lesson:** **Ticket number is the handle** for all future messages — trained into support staff.

---

## After-first-action scorecard (Unified Intake)

| Dimension | Stripe | Linear | Intercom | Zendesk | **Unified Intake** |
|-----------|--------|--------|----------|---------|-------------------|
| Object persists visibly | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Clear next step on screen | ✅ | ✅ | ✅ | ✅ | ❌ |
| Return path obvious | ✅ | ✅ | ✅ | ✅ | ❌ |
| State machine visible | ✅ | ✅ | ✅ | ✅ | ❌ |
| Multi-turn in one place | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Continuity score (/10)** | 9 | 9 | 9 | 8 | **3** |

---

## What professional SaaS does that we don't (after first submit)

1. **Keeps user on the record** — we keep user on the paste box  
2. **Shows lifecycle state** — we show collapses  
3. **Invites the next message** — we invite a **new** paste  
4. **Confirms outbound action** — we confirm copy only if user notices button  
5. **Pulls user back** — we have no pull mechanism  

---

## Closest analog in our product (already built, not surfaced)

The **reopen + 追加客户补充** path is structurally similar to Zendesk「add comment on ticket #123」— but it requires queue literacy equivalent to knowing a ticket number.

---

## Benchmark verdict

**Unified Intake after first action feels like a calculator, not a workspace.**

Professional SaaS grade for **post-first-action continuity:** **D (3/10)**  
Overall SaaS grade (P16-H): D+ for landing; **F for continuation**

---

*End of P16-X Phase 7 — SaaS Continuity Benchmark*
