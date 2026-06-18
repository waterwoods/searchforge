# P16 Stress Test Results

**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 5
**Run:** 2026-06-06T10:43:17.282952+00:00
**Engine:** `triage_conversation` · `triage_for_append` · LLM_GENERATION_ENABLED=0
**Scenarios:** 33 (20 realistic + 3 edge + 5 return-later + 5 append)

## Executive summary

| Metric | Value |
|--------|-------|
| Total scenarios | 33 |
| Passed (quality ≥80 + integrity) | **33/33 (100.0%)** |
| Route accuracy | 100.0% |
| Avg quality score | 98.2/100 |
| Append regressions | 0 |
| Continuity regressions | 0 |
| Avg minutes saved vs manual | 5.0 min |

---

## ST01 — 新 Tesla 买家 · Irvine — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 95/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing, phone |
| Still needed | delivery_date, name |
| Office next step | 联系客户补齐提车日期、姓名，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=[] still=[]
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing'] still=['name', 'phone']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing', 'phone'] still=['delivery_date', 'name']

## ST02 — Honda Accord · VIN 缺失 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, zip, primary_driver, insurance_status_add_to_existing, materials_send_question |
| Still needed | vin, delivery_date |
| Office next step | 联系客户补齐车架号、提车日期，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'zip', 'primary_driver', 'insurance_status_add_to_existing', 'materials_send_question'] still=['vin', 'delivery_date']

## ST03 — Teen driver · Rowland Heights — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']

## ST04 — 中英混合 · Toyota RAV4 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 92/100 |
| Collected | year, make_model, vin, zip, delivery_date, insurance_status_add_to_existing |
| Still needed | primary_driver, name, phone |
| Office next step | 联系客户补齐主驾驶人、姓名、电话，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=[] still=[]
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'insurance_status_add_to_existing'] still=['primary_driver', 'name', 'phone']

## ST05 — 保险卡已发 · Tesla Model 3 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, customer_says_materials_sent |
| Still needed | name, phone |
| Office next step | 联系客户补齐姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'insurance_status_add_to_existing', 'customer_says_materials_sent'] still=['vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing', 'customer_says_materials_sent'] still=['name', 'phone']

## ST06 — 有 ZIP 无 driver · BMW X5 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 88/100 |
| Collected | year, make_model, zip, delivery_date, primary_driver, insurance_status_add_to_existing |
| Still needed | vin |
| Office next step | 联系客户补齐车架号，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'zip', 'insurance_status_add_to_existing'] still=['vin', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin']

## ST07 — 有 driver 无 ZIP · Lexus RX — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, primary_driver, insurance_status_add_to_existing |
| Still needed | zip, delivery_date, name, phone |
| Office next step | 联系客户补齐邮编、提车日期、姓名、电话，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'vin', 'primary_driver', 'insurance_status_add_to_existing'] still=['zip', 'delivery_date', 'name', 'phone']

## ST08 — 两台车 · 先报一台 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver |
| Still needed | name, phone |
| Office next step | 联系客户补齐姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=[] still=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver'] still=['name', 'phone']

## ST09 — 改提车日期 · Honda CR-V — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 98/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing, phone |
| Still needed | delivery_date, name |
| Office next step | 联系客户补齐提车日期、姓名，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing'] still=['name', 'phone']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing', 'phone'] still=['delivery_date', 'name']

## ST10 — 换车了 · 从 Camry 改 RAV4 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 93/100 |
| Collected | year, vin, zip, primary_driver, insurance_status_add_to_existing |
| Still needed | make_model, delivery_date, name, phone |
| Office next step | 联系客户补齐车型、提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'insurance_status_add_to_existing'] still=['delivery_date', 'primary_driver', 'name', 'phone']
**Turn 2:** collected=['year', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['make_model', 'delivery_date', 'name', 'phone']

## ST11 — 家庭共用 · Subaru Outback — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 95/100 |
| Collected | year, make_model, vin, zip, delivery_date |
| Still needed | primary_driver, name, phone |
| Office next step | 联系客户补齐主驾驶人、姓名、电话，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=[] still=[]
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date'] still=['primary_driver', 'name', 'phone']

## ST12 — 退休父母主驾 · Toyota Corolla — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']

## ST13 — 大学生 · Mazda CX-5 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, name, phone |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'primary_driver'] still=['vin', 'zip', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'name', 'phone'] still=['delivery_date']

## ST14 — VIN 不确定 · 要查 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, zip, delivery_date, primary_driver, insurance_status_add_to_existing |
| Still needed | vin |
| Office next step | 联系客户补齐车架号，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin']

## ST15 — 只发了部分信息 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 95/100 |
| Collected | year, make_model, insurance_status_new_customer |
| Still needed | vin, zip, delivery_date, primary_driver |
| Office next step | 联系客户补齐车架号、邮编、提车日期、主驾驶人，然后出报价（客户问了保费，先补齐信息再报价） |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['insurance_status_new_customer'] still=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'insurance_status_new_customer'] still=['vin', 'zip', 'delivery_date', 'primary_driver']

## ST16 — 2天后回来补 VIN — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'zip', 'primary_driver'] still=['vin', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']

## ST17 — 1周后回来补电话 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | conversation |
| Route | `add_car` |
| Quality | 97/100 |
| Collected | year, make_model, vin, zip, primary_driver, name, phone |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'name'] still=['delivery_date', 'phone']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'name', 'phone'] still=['delivery_date']

