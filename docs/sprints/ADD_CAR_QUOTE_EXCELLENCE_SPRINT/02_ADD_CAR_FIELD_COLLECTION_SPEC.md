# Add-Car Field Collection Spec

**Sprint:** Add-Car Quote Excellence  
**Purpose:** Define fields, priority, collection order, and correction handling.

---

## 1. Field Definitions

| Field | Display | Min Useful? | Nice to Collect? | Extraction Hints |
|-------|---------|-------------|------------------|------------------|
| year | Year | ✓ | | 20XX regex |
| make_model | Make/Model | ✓ | | bmw, x5, x3, tesla, honda, toyota, etc. |
| vin | VIN | | ✓ | 17-char alphanumeric |
| zip | Zip code | ✓ | | 9XXXX regex |
| delivery_date | Delivery date | | ✓ | 下周, 提车, picking up, tomorrow |
| primary_driver | Primary driver | | ✓ | driver, 驾驶人, 谁开, 老婆开 |
| insurance_status | New vs add-to-existing | | ✓ | 加车→add; 新车→new |
| additional_drivers | Additional drivers | | ✓ | 还有别人, 就我 |

---

## 2. Minimum Useful Fields (Handoff Threshold)

**Quote-ready when:**
- (year + make_model) OR vin
- AND zip
- AND (delivery_date OR primary_driver)

**Rationale:** Zip alone is not enough; office needs at least delivery or driver context for quote.

---

## 3. Nice-to-Collect Before Handoff

- insurance_status (add-to-existing vs new customer)
- additional_drivers (yes/no)
- coverage_preference (deferred to V2)

---

## 4. Ask-Next Order

1. **Vehicle** (year + make_model) — when missing
2. **Zip** — when missing
3. **Delivery date + primary driver** — when vehicle+zip present, both missing
4. **Primary driver only** — when delivery present, driver missing (T2 only, to capture corrections)

---

## 5. Same-Goal Corrections (Stay in Same Case)

| Correction Type | Example | Behavior |
|-----------------|---------|----------|
| Wrong vehicle | 不是这个 是另一辆 2024 Tesla Model Y | Replace; extract from latest |
| Wrong ZIP | ZIP 改成 92620 | Replace; extract from latest |
| Wrong driver | 刚才说错了 是我老婆开 | Replace; extract from latest |
| Wrong year | 不是2023 是2024 | Replace; extract from latest |

**Implementation:** `_extract_add_car_fields` uses merged customer text; later messages override earlier. No special correction logic needed if extraction is robust.

---

## 6. Garaging / Document Clarification

When customer asks "garaging proof 是什么" in same turn as add-car info:
- Answer the question first (garaging = 车辆停放地址证明)
- Hand off (do not ask for driver)
- See HANDOFF_TIMING_AUDIT HT8 fix

---

## 7. Mixed-Intent Inside Add-Car

| Secondary | Example | Behavior |
|-----------|---------|----------|
| document_confusion | garaging proof 是什么 | Answer, hand off |
| coverage_adjust | 顺便 coverage 可以调吗 | Brief answer, hand off |
| premium_review | 顺便保费能不能一起看 | Primary add-car; note secondary |

---

*See also: 03_HANDOFF_QUOTE_READINESS_SPEC.md, add_car_quote_80_completion/03_CONVERSATION_SLOT_COLLECTION_SPEC.md*
