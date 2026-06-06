# P16-Z24 Case Results (after improvements)

**Run:** 2026-06-06T08:15:25.031086+00:00  
**Scenarios:** 30

## AC01 — 完整客户 · Tesla · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Tesla Model 3, VIN, zip, driver. 3 customer message(s). Latest: 我叫王明，手机626-555-0188，这些够你们报价了吗？...
- **Vehicle:** 2024 Tesla Model 3
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_add_to_existing, name, phone
- **Missing:** delivery_date
- **Broker next step:** 联系客户补齐提车日期，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 97/100

**Customer message:**

> 陈哥你好，刚提了2024 Tesla Model 3，想加到现有保单。
> VIN 5YJ3E1EA1KF123456，邮编91789，下周五3月15号提车，主驾是我本人。
> 我叫王明，手机626-555-0188，这些够你们报价了吗？

## AC02 — Complete customer · Toyota · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Toyota Camry, VIN, zip, driver. 3 customer message(s). Latest: Name is David Chen, phone 310-555-0142. Ready for quote?...
- **Vehicle:** 2023 Toyota Camry
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer, name, phone
- **Missing:** delivery_date
- **Broker next step:** 联系客户补齐提车日期，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 97/100

**Customer message:**

> Hi, I bought a 2023 Toyota Camry and need to add it to my policy.
> VIN 4T1B11HK5KU123456, ZIP 90210, picking up next Monday. I'm the primary driver.
> Name is David Chen, phone 310-555-0142. Ready for quote?

## AC03 — VIN缺失 · Honda · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2022 Honda Accord, zip, driver. 2 customer message(s). Latest: 邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？...
- **Vehicle:** 2022 Honda Accord
- **Collected:** year, make_model, zip, primary_driver, insurance_status_add_to_existing, materials_send_question
- **Missing:** vin, delivery_date
- **Broker next step:** 联系客户补齐车架号、提车日期，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 你好，我新买了2022 Honda Accord，想加保。
> 邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？

## AC04 — Driver missing · Toyota · mixed

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Toyota RAV4, VIN, zip. 2 customer message(s). Latest: VIN JTMB1RFV0RD123456 — who drives还没定，可能是我老婆也可能是我。...
- **Vehicle:** 2024 Toyota RAV4
- **Collected:** year, make_model, vin, zip
- **Missing:** delivery_date, primary_driver, name, phone
- **Broker next step:** 联系客户补齐提车日期、主驾驶人、姓名、电话，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 95/100

**Customer message:**

> 刚订了2024 Toyota RAV4，zip 94538，下周四delivery。
> VIN JTMB1RFV0RD123456 — who drives还没定，可能是我老婆也可能是我。

## AC05 — 保险卡已上传 · Tesla

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Tesla Model Y, VIN, zip, delivery, driver.  Client says already sent. 3 customer message(s). Latest: VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。...
- **Vehicle:** 2024 Tesla Model Y
- **Collected:** year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, customer_says_materials_sent
- **Missing:** name, phone
- **Broker next step:** 联系客户补齐姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 我买了台2024 Tesla Model Y，想加到保单。
> 刚才微信发了现有保险卡照片，你们收到了吗？
> VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。

## AC06 — 配偶主驾 · Lexus · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Lexus, VIN, zip. 2 customer message(s). Latest: 主驾是她，我偶尔开。邮编91776，VIN 2T2BZMCA8PC123456。...
- **Vehicle:** 2023 Lexus
- **Collected:** year, make_model, vin, zip
- **Missing:** delivery_date, primary_driver, name, phone
- **Broker next step:** 联系客户补齐提车日期、主驾驶人、姓名、电话，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 95/100

**Customer message:**

> 帮我给我老婆新买的那台2023 Lexus RX 350加险，下周提车。
> 主驾是她，我偶尔开。邮编91776，VIN 2T2BZMCA8PC123456。

## AC07 — Teen driver · Honda · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2021 Honda Civic, VIN, zip, driver. 2 customer message(s). Latest: He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in drivew...
- **Vehicle:** 2021 Honda Civic
- **Collected:** year, make_model, vin, zip, primary_driver
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> Adding a 2021 Honda Civic for my son who just got his license.
> He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in driveway.

## AC08 — Tesla 急单 · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Tesla Model 3, VIN, zip, driver. 2 customer message(s). Latest: VIN 5YJ3E1EA4RF123456 邮编94086 我开...
- **Vehicle:** 2024 Tesla Model 3
- **Collected:** year, make_model, vin, zip, primary_driver
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 明天就要提2024 Tesla Model 3了！！能今天加进保单吗？
> VIN 5YJ3E1EA4RF123456 邮编94086 我开

