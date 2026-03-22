# Mature Skeleton Backbone Blueprint

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Purpose:** Define why a mature backbone is needed now, what this sprint will define, and what it intentionally will not do.

---

## 1. Why a Mature Backbone Is Needed Now

The product has reached a critical inflection point:

- **Strong Add-Car flagship** — multi-turn collection, quote-ready visibility, identity/contact-lite, attachment-ready-lite
- **Workbench** — queue, case card, Collected/Still needed chips, broker_next_step, follow-up memory
- **Simulations / guardrails** — 64/64 guardrail, 41/41 multi-turn, handoff timing
- **Clear vertical direction** — California auto insurance, Chinese-speaking clients, Chen Kui-style broker workflows

**But:** Future progress will become messy unless the team defines a **stable mature backbone**. Right now there is no single reference for:

- What kind of product skeleton we are actually building on
- Which mature products we should borrow from
- How the customer page, intake flow, state flow, and broker handoff should be structured
- What rules should guide future professionalization and commercialization

Without a backbone, each sprint risks reinventing structure, copying the wrong patterns, or drifting toward enterprise-heavy or chatbot-centric choices that don't fit a small broker office.

---

## 2. Why Future Work Should Anchor to This Backbone

- **Consistency:** All future UI/product/flow sprints align to the same structural rules
- **Efficiency:** No need to re-debate page hierarchy, flow shape, or handoff format each sprint
- **Commercial clarity:** Backbone optimizes for trust, clarity, reduced broker rework, strong customer entry
- **Avoid drift:** Explicit "do not copy" and "do not build" guardrails prevent scope creep

---

## 3. What This Sprint Will Define

| Deliverable | Content |
|-------------|---------|
| **Page Backbone** | Hero/trust, primary action area, free input area, supporting/helper area; visual containment and hierarchy |
| **Flow Backbone** | Entry → triage/routing → information collection → confirmation → handoff → broker follow-up |
| **State Backbone** | need_more, almost_ready, quote_ready, attachment_received, contact_missing, escalation/urgent, closed/follow_up_pending |
| **Handoff Backbone** | Customer context, collected info, still needed, next step, attachment visibility, correction/already_sent visibility, readiness and urgency |

Plus:

- **Reference Pattern Analysis** — Stripe, Amazon-style, Intercom/Shopify-like, Zendesk-like: what to borrow, what not to copy
- **Borrow-vs-Build Decision Spec** — what to copy directly, adapt, build vertical-specific, defer
- **Mainline Guidance** — founder-usable summary; what future sprints should align to

---

## 4. What It Intentionally Will Not Do

- **Implementation** — No coding of the full backbone; this is a reference document
- **Deep visual design** — No pixel-level mockups or design system
- **Backend refactors** — No changes to triage, case store, or API
- **Exact UI assets** — No icons, illustrations, or brand assets
- **Generic benchmarking** — Not a competitive analysis; focused on structural patterns we can use
- **Blind copying** — Not "just copy Amazon" or any single product

---

## 5. Core Principle

**Do NOT reinvent everything. Do NOT blindly copy one company. Do NOT optimize for novelty.**

Instead: **borrow the strongest proven skeleton from mature products, then adapt it to our vertical insurance workflow.**

---

*End of blueprint*
