# Top Scenarios Selection Spec

**Sprint:** Top Scenarios Hardening Master Sprint

---

## In-Scope Scenarios (Loop 1 + Loop 2)

| # | Scenario | Why High-Value | Why Common | Why Now |
|---|----------|----------------|------------|---------|
| 1 | **Add-car quote** | Revenue driver; multi-turn collection | Daily; Chinese + English | Already strong; harden ultra-short + add-driver edge |
| 2 | **Payment issue / cancellation risk** | Urgency; same-day action | High frequency | Premium-vs-payment disambiguation gap |
| 3 | **Missing document / already sent** | Operational pain; "发过了" frustration | Very common | Already strong; minor phrasing gaps |
| 4 | **Remove vehicle / policy change** | Retention; clean removal | Common | Already strong; no-vehicle-context works |
| 5 | **Premium too high / renewal** | Retention; options review | Very common | "我发你账单了" misroutes to payment — fix |
| 6 | **Claim intake** | First-response guidance | Moderate | Already strong |
| 7 | **Add driver** | Policy change; teen/spouse | Common | **NEW:** Routes to unclear — add markers + reply |
| 8 | **Bundling / discount** | Cross-sell; home+auto | Moderate | **NEW:** Routes to unclear — add markers |

## Out-of-Scope (This Sprint)

- DMV/SR-22 (already works)
- English notice confusion (already works)
- Underwriting follow-up (already works)
- Mixed-intent (complex adversarial passes)
- Full add-driver multi-turn (defer to next sprint)

## Priority Order

1. **Loop 1:** Add-car, payment, missing document — fix premium-vs-payment, add-driver, bundling
2. **Loop 2:** Remove vehicle, premium, claim — verify no regressions; add driver + bundling markers

---

*See: 03_SCENARIO_HANDLING_MATRIX_SPEC.md*
