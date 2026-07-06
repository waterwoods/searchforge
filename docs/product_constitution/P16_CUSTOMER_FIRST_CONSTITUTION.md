# P16 Customer First Constitution

**Sprint:** P16-CUSTOMER-FIRST-CONSTITUTION-P0  
**Date:** 2026-06-07  
**Status:** Source of truth for Customer First Add-Car Intake  
**Supersedes:** Broker-paste-only framing where it conflicts with this document

---

## What P16 Is

P16 is the **Customer First Add-Car Intake System**.

**Core purpose:**

1. Customer submits add-car information.
2. Office sees what is complete and what is missing.
3. Broker confirms and controls final action.

**P16 is NOT:**

- CRM
- insurance core system
- WeChat bot
- full customer portal
- policy management system
- claim system

---

## The Eight Rules

These rules are product law. Future sprints, specs, and agent prompts must align with them unless this constitution is explicitly revised.

---

### Rule 1 — Customer Never Logs In

**What it means**

The customer never creates an account, enters a password, or completes OAuth as a requirement to start or finish add-car intake. They open a link and type. That is the whole access model.

**Why it exists**

Add-car intake happens inside WeChat threads, forwarded screenshots, and one-off links. Login walls kill completion before the customer reaches the first field. Brokers already know the customer by phone and name — the product should not pretend to be a consumer app.

**What complexity it removes**

- User accounts, password reset, email verification
- SSO, OAuth gates, session tokens tied to identity providers
- “Create account to track your request” portal thinking
- Multi-device sync via authenticated profiles

**What the system must NOT do**

- Require login before intake starts
- Block formal submit until the customer authenticates
- Treat WeChat OAuth as the primary return path (optional binding only, never mandatory)
- Build a “customer portal account” as Stage 1 scope

---

### Rule 2 — Phone Is The Return Key

**What it means**

When a customer comes back — same day or days later — they re-enter their **phone number** to find their **active add-car case**. Phone is the customer-facing continuity handle. No magic link, no login, no “check your email.”

**Why it exists**

Phone is what brokers and offices already use to match a person. It is the natural key for Chinese-speaking auto insurance customers in Southern California. It works without teaching customers a new concept.

**What complexity it removes**

- Magic links and expiring tokens
- Email-based case lookup
- Browser-only `session_id` as the only return path
- WeChat openid as required continuity

**What the system must NOT do**

- Rely on `sessionStorage` / `session_id` alone for multi-day return
- Require WeChat scan to resume a case
- Offer a case picker with many open cases (see Rule 7)
- Hide the phone lookup behind broker-only tools

---

### Rule 3 — Phone Required For Formal Submit

**What it means**

The customer cannot **formally submit** an add-car case to the office without a **valid phone number** on the record. Name may be collected earlier or later, but phone is mandatory at the formal-submit boundary.

**Why it exists**

Formal submit is the moment the office treats the case as real work. Without phone, the office cannot call back, the customer cannot return, and the broker cannot confirm identity. A “submitted” case with no phone is not office-ready.

**What complexity it removes**

- Office chasing broker for contact info after “submit”
- Ambiguous “we’ll reach you in WeChat” handoffs
- Cases in the queue that cannot be matched to a person
- Customer confusion about whether submit “counted”

**What the system must NOT do**

- Allow `formal_submitted_at` when phone is missing or invalid
- Treat phone as optional “conversion layer” after vehicle fields are complete
- Let `case_usable` or `handoff_pending` bypass phone for formal submit
- Accept placeholder or broker-only phone without customer-provided value

---

### Rule 4 — Progress = Missing Fields

**What it means**

The rule name anchors on **missing fields** — customer-facing progress is not a percentage bar or abstract “step 2 of 5.” It is a plain list of **what is still missing** (`still_needed_fields`) and **what is already collected**.

**Rule 4 interpretation (status visibility):** Progress is **not only** missing fields. Customer-facing status must let the customer answer the three north-star questions without calling the office:

