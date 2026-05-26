# Add-Car Quote — Conversation / Slot Collection Spec

**Sprint:** Add-Car Quote 80% Completion  
**Purpose:** Define slots, priority, collection order, and handoff logic.

---

## 1. Slot Definitions

| Slot | Display Name | Critical? | Optional? | Human Confirm? | Extraction Hints |
|------|--------------|------------|------------|----------------|------------------|
| year | Year | ✓ | | | 20XX regex |
| make_model | Make/Model | ✓ | | | bmw, tesla, honda, toyota, etc. |
| vin | VIN | | ✓ | ✓ | 17-char alphanumeric |
| zip | Zip code | ✓ | | | 9XXXX regex |
| delivery_date | Delivery date | | ✓ | | 下周, 提车, picking up, tomorrow |
| primary_driver | Primary driver | | ✓ | ✓ | driver, 驾驶人, 谁开 |
| insurance_status | New vs add-to-existing | | ✓ | | 加车→add; 新车+无加→ask |
| additional_drivers | Additional drivers needed | | ✓ | | 还有别人, 就我开, only me |
| coverage_preference | Full vs liability | | ✓ | | 全保, 半保, full coverage |

---

## 2. Priority Tiers

**Tier 1 (must have for handoff):**
- year + make_model (or VIN)
- zip

**Tier 2 (one of these for handoff):**
- delivery_date
- primary_driver
- insurance_status (when we can't infer)

**Tier 3 (nice to have):**
- additional_drivers
- coverage_preference

---

## 3. Recommended Collection Order

1. **Vehicle** (year + make_model) — if missing
2. **Zip** — if missing
3. **Delivery date** — if missing and vehicle+zip present
4. **Insurance status** — if ambiguous (new customer vs add-to-existing)
5. **Additional drivers** — "还有别人开这辆车吗？" when not stated
6. **Primary driver** — when additional_drivers = yes
7. **Coverage preference** — light touch, optional

---

## 4. "Next Best Missing Information" Logic

```
if not vehicle_ok:
    ask vehicle (year + make/model)
elif not zip:
    ask zip
elif not delivery and not driver and not insurance_status:
    ask delivery (or insurance_status if ambiguous)
elif additional_drivers unknown and vehicle+zip+delivery:
    ask additional_drivers
elif additional_drivers and not primary_driver:
    ask primary_driver
elif coverage_preference unknown and we have 4+ fields:
    optionally ask coverage_preference
else:
    hand off
```

---

## 5. Answer-First / Reassure-First

When user provides new info:
- **Acknowledge** what they said: "好的，2024年的。" / "Got it, 2024."
- **Then** ask next best question
- Do NOT repeat what they already gave

When user asks a question ("什么意思", "要发什么"):
- **Answer** the question first
- **Then** hand off or ask next

---

## 6. Human Confirmation Required

- **VIN** — broker must verify
- **primary_driver** — affects premium; broker confirms
- **insurance_status** when user says "new customer" — broker verifies existing policy

---

## 7. Handoff Threshold (Updated)

**Enough for handoff when:**
- (year + make_model) OR vin
- AND zip
- AND (delivery_date OR primary_driver OR insurance_status)

**Stricter than before:** zip is required; one of delivery/driver/insurance_status is required.  
**Rationale:** Zip alone is not enough for a good quote; office needs at least delivery or driver context.

---

*See also: LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md §4.1*
