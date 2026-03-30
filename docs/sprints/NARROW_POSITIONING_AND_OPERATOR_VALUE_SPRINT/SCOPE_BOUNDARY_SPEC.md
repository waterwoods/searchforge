# Scope Boundary Spec — Unified Intake (Now / Later / Never)

## Philosophy

Narrow scope makes the product **believable, shippable, and repeatable**. Saying “no” to platform features is how small offices **trust** the pitch.

## In scope **now** (current product promise)

- **Paste-based unified intake** of customer text.
- **Triage output:** issue category, urgency, broker_next_step, client_prep, client_reply_draft, manual_followup_needed (see `REQUIRED_FIELDS` in `triage.py`).
- **Workflow / case hints:** collection stage, collected vs still needed fields, handoff readiness (where implemented).
- **Broker workbench UX:** queue, case sheet, follow-up memory, reopen context, founder demo queue—**as packaged** in standard scenario doc.
- **High-frequency scenario coverage** aligned with the **7 core scenarios** (add-car as flagship, plus billing, docs, renewal, claim first notice, talk-to-agent, etc.).
- **Client pack + industry config** for same-CA-auto replication (voice, handoff phrases, UI copy); **improving** isolation where audits flag leaks.

## Out of scope **now** (do not sell or build toward in the same sprint)

- **Full policy execution** (bind, endorse, cancel on behalf of customer).
- **Carrier-side completion** (API actions, automatic uploads to carrier portals).
- **Complex policy advice / legal or suitability judgment** beyond retrieval-assisted demo (RAG demo is a **different** surface from Unified Intake triage).
- **Complete CRM replacement** (customer 360, pipeline, commissions, accounting).
- **Full multi-intent automation** across arbitrary insurance lines and jurisdictions.
- **Generalized all-insurance office automation** (“runs your agency”).

## Maybe later (explicitly deferred, could return with new product phase)

- Email / WeChat / SMS **integration** (inbound connectors).
- OCR / attachment ingestion.
- Deeper case **persistence** and multi-user **production** ops model.
- Multi-tenant **auth** and Stripe (per paid pilot goal non-goals for v1).
- Broader **line-of-business** (home, commercial) **after** CA auto intake is a repeatable SKU.

## Never / not this product version

- **Autonomous outbound** messaging without human approval for broker-facing comms (violates trust model).
- **“Platform for every vertical”** as the near-term strategy—**cross-industry expansion is not the current priority**; same-industry hot-plug is.

## Boundary table (founder cheat sheet)

| Topic | Now | Not now |
|-------|-----|---------|
| Intake structuring | Yes | — |
| Draft generation (editable) | Yes | Auto-send |
| Urgency / escalation | Yes | Guaranteed legal/compliance correctness |
| Workbench / queue | Yes (package) | Full CRM |
| Add-car path | Flagship demo path | End-to-end quote engine |
| Client packs | Yes (replication enabler) | Zero engineering per broker without effort |

---

*Sources: `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`, `docs/goals/insurance_paid_pilot_goal.md` (non-goals), `docs/STANDARD_SCENARIO_PACKAGE.md` (not included).*
