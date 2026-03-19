# Acceptance / Trial Readiness Criteria

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. Trial Package Clarity

| Criterion | Pass when |
|-----------|-----------|
| Package name defined | Real Broker Trial Package (or Chen Kui 1-Week Pilot) |
| Target broker profile | California auto broker, Chinese-speaking clients, 1–5 person office |
| Included scenarios | 5 core (SIM1–SIM5) + 2 extended; clearly listed |
| Excluded items | Email/WeChat integration, OCR, CRM, multi-tenant, Stripe |

---

## 2. Included Scenario Usefulness

| Criterion | Pass when |
|-----------|-----------|
| Cancellation risk | Urgency, same-day action, broker next move clear |
| Missing document | Structured follow-up, verify receipt, clarification |
| Add-car quote | Multi-turn, Collected chips, handoff at turn 3 |
| Premium review | Retention follow-up, policy/bill mentioned |
| Claim intake | First-response guidance, collected/still-needed |

---

## 3. Office Usability

| Criterion | Pass when |
|-----------|-----------|
| Broker can paste and start case | Yes |
| Broker sees Case focus, next move, Collected, Still needed | Yes |
| Broker can reopen, update status, save follow-up | Yes |
| Broker gets draft to edit | Yes |
| No auto-send | Yes |
| Guardrail passes | `guardrail_inbox_triage.sh` PASS |

---

## 4. Setup Simplicity

| Criterion | Pass when |
|-----------|-----------|
| Pre-trial checklist exists | Yes |
| Founder demo queue loads | Yes |
| Simulation Assistant works | SIM1–SIM5 runnable |
| One-sentence pitch | "试用一个月：帮你把客户发来的messy消息整理成结构化case..." |

---

## 5. Measurable Value

| Criterion | Pass when |
|-----------|-----------|
| Metrics doc exists | Trial Metrics Spec |
| Value validation questions | 5 questions defined |
| Observation log template | Yes |

---

## 6. Trust / Readiness

| Criterion | Pass when |
|-----------|-----------|
| Founder can explain simply | Yes |
| Broker can understand in 5 min | Yes |
| What remains weak is documented | Yes |

---

## 7. Acceptable to Defer

- Email/WeChat/SMS integration
- OCR upload
- Full CRM
- Multi-tenant, Stripe
- Carrier API integration

---

*End of Acceptance Criteria*
