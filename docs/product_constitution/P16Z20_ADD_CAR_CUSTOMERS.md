# P16-Z20 Phase 1 — 20 Realistic Add-Car Customers

**Date:** 2026-06-03  
**Sprint:** P16-Z20 Add-Car Commercial Simulation  
**Format:** WeChat-style multi-turn conversations (customer → broker office)  
**Machine-readable:** `configs/p16z20_add_car_customers.json`

---

## Scenario mix

| Dimension | Count | IDs |
|-----------|-------|-----|
| Complete customer | 4 | AC01, AC02, AC10, AC13 |
| Incomplete customer | 6 | AC03, AC04, AC11, AC12, AC15, AC17, AC20 |
| VIN missing | 4 | AC03, AC17, AC20, AC13 (resolved turn 3) |
| Driver missing / ambiguous | 3 | AC04, AC15, AC06 |
| Insurance card / materials sent | 3 | AC05, AC16, AC20 |
| Spouse driver | 3 | AC06, AC14, AC20 |
| Teenage driver | 2 | AC07, AC15 |
| Tesla | 5 | AC01, AC05, AC08, AC16, AC19 |
| Toyota | 5 | AC02, AC04, AC09, AC13, AC17 |
| Honda | 4 | AC03, AC07, AC10, AC15, AC18 |
| Chinese only | 6 | AC01, AC03, AC05, AC06, AC08, AC11, AC14, AC16, AC20 |
| English only | 4 | AC02, AC07, AC10, AC12, AC17, AC19 |
| Mixed language | 3 | AC04, AC09, AC15 |

---

## AC01 — 完整客户 · Tesla · 中文

**Tags:** complete, tesla, chinese

```
客户: 陈哥你好，刚提了2024 Tesla Model 3，想加到现有保单。
客户: VIN 5YJ3E1EA1KF123456，邮编91789，下周五3月15号提车，主驾是我本人。
客户: 我叫王明，手机626-555-0188，这些够你们报价了吗？
```

---

## AC02 — Complete customer · Toyota · English

**Tags:** complete, toyota, english

```
Customer: Hi, I bought a 2023 Toyota Camry and need to add it to my policy.
Customer: VIN 4T1B11HK5KU123456, ZIP 90210, picking up next Monday. I'm the primary driver.
Customer: Name is David Chen, phone 310-555-0142. Ready for quote?
```

---

## AC03 — VIN缺失 · Honda · 中文

**Tags:** vin_missing, honda, chinese, incomplete

```
客户: 你好，我新买了2022 Honda Accord，想加保。
客户: 邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？
```

---

## AC04 — Driver missing · Toyota · mixed

**Tags:** driver_missing, toyota, mixed, incomplete

```
Customer: 刚订了2024 Toyota RAV4，zip 94538，下周四delivery。
Customer: VIN JTMB1RFV0RD123456 — who drives还没定，可能是我老婆也可能是我。
```

---

## AC05 — 保险卡已上传 · Tesla

**Tags:** insurance_card, tesla, chinese

```
客户: 我买了台2024 Tesla Model Y，想加到保单。
客户: 刚才微信发了现有保险卡照片，你们收到了吗？
客户: VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。
```

---

## AC06 — 配偶主驾 · Lexus · 中文

**Tags:** spouse_driver, chinese

```
客户: 帮我给我老婆新买的那台2023 Lexus RX 350加险，下周提车。
客户: 主驾是她，我偶尔开。邮编91776，VIN 2T2BZMCA8PC123456。
```

---

## AC07 — Teen driver · Honda · English

**Tags:** teenage_driver, honda, english

```
Customer: Adding a 2021 Honda Civic for my son who just got his license.
Customer: He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in driveway.
```

---

## AC08 — Tesla 急单 · 中文

**Tags:** tesla, chinese, urgent

```
客户: 明天就要提2024 Tesla Model 3了！！能今天加进保单吗？
客户: VIN 5YJ3E1EA4RF123456 邮编94086 我开
```

