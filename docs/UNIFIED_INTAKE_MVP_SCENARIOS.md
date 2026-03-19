# Unified Intake MVP — Scenario Pack

**Purpose:** Reusable test cases for triage MVP. Each scenario has input, expected outputs, and notes.

**Machine-readable format:** `configs/inbox_triage_scenarios.json`  
**Proxy calibration pack:** `configs/chen_kui_proxy_calibration_cases.json`

---

## Scenario Format

Each scenario includes:

- `id`: Short identifier (S1–S12)
- `input`: Example message text
- `expected_category`: Issue category
- `expected_urgency`: low | medium | high | critical
- `expected_manual_followup`: boolean
- `expected_draft_language`: optional `zh` or `en` when the client-facing draft should clearly favor one language
- `expected_draft_contains_any`: optional phrases that help lock in realistic draft wording
- `notes`: What broker next step / client draft should convey

---

## Demo Showcase Set

Use these first when presenting the product:

| Showcase | Scenario | Why it works in demo |
|----------|----------|----------------------|
| **Urgent** | `S3` / `R2` / `R6` | Makes urgency and same-day broker action obvious |
| **Operational** | `S2` / `R5` / `R7` | Shows document chase + broker coordination on cleaner and messier wording |
| **Messy real-world** | `R7` / `S7` / `R4` | Shows value on broker shorthand, vague client messages, and fragmented notices |
| **Payment risk** | `S9` / `R3` / `R8` | Shows a believable high-risk broker case even when wording is short or broken |

If time is short, demo in this order: `S3` → `S2` → `R7`.

**Founder-demo route now preferred:** Load founder demo queue → `R12` (cancellation risk, opens first) → reopen `R7` from Recent cases → `R14` or `R13`.

- `R12` = cancellation risk / same-day broker action
- reopened `R7` = saved follow-up continuity
- `R14` or `R13` = everyday quote / retention work that helps justify payment

**Founder demo queue (10 cases):** cancellation risk, missing document follow-up, add car, premium review, DMV/SR-22, payment failed, remove car, English+Chinese confusion, declaration page missing, Chinese cancellation summary.

---

## Scenarios

### S1: Missing Signature

**Input:**
```
客户发来截图：保单申请需要签名，但客户说「我签了呀，怎么还说要签？」
```

**Expected:** `missing_signature`, `medium`, `true`  
**Notes:** Broker should verify which document, which field; client may have signed wrong place.

---

### S2: Missing Document

**Input:**
```
Underwriting requested driver's license copy. Client says "I already sent it last week."
```

**Expected:** `missing_document`, `medium`, `true`  
**Notes:** Broker should confirm what was received; may need to resend or escalate to underwriting.

---

### S3: Cancellation Warning

**Input:**
```
Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.
```

**Expected:** `cancellation_warning`, `critical`, `true`  
**Notes:** Immediate broker action; client needs to pay or contact carrier. Strongest urgency showcase.

---

### S4: Policy Delay / Pending Issuance

**Input:**
```
Your policy is pending issuance. We will notify you within 5-7 business days.
```

**Expected:** `policy_delay_pending`, `low`, `false`  
**Notes:** Informational; broker can draft "we're on it, expect update soon."

---

### S5: Underwriting Follow-up

**Input:**
```
Underwriting needs clarification on prior claims. Please respond within 10 days.
```

**Expected:** `underwriting_followup`, `high`, `true`  
**Notes:** Broker should help client gather info; deadline matters.

---

### S6: Renewal Reminder

**Input:**
```
Renewal reminder: Your policy renews in 45 days. No action needed at this time.
```

**Expected:** `renewal_reminder`, `low`, `false`  
**Notes:** Informational; optional broker outreach for retention.

---

### S7: Customer Asks "What Does This Mean?"