| Dimension | Customer question |
|-----------|-------------------|
| **Submit state** | Did I submit my request? |
| **Missing fields** | What is still missing? |
| **Contact state** | What is the current contact state? |

**Allowed on the customer surface**

- Submit state visibility (e.g. not yet submitted / formally submitted)
- Missing-field list aligned with office truth
- Contact state visibility (e.g. waiting on customer, waiting on office, waiting on broker)
- Broker expectation language (“we will contact you when…”) when the broker or office sets it

**Forbidden on the customer surface**

- Hard system SLA promises (“within 24 hours”) the product cannot enforce
- Fake progress bars or “processing” spinners that hide gaps or submit state
- Contact timing guarantees without broker/office backing

**Why it exists**

Brokers and customers think in concrete gaps — VIN, ZIP, driver, phone — not lifecycle jargon. Missing-field progress is honest, auditable, and matches what the office sees. Submit state and contact state complete the picture so the customer does not need to call for basic status.

**What complexity it removes**

- Fake progress bars that lie about readiness
- Duplicate status vocabularies (customer vs office vs broker)
- “Almost done” states that hide blocking gaps
- Separate customer progress model from office truth
- Phone callbacks solely to learn “did my submit count?” or “who is waiting on whom?”

**What the system must NOT do**

- Show 100% progress while `still_needed_fields` is non-empty
- Hide missing fields, submit state, or contact state behind “processing” or spinner UX
- Use different gap lists on customer surface vs workbench
- Promise fixed contact timing or SLA the system cannot support

---

### Rule 5 — Only Broker Closes Or Reopens A Case

**What it means**

Lifecycle terminal states — **closed**, **reopened**, **cancelled for office purposes** — are **broker-controlled** actions on the workbench. The customer can submit, append, and see status, but cannot close a case or force it back open.

**Why it exists**

The broker is legally and commercially responsible for the client relationship. Letting customers close cases creates orphan records, lost follow-ups, and disputes about what was “finished.”

**What complexity it removes**

- Customer self-service case cancellation flows
- Automatic case closure on idle timeout (without broker visibility)
- Office reopening without broker audit trail
- Competing “done” signals from customer vs broker

**What the system must NOT do**

- Expose “Close my request” to customers in Stage 1
- Auto-close active cases silently after N days
- Let office assistants change terminal lifecycle without broker role
- Reopen merged cases without explicit broker action

---

### Rule 6 — Broker Confirms Identity

**What it means**

Customer-claimed name and phone are **claimed**, not **verified**. Before high-trust actions (quote bind, policy change execution), the **broker confirms** identity — typically by matching phone to existing client records or a quick WeChat/phone check. The product surfaces claimed vs confirmed where it matters; it does not pretend verification happened.

**Why it exists**

Customers typo names, share family phones, or submit before the broker knows who they are. The office needs a human confirmation step, not an automated “verified ✓” badge.

**What complexity it removes**

- KYC / ID verification pipelines
- Automated “identity verified” legal claims
- False confidence in customer-entered contact data
- Office acting on unconfirmed identity as if it were CRM truth

**What the system must NOT do**

- Display “identity verified” without broker action
- Skip broker review on formal submit
- Treat extracted phone from chat as confirmed without broker glance
- Build credit-bureau or document ID checks in Stage 1

---

### Rule 7 — One Customer = One Active Case

**What it means**

For a given customer (same normalized phone), the system maintains **at most one active add-car case** at a time. Returning customers resume that case. A **new** add-car matter starts only when the broker closes the prior case or explicitly opens a new one.

**Why it exists**

Multiple open add-car cases for the same phone confuse customers (“which one did I submit?”), duplicate office work, and break the Phone Return Key model.

**What complexity it removes**

- Multi-case picker UI for customers
- Duplicate queue entries from repeat “start over” clicks
- Merge/fork decision trees on every return visit
- CRM-style case portfolios per person

