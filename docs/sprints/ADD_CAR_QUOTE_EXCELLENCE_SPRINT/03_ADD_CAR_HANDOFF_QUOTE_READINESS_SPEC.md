# Add-Car Handoff / Quote-Readiness Spec

**Sprint:** Add-Car Quote Excellence  
**Purpose:** Define when to hand off, when to keep asking, when quote-ready, when under-filled.

---

## 1. When Add-Car Should Hand Off

| Condition | Action |
|-----------|--------|
| vehicle (year+model or VIN) + zip + (delivery or driver) | Hand off |
| First turn with full info | Hand off immediately |
| T2 with full info + doc clarification (garaging) | Answer question, hand off |
| T3 after driver added (T2 asked driver) | Hand off |

---

## 2. When Add-Car Should Keep Asking

| Condition | Ask |
|-----------|-----|
| No vehicle (year+model or VIN) | Ask year + make/model |
| No zip | Ask zip |
| No delivery AND no driver | Ask delivery + driver |
| T2: delivery present, driver missing | Ask driver (one more turn for corrections) |
| T2: delivery + doc clarification in same msg | Do NOT ask driver; answer + hand off |

---

## 3. Quote-Ready Threshold

**Enough when:** `_add_car_enough_for_handoff(fields)` = True

```
vehicle_ok = (year AND model) OR vin
has_zip = True
has_delivery_or_driver = delivery OR driver
return vehicle_ok AND has_zip AND has_delivery_or_driver
```

---

## 4. Under-Filled Threshold

**Under-filled when:** Hand off would occur with:
- Only year (no model)
- Only zip (no delivery, no driver)
- Only model (no year)

Current implementation prevents this: we ask before handoff.

---

## 5. Side Questions Before Handoff

| Side Question | Behavior |
|---------------|----------|
| garaging proof 是什么 | Answer; hand off (HT8) |
| dec page 是什么 | Answer; hand off |
| coverage 可以调吗 | Brief answer; hand off |
| 保单是不是快到期 | Note secondary; hand off add-car |

---

## 6. Same-Case Corrections

Corrections ("不是X5，是X3", "ZIP 改成 92620") stay in same case. Extraction uses merged customer text; latest message overrides.

---

*See also: triage.py _add_car_enough_for_handoff, _get_next_ask_for_add_car*