**Input:**
```
客户发来一张DMV的信，问「这是什么意思？我需要做什么？」
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** Broker should explain in plain language; client may need to take action. Good for a broker-assist story.

---

### S8: Screenshot with Unclear Urgency

**Input:**
```
[Forwarded email, subject: "Important - Action Required" but body is just a generic marketing footer]
```

**Expected:** `unclear`, `medium`, `true`  
**Notes:** Ambiguous; broker should review and clarify with client.

---

### S9: Payment / Lapse / Expiration

**Input:**
```
Payment failed. Your card on file was declined. Please update payment method.
```

**Expected:** `payment_lapse_expiration`, `high`, `true`  
**Notes:** Client needs to update payment; risk of lapse. Good secondary high-priority demo case.

---

### S10: Low-Urgency Informational

**Input:**
```
Your proof of insurance has been emailed to the DMV. No further action required.
```

**Expected:** `informational`, `low`, `false`  
**Notes:** Can send brief "all set" reply.

---

### S11: Escrow / Mortgage Request

**Input:**
```
Escrow department requests updated declaration page for loan refinance. Due in 14 days.
```

**Expected:** `missing_document`, `medium`, `true`  
**Notes:** Broker provides dec page; client may need to forward to escrow.

---

### S12: HOA / Lienholder Notice

**Input:**
```
Lienholder requests certificate of insurance. Policy number and effective dates needed.
```

**Expected:** `informational`, `medium`, `false`  
**Notes:** Standard request; broker can generate COI and draft reply.

---

### R7: Mixed-Language Document Chase

**Input:**
```
UW follow up - need dec page + garaging proof. 客户说上周发过了
```

**Expected:** `missing_document`, `medium`, `true`  
**Notes:** Realistic broker shorthand plus client summary; should still stay out of generic `unclear`.

---

### R8: Broken Payment / Interruption Wording

**Input:**
```
AutoPay failed again, please update card to avoid interruption in coverage
```

**Expected:** `payment_lapse_expiration`, `high`, `true`  
**Notes:** Short payment failure wording should still feel like a real lapse-risk case, not a vague clarification request.

---

### R9: Mixed Overdue / Policy-Stop Question

**Input:**
```
客户问 这个是不是保单要停了? 他说昨天收到账单 overdue
```

**Expected:** `payment_lapse_expiration`, `high`, `true`  
**Notes:** Mixed Chinese + English wording should still surface payment/lapse risk rather than falling back to a generic unclear bucket.

---

### R10: DMV / SR-22 Help Wording

**Input:**
```
Need SR-22 filing proof for DMV suspension clearance, what should client bring?
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** DMV / suspension help wording should feel like a real broker-help question, not an unclassified fragment.

---

### R11: English Payment Notice With Chinese Client Question

**Input:**
```
客户问：这个英文 notice 说 payment failed，我现在怎么办？
```

**Expected:** `payment_lapse_expiration`, `high`, `true`  
**Notes:** The draft should answer back in short Chinese instead of falling into a generic English support tone.

---

### R12: English Cancellation Notice With Chinese Summary

**Input:**
```
Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？
```

**Expected:** `cancellation_warning`, `critical`, `true`  
**Notes:** Mixed-language cancellation wording should still lead to a short Chinese broker-usable draft.

---

### R13: Premium Too High

**Input:**
```
客户说这个月保费太高了，能不能看看怎么降一点
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** Should read like a real broker reviewing why the premium changed and what can realistically be adjusted.

---

### R14: Add-Car Quote Request

**Input:**
```
客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** Should ask for concrete vehicle details and keep the quote/add-car workflow moving instead of falling back to `unclear`.

---

### R17: English Add-Car Quote Request

**Input:**
```
I bought a new BMW X5, how much is insurance?
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** English add-car/quote request; should ask for vehicle details (year, model, VIN, delivery date, zip, driver), not generic "provide more context."

---

## Fragmented Demo Cases

These cases matter because they feel closer to what a broker actually receives:

- `R2` mixed-language cancellation summary
- `R4` vague screenshot / customer confusion
- `R5` fragmented document request
- `R6` Chinese cancellation warning
- `R7` mixed shorthand document chase
- `R8` short AutoPay interruption risk
- `R9` mixed overdue / policy-stop question
- `R10` DMV / SR-22 help wording
- `R11` English payment notice with Chinese client question
- `R12` English cancellation notice with Chinese summary
- `R13` premium-too-high review request
- `R14` add-car quote request
- `R15` remove-car request
- `R16` declaration page missing with client confusion
- `R17` English add-car quote request

For demo quality, these should still produce a coherent case card, not just technically valid JSON.

The founder-demo starter queue should feel alive with this mix:

- one same-day payment/cancellation risk case
- one waiting-on-client document case with a saved next-contact date
- one add-car quote case
- one premium-review case
- one DMV / SR-22 help case

---

## Category Coverage Summary

| Category | Scenarios |
|----------|-----------|
| missing_signature | S1 |
| missing_document | S2, S11, R5, R7, R16 |
| cancellation_warning | S3 |
| policy_delay_pending | S4 |
| underwriting_followup | S5 |
| renewal_reminder | S6 |
| customer_question | S7, R10, R13, R14, R15, R17 |
| payment_lapse_expiration | S9, R3, R8, R9 |
| informational | S10, S12 |
| unclear | S8 |

---

*End of scenario pack*
