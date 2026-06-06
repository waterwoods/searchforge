# P16-Z24 AI Customer Scenarios

**Generated:** 2026-06-06  
**Purpose:** 30 realistic Add-Car WeChat-style customers for Chen Kui demo readiness.

| ID | Title | Tags | Turns |
|----|-------|------|-------|
| AC01 | 完整客户 · Tesla · 中文 | complete, tesla, chinese, existing_policy | 3 |
| AC02 | Complete customer · Toyota · English | complete, toyota, english, existing_policy | 3 |
| AC03 | VIN缺失 · Honda · 中文 | vin_missing, honda, chinese, incomplete | 2 |
| AC04 | Driver missing · Toyota · mixed | driver_missing, toyota, mixed, incomplete | 2 |
| AC05 | 保险卡已上传 · Tesla | insurance_card, tesla, chinese | 3 |
| AC06 | 配偶主驾 · Lexus · 中文 | spouse_driver, chinese | 2 |
| AC07 | Teen driver · Honda · English | teenage_driver, honda, english | 2 |
| AC08 | Tesla 急单 · 中文 | tesla, chinese, urgent | 2 |
| AC09 | Toyota · 中英混合 | toyota, mixed_language | 2 |
| AC10 | Honda CR-V · English complete | honda, english, complete | 3 |
| AC11 | 中文极简开场 | chinese, incomplete, minimal | 1 |
| AC12 | English minimal opener | english, incomplete, minimal | 1 |
| AC13 | VIN 最后一轮补齐 · Toyota | toyota, chinese, multi_turn | 3 |
| AC14 | 家庭多车 + 价格问题 · 中文 | chinese, family_context, price_question | 3 |
| AC15 | Teen + spouse confusion · mixed | teenage_driver, spouse_driver, mixed_language | 3 |
| AC16 | 材料说已发 · 中文 | materials_sent, chinese | 2 |
| AC17 | VIN晚点 · Toyota · English | vin_missing, toyota, english | 2 |
| AC18 | 新客户 · 无现有保单 · 中文 | new_customer, chinese | 2 |
| AC19 | Urgent same-day · Tesla English | tesla, english, urgent | 2 |
| AC20 | 混合意图 · spouse + materials + 删车旁问 | spouse_driver, materials_sent, chinese, mixed_intent | 5 |
| AC21 | ZIP缺失 · BMW · 中文 | zip_missing, bmw, chinese, incomplete | 2 |
| AC22 | 提车日未定 · Mercedes · 中文 | delayed_delivery, mercedes, chinese | 2 |
| AC23 | 现有保单客户 · Toyota · 中文 | existing_policy, toyota, chinese | 2 |
| AC24 | 保费咨询 · Honda · 中文 | price_question, honda, chinese | 2 |
| AC25 | Teen driver · 中文首条 | teenage_driver, chinese | 2 |
| AC26 | Insurance card mention · English | insurance_card, english | 2 |
| AC27 | Mixed language · ZIP missing | mixed_language, zip_missing | 2 |
| AC28 | Urgent + price · English | urgent, price_question, english | 2 |
| AC29 | Spouse driver · delayed VIN · English | spouse_driver, vin_missing, english | 2 |
| AC30 | Existing policy complete · English | existing_policy, complete, english | 3 |

---

## AC01 — 完整客户 · Tesla · 中文

**Tags:** complete, tesla, chinese, existing_policy  
**Completeness:** complete

**Turn 1:** 陈哥你好，刚提了2024 Tesla Model 3，想加到现有保单。
**Turn 2:** VIN 5YJ3E1EA1KF123456，邮编91789，下周五3月15号提车，主驾是我本人。
**Turn 3:** 我叫王明，手机626-555-0188，这些够你们报价了吗？

## AC02 — Complete customer · Toyota · English

**Tags:** complete, toyota, english, existing_policy  
**Completeness:** complete

**Turn 1:** Hi, I bought a 2023 Toyota Camry and need to add it to my policy.
**Turn 2:** VIN 4T1B11HK5KU123456, ZIP 90210, picking up next Monday. I'm the primary driver.
**Turn 3:** Name is David Chen, phone 310-555-0142. Ready for quote?

## AC03 — VIN缺失 · Honda · 中文

**Tags:** vin_missing, honda, chinese, incomplete  
**Completeness:** incomplete

**Turn 1:** 你好，我新买了2022 Honda Accord，想加保。
**Turn 2:** 邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？

## AC04 — Driver missing · Toyota · mixed

**Tags:** driver_missing, toyota, mixed, incomplete  
**Completeness:** incomplete

