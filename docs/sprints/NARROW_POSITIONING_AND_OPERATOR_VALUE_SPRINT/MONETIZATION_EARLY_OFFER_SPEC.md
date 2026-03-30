# Monetization / Early Offer Spec — Small Office, Pilot-First

## What the office is paying for (the SKU)

Not “software in the abstract”—they pay for **outcomes at intake**:

1. **Structured cases** from pasted messages (less chaos).
2. **Faster drafts** to customers (edit vs write from scratch).
3. **Clearer handoffs** to the broker (one next step, visible collected/needed).
4. **Escalation visibility** for time-sensitive items (payment/cancel risk, etc.).

Package this as **“Broker Standard Package”** language from `docs/STANDARD_SCENARIO_PACKAGE.md` but **price the narrow slice**: intake + workbench ritual, not CRM replacement.

## Why a small office might accept a monthly fee

- **Labor math:** If an assistant saves **even 20–40 minutes/day** on triage and re-asks, a modest monthly fee is cheaper than incremental headcount or overtime.
- **Risk reduction:** Missed cancellations and payment lapses have **direct** revenue and E&O-adjacent stress; tooling that **surfaces** urgency is emotionally legible.
- **Low switching cost trial:** Pilot is **paste-only**—no carrier integration required to **start**.

## Pricing logic (realistic, founder-led)

- **Do not** anchor on enterprise per-seat list prices.
- **Do** anchor on: **pilot monthly** (e.g. one flat fee for one office location) + clear **monthly cap** on usage if needed later.
- **Manual payment** (Zelle/Venmo/WeChat) remains acceptable per `docs/goals/insurance_paid_pilot_goal.md` for v1.
- **Success metric for first dollars:** testimonial + **repeat use**, not feature count.

## Trial / pilot framing (believable)

- **Length:** 2–4 weeks “try it on real pasted messages.”
- **Success criteria:** They paste real traffic; drafts are **mostly edited, not discarded**; broker names **one** scenario where fire-drill risk dropped (e.g. billing, missing doc, add-car).
- **Explicit non-promise:** No OCR, no inbox auto-pull, no auto-send—**reduces** refund/churn from mismatched expectations.

## Best first customer profile

- **Small CA auto broker** (1–5 people), **Chinese-speaking clientele**, heavy WeChat/email text.
- Already **manually** triages; not expecting AMS replacement.
- **Chen Kui–shaped** reference customer is intentional: same segment, repeatable playbook.

## Proof before broader selling

- **Guardrail + scenario batteries PASS** before claiming stability (`scripts/guardrail_inbox_triage.sh`, scenario runners).
- **1 broker** using real messages with **documented** before/after anecdote.
- **Second broker drill** style validation before claiming **hot-plug** in sales copy—say **“configurable for same-industry offices”** until isolation audits are green across all promised paths.

---

*Aligned with: `docs/goals/insurance_paid_pilot_goal.md`, `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`.*
