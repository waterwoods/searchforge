# P16 Edge Case Pack

**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 2  
**Date:** 2026-06-06  
**Purpose:** 3 difficult cases — conflicting info, ZIP change, driver change  
**Audience:** Pre-pilot stress test before CK-001

---

| ID | Title | Difficulty |
|----|-------|------------|
| EC01 | 冲突信息 · 年份对不上 | Customer gives conflicting year |
| EC02 | 改 ZIP · 搬家 | Customer changes ZIP mid-thread |
| EC03 | 改主驾 · 从本人改配偶 | Customer changes primary driver |

---

## EC01 — 冲突信息 · 年份对不上

**Scenario:** Customer first says 2024 BMW, then corrects to 2023 after dealer clarification.

**Turn 1:**
> 加一台2024 BMW 330i VIN WBA8E1C50NK123456 邮编90210 我开

**Turn 2:**
> 等等 销售说其实是2023款的 你按2023报吧

**Expected behavior:**
- Route: `add_car`
- Accept corrected year (2023) on turn 2
- Preserve VIN, ZIP, driver across correction
- Broker step flags year confirmation if ambiguous

**Stress test result:** PASS (quality 100)

---

## EC02 — 改 ZIP · 搬家

**Scenario:** Customer provides ZIP 91789, then moves to Irvine and updates to 92618.

**Turn 1:**
> 2024 Tesla Model 3 加保 VIN 5YJ3E1EA1KF123456 邮编91789 主驾我 下周五提车

**Turn 2:**
> 不好意思 我们刚搬到 Irvine 了 邮编改成92618

**Expected behavior:**
- Route: `add_car`
- Update ZIP to 92618 without losing VIN, vehicle, driver
- Broker step reflects new garaging ZIP
- No case duplication

**Stress test result:** PASS (quality 100)

---

## EC03 — 改主驾 · 从本人改配偶

**Scenario:** Customer initially says self is primary driver, then changes to spouse Linda.

**Turn 1:**
> 2023 Lexus ES 350 加险 VIN 58ABZ1B10PU123456 邮编91765 主驾我本人 下周提车

**Turn 2:**
> 改一下 主驾改成我老婆 Linda 她开比较多

**Expected behavior:**
- Route: `add_car`
- Update primary_driver to spouse
- Preserve VIN, ZIP, vehicle, delivery
- Office step mentions driver change for rating

**Stress test result:** PASS (quality 100)

---

## Edge case design notes

These cases mirror real SoCal Chinese broker threads where customers:
- Correct themselves after talking to dealer
- Move between San Gabriel Valley and Orange County mid-quote
- Decide spouse should be rated driver after initial "我开"

All three passed with zero field loss and correct `add_car` routing.

---

*Results: [`P16_STRESS_TEST_RESULTS.md`](./P16_STRESS_TEST_RESULTS.md)*
