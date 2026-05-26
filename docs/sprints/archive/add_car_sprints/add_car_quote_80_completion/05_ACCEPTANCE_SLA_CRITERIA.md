# Add-Car Quote 80% Completion — Acceptance / SLA Criteria

**Sprint:** Add-Car Quote 80% Completion  
**Purpose:** Practical criteria for realism, handoff, and business usefulness.

---

## 1. What Counts as a More Realistic Add-Car Flow

| Criterion | Pass | Fail |
|-----------|------|------|
| **Turn depth** | 4–5 turns when user gives partial info | Always 2 turns |
| **Next best question** | Asks zip when vehicle only; asks delivery when vehicle+zip | Asks everything at once or nothing |
| **Handoff threshold** | Vehicle + zip + (delivery or driver) | Vehicle + zip only (zip alone) |
| **First response** | Asks 1–2 items, acknowledges intent | Generic "provide more context" |
| **Case summary** | Collected / Still needed reflect new slots | Only year, model, zip |

---

## 2. What Counts as Too Short / Too Demo-Like

- Hand off after 1 turn when only vehicle given (no zip)
- Hand off with zip only, no delivery or driver
- First turn asks for 6 items in one sentence
- No "additional drivers?" when it would be natural to ask
- Case summary does not mention delivery or driver when collected

---

## 3. What Counts as Too Long / Too Rigid

- Asking for coverage preference in turn 2
- More than 5 customer turns before handoff
- Asking for insurance status when "加车" clearly implies add-to-existing
- Repeating the same question
- Not handing off when we have vehicle+zip+delivery

---

## 4. What Counts as a Good Handoff Point

- Vehicle (year+model or VIN) + zip + (delivery or driver)
- OR user says "先这样" / "你先看"
- OR 5+ turns
- Case summary includes: Collected: year, model, zip, delivery (or driver)
- Broker can run quote or escalate without chasing 2+ critical fields

---

## 5. What Counts as Acceptable Business Usefulness for Pilot

- Add-Car flow feels like real office intake to founder
- No regression on inbox triage scenarios (R14, R17, R18, D4, ER1, ER2, AC-*)
- No regression on multi-turn sims (MT1, MT2, MT11, MT13, MT15, MT16, MT18, MT19, MT30, MT35)
- Guardrail passes
- Founder can demo Add-Car as "stronger than before"

---

*See also: 06_FOUNDER_DEMO_INSPECTION_NOTES.md*
