# Scenario Handling Matrix Spec — Phase 2

**Sprint:** Top Scenarios Hardening Phase 2

---

## Billing Clarification (NEW — Fix Misroute)

| Field | Value |
|-------|-------|
| Scenario name | billing_clarification |
| Business goal | Explain bill/notice; NOT payment failure |
| Common phrasings | 账单什么意思, 账单看不懂, bill 什么意思, what does this bill mean |
| Correct interpretation | Customer asking what a bill/notice means — clarification, not urgency |
| First useful reply | "把完整账单或通知发我，我先帮你看一下，再告诉你重点。" |
| Next-best-question | Full bill/notice |
| Route | customer_question (NOT payment_lapse_expiration) |
| Handoff | When full bill/notice provided |
| Guardrails | **Bill + question markers = clarification. Bill + payment_failed/overdue = payment.** |

---

## Remove Vehicle

| Field | Value |
|-------|-------|
| Scenario name | remove_vehicle |
| Business goal | Remove sold vehicle from policy |
| Common phrasings | 减车, 拿掉, 卖车, 删车, remove car, sold |
| Correct interpretation | Vehicle removal request |
| First useful reply | "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。" |
| Guardrails | 减车 = remove vehicle; ensure markers include 减车 |

---

## Claim First Notice

| Field | Value |
|-------|-------|
| Scenario name | claim_intake |
| Common phrasings | 报事故, 刚撞了, accident, file a claim |
| Guardrails | Already strong; verify 报事故 routes correctly |

---

## Renewal Increase

| Field | Value |
|-------|-------|
| Scenario name | premium_review |
| Common phrasings | 续保涨价, 续保涨, premium too high |
| Guardrails | Already in premium_review; verify |

---

*See: 04_CONVERSATION_STRATEGY_SPEC.md (unchanged from Phase 1)*
