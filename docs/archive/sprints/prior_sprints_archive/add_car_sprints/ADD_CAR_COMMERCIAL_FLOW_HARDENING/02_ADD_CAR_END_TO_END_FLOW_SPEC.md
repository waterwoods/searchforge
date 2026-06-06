# Add-Car End-to-End Flow Spec

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Full customer-to-broker flow: entry, intake, field completion, attachment, quote-ready, handoff, broker follow-up.

---

## 1. Flow Overview

```
Customer Entry → Intake (multi-turn) → Field Completion → [Attachment] → Quote-Ready → Handoff → Broker Follow-Up
```

| Phase | Owner | What Happens |
|-------|-------|--------------|
| **Entry** | Customer | Paste message; system infers add-car intent |
| **Intake** | System + Customer | Ask for vehicle, zip, delivery/driver; extract from chat |
| **Field completion** | System | Collected vs still-needed; corrections in same case |
| **Attachment** | Customer (optional) | Upload registration, VIN photo, dec page |
| **Quote-ready** | System | vehicle + zip + (delivery OR driver) → handoff threshold |
| **Handoff** | System | Case created; broker sees workbench |
| **Broker follow-up** | Broker | Run quote; confirm contact; request materials if needed |

---

## 2. Entry

| Step | Behavior |
|------|----------|
| Customer pastes | "加车 2024 Tesla Model Y 90210 下周提车" |
| System infers | add_car intent |
| System extracts | year, make_model, zip, delivery_date |
| If enough | Hand off T1 |
| If not enough | Ask for next missing field |

**Entry variants:**
- Full info T1 → handoff immediately
- Partial info → ask vehicle, zip, or delivery/driver
- Mixed intent ("顺便 coverage 可以调吗") → answer briefly, collect add-car, hand off when ready

---

## 3. Intake (Multi-Turn)

| Turn | Customer | System |
|------|----------|--------|
| T1 | 加车 2024 X5 | Ask zip |
| T2 | 90210 下周提车 | Ask primary driver (optional; HT1 pattern) |
| T3 | 我开 | Hand off |

**Ask-next order:**
1. Vehicle (year + make_model) — when missing
2. Zip — when missing
3. Delivery + driver — when vehicle+zip present, both missing
4. Driver only — when delivery present, driver missing (T2 correction turn)

**Corrections:** "不是X5，是X3" / "ZIP 改成 92620" / "是我老婆开" — same case; extraction uses merged text; latest overrides.

---

## 4. Field Completion

| Field | Min Useful? | Nice to Collect? |
|-------|-------------|------------------|
| year | ✓ | |
| make_model | ✓ | |
| vin | | ✓ |
| zip | ✓ | |
| delivery_date | | ✓ (or primary_driver) |
| primary_driver | | ✓ (or delivery_date) |
| insurance_status | | ✓ |
| additional_drivers | | ✓ |

**Quote-ready threshold:** (year + make_model) OR vin + zip + (delivery_date OR primary_driver)

---

## 5. Attachment (Optional)

| Step | Behavior |
|------|----------|
| Customer uploads | Registration, VIN photo, dec page, screenshot |
| System stores | case_attachments; type, filename |
| Broker sees | "Materials received" or "Registration/dec page optional" |
| Attachment | Does NOT change quote-ready; separate signal |

---

## 6. Quote-Ready

| Condition | Action |
|-----------|--------|
| vehicle + zip + (delivery OR driver) | Hand off |
| First turn with full info | Hand off immediately |
| T2 with full info + doc clarification (garaging) | Answer question, hand off |
| T3 after driver added | Hand off |

**Side questions before handoff:**
- garaging proof 是什么 → Answer; hand off
- coverage 可以调吗 → Brief answer; hand off
- 保单是不是快到期 → Note secondary; hand off add-car

---

## 7. Handoff

| Element | Content |
|---------|---------|
| Case focus | Add car quote |
| quote_ready_status | quote_ready / almost_ready / need_more |
| contact_ready | name + phone or "needed" |
| attachment_received | Yes / No |
| collected_fields | year, make_model, zip, delivery_date, primary_driver |
| still_needed_fields | (empty or verify items) |
| broker_next_step | "Run quote for {vehicle}. Confirm delivery/driver. Confirm name/phone for follow-up." |

---

## 8. Broker Follow-Up

| Broker Action | When |
|---------------|------|
| Run quote | Always when quote-ready |
| Confirm delivery/driver | When collected; verify before binding |
| Confirm name/phone | When contact missing; broker_next_step says so |
| Request materials | When no attachment; optional; broker_next_step says "Registration/dec page optional" |
| Verify correction | When correction badge; use latest collected fields |

---

*See also: 03_ADD_CAR_READINESS_COMPLETENESS_SPEC.md, 04_ADD_CAR_BROKER_WORKBENCH_USABILITY_SPEC.md*
