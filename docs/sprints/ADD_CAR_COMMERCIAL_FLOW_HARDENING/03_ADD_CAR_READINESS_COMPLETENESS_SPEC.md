# Add-Car Readiness Completeness Spec

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Need more / Almost ready / Quote-ready definitions; contact and attachment interaction; combinations.

---

## 1. Core Readiness States

| State | Meaning | Handoff? |
|-------|---------|----------|
| **need_more** | Missing vehicle, zip, or both delivery and driver | No; keep asking |
| **almost_ready** | Vehicle + zip; missing delivery AND driver | No; ask delivery/driver |
| **quote_ready** | vehicle + zip + (delivery OR driver) | Yes |

**Quote-ready formula:**
```
vehicle_ok = (year AND make_model) OR vin
has_zip = True
has_delivery_or_driver = delivery_date OR primary_driver
quote_ready = vehicle_ok AND has_zip AND has_delivery_or_driver
```

---

## 2. Contact Readiness (Separate Signal)

| State | Meaning |
|-------|---------|
| **contact_ready** | Name + phone collected |
| **contact_needed** | Quote-ready or almost_ready but name/phone missing |

**Contact does NOT block quote-ready.** Broker can run quote; broker_next_step says "Confirm name/phone for follow-up."

---

## 3. Attachment Presence (Separate Signal)

| Signal | Meaning |
|--------|---------|
| **attachment_received** | At least one attachment uploaded |
| **attachment_count** | Number of attachments |
| **attachment_types** | registration, vin_photo, dec_page, screenshot |

**Attachment does NOT change quote-ready.** It is an accelerator; broker sees "Materials received" vs "Registration/dec page optional."

---

## 4. Combined Display Matrix

| quote_ready_status | contact | attachment | Display |
|--------------------|---------|------------|---------|
| quote_ready | ready | yes | Quote-ready · Contact complete · Materials received |
| quote_ready | ready | no | Quote-ready · Contact complete · Registration/dec page optional |
| quote_ready | needed | yes | Quote-ready · Contact needed · Materials received |
| quote_ready | needed | no | Quote-ready · Contact needed · Registration/dec page optional |
| almost_ready | ready | yes | Almost ready · Contact complete · Materials received |
| almost_ready | ready | no | Almost ready · Contact complete · Registration/dec page optional |
| almost_ready | needed | yes | Almost ready · Contact needed · Materials received |
| almost_ready | needed | no | Almost ready · Contact needed · Registration/dec page optional |
| need_more | — | yes | Need more · Materials received |
| need_more | — | no | Need more · Registration/dec page optional |

---

## 5. Contact and Attachment Interaction

**Key rule:** Quote-ready, contact, and attachment are **independent signals**. No signal blocks another for handoff.

| Question | Answer |
|----------|--------|
| Can case be quote-ready without contact? | Yes |
| Can case be quote-ready without attachment? | Yes |
| Does attachment imply quote-ready? | No |
| Does contact imply quote-ready? | No |
| What does broker do when quote-ready but contact missing? | Run quote; broker_next_step says "Confirm name/phone for follow-up" |
| What does broker do when quote-ready but no attachment? | Run quote; broker_next_step says "Registration/dec page optional" |

---

## 6. Correction and Already-Sent (Add-On Signals)

| Signal | Meaning |
|--------|---------|
| **correction** | Customer corrected vehicle, zip, or driver; use latest |
| **already_sent** | Customer said "already sent" (more common in missing_document) |

For add-car, **correction** is the main add-on. When present, broker should use latest collected fields.

---

*See also: 04_ADD_CAR_BROKER_WORKBENCH_USABILITY_SPEC.md, ADD_CAR_IDENTITY_CONTACT_LITE/03_QUOTE_READY_CONTACT_READINESS_SPEC.md, ADD_CAR_ATTACHMENT_READY_LITE/04_QUOTE_READY_ATTACHMENT_STATE_SPEC.md*