**What the system must NOT do**

- Show a list of open cases and ask the customer to choose (out of scope for now)
- Auto-create a second active add-car case for the same phone without broker close/split
- Treat “different vehicle” in chat as a silent new case while the old one is still active
- Optimize for “one person, many concurrent service records” in the add-car wedge

**Note:** Historical closed cases may exist. Rule 7 governs **active** cases only.

---

### Rule 8 — One Business Flow At A Time

**What it means**

A customer thread may contain many topics — add a vehicle, file a claim, ask about a policy, ask about billing. The AI advances **exactly one business flow** at a time per customer. Once a flow is open, the AI stays inside it until that flow reaches a terminal state (broker confirms, customer declines, or broker closes/splits). Other topics raised mid-flow are acknowledged briefly and **politely deferred** — flagged for the broker, never processed in parallel.

**Why it exists**

Real conversations are messy; real brokers are not confused by that, because a human broker instinctively finishes today's ask before starting the next one. An AI that tries to be "smarter" by advancing two flows at once cross-contaminates state (a claim date captured into a vehicle field), produces replies with no clear topic, and hands the broker a case that is two half-finished jobs instead of one clear one. This rule makes the AI behave like the best human assistant already does, not like a general-purpose multi-tasking bot.

**What complexity it removes**

- Cross-intent merge/split resolvers for simultaneously active topics
- Conflict states caused purely by topic mixing (e.g. "BROKER_REVIEW" triggered by mixed claim + add-car language in one message)
- Secondary-intent field-merge logic and multi-topic precedence rules embedded in reply templates
- Parallel flow state machines and generic multi-flow orchestration engines
- Pairwise testing of every topic combination (claim+payment, premium+doc, add-car+garaging, …)

**What the system must NOT do**

- Start slot-filling, drafting, or a new case for a second topic while a flow is already open for that customer
- Silently switch the active flow because the customer mentioned a second topic once
- Merge fields from two different topics into one flow's state
- Ask the customer "which do you want first" mid-flow — the first flow is already chosen; defer the rest, don't re-litigate
- Build a generic rules engine or workflow framework to process multiple topics "at once" — one flag per deferred topic (see Track B0's `claim_mentioned_at` pattern), not a multi-flow engine

**Relationship to Rule 7:** Rule 7 governs case **identity** (at most one active case record per phone). Rule 8 governs conversational **attention** (at most one flow gets the AI's processing at a time). A customer could theoretically have one active case yet still confuse the AI by raising a second topic inside it — Rule 8 is what stops that regardless of case identity.

---

## Role Timing Goals

| Role | Goal | Question answered |
|------|------|-------------------|
| **Customer** | **3 minutes** to submit | “Did I submit it?” |
| **Office** | **10 seconds** to understand | “What is complete / missing?” |
| **Broker** | **30 seconds** to confirm | “Is this the right person and case?” |

---

## Customer First North Star (companion)

**Umbrella principle:** **Customer Must Always Know The Status**

The customer must be able to answer — **without calling the office**:

1. **Did I submit my request?** (submit state)
2. **What is still missing?** (missing fields)
3. **What is the current contact state?** (who is waiting on whom)

Office and broker surfaces exist to make those three answers true on the customer surface — not to replace them with internal jargon or mandatory phone callbacks for basic status.

---

## Implementation Boundary (this sprint)

This document defines **rules only**. It does not authorize:

- SMS OTP
- WeChat OAuth as required path
- WeChat bot integration
- OCR-first intake
- Multi-case customer picker
- CRM features
- Payment integration
- Postgres data cleanup (separate phased sprint)

See `P16_CUSTOMER_FIRST_GAP_REVIEW.md` for current code/doc conflicts and `P16_CUSTOMER_FIRST_P0_SUMMARY.md` for next sprint order.

---

*End of P16 Customer First Constitution*
