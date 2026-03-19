# Backend Redeploy + Founder Trial — Acceptance / Operational Criteria

## Pre-Deploy

- [ ] `_is_billing_clarification_request` exists and checks 账单 + 什么意思/看不懂 before payment routing
- [ ] `_is_remove_vehicle_request` matches 减车 + vehicle_context (车)
- [ ] `_is_claim_intake_request` matches 报事故, 刚撞了
- [ ] `_is_premium_review_request` matches 续保涨
- [ ] TSH2 scenarios (BC1, BC2, CL1, RN1, RV1) in inbox_triage_scenarios.json
- [ ] All validation scripts pass (no blocker)

## Deploy

- [ ] `deploy_rag_demo.sh` completes without error
- [ ] Service URL returned
- [ ] /healthz returns 200
- [ ] /readyz returns 200 (or acceptable if Qdrant warming)

## Post-Deploy (Production Truth)

| Scenario | Pass = category + reply behavior |
|----------|-----------------------------------|
| A 账单什么意思 | customer_question, NOT payment_lapse; reply asks for bill, offers to explain |
| B 这个账单我看不懂 | Same as A |
| C 减车，卖掉了 | customer_question; reply asks for sale date/vehicle/transfer |
| D 报事故，刚撞了 | customer_question; reply asks for photos/other driver/what happened |
| E 续保涨了好多，帮我看看 | customer_question; reply asks for policy/bill/renewal notice; NOT payment failure |

## Operational Judgment

- Backend live: yes/no
- Scenarios live: yes/no
- Which passed: list
- Biggest remaining weakness: one sentence
- Andy can test on live frontend: yes/no
