# Founder Inspection Notes

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** What founder should inspect after this sprint.

---

## 1. What to Inspect

| Area | What to check |
|------|---------------|
| **Quote-ready badge** | Add-car cases show "Quote-ready" / "Almost ready" / "Need more" |
| **Collected vs still-needed** | Green/orange tags visible; labels humanized |
| **Chat + structure** | During add-car chat, collected/still-needed appear; no disconnect |
| **Broker summary** | broker_next_step includes vehicle when available |
| **Handoff** | Case card feels structured, not "just chat" |

---

## 2. Exact Vercel Tests

1. **Full add-car in 2 turns:** "我想加车" → "2024 Tesla Model Y, 90210, 下周提车" — expect Quote-ready, handoff
2. **Partial then complete:** "我买了台X5" → "2024, 90210" → "下周提车" — expect Need more → Almost ready → Quote-ready
3. **Skip VIN:** "加车 2024 Honda Accord 92620 我开" — expect Quote-ready without VIN
4. **Correction:** "不是X5 是X3, 2024, 90210, 下周提车" — expect Quote-ready, vehicle = X3
5. **Side question:** "加车 2024 X5 90210 下周提车，garaging proof 是什么" — expect answer + handoff
6. **Queue view:** Open workbench; add-car case shows quote_ready_status and collected/still-needed

---

## 3. "Good Enough to Show Chen Kui"

- Add-car no longer feels like "chat about a vehicle"
- Broker sees structured intake with quote-ready status
- Founder can say: "We collect year, model, zip, delivery/driver — and you see exactly what's ready for quote"

---

*See also: 01_ADD_CAR_REAL_INTAKE_LITE_BLUEPRINT.md*
