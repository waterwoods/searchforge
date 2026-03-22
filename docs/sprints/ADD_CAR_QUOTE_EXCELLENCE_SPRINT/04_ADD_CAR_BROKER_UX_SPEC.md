# Add-Car Broker UX Spec

**Sprint:** Add-Car Quote Excellence  
**Purpose:** Define what broker sees in summary, broker_next_step, collected vs still-needed.

---

## 1. Broker Summary Expectations

| Element | Content |
|---------|---------|
| intent_hint | "Add car to existing policy." or "New quote / new vehicle." |
| collected_hint | "Collected: year, model, zip, delivery." (or driver) |
| still_needed_hint | "Still needed: main driver." (when delivery present, driver missing) |
| context_hint | "Correction: vehicle updated." when 不是/说错了 detected |
| vehicle_concrete | (Enhancement) "2024 Tesla Model Y" when extractable |

---

## 2. broker_next_step Expectations

**When quote-ready:**
```
Run quote for collected vehicle details (year, model, zip).
Confirm delivery date and driver with client before binding.
```

**Enhancement:** Include concrete vehicle when available, e.g.:
```
Run quote for 2024 Tesla Model Y (zip 90210).
Confirm delivery date and driver with client before binding.
```

---

## 3. Collected vs Still-Needed Chips

| When | collected_fields | still_needed_fields |
|------|------------------|---------------------|
| Quote-ready, has delivery | year, make_model, zip, delivery_date | primary_driver (optional) |
| Quote-ready, has driver | year, make_model, zip, primary_driver | delivery_date (optional) |
| Quote-ready, has both | year, make_model, zip, delivery_date, primary_driver | (empty or verify items) |
| Not quote-ready | partial | year, make_model, zip, delivery_date, primary_driver |

---

## 4. What Makes Add-Car "Excellent" From Broker Side

1. **Concrete vehicle** — "2024 Tesla Model Y" not just "model"
2. **Clear next step** — "Run quote" + "Confirm delivery/driver"
3. **Collected vs still-needed** — Broker knows what's done, what to verify
4. **Correction visible** — If customer corrected, summary reflects latest
5. **No redundant asks** — Broker doesn't receive case with "please send year" when year was given

---

*See also: triage.py _add_car_structured_fields, _build_conversation_summary*