## AC09 — Toyota · 中英混合

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Toyota Highlander, VIN, zip, delivery, driver. 2 customer message(s). Latest: VIN 5TDDZRFH8PS123456，zip 95123，pick up 下周五，primary driver是我。...
- **Vehicle:** 2023 Toyota Highlander
- **Collected:** year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing
- **Missing:** name, phone
- **Broker next step:** 联系客户补齐姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> Hi陈哥，新买了2023 Toyota Highlander，想add to existing policy。
> VIN 5TDDZRFH8PS123456，zip 95123，pick up 下周五，primary driver是我。

## AC10 — Honda CR-V · English complete

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Honda CR-V, VIN, zip, driver.  Policy #: please. 3 customer message(s). Latest: Jennifer Wu, 858-555-0199...
- **Vehicle:** 2024 Honda CR-V
- **Collected:** year, make_model, vin, zip, primary_driver, name, phone, policy_number
- **Missing:** delivery_date
- **Broker next step:** 联系客户补齐提车日期，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 97/100

**Customer message:**

> Need to add my new 2024 Honda CR-V to policy please.
> VIN 7FARW2H89RE123456, ZIP 92101, delivery March 20, I'm primary driver.
> Jennifer Wu, 858-555-0199

## AC11 — 中文极简开场

- **Route:** `add_car`
- **Draft summary:** Add car to existing policy. 1 customer message(s). Latest: 想加一台新车...
- **Vehicle:** —
- **Collected:** insurance_status_add_to_existing
- **Missing:** year, make_model, vin, zip, delivery_date, primary_driver
- **Broker next step:** 联系客户补齐年份、车型、车架号、邮编，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 83/100

**Customer message:**

> 想加一台新车

## AC12 — English minimal opener

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle. 1 customer message(s). Latest: New car quote please...
- **Vehicle:** —
- **Collected:** insurance_status_new_customer
- **Missing:** year, make_model, vin, zip, delivery_date, primary_driver
- **Broker next step:** 联系客户补齐年份、车型、车架号、邮编，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 83/100

**Customer message:**

> New car quote please

## AC13 — VIN 最后一轮补齐 · Toyota

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Toyota Corolla, VIN, zip, driver. 3 customer message(s). Latest: VIN 2T1BURHE0PC123456 刚收到...
- **Vehicle:** 2023 Toyota Corolla
- **Collected:** year, make_model, vin, zip, primary_driver, materials_still_pending
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 97/100

**Customer message:**

> 买了2023 Toyota Corolla，邮编90640，这周日提车，我开。
> VIN还没拿到，销售说今天给我。
> VIN 2T1BURHE0PC123456 刚收到

## AC14 — 家庭多车 + 价格问题 · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 BMW X3, VIN, zip, driver.  Policy #: 9123456. 3 customer message(s). Latest: 另外想问能不能一起bundle便宜点？先帮我把X3加进去。...
- **Vehicle:** 2024 BMW X3
- **Collected:** year, make_model, vin, zip, primary_driver, policy_number
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 家里已有两台车在这个保单，现在再买一台2024 BMW X3给太太开。
> 她主驾。邮编91364，VIN 5UX53DP04N9123456，下月1号提车。
> 另外想问能不能一起bundle便宜点？先帮我把X3加进去。

## AC15 — Teen + spouse confusion · mixed

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2022 Honda, VIN, zip, driver. 3 customer message(s). Latest: Who should be primary driver? 你帮我建议一下...
- **Vehicle:** 2022 Honda
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer, additional_drivers_yes
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 88/100

**Customer message:**

> Bought 2022 Honda Pilot — 主要给我老婆开，但17岁儿子也会开。
> VIN 5FNYF6H50NB123456 ZIP 92804 delivery next week
> Who should be primary driver? 你帮我建议一下

## AC16 — 材料说已发 · 中文

- **Route:** `add_car`
- **Draft summary:** Add car to existing policy.  Collected: 2023 Tesla Model 3, VIN, zip.  Client says already sent. 2 customer message(s). Latest: 驾照和garaging proof上周都在微信发过了，你们收到了吗？...
- **Vehicle:** 2023 Tesla Model 3
- **Collected:** year, make_model, vin, zip, insurance_status_add_to_existing, customer_says_materials_sent
- **Missing:** delivery_date, primary_driver, name, phone
- **Broker next step:** 联系客户补齐提车日期、主驾驶人、姓名、电话，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 95/100

**Customer message:**

