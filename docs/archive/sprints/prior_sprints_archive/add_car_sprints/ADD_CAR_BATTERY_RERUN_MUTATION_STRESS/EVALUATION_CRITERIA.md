# Evaluation Criteria — Add-Car Mutation & Battery Re-Run

Use these for **human** grading of each scenario’s **final state** (and critical mid-turns for intent).

## Checklist (each scenario)

1. **Playbook:** Stays on Add-Car / `customer_question` (not spurious `premium_review` / `unclear` unless scenario is explicitly non–add-car).
2. **Extraction:** ZIP, delivery, driver cues parsed when present; `collected_fields` / `still_needed_fields` sane where visible.
3. **Already-sent intent:** Questions or tentative offers must **not** produce “您说材料发过了” unless customer actually asserted send/completion.
4. **Customer-facing reply:** Office-realistic Chinese or English match; not robotic “thank you for reaching out”; not wrong factual claims.
5. **Broker-facing `broker_next_step`:** Actionable; mentions verify materials when customer asserts WeChat/screenshot sent.

## Classification rubric

| Label | Meaning |
|-------|---------|
| **Strong** | All five checks pass; broker comfortable showing verbatim. |
| **Acceptable** | No trust-breaking; minor friction (generic handoff copy, redundant confirm, thin acknowledgment). |
| **Weak** | Confusing customer copy, wrong slot priority, or broker step missing obvious action. |
| **Trust-breaking** | Wrong category, false “already sent,” or customer-visible contradiction. |

## Regression rules

- **Regression:** Previously passing `ACB-*` or ACE* scenario now fails automation (`weak` classification) or shows trust-breaking behavior.
- **Fixed:** Prior known failure mode no longer reproduces on the same or mutation string.
