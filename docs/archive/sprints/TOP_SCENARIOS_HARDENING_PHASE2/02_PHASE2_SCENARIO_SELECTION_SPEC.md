# Phase 2 Scenario Selection Spec

**Sprint:** Top Scenarios Hardening Phase 2

---

## Chosen Scenarios (3–4)

| # | Scenario | Why High-Value | Why Common | Why Now | Broker Follow-Up Reduction |
|---|----------|----------------|------------|---------|----------------------------|
| 1 | **Billing clarification** | Customer confused by bill/notice; wrong route = wrong urgency | "账单什么意思", "bill 看不懂" | **Currently misroutes to payment_lapse_expiration** — urgent when it's a question | Broker gets correct "explain bill" vs "fix payment" |
| 2 | **Remove vehicle** | Policy change; clean removal | 减车, 卖掉了, remove car | Verify 减车 shorthand; add variants if weak | Already strong; ensure no regression |
| 3 | **Claim first notice** | First-response guidance; urgent | 报事故, 刚撞了 | Already strong; verify edge phrasings | No change if strong |
| 4 | **Renewal increase** | Retention; options review | 续保涨价, 续保涨 | Already strong; verify | No change if strong |

---

## Out of Scope

- Add driver correction (LC-AC3) — deferred
- Bundling deepening — Phase 1 sufficient
- Payment vs premium — Phase 1 fixed
- DMV/SR-22, underwriting, mixed-intent

---

## Priority

1. **Loop 1:** Billing clarification (fix misroute); remove vehicle (verify + 减车)
2. **Loop 2:** Claim, renewal (verify); add scenarios if gaps

---

*See: 03_SCENARIO_HANDLING_MATRIX_SPEC_PHASE2.md*