> 加一台2023 Tesla Model 3，VIN 5YJ3E1EA1KF654321 邮编92602 周五提车
> 驾照和garaging proof上周都在微信发过了，你们收到了吗？

## AC17 — VIN晚点 · Toyota · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Toyota, zip, driver. 2 customer message(s). Latest: Don't have VIN yet — dealer will text me tonight. Can you start the quote?...
- **Vehicle:** 2024 Toyota
- **Collected:** year, make_model, zip, primary_driver, name
- **Missing:** vin, delivery_date
- **Broker next step:** 联系客户补齐车架号、提车日期，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 2024 Toyota Tacoma, ZIP 95757, picking up Friday, I'm the driver.
> Don't have VIN yet — dealer will text me tonight. Can you start the quote?

## AC18 — 新客户 · 无现有保单 · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Honda, VIN, zip, driver. 2 customer message(s). Latest: VIN 3CZRZ1H59PM123456，邮编91748，下周提车，我开。手机626-888-0123...
- **Vehicle:** 2023 Honda
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer, name, phone
- **Missing:** delivery_date
- **Broker next step:** 联系客户补齐提车日期，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 我是新客户，第一次在你们这买保险，刚买了2023 Honda HR-V。
> VIN 3CZRZ1H59PM123456，邮编91748，下周提车，我开。手机626-888-0123

## AC19 — Urgent same-day · Tesla English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: Tesla Model Y, VIN, zip, driver. 2 customer message(s). Latest: VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary...
- **Vehicle:** Tesla Model Y
- **Collected:** make_model, vin, zip, primary_driver, name
- **Missing:** year, delivery_date, phone
- **Broker next step:** 联系客户补齐年份、提车日期、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 96/100

**Customer message:**

> Picking up my Tesla Model Y TODAY — need insurance ASAP!
> VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary

## AC20 — 混合意图 · spouse + materials + 删车旁问

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Lexus, zip.  Client says already sent. 5 customer message(s). Latest: 先专注把这台RX加进去吧，另一台我之后再单独说。...
- **Vehicle:** 2023 Lexus
- **Collected:** year, make_model, zip, materials_send_question, customer_says_materials_sent
- **Missing:** vin, delivery_date, primary_driver
- **Broker next step:** 联系客户补齐车架号、提车日期、主驾驶人，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 95/100

**Customer message:**

> 帮我给我配偶新买的那台2023 Lexus RX加险，下周提车。
> 驾照复印件我上周已经在微信发过了，你们那边收到了吗？
> 邮编91776。VIN我晚点拍给你可以吗？
> 另外想问一下，我现在保单里另一台旧车能不能拿掉重新报？
> 先专注把这台RX加进去吧，另一台我之后再单独说。

## AC21 — ZIP缺失 · BMW · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 BMW X5, VIN, driver. 2 customer message(s). Latest: 邮编还没拿到，搬家到Irvine，地址确认了发你。...
- **Vehicle:** 2024 BMW X5
- **Collected:** year, make_model, vin, primary_driver, materials_still_pending
- **Missing:** zip, delivery_date, name, phone
- **Broker next step:** 联系客户补齐邮编、提车日期、姓名、电话，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 陈哥，刚定了2024 BMW X5，VIN 5UXCR6C04R9123456，下周五提车，我开。
> 邮编还没拿到，搬家到Irvine，地址确认了发你。

## AC22 — 提车日未定 · Mercedes · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024, VIN, zip, driver. 2 customer message(s). Latest: 提车日还没定，销售说最早下下周，最晚月底，能先报个价吗？...
- **Vehicle:** 2024
- **Collected:** year, make_model, vin, zip, primary_driver
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 96/100

**Customer message:**

> 订了2024 Mercedes GLC 300，VIN 4JGFB4KB4RA123456，邮编92618，主驾是我。
> 提车日还没定，销售说最早下下周，最晚月底，能先报个价吗？

## AC23 — 现有保单客户 · Toyota · 中文

- **Route:** `add_car`
- **Draft summary:** Add car to existing policy.  Collected: 2023 Toyota Camry, VIN, zip, delivery, driver. 2 customer message(s). Latest: VIN 5TDGRKEC0PS123456 邮编91765 她主驾 下周四提车...
- **Vehicle:** 2023 Toyota Camry
- **Collected:** year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing, additional_drivers_yes
- **Missing:** name, phone
- **Broker next step:** 联系客户补齐姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 陈哥，我保单里那台Camry还在吧？现在又要加一台2023 Toyota Sienna给老婆开。
> VIN 5TDGRKEC0PS123456 邮编91765 她主驾 下周四提车