---

## AC09 — Toyota · 中英混合

**Tags:** toyota, mixed_language

```
Customer: Hi陈哥，新买了2023 Toyota Highlander，想add to existing policy。
Customer: VIN 5TDDZRFH8PS123456，zip 95123，pick up 下周五，primary driver是我。
```

---

## AC10 — Honda CR-V · English complete

**Tags:** honda, english, complete

```
Customer: Need to add my new 2024 Honda CR-V to policy please.
Customer: VIN 7FARW2H89RE123456, ZIP 92101, delivery March 20, I'm primary driver.
Customer: Jennifer Wu, 858-555-0199
```

---

## AC11 — 中文极简开场

**Tags:** chinese, incomplete, minimal

```
客户: 想加一台新车
```

---

## AC12 — English minimal opener

**Tags:** english, incomplete, minimal

```
Customer: New car quote please
```

---

## AC13 — VIN 最后一轮补齐 · Toyota

**Tags:** toyota, chinese, multi_turn

```
客户: 买了2023 Toyota Corolla，邮编90640，这周日提车，我开。
客户: VIN还没拿到，销售说今天给我。
客户: VIN 2T1BURHE0PC123456 刚收到
```

---

## AC14 — 家庭多车背景 · 中文

**Tags:** chinese, family_context

```
客户: 家里已有两台车在这个保单，现在再买一台2024 BMW X3给太太开。
客户: 她主驾。邮编91364，VIN 5UX53DP04N9123456，下月1号提车。
客户: 另外想问能不能一起bundle便宜点？先帮我把X3加进去。
```

---

## AC15 — Teen + spouse confusion · mixed

**Tags:** teenage_driver, spouse_driver, mixed_language

```
Customer: Bought 2022 Honda Pilot — 主要给我老婆开，但17岁儿子也会开。
Customer: VIN 5FNYF6H50NB123456 ZIP 92804 delivery next week
Customer: Who should be primary driver? 你帮我建议一下
```

---

## AC16 — 材料说已发 · 中文

**Tags:** materials_sent, chinese

```
客户: 加一台2023 Tesla Model 3，VIN 5YJ3E1EA1KF654321 邮编92602 周五提车
客户: 驾照和garaging proof上周都在微信发过了，你们收到了吗？
```

---

## AC17 — VIN晚点 · Toyota · English

**Tags:** vin_missing, toyota, english

```
Customer: 2024 Toyota Tacoma, ZIP 95757, picking up Friday, I'm the driver.
Customer: Don't have VIN yet — dealer will text me tonight. Can you start the quote?
```

---

## AC18 — 新客户 · 无现有保单 · 中文

**Tags:** new_customer, chinese

```
客户: 我是新客户，第一次在你们这买保险，刚买了2023 Honda HR-V。
客户: VIN 3CZRZ1H59PM123456，邮编91748，下周提车，我开。手机626-888-0123
```

---

## AC19 — Urgent same-day · Tesla English

**Tags:** tesla, english, urgent

```
Customer: Picking up my Tesla Model Y TODAY — need insurance ASAP!
Customer: VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary
```

---

## AC20 — 高风险混合 · spouse + materials · 中文

**Tags:** spouse_driver, materials_sent, chinese, high_risk  
*(Same script as Role D scenario ADD_CAR_B — boundary / mixed-intent stress test)*

```
客户: 帮我给我配偶新买的那台2023 Lexus RX加险，下周提车。
客户: 驾照复印件我上周已经在微信发过了，你们那边收到了吗？
客户: 邮编91776。VIN我晚点拍给你可以吗？
客户: 另外想问一下，我现在保单里另一台旧车能不能拿掉重新报？
客户: 先专注把这台RX加进去吧，另一台我之后再单独说。
```

---

*Next: Phase 2 simulation → `P16Z20_SIMULATION_RESULTS.md`*
