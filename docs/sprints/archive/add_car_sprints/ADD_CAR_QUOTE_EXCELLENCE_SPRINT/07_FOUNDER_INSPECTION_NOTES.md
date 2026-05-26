# Founder Inspection Notes — Add-Car Quote Excellence

**Sprint:** Add-Car Quote Excellence  
**Purpose:** What founder should inspect after this sprint; exact manual test cases.

---

## 1. What to Inspect After Sprint

| Area | What to Check |
|------|---------------|
| Ask-next | Does system ask for next missing field naturally? |
| Correction | "不是X5，是X3" — does case show X3? |
| Garaging same turn | "90210 下周提车 对了 garaging proof 是什么" — answer + handoff? |
| Broker summary | Does summary show concrete vehicle (year, model)? |
| broker_next_step | "Run quote for..." + "Confirm delivery/driver"? |
| Collected/still-needed | Chips accurate in Workbench? |

---

## 2. Exact Vercel Test Cases (4–6)

| # | Input | Expected |
|---|-------|----------|
| 1 | 加车 2024 Tesla Model Y → 90210 下周提车 | Handoff T2; summary has year, model, zip, delivery |
| 2 | 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 | Answer garaging; handoff T2 |
| 3 | 加车 2021 Honda → 不是这个 是 2024 Tesla Model Y → 90210 下周提车 | Handoff T3; collected shows 2024 Tesla |
| 4 | 加车 2024 Tesla Model Y → 90210 下周提车 → 对了 是我老婆开 | Ask driver T2; handoff T3 with driver |
| 5 | 想加车 顺便 coverage 可以调吗 | Answer coverage briefly; collect add-car; no handoff T1 (need vehicle) |
| 6 | 加车 2024 X5 90210 下周提车 我开 | Handoff T1; full info |

---

## 3. What "Excellent Enough for Trial" Looks Like

- No "please provide more context" for clear add-car intent
- Broker receives case with concrete vehicle + zip + delivery/driver
- broker_next_step tells broker exactly what to do
- Corrections and late details captured in same case
- Side questions (garaging, coverage) answered before handoff

---

*See also: ADD_CAR_QUOTE_EXCELLENCE_SPRINT_REPORT.md*
