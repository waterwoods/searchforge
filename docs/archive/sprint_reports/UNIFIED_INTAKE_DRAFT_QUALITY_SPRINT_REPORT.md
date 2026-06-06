# Unified Intake Draft Quality Sprint Report

**Date:** 2026-03-07  
**Sprint focus:** Category-specific `client_reply_draft` quality for rule-based triage

---

## 1. Primary objective

**Target:** Make `client_reply_draft` more tailored by issue category so brokers can copy, lightly edit, and send with less manual rewriting.

**Why it mattered most:** The rule-based path (LLM disabled or unavailable) previously returned the same generic draft for every category: *"Thank you for reaching out. We are reviewing your message and will follow up shortly. If you have any documents to share, please send them at your earliest convenience."* That draft was too generic for cancellation warnings, payment failures, missing documents, and unclear messages—brokers had to rewrite heavily. Improving category-specific drafts directly reduces broker work and moves the product toward repeat use and paid value.

---

## 2. Primary changes made

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Added `_get_category_templates()` with category-specific `broker_next_step`, `client_prep`, and `client_reply_draft` for all 10 categories. Rule-based triage now uses these templates instead of a single generic draft. |
| `scripts/run_inbox_triage_scenarios.py` | Added `DRAFT_QUALITY_PHRASES` and a draft-quality check: for `cancellation_warning`, `payment_lapse_expiration`, and `missing_document`, the draft must contain at least one expected phrase (e.g., "cancellation", "urgent", "payment", "document") to ensure tailored output. |

**What changed in triage.py:**

- **Before:** One generic draft for all categories.
- **After:** Each category has its own:
  - `broker_next_step` (actionable for broker)
  - `client_prep` (what client should prepare)
  - `client_reply_draft` (client-facing, broker-editable)

**Why it helps:** Brokers see drafts that acknowledge the issue, mention urgency when appropriate, and state the next step. The draft is still editable and avoids legal/financial promises.

---

## 3. Draft-quality verification result

| Category | Before | After |
|----------|--------|-------|
| **cancellation_warning** | Generic "reviewing... follow up shortly" | "This notice requires urgent attention—your policy may be at risk of cancellation. Please check your payment status or contact us right away..." |
| **missing_document** | Same generic | "We received a request for an additional document. Please send a clear copy... If you already sent it, let us know and we'll verify on our end." |
| **payment_lapse_expiration** | Same generic | "Your recent payment did not go through... Please update your payment method... or reply with your preferred way to pay so we can assist." |
| **unclear** | Same generic | "We'd like to make sure we understand correctly. Could you share a bit more detail or the full notice so we can give you an accurate response?" |
| **customer_question** | Same generic | "We're happy to help explain what this means. We're reviewing it and will get back to you shortly with a clear summary and any next steps..." |
| **missing_signature** | Same generic | "It looks like we still need a signature on one of the documents. Please check which form or page is indicated—sometimes it's a different section..." |
| **underwriting_followup** | Same generic | "Underwriting has requested some additional information with a deadline. We'll help you gather what's needed—please reply with any details..." |
| **renewal_reminder** | Same generic | "Your renewal is coming up soon. No action is needed right now—we'll reach out when it's time to review your options." |
| **informational** | Same generic | "Everything looks good on our end—no further action is needed from you at this time." |
| **policy_delay_pending** | Same generic | "Your policy is being processed and we expect an update within 5–7 business days. We'll notify you as soon as it's ready." |

**Result:** Better across all categories. Drafts are now category-appropriate and closer to usable broker messages.

---

## 4. Secondary objective (done)

**Selected:** Add a small label clarifying that the draft should be reviewed before sending.

**Why chosen:** Reduces risk of brokers sending drafts without review; aligns with the standard that the draft is "editable by broker before sending."

**Change:** In `ui/src/pages/UnifiedIntakePage.tsx`, added `— review before sending` next to "Client-facing draft (copy to WeChat/email)".

**Result:** Label is visible and reinforces that the draft is a starting point, not final.

---

## 5. Validation / guardrail result

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | PASS | UI compiles |
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | 18/18 PASS | Category, urgency, manual_followup, draft quality |
| `bash scripts/guardrail_inbox_triage.sh` | PASS | Scenario pack, output shape, API route |
| `PYTHONPATH=. python3 scripts/test_inbox_triage_api.py` | PASS | API contract, required fields |
| `bash scripts/unified_intake_smoke_check.sh` | PASS | Guardrail + manual smoke steps |

---

## 6. Business / broker impact

- **More useful drafts:** Brokers get category-specific drafts that acknowledge the issue, mention urgency when needed, and state the next step.
- **Less rewriting:** Brokers can copy, lightly edit, and send instead of rewriting from scratch.
- **Product value:** Moves toward repeat use and paid value by making the copy-to-client flow practical.

---

## 7. Manual-work reduction

- **Andy no longer needs to:** Manually imagine or rewrite drafts for cancellation, payment, missing doc, unclear, etc., when using the rule-based path.
- **Cursor can now:** Generate category-specific drafts in the rule-based triage path.
- **OpenClaw can now:** Validate draft quality via `DRAFT_QUALITY_PHRASES` in the scenario runner.

---

## 8. Remaining blocker(s)

None. Draft quality is improved; validation passes.

---

## 9. Recommended next sprint

**One clear next step:** Add 1–2 scenarios with `expected_draft_contains` (or similar) in the scenario pack for `customer_question` and `unclear` to lock in draft tone/structure expectations, or extend `DRAFT_QUALITY_PHRASES` to those categories if desired.

---

*Sprint completed on Unified Intake mainline. No scope expansion.*
