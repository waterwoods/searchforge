# Package 2.0 Handling Matrix Spec

**Sprint:** Standard Scenario Package 2.0  
**Purpose:** Define handling for each chosen scenario end-to-end.

---

## 1. Add-car / Quote

| Dimension | Spec |
|-----------|------|
| **Scenario name** | Quote / Add-car |
| **Business goal** | Collect vehicle + location/delivery for quote; hand off to broker |
| **Common phrasings** | "加一台2025 CR-V", "新车报价", "I bought a BMW X5, how much?", "刚提车，保险多少" |
| **Correct route** | customer_question (add_vehicle sub-type) |
| **First useful reply** | Ask year + model (or zip if year+model present); "先把年份和地址邮编发我，我就能帮你算报价" |
| **Later-turn collection order** | year → model → zip → delivery (or driver); max 3–4 turns |
| **Handoff threshold** | (year+model OR VIN) + (zip OR delivery OR driver) |
| **Summary expectations** | "New quote / new vehicle. Collected: year, model, zip, delivery. X customer message(s). Latest: ..." |
| **Workbench usefulness** | Collected: year, model, zip, delivery; Still needed: (optional) driver, VIN |
| **Major failure modes** | Generic "please provide more context"; wrong category (renewal_reminder); over-asking |
| **Guardrails** | Must NOT route add-car to unclear; must ask for concrete fields, not generic |

---

## 2. Material Collection / Already Sent

| Dimension | Spec |
|-----------|------|
| **Scenario name** | Material collection / already sent |
| **Business goal** | Identify missing item(s); capture "client says sent" status; hand off for broker verification |
| **Common phrasings** | "dec page missing", "客户说上周发了", "need garaging proof, client says already sent" |
| **Correct route** | missing_document |
| **First useful reply** | Name item(s); ask for resend; mention "如果之前发过，跟我说一声，我帮你核对" |
| **Later-turn collection order** | Item 1 status → Item 2 status; handle "garaging 是什么意思" → explain first, then hand off |
| **Handoff threshold** | Item(s) identified + sent status clear (sent, not sent, will send) |
| **Summary expectations** | "Missing document follow-up. Collected: dec page resent, garaging still needed. Client says sent dec page. X messages. Latest: ..." |
| **Workbench usefulness** | Collected: dec_page_sent, garaging_sent (when applicable); Still needed: verify_receipt when client says sent |
| **Major failure modes** | Route to customer_question when doc chase; ignore "already sent"; generic handoff |
| **Guardrails** | When client says "发过了", summary must say "Client says sent"; broker_next_step: verify with carrier |

---

## 3. Renewal Premium / Premium Review

| Dimension | Spec |
|-----------|------|
| **Scenario name** | Renewal increase / premium review |
| **Business goal** | Capture premium concern; get policy/bill for review; hand off |
| **Common phrasings** | "保费太高", "续保涨了", "premium too high", "能不能便宜" |
| **Correct route** | customer_question (premium_review sub-type) |
| **First useful reply** | "我先帮你看...把现在保单和最新账单发我（先发其中一个也行）" |
| **Later-turn collection order** | Policy/bill mention → sent status |
| **Handoff threshold** | Policy or bill mentioned or sent |
| **Summary expectations** | "Premium review / too high. Collected: policy/bill sent. X messages. Latest: ..." |
| **Workbench usefulness** | Collected: policy_bill_sent; Still needed: (none when sent) |
| **Major failure modes** | Route to renewal_reminder (informational); generic "provide more context" |
| **Guardrails** | Must NOT route premium concern to renewal_reminder; must ask for policy/bill |

---

## 4. Payment / Cancellation Risk

| Dimension | Spec |
|-----------|------|
| **Scenario name** | Payment failed / cancellation risk |
| **Business goal** | State urgency; get notice/screenshot; hand off for same-day action |
| **Common phrasings** | "payment failed", "保单要停", "cancellation notice", "已经付了" |
| **Correct route** | payment_lapse_expiration or cancellation_warning |
| **First useful reply** | "现在最关键的是把最新通知或付款截图发我...今天尽快处理" |
| **Later-turn collection order** | Notice/screenshot → "already paid" handling |
| **Handoff threshold** | Notice, screenshot, or "I sent it" / "I paid" mentioned |
| **Summary expectations** | "Payment failed / lapse risk. Collected: client says sent notice/screenshot. X messages. Latest: ..." |
| **Workbench usefulness** | Collected: notice_sent, screenshot_sent, already_paid_claimed; Still needed: verify_with_carrier |
| **Major failure modes** | Miss urgency; ignore "already paid"; generic handoff |
| **Guardrails** | When "已经付了", broker_next_step: "Confirm payment received with carrier; if not, process today" |

---

## 5. Talk to Agent / Case Handoff

| Dimension | Spec |
|-----------|------|
| **Scenario name** | Talk to Agent / case handoff |
| **Business goal** | Detect customer wants human; hand off with draft mentioning office |
| **Common phrasings** | "联系人工", "找陈奎", "talk to agent", "想找办公室" |
| **Correct route** | customer_requested_human |
| **First useful reply** | Draft mentions 陈奎/办公室/联系; hand off immediately |
| **Later-turn** | N/A (hand off on first detection) |
| **Handoff threshold** | Immediate on detection |
| **Summary expectations** | "Customer requested human. X messages. Latest: ..." |
| **Workbench usefulness** | broker_next_step: "Customer wants to speak with office; follow up as requested" |
| **Major failure modes** | Route to customer_question; draft doesn't mention office |
| **Guardrails** | Draft must contain 陈奎 or 联系 or 办公室 |

---

*End of Package 2.0 Handling Matrix Spec*
