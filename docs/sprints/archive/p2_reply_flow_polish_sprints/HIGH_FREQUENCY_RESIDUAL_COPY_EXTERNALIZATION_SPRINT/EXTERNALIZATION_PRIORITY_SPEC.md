# Externalization Priority Spec

## Decision rubric

Externalize **now** only if:

1. Text is **customer-visible** in `client_reply_draft` (or next-ask draft).
2. It appears on a **high-traffic** intent (add-car, premium, payment, common questions).
3. Override is **low risk**: string swap only, no new branches.
4. **A/B testable** with deterministic rule mode (`LLM_GENERATION_ENABLED=0`).

## This sprint (approved: 4 families)

| # | Family | Mechanism | Client B action |
|---|--------|-----------|-----------------|
| 1 | Add-car price caveat | `stitched.add_car_price_caveat` | SoCal strings (本所 / desk) |
| 2 | Document-already-sent tail | `stitched.document_already_sent_tail` | SoCal strings |
| 3 | Add-driver reply | `reply_templates` + `reply_overrides` | SoCal overrides |
| 4 | Bundling reply | `reply_templates` + `reply_overrides` | SoCal overrides |

## Deferred

- Full **premium_review** body (still industry template; only tail was client-specific this round).
- **Missing_signature / underwriting / renewal** customer one-liners → future `reply_templates` keys.
- **Coverage-adjust** and other **handoff suffix** lines still containing 办公室 for Client B.

## Keep in code

- Anything that **changes** when category or `manual_followup_needed` flips (unless already isolated).
- **Regex / marker** lists used for detection.
