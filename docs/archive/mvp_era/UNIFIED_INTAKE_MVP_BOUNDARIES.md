# Unified Intake MVP — Business Value & Implementation Boundaries

**Purpose:** Define why a broker would pay for this, and what to build vs defer.

---

## 1. Business Value — Why a Broker Would Use This

A broker like 陈奎 would say this is worth using when:

| Pain | What MVP Addresses |
|------|--------------------|
| **"This saves me time"** | One paste → structured triage. No manual reading/sorting. Client-ready draft reduces copy-paste. |
| **"This reduces repeated explanation"** | Draft reply is tailored to category; broker edits instead of writing from scratch. |
| **"This reduces missed follow-ups"** | Urgency + escalation flag surface what needs same-day action. |
| **"This is worth using again"** | Output is consistent, predictable, and actionable. Broker trusts the triage. |

**Concrete success signals:**

- Broker pastes 5+ messages in a session without abandoning
- Broker uses `client_reply_draft` with minimal edits (not full rewrite)
- Broker says "I would use this tomorrow" after a 10-minute try

---

## 2. What Must Be True for It to Feel Worth Paying For

1. **Triage is reliable** — Category and urgency match broker intuition on real messages
2. **Draft is usable** — Professional tone; broker edits, not rewrites
3. **Escalation is sensible** — Critical/high items flagged; low/informational not over-flagged
4. **No surprises** — Output shape stable; no random failures

---

## 3. Implementation Boundaries

### Build Next

- Expose Unified Intake via simple UI (paste box → triage result)
- Ensure scenario pack passes with LLM enabled
- Add broker-facing copy of triage result (for WeChat/email)
- Validate with 1–2 real broker messages (陈奎 or proxy)

### Do Later

- Email/WeChat/SMS integration
- Case/customer linking
- Rich CRM-style history or "similar past cases"
- Multi-broker / auth

### Do Not Do Now

- Full CRM
- Automatic outbound messaging
- Stripe/billing integration
- Multi-tenant auth
- Broad customer support platform
- Huge UI overhaul

---

## 4. Safe Demo Claims

What Andy can safely say:

- "This is a unified intake surface for pasted inbound text."
- "It turns a messy message into a structured broker case card."
- "It suggests the next broker action and drafts a client reply."
- "The broker still reviews and decides what to send."

What Andy should not claim:

- "It reads screenshots directly."
- "It is connected to email, SMS, WeChat, or CRM."
- "It automatically sends replies or updates cases."
- "It already has full customer history or policy context."

---

## 5. v1 Boundary Reminder

Unified Intake MVP v1 is intentionally a **demo-safe work surface**, not a production operations platform.

The goal is to prove:

1. One entry
2. Structured triage
3. Clear broker action
4. Clear client draft
5. Honest visibility into when manual follow-up is required

Anything beyond that belongs in the next product step, not this sprint.

---

*End of boundaries doc*