**Turn 1:** 刚订了2024 Toyota RAV4，zip 94538，下周四delivery。
**Turn 2:** VIN JTMB1RFV0RD123456 — who drives还没定，可能是我老婆也可能是我。

## AC05 — 保险卡已上传 · Tesla

**Tags:** insurance_card, tesla, chinese  
**Completeness:** partial

**Turn 1:** 我买了台2024 Tesla Model Y，想加到保单。
**Turn 2:** 刚才微信发了现有保险卡照片，你们收到了吗？
**Turn 3:** VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。

## AC06 — 配偶主驾 · Lexus · 中文

**Tags:** spouse_driver, chinese  
**Completeness:** partial

**Turn 1:** 帮我给我老婆新买的那台2023 Lexus RX 350加险，下周提车。
**Turn 2:** 主驾是她，我偶尔开。邮编91776，VIN 2T2BZMCA8PC123456。

## AC07 — Teen driver · Honda · English

**Tags:** teenage_driver, honda, english  
**Completeness:** partial

**Turn 1:** Adding a 2021 Honda Civic for my son who just got his license.
**Turn 2:** He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in driveway.

## AC08 — Tesla 急单 · 中文

**Tags:** tesla, chinese, urgent  
**Completeness:** partial

**Turn 1:** 明天就要提2024 Tesla Model 3了！！能今天加进保单吗？
**Turn 2:** VIN 5YJ3E1EA4RF123456 邮编94086 我开

## AC09 — Toyota · 中英混合

**Tags:** toyota, mixed_language  
**Completeness:** partial

**Turn 1:** Hi陈哥，新买了2023 Toyota Highlander，想add to existing policy。
**Turn 2:** VIN 5TDDZRFH8PS123456，zip 95123，pick up 下周五，primary driver是我。

## AC10 — Honda CR-V · English complete

**Tags:** honda, english, complete  
**Completeness:** complete

**Turn 1:** Need to add my new 2024 Honda CR-V to policy please.
**Turn 2:** VIN 7FARW2H89RE123456, ZIP 92101, delivery March 20, I'm primary driver.
**Turn 3:** Jennifer Wu, 858-555-0199

## AC11 — 中文极简开场

**Tags:** chinese, incomplete, minimal  
**Completeness:** incomplete

**Turn 1:** 想加一台新车

## AC12 — English minimal opener

**Tags:** english, incomplete, minimal  
**Completeness:** incomplete

**Turn 1:** New car quote please

## AC13 — VIN 最后一轮补齐 · Toyota

**Tags:** toyota, chinese, multi_turn  
**Completeness:** complete

**Turn 1:** 买了2023 Toyota Corolla，邮编90640，这周日提车，我开。
**Turn 2:** VIN还没拿到，销售说今天给我。
**Turn 3:** VIN 2T1BURHE0PC123456 刚收到

## AC14 — 家庭多车 + 价格问题 · 中文

**Tags:** chinese, family_context, price_question  
**Completeness:** partial

**Turn 1:** 家里已有两台车在这个保单，现在再买一台2024 BMW X3给太太开。
**Turn 2:** 她主驾。邮编91364，VIN 5UX53DP04N9123456，下月1号提车。
**Turn 3:** 另外想问能不能一起bundle便宜点？先帮我把X3加进去。

## AC15 — Teen + spouse confusion · mixed

**Tags:** teenage_driver, spouse_driver, mixed_language  
**Completeness:** incomplete

**Turn 1:** Bought 2022 Honda Pilot — 主要给我老婆开，但17岁儿子也会开。
**Turn 2:** VIN 5FNYF6H50NB123456 ZIP 92804 delivery next week
**Turn 3:** Who should be primary driver? 你帮我建议一下

## AC16 — 材料说已发 · 中文

**Tags:** materials_sent, chinese  
**Completeness:** partial

**Turn 1:** 加一台2023 Tesla Model 3，VIN 5YJ3E1EA1KF654321 邮编92602 周五提车
**Turn 2:** 驾照和garaging proof上周都在微信发过了，你们收到了吗？

## AC17 — VIN晚点 · Toyota · English

**Tags:** vin_missing, toyota, english  
**Completeness:** incomplete

**Turn 1:** 2024 Toyota Tacoma, ZIP 95757, picking up Friday, I'm the driver.
**Turn 2:** Don't have VIN yet — dealer will text me tonight. Can you start the quote?

## AC18 — 新客户 · 无现有保单 · 中文

**Tags:** new_customer, chinese  
**Completeness:** partial

