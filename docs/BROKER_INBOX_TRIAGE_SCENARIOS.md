# Broker Inbox Triage — Scenario Pack

**Purpose:** Reusable test cases for triage MVP. Each scenario has input, expected outputs, and notes.

---

## Scenario Format

Each scenario includes:

- `id`: Short identifier
- `input`: Example message text
- `expected_category`: Issue category
- `expected_urgency`: low | medium | high | critical
- `expected_manual_followup`: boolean
- `notes`: What broker next step / client draft should convey

---

## Scenarios

### S1: Missing Signature

**Input:**
```
客户发来截图：保单申请需要签名，但客户说"我签了呀，怎么还说要签？"
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
**Notes:** Immediate broker action; client needs to pay or contact carrier.

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
客户发来一张DMV的信，问"这是什么意思？我需要做什么？"
```

**Expected:** `customer_question`, `medium`, `true`  
**Notes:** Broker should explain in plain language; client may need to take action.

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
**Notes:** Client needs to update payment; risk of lapse.

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

**Expected:** `missing_document` or `informational`, `medium`, `true`  
**Notes:** Broker provides dec page; client may need to forward to escrow.

---

### S12: HOA / Lienholder Notice

**Input:**
```
Lienholder requests certificate of insurance. Policy number and effective dates needed.
```

**Expected:** `missing_document` or `informational`, `medium`, `false`  
**Notes:** Standard request; broker can generate COI and draft reply.

---

## Machine-Readable Format

See `configs/inbox_triage_scenarios.json` for JSON format used by scenario runner.

---

*End of scenario pack*
