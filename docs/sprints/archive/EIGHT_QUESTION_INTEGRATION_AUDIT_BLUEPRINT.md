# Eight-Question Integration Audit — Sprint Blueprint

**Sprint:** Eight-Question Integration Audit + Fix Sprint  
**Date:** 2026-03-14  
**Target budget:** 30–45 minutes

---

## Why This Audit Matters Now

The founder selected **8 high-value auto-insurance question types** for product integration. Before claiming "integrated," we must verify:

- Are they actually wired into the product, or only in docs/config?
- Which are visible and testable from the frontend?
- Which are demo-ready vs docs-only?

**Risk if we skip:** Founder opens frontend tonight and sees only 3–4 of the 8; trust erodes.

---

## What "Integrated Enough" Means

| Level | Definition |
|-------|------------|
| **Fully integrated** | Present in: docs, handling matrix, backend triage logic, inbox/scenario configs, Simulation Assistant, and frontend-visible. Realistic phrasing. Demo-ready. |
| **Partially integrated** | Present in 3–4 of the above; missing from Simulation Assistant or frontend visibility. |
| **Weakly integrated** | Present in docs/config only; backend may route to generic `customer_question` but no tailored handling or visible scenario. |
| **Not integrated** | Not present in any product surface; docs-only or missing. |

---

## What Counts as Partial Integration

- Question type is in backend logic (e.g. `_is_premium_review_request`) but no dedicated Simulation Assistant scenario.
- Scenario exists in inbox_triage but not in Simulation Assistant recommended set.
- Flow type uses a different name (e.g. `renewal_premium` vs `premium_too_high`) but same intent.

---

## What Counts as Missing Integration

- No backend detection (falls to generic `customer_question` or `unclear`).
- No inbox_triage scenario.
- No Simulation Assistant scenario.
- Not visible in founder-facing UI.

---

## The 8 Question Types (Canonical)

1. **new_car_quote** — Add vehicle, get quote  
2. **cancellation_warning** — Policy will cancel  
3. **payment_failed** — Payment issue, lapse risk  
4. **missing_document** — UW requested, client confused or says sent  
5. **already_sent_followup** — Confirmation that document was sent (FAST path)  
6. **notice_confusion** — English notice, client confused  
7. **premium_too_high** — Premium review, want to lower  
8. **claim_intake** — Accident, first-step guidance  

---

*Next: Execution Outline, Acceptance Criteria*