**Turn 1:** 我是新客户，第一次在你们这买保险，刚买了2023 Honda HR-V。
**Turn 2:** VIN 3CZRZ1H59PM123456，邮编91748，下周提车，我开。手机626-888-0123

## AC19 — Urgent same-day · Tesla English

**Tags:** tesla, english, urgent  
**Completeness:** partial

**Turn 1:** Picking up my Tesla Model Y TODAY — need insurance ASAP!
**Turn 2:** VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary

## AC20 — 混合意图 · spouse + materials + 删车旁问

**Tags:** spouse_driver, materials_sent, chinese, mixed_intent  
**Completeness:** incomplete

**Turn 1:** 帮我给我配偶新买的那台2023 Lexus RX加险，下周提车。
**Turn 2:** 驾照复印件我上周已经在微信发过了，你们那边收到了吗？
**Turn 3:** 邮编91776。VIN我晚点拍给你可以吗？
**Turn 4:** 另外想问一下，我现在保单里另一台旧车能不能拿掉重新报？
**Turn 5:** 先专注把这台RX加进去吧，另一台我之后再单独说。

## AC21 — ZIP缺失 · BMW · 中文

**Tags:** zip_missing, bmw, chinese, incomplete  
**Completeness:** incomplete

**Turn 1:** 陈哥，刚定了2024 BMW X5，VIN 5UXCR6C04R9123456，下周五提车，我开。
**Turn 2:** 邮编还没拿到，搬家到Irvine，地址确认了发你。

## AC22 — 提车日未定 · Mercedes · 中文

**Tags:** delayed_delivery, mercedes, chinese  
**Completeness:** partial

**Turn 1:** 订了2024 Mercedes GLC 300，VIN 4JGFB4KB4RA123456，邮编92618，主驾是我。
**Turn 2:** 提车日还没定，销售说最早下下周，最晚月底，能先报个价吗？

## AC23 — 现有保单客户 · Toyota · 中文

**Tags:** existing_policy, toyota, chinese  
**Completeness:** partial

**Turn 1:** 陈哥，我保单里那台Camry还在吧？现在又要加一台2023 Toyota Sienna给老婆开。
**Turn 2:** VIN 5TDGRKEC0PS123456 邮编91765 她主驾 下周四提车

## AC24 — 保费咨询 · Honda · 中文

**Tags:** price_question, honda, chinese  
**Completeness:** partial

**Turn 1:** 刚买了2023 Honda HR-V，保费大概多少？VIN 3CZRZ1H59PM123456 邮编91748
**Turn 2:** 下周提车，我开。加到现有保单。

## AC25 — Teen driver · 中文首条

**Tags:** teenage_driver, chinese  
**Completeness:** partial

**Turn 1:** 给我儿子刚买的2021 Honda Civic加险，他17岁刚拿驾照，主驾是他。
**Turn 2:** VIN 2HGFC2F59MH123456 邮编92801 车已经在车库了

## AC26 — Insurance card mention · English

**Tags:** insurance_card, english  
**Completeness:** partial

**Turn 1:** Adding 2024 Tesla Model 3 to my policy — sent you a photo of my current insurance card on WeChat.
**Turn 2:** VIN 5YJ3E1EA4RF123456 ZIP 94086 picking up Friday, I'm primary driver.

## AC27 — Mixed language · ZIP missing

**Tags:** mixed_language, zip_missing  
**Completeness:** partial

**Turn 1:** Hi陈哥 bought a 2024 Lexus RX 350, VIN 2T2BZMCA8PC123456, delivery next Monday.
**Turn 2:** ZIP还在办，应该还是91776，primary driver是我老婆。

## AC28 — Urgent + price · English

**Tags:** urgent, price_question, english  
**Completeness:** partial

**Turn 1:** Need to add my 2024 Tesla Model Y TODAY — how much will it cost roughly?
**Turn 2:** VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary, picking up this afternoon.

## AC29 — Spouse driver · delayed VIN · English

**Tags:** spouse_driver, vin_missing, english  
**Completeness:** incomplete

**Turn 1:** My wife is getting a 2023 Lexus RX — she'll be primary driver, pickup next week.
**Turn 2:** VIN not ready yet, dealer says tomorrow. ZIP 91364.

## AC30 — Existing policy complete · English

**Tags:** existing_policy, complete, english  
**Completeness:** complete

**Turn 1:** Hi — need to add my new 2024 Toyota RAV4 to our existing family policy.
**Turn 2:** VIN JTMB1RFV0RD123456, ZIP 92618, delivery March 22, my wife drives it mostly.
**Turn 3:** Lisa Wang, 949-555-0177 — let me know if you need anything else for the quote.
