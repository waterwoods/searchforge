# Acceptance / Sellability Criteria

**Purpose:** Define practical criteria for package clarity, scenario quality, handoff usefulness, office usefulness, pilot-readiness, and explainability.

---

## 1. Package Clarity

| Criterion | Pass when |
|-----------|-----------|
| Package has a clear name | "Broker Standard Package" or equivalent |
| Target user is explicit | Small CA auto broker; Chinese-speaking clients |
| Included scenarios are listed | 7 core scenarios defined |
| Excluded/deferred are listed | Email/WeChat/SMS, CRM, multi-tenant, etc. |

---

## 2. Included Scenario Quality

| Criterion | Pass when |
|-----------|-----------|
| Top 5 scenarios pass simulation | SIM1–SIM5 or equivalent |
| Add-car handoff at turn 3 | SIM3, SIM15 |
| Cancellation risk shows urgency | Same-day action; critical |
| Missing document shows verify receipt | "Customer says sent" path |

---

## 3. Handoff Usefulness

| Criterion | Pass when |
|-----------|-----------|
| broker_next_step is operational | One sentence; actionable |
| Collected / Still needed chips show | Add-car, renewal, claim, missing-doc |
| Client reply draft is editable | Broker can copy and edit |

---

## 4. Office Usefulness

| Criterion | Pass when |
|-----------|-----------|
| Queue shows Work now / Waiting | Grouping visible |
| Case focus is clear | Add car, renewal, claim, missing doc |
| Reopen shows Resume here | waiting_on, next_contact_by, note |

---

## 5. Pilot-Readiness

| Criterion | Pass when |
|-----------|-----------|
| Guardrail passes | `bash scripts/guardrail_inbox_triage.sh` |
| Smoke check passes | `bash scripts/unified_intake_smoke_check.sh` |
| UI builds | `cd ui && npm run build` |

---

## 6. Explainability to Paying Prospect

| Criterion | Pass when |
|-----------|-----------|
| One-sentence offer exists | "试用一个月：帮你把客户发来的messy消息整理成结构化case..." |
| Founder can demo in 5–10 min | Load founder demo queue → cancellation → missing doc → add-car |
| Value validation questions exist | 5 post-trial questions |

---

## 7. Acceptable to Defer

| Deferred | Acceptable |
|----------|------------|
| Email/WeChat/SMS integration | Yes |
| OCR upload | Yes |
| Full CRM | Yes |
| Multi-tenant | Yes |
| Stripe billing | Yes |

---

*End of Acceptance / Sellability Criteria*
