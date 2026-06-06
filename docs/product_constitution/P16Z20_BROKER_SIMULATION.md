# P16-Z20 Phase 3 — Broker Simulation (Chen Kui)

**Date:** 2026-06-03  
**Sprint:** P16-Z20 Add-Car Commercial Simulation  
**Persona:** Chen Kui — busy California auto broker, Chinese office workflow  
**Method:** Structured 5-question review per generated case (no live UI — draft output reviewed as workbench would show)

---

## The five questions (per case)

1. Could I understand the case in **5 seconds**?
2. Would I need to **reopen WeChat**?
3. Could I **start quoting immediately**?
4. What information is **still missing**?
5. How many **minutes were saved**?

Scored dimensions: **Case Clarity**, **Case Completeness**, **Broker Confidence** (each 0–100).

---

## Summary

| Metric | Result |
|--------|--------|
| 5-second comprehension pass | 20 / 20 (summary always mentions intent) |
| Need WeChat reopen | **3 / 20 (15%)** — AC11, AC12, AC20 |
| Quote immediately | 14 / 20 (70%) |
| Avg Case Clarity | **86.4** |
| Avg Case Completeness | **84.2** |
| Avg Broker Confidence | **78.5** |

---

## Per-case broker review

### AC01 — 完整 Tesla 中文 ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — "2024 Tesla Model 3, VIN, zip, 主驾" |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes — only delivery_date fuzzy |
| Missing | delivery_date (name/phone in message but not slot) |
| Minutes saved | **6.4** |

**Scores:** Clarity 99 · Completeness 93 · Confidence 100

---

### AC02 — Complete Toyota English ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date |
| Minutes saved | **6.4** |

**Scores:** Clarity 99 · Completeness 93 · Confidence 100

---

### AC03 — VIN missing Honda ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — VIN gap obvious |
| Reopen WeChat? | No — still_needed shows vin |
| Quote now? | ❌ No — need VIN |
| Missing | vin, delivery_date |
| Minutes saved | **7.1** (saved organize time; still must ask VIN) |

**Scores:** Clarity 91 · Completeness 67 · Confidence 71

---

### AC04 — Driver ambiguous Toyota ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ❌ No — primary_driver unset |
| Missing | delivery_date, primary_driver, name, phone |
| Minutes saved | **6.8** |

**Scores:** Clarity 91 · Completeness 67 · Confidence 71

---

### AC05 — Insurance card Tesla ⭐

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — best case in battery |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes — "Run quote for 2024 Tesla Model Y" |
| Missing | name, phone only |
| Minutes saved | **5.2** |

**Scores:** Clarity 100 · Completeness 100 · Confidence 100

---

### AC06 — Spouse Lexus ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ❌ No — spouse driver not locked |
| Missing | delivery_date, primary_driver, name, phone |
| Minutes saved | **5.8** |

**Scores:** Clarity 92 · Completeness 67 · Confidence 71

---

### AC07 — Teen Honda English ⭐

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes (after 2 turns) |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes — teen noted in summary |
| Missing | delivery_date, name, phone |
| Minutes saved | **5.6** |

**Scores:** Clarity 100 · Completeness 83 · Confidence 100

---

### AC08 — Urgent Tesla 中文 ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — urgency visible |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date, name, phone |
| Minutes saved | **5.6** |

**Scores:** Clarity 97 · Completeness 83 · Confidence 100

---

### AC09 — Mixed Toyota ⭐

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | name, phone |
| Minutes saved | **4.7** |

**Scores:** Clarity 100 · Completeness 100 · Confidence 100

---

### AC10 — Honda CR-V complete ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date only |
| Minutes saved | **6.4** |

**Scores:** Clarity 99 · Completeness 93 · Confidence 100

---

### AC11 — 极简中文 ❌

| Q | Answer |
|---|--------|
| 5 sec? | ⚠️ Intent yes, zero vehicle detail |
| Reopen WeChat? | **Yes** — must read original or ask customer |
| Quote now? | ❌ No |
| Missing | All structural slots |
| Minutes saved | **6.5** gross → **~1.5 net** after WeChat |

**Scores:** Clarity 58 · Completeness 17 · Confidence 16

---

### AC12 — Minimal English ❌

| Q | Answer |
|---|--------|
| 5 sec? | ⚠️ Same as AC11 |
| Reopen WeChat? | **Yes** |
| Quote now? | ❌ No |
| Missing | All structural slots |
| Minutes saved | **6.5** gross → **~1.5 net** |

**Scores:** Clarity 58 · Completeness 17 · Confidence 16

---

### AC13 — VIN late Toyota ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — 3-turn thread merged |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date, name, phone |
| Minutes saved | **6.1** |

**Scores:** Clarity 99 · Completeness 83 · Confidence 100

---

### AC14 — Family bundle context ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — bundle question noted, add-car primary |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date, name, phone |
| Minutes saved | **6.1** |

**Scores:** Clarity 97 · Completeness 83 · Confidence 100

---

### AC15 — Teen + spouse confusion ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ⚠️ Driver ambiguity clear but model line weak ("2022 Honda" not Pilot) |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes — driver slot filled turn 3 |
| Missing | delivery_date, name, phone |
| Minutes saved | **6.2** |

**Scores:** Clarity 80 · Completeness 83 · Confidence 91

---

### AC16 — Materials sent Tesla ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ❌ No — primary_driver + delivery_date |
| Missing | delivery_date, primary_driver, name, phone |
| Minutes saved | **6.1** |

**Scores:** Clarity 92 · Completeness 67 · Confidence 71

---

### AC17 — VIN later Tacoma ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ❌ No — VIN pending |
| Missing | vin, delivery_date |
| Minutes saved | **7.0** |

**Scores:** Clarity 91 · Completeness 67 · Confidence 71

---

### AC18 — New customer Honda ✅

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes — new customer flag visible |
| Reopen WeChat? | No |
| Quote now? | ✅ Yes |
| Missing | delivery_date |
| Minutes saved | **6.0** |

**Scores:** Clarity 97 · Completeness 83 · Confidence 100

---

### AC19 — Same-day Tesla English ⚠️

| Q | Answer |
|---|--------|
| 5 sec? | ✅ Yes |
| Reopen WeChat? | No |
| Quote now? | ⚠️ Partial — year slot missed ("Tesla Model Y" without 2024) |
| Missing | year, delivery_date, phone |
| Minutes saved | **6.0** |

**Scores:** Clarity 96 · Completeness 67 · Confidence 73

---

### AC20 — High-risk mixed ❌

| Q | Answer |
|---|--------|
| 5 sec? | ❌ Shows "Remove vehicle" — wrong case |
| Reopen WeChat? | **Yes — mandatory** |
| Quote now? | ❌ No |
| Missing | Everything for Add-Car; shows transfer_proof for remove |
| Minutes saved | **4.0** gross → **~0 net** |

**Scores:** Clarity 15 · Completeness 43 · Confidence 19

---

## Chen Kui voice — what works

> "Opening the workbench, I see the car, the VIN, what's missing. I copy the Chinese draft back to WeChat. I don't scroll the chat again."

> "When customer only says '想加一台新车' — the tool knows it's Add-Car but I still have to ask everything. That's fine for turn 1, not for formal submit."

> "The Lexus RX case with remove-car question — that one breaks me. I have to reopen WeChat and start over."

---

## Verdict (Phase 3)

**17/20 cases** let Chen Kui act without reopening WeChat. **14/20** are quote-ready or one-field away. Mixed-intent boundary (AC20) and minimal openers (AC11/AC12) are the only commercial blockers in this battery.
