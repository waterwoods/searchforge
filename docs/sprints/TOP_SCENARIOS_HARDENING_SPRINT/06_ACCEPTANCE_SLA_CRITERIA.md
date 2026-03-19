# Acceptance / SLA Criteria

**Sprint:** Top Scenarios Hardening Master Sprint

---

## Realism

- Add driver "加个司机" → customer_question with add-driver reply (not unclear)
- Bundling "一起买能打折" → customer_question with bundling/premium-style reply (not unclear)
- Premium + "我发你账单了" → customer_question / premium_review (not payment_lapse_expiration)

## Scenario Coverage

- All 53 existing inbox triage scenarios pass
- New scenarios for add-driver, bundling, premium-bill-sent pass

## Correct Routing

- No regression on payment, cancellation, missing_document
- Premium context takes precedence over payment when both could match

## Multi-Turn Usefulness

- 38 multi-turn simulations remain Strong
- No new Weak classifications

## Handoff Quality

- Unchanged; already meets MATURE_INTAKE_SKELETON

## Case Summary Usefulness

- Unchanged; already strong

## Acceptable to Defer

- LC-AC3 (driver correction handoff timing) — 1 Friction acceptable
- Full add-driver multi-turn collection — next sprint
- Full bundling workflow — next sprint

---

*See: 07_FOUNDER_DEMO_INSPECTION_NOTES.md*
