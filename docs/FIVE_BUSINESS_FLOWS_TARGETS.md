# 5 Business Flows — Targets and Acceptance Criteria

**Sprint:** 5 Business Flows Verticalization  
**Purpose:** Define what "good enough for demo" means for each flow before implementation.

---

## Flow 1: Add Car / New Quote

### Customer-side success
- Customer asks naturally (Chinese, English, mixed, shorthand)
- System asks for year, model, VIN (if available), zip, delivery, driver — not generic "provide more context"
- Max 2–3 turns; hand off when year+model+zip (or equivalent) present

### Broker-side success
- Case shows "Add car / new quote"
- Collected: year, model, zip, delivery, driver (when extractable)
- broker_next_step: "Collect new vehicle details, confirm delivery and driver, then quote or add same day"

### Simulation success
- Add-car variants (AC1–AC10) → customer_question, draft contains 报价/VIN/quote
- Multi-turn MT1, MT2, MT11, MT13, MT15, MT16 pass

### Intentionally NOT in scope
- Live carrier quote pricing
- VIN validation
- Lienholder lookup

---

## Flow 2: Renewal / Premium Too High / Coverage Adjustment

### Customer-side success
- Customer says premium too high, wants to lower, asks about coverage change
- System asks for policy/bill, explains review path
- Hand off when policy or bill mentioned

### Broker-side success
- Case shows "Premium review / too high"
- broker_next_step: "Review why premium increased, check vehicle/driver/address/coverage changes, send 1–2 realistic options"

### Simulation success
- Premium review variants (PR1–PR5) → customer_question, draft contains 保费/policy/bill
- Multi-turn MT4 pass

### Intentionally NOT in scope
- Rate comparison engine
- Coverage recommendation engine

---

## Flow 3: Claim Intake / Accident First Response

### Customer-side success
- Customer says "刚出事故" / "car accident just happened" / "what should I collect?"
- System gives first-step guidance: safety, photos, other driver info, license, insurance
- Explains what to collect and how office follows up
- Hand off after 1–2 turns with clear broker next step

### Broker-side success
- Case shows "Claim intake / accident first response"
- broker_next_step: "Confirm accident details, guide client to report claim, collect photos and other-driver info"
- client_prep: "Accident details, photos, other driver info, policy number"

### Simulation success
- Claim variants → customer_question (or new claim_intake category), draft contains 事故/accident/collect/照片/photos

### Intentionally NOT in scope
- Claims adjudication
- Damage assessment
- Carrier claims portal integration

---

## Flow 4: Notice / Payment / Cancellation Confusion

### Customer-side success
- Customer confused by payment failed, cancel pending, last notice, "is this urgent?"
- System states urgency when applicable, asks for notice/screenshot
- Hand off when notice or payment proof mentioned

### Broker-side success
- Case shows "Payment failed" or "Cancellation warning"
- Urgency: high or critical when appropriate
- broker_next_step: "Confirm payment status, check carrier balance, help client fix today"

### Simulation success
- Payment/cancellation variants (PF1–PF5) → payment_lapse_expiration or cancellation_warning
- Draft contains 付款/payment/今天/notice

### Intentionally NOT in scope
- Payment processing
- Carrier payment API

---

## Flow 5: Document Chase / Underwriting Follow-up

### Customer-side success
- Customer says "I already sent it" / "缺材料" / "declaration page missing"
- System names the missing item, asks for resend or confirms we will check
- Explains document meaning when confused (declaration page, garaging proof)
- Hand off when item + sent status clear

### Broker-side success
- Case shows "Missing document"
- Collected: which items resent, which still needed
- broker_next_step: "Confirm what's missing, check if carrier received, resend or chase before file stalls"

### Simulation success
- Missing doc variants (MD1–MD5) → missing_document
- Draft contains 发我/核对/declaration/garaging

### Intentionally NOT in scope
- OCR of documents
- Document verification

---

*End of flow targets*
