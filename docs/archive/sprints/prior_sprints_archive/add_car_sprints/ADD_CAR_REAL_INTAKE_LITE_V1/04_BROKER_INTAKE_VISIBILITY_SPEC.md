# Broker Intake Visibility Spec

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** Define what broker sees in workbench for add-car.

---

## 1. What Broker Sees

| Element | Content |
|---------|---------|
| **quote_ready_status** | "Quote-ready" / "Almost ready" / "Need more" badge |
| **collected_fields** | year, make_model, zip, delivery_date, primary_driver, vin (as collected) |
| **still_needed_fields** | What office should confirm or request |
| **conversation_summary** | Intent + vehicle concrete + collected hint |
| **broker_next_step** | "Run quote for 2024 Tesla Model Y. Confirm delivery date and driver with client before binding." |

---

## 2. Collected vs Still-Needed Layout

- **Collected:** Green tags; humanized labels (Year, Make/Model, ZIP, Delivery, Primary driver, VIN)
- **Still needed:** Orange tags; humanized labels
- **Quote-ready badge:** Green when quote_ready; gold when almost_ready; orange when need_more

---

## 3. broker_next_step for Add-Car

| State | broker_next_step style |
|-------|-------------------------|
| Quote-ready | "Run quote for {vehicle}. Confirm delivery date and driver with client before binding." |
| Almost ready | "Run quote for {vehicle}. Ask client for delivery date and main driver before binding." |
| Need more | "Ask client for {missing} before running quote." |

---

## 4. What Reduces Broker Rework

1. **Concrete vehicle** — "2024 Tesla Model Y" not just "model"
2. **Quote-ready status** — Broker knows immediately if case is actionable
3. **Clear still-needed** — Broker knows what to verify or request
4. **No redundant asks** — Don't hand off with "please send year" when year was given

---

## 5. Add-Car Case Card Feel

- Structured add-car block: vehicle, zip, delivery, driver, quote_ready_status
- Not a giant form; compact tags + status
- Broker can scan in 2–3 seconds

---

*See also: 03_QUOTE_READY_STATE_SPEC.md, triage.py _build_conversation_summary*