## AC24 — 保费咨询 · Honda · 中文

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Honda, VIN, zip, driver. 2 customer message(s). Latest: 下周提车，我开。加到现有保单。...
- **Vehicle:** 2023 Honda
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer, premium_zh
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价（客户问了保费，先补齐信息再报价）
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 刚买了2023 Honda HR-V，保费大概多少？VIN 3CZRZ1H59PM123456 邮编91748
> 下周提车，我开。加到现有保单。

## AC25 — Teen driver · 中文首条

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2021 Honda Civic, VIN, zip, driver. 2 customer message(s). Latest: VIN 2HGFC2F59MH123456 邮编92801 车已经在车库了...
- **Vehicle:** 2021 Honda Civic
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> 给我儿子刚买的2021 Honda Civic加险，他17岁刚拿驾照，主驾是他。
> VIN 2HGFC2F59MH123456 邮编92801 车已经在车库了

## AC26 — Insurance card mention · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Tesla Model 3, VIN, zip, driver. 2 customer message(s). Latest: VIN 5YJ3E1EA4RF123456 ZIP 94086 picking up Friday, I'm primary driver....
- **Vehicle:** 2024 Tesla Model 3
- **Collected:** year, make_model, vin, zip, primary_driver, name
- **Missing:** delivery_date, phone, notice_image
- **Broker next step:** 联系客户补齐提车日期、电话、notice_image，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> Adding 2024 Tesla Model 3 to my policy — sent you a photo of my current insurance card on WeChat.
> VIN 5YJ3E1EA4RF123456 ZIP 94086 picking up Friday, I'm primary driver.

## AC27 — Mixed language · ZIP missing

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Lexus, VIN, zip, driver. 2 customer message(s). Latest: ZIP还在办，应该还是91776，primary driver是我老婆。...
- **Vehicle:** 2024 Lexus
- **Collected:** year, make_model, vin, zip, primary_driver, insurance_status_new_customer
- **Missing:** delivery_date, name, phone
- **Broker next step:** 联系客户补齐提车日期、姓名、电话，然后出报价
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> Hi陈哥 bought a 2024 Lexus RX 350, VIN 2T2BZMCA8PC123456, delivery next Monday.
> ZIP还在办，应该还是91776，primary driver是我老婆。

## AC28 — Urgent + price · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Tesla Model Y, VIN, zip, driver. 2 customer message(s). Latest: VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary, picking up this afternoon....
- **Vehicle:** 2024 Tesla Model Y
- **Collected:** year, make_model, vin, zip, primary_driver, name
- **Missing:** delivery_date, phone
- **Broker next step:** 联系客户补齐提车日期、电话，然后出报价（客户问了保费，先补齐信息再报价）
- **Handoff ready:** True / **Action ready:** True
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> Need to add my 2024 Tesla Model Y TODAY — how much will it cost roughly?
> VIN 7SAYGDEE8RA123456 ZIP 94025 I'm primary, picking up this afternoon.

## AC29 — Spouse driver · delayed VIN · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2023 Lexus, zip, delivery, driver. 2 customer message(s). Latest: VIN not ready yet, dealer says tomorrow. ZIP 91364....
- **Vehicle:** 2023 Lexus
- **Collected:** year, make_model, zip, delivery_date, primary_driver
- **Missing:** vin
- **Broker next step:** 联系客户补齐车架号，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 100/100

**Customer message:**

> My wife is getting a 2023 Lexus RX — she'll be primary driver, pickup next week.
> VIN not ready yet, dealer says tomorrow. ZIP 91364.

## AC30 — Existing policy complete · English

- **Route:** `add_car`
- **Draft summary:** New quote / new vehicle.  Collected: 2024 Toyota RAV4, VIN, zip. 3 customer message(s). Latest: Lisa Wang, 949-555-0177 — let me know if you need anything else for the quote....
- **Vehicle:** 2024 Toyota RAV4
- **Collected:** year, make_model, vin, zip, phone
- **Missing:** delivery_date, primary_driver, name
- **Broker next step:** 联系客户补齐提车日期、主驾驶人、姓名，然后出报价
- **Handoff ready:** False / **Action ready:** False
- **Need WeChat:** NO
- **Quality:** 84/100

**Customer message:**

> Hi — need to add my new 2024 Toyota RAV4 to our existing family policy.
> VIN JTMB1RFV0RD123456, ZIP 92618, delivery March 22, my wife drives it mostly.
> Lisa Wang, 949-555-0177 — let me know if you need anything else for the quote.
