# Add-Car Quote Flow Design Spec

**Sprint:** Add-Car Quote 80% Completion  
**Purpose:** Define the target standard Add-Car Quote flow in a realistic business way.

---

## 1. User Problem

The customer wants to:
- Add a new vehicle to an existing policy, or
- Get a quote for a new vehicle (new customer or new policy)

They often provide information in fragments (WeChat, SMS, voice). The office needs enough structured information to run a quote or hand off to an underwriter without excessive back-and-forth.

---

## 2. Flow Goal

Collect the **minimum useful set** of information for a California auto insurance quote, in a **natural conversational order**, and hand off when the broker has enough to act.

---

## 3. Likely Questions to Collect (7–8 Logical Steps)

| # | Category | Fields | When to Ask | Can Skip If |
|---|----------|--------|--------------|-------------|
| 1 | **Location** | zip (or address) | Early — affects rate | Already in message |
| 2 | **Vehicle** | year, make, model (or VIN) | First if missing | VIN or full vehicle given |
| 3 | **New purchase** | newly_purchased, delivery_date | When vehicle known | "下周提车" / "picking up" in message |
| 4 | **Insurance status** | current_insurance (new vs add-to-existing) | After vehicle | "加车" / "add to policy" implies existing |
| 5 | **Additional drivers** | additional_drivers_needed | After vehicle + zip | User says "就我开" / "only me" |
| 6 | **Driver profile** | primary_driver (who drives) | When relevant | Single driver, no add needed |
| 7 | **Coverage direction** | coverage_preference (full/liability, tier) | Optional, light touch | User specifies or office infers |
| 8 | **Handoff** | — | When enough collected | Threshold met |

---

## 4. What Can Be Skipped If Already Known

- **Zip:** Skip if in message (e.g. "90210", "92705")
- **Vehicle:** Skip if year+model or VIN given
- **Delivery:** Skip if "下周提车", "picking up tomorrow" in message
- **Insurance status:** Infer "add-to-existing" from "加车", "add car", "想加一台"
- **Additional drivers:** Skip if "就我开", "only me", "我一个人开"
- **Coverage:** Skip in first 2–3 turns; office can ask later

---

## 5. Recommended Collection Order

**Priority order (next best missing info):**

1. **Vehicle** (year + make/model or VIN) — cannot quote without it
2. **Zip** — rate varies by location; needed early
3. **Delivery date** — when coverage starts; affects quote timing
4. **Insurance status** — new customer vs add-to-existing; affects workflow
5. **Additional drivers** — "还有别人开这辆车吗？"
6. **Primary driver** — who is main driver; affects premium
7. **Coverage preference** — "想要全保还是半保？" (light touch, optional)

**Inference rules:**
- "加车" / "add car" / "想加一台" → assume add-to-existing
- "新车" / "new car" / "刚买" / "bought" without "加" → could be new customer or add; ask if ambiguous
- "下周提车" / "picking up" → delivery_date present

---

## 6. When to Stop Collecting and Hand Off

**Hand off when:**
- (year+model OR VIN) + zip + (delivery OR driver OR insurance_status)
- OR user says "先这样", "你先看", "你先报价"
- OR 5+ customer turns (avoid endless loop)
- OR we have vehicle + zip and user has not responded to 1–2 follow-ups

**Do NOT hand off when:**
- Only vehicle, no zip
- Only zip, no vehicle
- Vehicle + zip but no delivery/driver and user might easily provide it

---

## 7. Flow Shape (Not Every Run Needs Every Step)

```
Detect add-car intent
  → Ask vehicle if missing
  → Ask zip if missing
  → Ask delivery if missing (when vehicle+zip present)
  → Ask insurance status if ambiguous (new vs add)
  → Ask additional drivers if not stated
  → Ask primary driver if multiple drivers
  → (Optional) Ask coverage preference
  → Hand off with summary
```

Typical runs:
- **Full info T1:** "2025 CR-V, 92705, 下周提车" → hand off immediately
- **Partial T1:** "想加一台X5" → ask year+zip → T2 "2024, 90210" → ask delivery/driver → T3 "下周拿" → hand off
- **Vague T1:** "新车保险多少" → ask vehicle → T2 "2025 CR-V" → ask zip → T3 "90210" → hand off

---

*See also: 03_CONVERSATION_SLOT_COLLECTION_SPEC.md, LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md*
