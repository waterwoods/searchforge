# Founder Mainline Notes

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Purpose:** What Andy should remember; how to use as mainline reference; how future sprints should align.

---

## 1. What Andy Should Hold in Mind

### The Mainline Axis

- **We are building a mature commercial intake backbone** — not reinventing, not blindly copying, not optimizing for novelty.
- **Borrow the strongest skeleton from mature products** — Stripe (page), Amazon (flow), Intercom (handoff), Zendesk (state) — then adapt to vertical insurance.
- **Four backbones are the heart:** Page, Flow, State, Handoff. Every future sprint should align to them.

### What to Copy

- Page hierarchy (hero → primary → secondary)
- Service entry by need (our 7 scenarios)
- Ticket structure (issue + context + status + next action)
- Handoff context (what customer said, what's needed)

### What to Adapt

- Trust messaging ("office will follow up")
- Flow shape (detect → ask → enough? → hand off)
- Status workflow (simpler than Zendesk)
- Quick actions (draft editable, no auto-send)

### What to Avoid

- Blind copying of one product (e.g. "just copy Amazon")
- Enterprise-heavy (SLA, macros, triggers, multi-channel)
- Chatbot-centric (real-time chat, marketing automation)
- Scope creep (real-time chat, OCR, carrier API, Stripe — all deferred)

---

## 2. How to Use as Mainline Reference

| Situation | Action |
|-----------|--------|
| **Starting a UI sprint** | Read Page Backbone; ensure hero, primary actions, free input align |
| **Starting a flow sprint** | Read Flow Backbone; ensure entry → triage → collect → handoff → follow-up |
| **Adding or changing state** | Read State Backbone; use need_more, almost_ready, quote_ready, etc. |
| **Changing handoff format** | Read Handoff Backbone; case focus, next move, collected, still needed |
| **Evaluating a feature request** | Check Borrow-vs-Build; defer list |
| **Scope creep** | Push back using defer list; "not in backbone" |

---

## 3. How Future Sprints Should Align

- **Before starting:** Which backbone(s) does this sprint touch? Read those sections.
- **During:** Check alignment at key milestones; don't drift.
- **After:** If backbone needs refinement, document why; update with explicit rationale.
- **Never:** Build real-time chat, multi-channel, full ticketing, carrier API, OCR, Stripe, multi-tenant without explicit backbone update and founder approval.

---

## 4. One-Paragraph Summary

We borrow page hierarchy from Stripe, service entry from Amazon, handoff context from Intercom, and ticket/state structure from Zendesk. We adapt all of it for a small California auto insurance broker office serving Chinese-speaking clients. We build vertical-specific: add-car multi-turn, quote-ready, cancellation urgency, missing doc + already_sent, Chen Kui tone. We defer: real-time chat, multi-channel, full ticketing, carrier API, OCR, Stripe, multi-tenant. The four backbones — Page, Flow, State, Handoff — are the stable reference. Future sprints align to them.

---

*End of Founder Mainline Notes*
