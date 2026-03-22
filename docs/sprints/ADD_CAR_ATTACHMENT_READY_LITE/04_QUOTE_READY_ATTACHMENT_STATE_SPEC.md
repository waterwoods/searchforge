# Quote-Ready + Attachment State Spec

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Define how attachment presence interacts with quote-ready; keep logic simple and explainable.

---

## 1. Quote-Ready Unchanged

Quote-ready is determined by **field completeness only** (vehicle, zip, delivery/driver):

- **Quote-ready** — All P0 fields collected
- **Almost ready** — Missing 1–2 non-blocking fields
- **Need more** — Missing vehicle, zip, or both delivery and driver

**Attachment does NOT change quote-ready status.**

---

## 2. Attachment Presence as Separate Signal

| Signal | Meaning |
|--------|---------|
| `attachment_received` | At least one attachment uploaded for this case |
| `attachment_count` | Number of attachments |
| `attachment_types` | List of types (registration, vin_photo, dec_page, screenshot) |

---

## 3. Combined Display for Broker

| Quote-ready | Attachment | Display |
|-------------|-------------|---------|
| quote_ready | Yes | Quote-ready · Materials received |
| quote_ready | No | Quote-ready · Registration/dec page optional |
| almost_ready | Yes | Almost ready · Materials received |
| almost_ready | No | Almost ready · Registration/dec page optional |
| need_more | Yes | Need more · Materials received |
| need_more | No | Need more · Registration/dec page optional |

---

## 4. broker_next_step When Attachments Exist vs Not

| State | With attachment | Without attachment |
|-------|-----------------|-------------------|
| Quote-ready | "Run quote. Materials received. Confirm delivery/driver with client before binding." | "Run quote. Confirm delivery/driver with client before binding. Registration/dec page optional." |
| Almost ready | "Run quote. Materials received. Ask for delivery/driver if needed." | "Run quote. Ask for delivery/driver. Registration/dec page optional." |
| Need more | "Ask for {missing}. Materials received." | "Ask for {missing}. Registration/dec page optional." |

---

## 5. Non-Negotiable: Attachment Does Not Auto-Change Broker Decisions

- Attachment presence does NOT imply extracted data is reliable
- Broker still confirms manually
- No auto-fill from documents in V1

---

*See also: 03_QUOTE_READY_STATE_SPEC.md (ADD_CAR_REAL_INTAKE_LITE_V1)*
