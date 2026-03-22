# Minimal Intake Field Spec

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** Define the minimal field set for V1 real intake.

---

## 1. Field Definitions

| Field | P0 (Required) | P1 (Recommended) | Optional | Chat Can Populate |
|-------|---------------|------------------|----------|-------------------|
| **year** | ✓ | | | ✓ (20XX regex) |
| **make_model** | ✓ | | | ✓ (bmw, tesla, honda, etc.) |
| **zip** | ✓ | | | ✓ (9XXXX) |
| **delivery_date** | ✓* | | | ✓ (下周, 提车, picking up) |
| **primary_driver** | ✓* | | | ✓ (谁开, 老婆开, main driver) |
| **vin** | | | ✓ | ✓ (17-char) |
| **name** | | ✓ | | ✓ (deferred: simple extraction) |
| **phone** | | ✓ | | ✓ (deferred: simple extraction) |
| **email** | | | ✓ | Deferred to V2 |

*Quote-ready requires (delivery_date OR primary_driver). Both recommended but not both required.

---

## 2. P0 Fields (Quote-Ready Minimum)

- **Vehicle:** (year + make_model) OR vin
- **Zip**
- **Delivery or driver:** delivery_date OR primary_driver

---

## 3. P1 Fields (Recommended Before Handoff)

- **Name** — office needs to know who to call
- **Phone** — office needs contact
- **Delivery + driver** — both when possible (one is minimum)

---

## 4. Optional / Accelerator

- **VIN** — speeds quote; not blocking
- **insurance_status** — add-to-existing vs new (already extracted)
- **additional_drivers** — yes/no (already extracted)

---

## 5. What Chat Can Populate Automatically

| Field | Extraction | Notes |
|-------|------------|-------|
| year | 20XX regex | Already in _extract_add_car_fields |
| make_model | Keyword list | Already in _extract_add_car_fields |
| zip | 9XXXX regex | Already in _extract_add_car_fields |
| delivery_date | Keywords (下周, 提车, picking up) | Already in _extract_add_car_fields |
| primary_driver | Keywords (谁开, 老婆开) | Already in _extract_add_car_fields |
| vin | 17-char alphanumeric | Already in _extract_add_car_fields |
| name | Deferred V1 | Simple pattern: "我是X", "我叫X" |
| phone | Deferred V1 | Simple pattern: 10-digit, (XXX) XXX-XXXX |

**V1 scope:** Name/phone extraction deferred; focus on quote_ready_status and visibility. Add name/phone in V2 if needed.

---

## 6. Why VIN Is Optional

- Many customers don't have VIN at first contact
- Year + make/model is sufficient for initial quote
- Office can request VIN during follow-up
- Blocking on VIN would increase friction and feel "heavy"

---

*See also: 03_QUOTE_READY_STATE_SPEC.md*
