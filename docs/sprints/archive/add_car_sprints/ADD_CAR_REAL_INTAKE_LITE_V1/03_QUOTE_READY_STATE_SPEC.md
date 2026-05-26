# Quote-Ready State Spec

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** Define Quote-ready, Almost ready, Need more — simple and explainable.

---

## 1. Three States

| State | Meaning | Broker Action |
|-------|---------|---------------|
| **Quote-ready** | All P0 fields collected; office can run quote | Run quote; confirm delivery/driver with client before binding |
| **Almost ready** | Missing 1–2 non-blocking fields (e.g. driver when delivery present) | Quick follow-up or run quote with assumption |
| **Need more** | Missing vehicle, zip, or both delivery and driver | Ask customer for missing info before handoff |

---

## 2. Exact Field Combinations

### Quote-ready

```
vehicle_ok = (year AND make_model) OR vin
has_zip = True
has_delivery_or_driver = delivery_date OR primary_driver
return vehicle_ok AND has_zip AND has_delivery_or_driver
```

Aligns with existing `_add_car_enough_for_handoff`.

### Almost ready

- Has vehicle + zip; missing delivery AND driver
- Has vehicle + zip + delivery; missing driver (optional T2 ask)
- Has vehicle + zip + driver; missing delivery (nice-to-have)

### Need more

- Missing vehicle (year+model or VIN)
- Missing zip
- Missing both delivery and driver

---

## 3. What "Still Needed" Shows

| State | still_needed_fields |
|-------|---------------------|
| Quote-ready | delivery_date, primary_driver (whichever missing — optional) |
| Almost ready | delivery_date, primary_driver (whichever missing) |
| Need more | year, make_model, zip, delivery_date, primary_driver (as applicable) |

---

## 4. Implementation

- Add `quote_ready_status` to triage output: `"quote_ready"` | `"almost_ready"` | `"need_more"`
- Only for add-car (`issue_category` add_car / add_car_quote)
- Derive from `_add_car_enough_for_handoff` and field completeness

---

*See also: triage.py _add_car_enough_for_handoff, _add_car_structured_fields*
