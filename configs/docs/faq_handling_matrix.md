# FAQ Handling Matrix — Auto Insurance Broker

**Source:** Auto Insurance FAQ Intake Corpus (configs/auto_insurance_faq_intake_corpus.json)  
**Sprint:** FAQ Corpus Productization  
**Purpose:** Office operating doc — customer asks X → office says Y → still need Z → route

---

## Selected Top 8 Question Types

| # | Topic | Route | Why Selected |
|---|-------|-------|--------------|
| 1 | new_car_quote | LLM | Top frequency, mixed language, progressive ask |
| 2 | cancellation_warning | LLM | Critical urgency, must not downgrade |
| 3 | payment_failed | LLM | High urgency, lapse risk |
| 4 | missing_document | LLM | Turn 1; mixed broker shorthand |
| 5 | already_sent_followup | FAST | Turn 2+; rule handoff works |
| 6 | notice_confusion | LLM | English notice, client confused |
| 7 | premium_too_high | LLM | Retention; must NOT get renewal_reminder |
| 8 | claim_intake | LLM | First-response guidance, hit-and-run variant |

---

## Handling Framework by Type

### Q1 — new_car_quote (Add vehicle, get quote)

| Field | Content |
|-------|---------|
| **Customer asks** | 我买了台宝马X5，想问下保费多少钱 / 宝马x5，多少钱 / I bought a new BMW X5, how much is insurance? |
| **Office says first** | Acknowledge vehicle; ask for year, model, zip (or delivery/driver). Progressive: 1–2 things at a time. |
| **Still need to collect** | year, model or VIN, zip or address, delivery date, primary driver |
| **Do NOT overpromise** | Never quote dollar amount without full underwriting |
| **Trust boundary** | Human must confirm quote |
| **Route** | LLM |

---

### Q2 — cancellation_warning (Policy will cancel)

| Field | Content |
|-------|---------|
| **Customer asks** | Notice: Policy will be cancelled in 7 days. / 这个是不是保单要停了？我昨天收到账单 overdue |
| **Office says first** | Immediate urgency; ask for notice, payment proof; today action. |
| **Still need to collect** | notice, payment status or screenshot |
| **Do NOT overpromise** | Never confirm policy status |
| **Trust boundary** | Human handles |
| **Route** | LLM |

---

### Q3 — payment_failed (Payment issue, lapse risk)

| Field | Content |
|-------|---------|
| **Customer asks** | Payment failed. Your card on file was declined. / payment failed，现在怎么办 / 这个英文 notice 说 payment failed，我现在怎么办？ |
| **Office says first** | State urgency; ask for notice or payment proof; today action. |
| **Still need to collect** | notice, payment screenshot, callback number |
| **Do NOT overpromise** | Never confirm payment status |
| **Trust boundary** | Human verifies with carrier |
| **Route** | LLM |

---

### Q4 — missing_document (UW requested, client confused or says sent)

| Field | Content |
|-------|---------|
| **Customer asks** | 要驾照 copy，我上周就发过了 / UW follow up - need dec page. 上周发过了 |
| **Office says first** | Name the item; ask for resend or confirm we will verify. |
| **Still need to collect** | item identified, sent status clear |
| **Do NOT overpromise** | Never confirm carrier received |
| **Trust boundary** | Human verifies with underwriting |
| **Route** | LLM (Turn 1) |

---

### Q5 — already_sent_followup (Confirmation that document was sent)

| Field | Content |
|-------|---------|
| **Customer asks** | 发你了 / 我发了截图 / sent / 上周发过了 |
| **Office says first** | Acknowledge; hand off to broker to verify. |
| **Still need to collect** | (none — broker verifies) |
| **Do NOT overpromise** | Never confirm receipt |
| **Trust boundary** | Broker verifies |
| **Route** | FAST |

---

### Q6 — notice_confusion (English notice, need explanation)

| Field | Content |
|-------|---------|
| **Customer asks** | 这张DMV信什么意思？我需要做什么？ / 这个英文 notice 什么意思？ / what does this notice mean |
| **Office says first** | Reassure; ask for full notice or clearer photo; we will explain. |
| **Still need to collect** | full notice, clearer photo |
| **Do NOT overpromise** | Never interpret legal/formal notice without human review |
| **Trust boundary** | Human interprets |
| **Route** | LLM |

---

### Q7 — premium_too_high (Premium review, want to lower)

| Field | Content |
|-------|---------|
| **Customer asks** | 这个月保费太高了，能不能看看怎么降一点 / 续保涨了好多，有办法吗 / Client says renewal premium is too high |
| **Office says first** | Reassure options exist; ask for policy or bill (one is enough). |
| **Still need to collect** | current policy, renewal notice, bill |
| **Do NOT overpromise** | No specific dollar savings promise |
| **Trust boundary** | Human reviews options |
| **Route** | LLM (must NOT get renewal_reminder) |

---

### Q8 — claim_intake (Accident, first-step guidance)

| Field | Content |
|-------|---------|
| **Customer asks** | 刚出事故了，要收集什么？ / 刚撞了，对方跑了，我现在先干嘛 / Car accident just happened, what should I collect? |
| **Office says first** | Brief empathy; first-step: safety, photos, other driver info. Hit-and-run: emphasize plate, photos. |
| **Still need to collect** | accident details, photos, other driver info (if not hit-and-run) |
| **Do NOT overpromise** | Never advise on fault or claim outcome |
| **Trust boundary** | Human handles claim |
| **Route** | LLM |

---

## FAST Path Summary

| Topic | When | Why |
|-------|------|-----|
| already_sent_followup | Turn 2+ | Clear pattern; rule handoff works |
| what_to_send | Turn 2+ | Clarification; rules have doc list |
| add_car_field_followup | Turn 2+ | Clear field; rule extraction |
| handoff_confirmation | Turn 2+ | 可以了 / ok — rule handoff |

---

## Human Confirmation Required

| Topic | Why |
|-------|-----|
| moving_zip_change | Policy change; ZIP affects rate |
| adding_driver | Policy change; driver affects rate |
| cancellation_warning | Never confirm policy status |
| payment_failed | Never confirm payment status |
| missing_document (customer_says_sent) | Broker must verify carrier received |
| add_car (VIN, primary_driver) | Quote-critical; human confirms |
