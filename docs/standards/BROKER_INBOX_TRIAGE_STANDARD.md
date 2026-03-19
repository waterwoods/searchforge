# Broker Inbox Triage — Quality Standard

**Purpose:** What must be true before this MVP is considered useful for internal review.

---

## 1. Output Shape

Every triage result MUST include exactly these six fields:

| Field | Type | Required |
|-------|------|----------|
| `issue_category` | string | Yes |
| `urgency` | string (low/medium/high/critical) | Yes |
| `broker_next_step` | string | Yes |
| `client_prep` | string | Yes |
| `client_reply_draft` | string | Yes |
| `manual_followup_needed` | boolean | Yes |

---

## 2. Issue Categories (MVP Set)

At minimum, the classifier MUST recognize:

- `missing_signature`
- `missing_document`
- `cancellation_warning`
- `policy_delay_pending`
- `underwriting_followup`
- `renewal_reminder`
- `customer_question`
- `payment_lapse_expiration`
- `informational`
- `unclear` (when input is ambiguous)

---

## 3. Urgency Levels

| Level | Meaning |
|-------|---------|
| `critical` | Immediate action; policy at risk |
| `high` | Same-day follow-up |
| `medium` | Within 1–3 business days |
| `low` | Informational; no rush |

---

## 4. Client-Ready Draft Rules

- Professional, courteous tone
- No legal/financial advice beyond general guidance
- No promises broker cannot keep
- Editable by broker before sending
- Bilingual (Chinese/English) acceptable if broker serves Chinese-speaking clients

---

## 5. Escalation Flag

- `manual_followup_needed: true` when: unclear input, high/critical urgency, sensitive topic, or client explicitly asked for broker
- `manual_followup_needed: false` when: clear informational, renewal reminder, or simple document request with clear instructions

---

## 6. Failure / Drift

- **Failure**: Output missing any required field; invalid urgency; unsafe client draft
- **Drift**: Scenario pack regression; new categories added without doc update; escalation logic changed without scenario re-run

---

*End of standard*