## ST18 — Append 只补电话 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, phone |
| Still needed | — |
| Office next step | 信息齐全，可直接为2024 Tesla Model Y出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `电话949-555-1234` → lost=none

## ST19 — Append 只补姓名 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver, name |
| Still needed | — |
| Office next step | 信息齐全，可直接为2023 Toyota Camry出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `姓名：李华` → lost=none

## ST20 — Append 多次补全 — **PASS**

| Field | Value |
|-------|-------|
| Category | realistic |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, name, phone |
| Still needed | — |
| Office next step | 信息齐全，可直接为2024 Honda CR-V出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `提车改到下周五了` → lost=none
**Append 2:** `我叫Jennifer Wu` → lost=none
**Append 3:** `858-555-0199` → lost=none

## EC01 — 冲突信息 · 年份对不上 — **PASS**

| Field | Value |
|-------|-------|
| Category | edge |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']

## EC02 — 改 ZIP · 搬家 — **PASS**

| Field | Value |
|-------|-------|
| Category | edge |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver'] still=['name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']

## EC03 — 改主驾 · 从本人改配偶 — **PASS**

| Field | Value |
|-------|-------|
| Category | edge |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']

## RL01 — Return-later · Day1→3→5→7 — **PASS**

| Field | Value |
|-------|-------|
| Category | return_later |
| Mode | conversation |
| Route | `add_car` |
| Quality | 97/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing, name, phone |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['vin', 'delivery_date']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver', 'insurance_status_add_to_existing'] still=['name', 'phone']
**Turn 4:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing', 'name', 'phone'] still=['delivery_date']

## RL02 — Return-later · 先车型后VIN — **PASS**

| Field | Value |
|-------|-------|
| Category | return_later |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'insurance_status_add_to_existing'] still=['vin', 'zip', 'delivery_date', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'zip', 'insurance_status_add_to_existing'] still=['vin', 'delivery_date', 'primary_driver']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'insurance_status_add_to_existing'] still=['delivery_date', 'name', 'phone']

## RL03 — Return-later · 3天后补ZIP — **PASS**

| Field | Value |
|-------|-------|
| Category | return_later |
| Mode | conversation |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver |
| Still needed | delivery_date, name, phone |
| Office next step | 联系客户补齐提车日期、姓名、电话，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'delivery_date', 'primary_driver'] still=['zip', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']

## RL04 — Return-later · 5天后补driver — **PASS**

| Field | Value |
|-------|-------|
| Category | return_later |
| Mode | conversation |
| Route | `add_car` |
| Quality | 97/100 |
| Collected | year, make_model, zip, primary_driver |
| Still needed | vin, delivery_date |
| Office next step | 联系客户补齐车架号、提车日期，然后出报价 |
| Handoff ready | False |
| Action ready | False |
| Formal submit ready | False |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'zip', 'delivery_date'] still=['vin', 'primary_driver']
**Turn 2:** collected=['year', 'make_model', 'zip', 'primary_driver'] still=['vin', 'delivery_date']

## RL05 — Return-later · 7天后补姓名电话 — **PASS**

| Field | Value |
|-------|-------|
| Category | return_later |
| Mode | conversation |
| Route | `add_car` |
| Quality | 95/100 |
| Collected | year, make_model, vin, zip, primary_driver, phone |
| Still needed | delivery_date, name |
| Office next step | 联系客户补齐提车日期、姓名，然后出报价 |
| Handoff ready | True |
| Action ready | True |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | N/A |

**Turn 1:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']
**Turn 2:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver'] still=['delivery_date', 'name', 'phone']
**Turn 3:** collected=['year', 'make_model', 'vin', 'zip', 'primary_driver', 'phone'] still=['delivery_date', 'name']

## AP01 — Append · 只补姓名 — **PASS**

| Field | Value |
|-------|-------|
| Category | append_battery |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, name |
| Still needed | — |
| Office next step | 信息齐全，可直接为2024 Tesla Model Y出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `Name: Li Hua` → lost=none

## AP02 — Append · 只补电话 — **PASS**

| Field | Value |
|-------|-------|
| Category | append_battery |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, phone |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `Phone: 949-555-1234` → lost=none

## AP03 — Append · 补VIN — **PASS**

| Field | Value |
|-------|-------|
| Category | append_battery |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, zip, primary_driver, vin |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `VIN 1HGCV1F34NA123456` → lost=none

## AP04 — Append · 补ZIP — **PASS**

| Field | Value |
|-------|-------|
| Category | append_battery |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, primary_driver, zip |
| Still needed | delivery_date |
| Office next step | 联系客户补齐提车日期，然后出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `ZIP 91776` → lost=none

## AP05 — Append · 连续三次 — **PASS**

| Field | Value |
|-------|-------|
| Category | append_battery |
| Mode | append |
| Route | `add_car` |
| Quality | 100/100 |
| Collected | year, make_model, vin, zip, primary_driver, delivery_date, phone |
| Still needed | — |
| Office next step | 信息齐全，可直接为2024 Honda CR-V出报价 |
| Handoff ready | True |
| Action ready | None |
| Formal submit ready | True |
| Continuity OK | True |
| Append OK | True |

**Append 1:** `Delivery next Friday` → lost=none
**Append 2:** `Jennifer Wu` → lost=none
**Append 3:** `858-555-0199` → lost=none
