# P16-Z24 Chen Kui Demo Set

## Best 3 demo cases

### AC03 — VIN缺失 · Honda · 中文

**Customer message:**

> 你好，我新买了2022 Honda Accord，想加保。
> 邮编92618，这周六提车，主驾是我。VIN我晚点拍给你可以吗？

**Generated Draft Case:** 客户咨询加车报价

**Broker view:** 联系客户补齐车架号、提车日期，然后出报价

**Vehicle:** 2022 Honda Accord

**Why it saves time:** ~7.1 min vs manual read/organize/follow-up

**Talking point:** Structured add-car intake — broker confirms, office quotes

### AC05 — 保险卡已上传 · Tesla

**Customer message:**

> 我买了台2024 Tesla Model Y，想加到保单。
> 刚才微信发了现有保险卡照片，你们收到了吗？
> VIN 7SAYGDEE5PA123456，邮编90024，下周三提车，我开。

**Generated Draft Case:** 客户咨询加车报价

**Broker view:** 联系客户补齐姓名、电话，然后出报价

**Vehicle:** 2024 Tesla Model Y

**Why it saves time:** ~5.2 min vs manual read/organize/follow-up

**Talking point:** 保险卡已发 — 材料核对 + 结构化字段，省重复追问

### AC07 — Teen driver · Honda · English

**Customer message:**

> Adding a 2021 Honda Civic for my son who just got his license.
> He's 17, primary driver. VIN 2HGFC2F59MH123456, ZIP 92801, car already in driveway.

**Generated Draft Case:** 客户咨询加车报价

**Broker view:** 联系客户补齐提车日期、姓名、电话，然后出报价

**Vehicle:** 2021 Honda Civic

**Why it saves time:** ~5.6 min vs manual read/organize/follow-up

**Talking point:** Structured add-car intake — broker confirms, office quotes

## Worst 3 — do NOT demo

### AC30 — Existing policy complete · English (quality 84)

- Route: `add_car` | Need WeChat: NO
- Weakness: delivery_date, primary_driver, name

### AC11 — 中文极简开场 (quality 83)

- Route: `add_car` | Need WeChat: NO
- Weakness: year, make_model, vin, zip, delivery_date, primary_driver

### AC12 — English minimal opener (quality 83)

- Route: `add_car` | Need WeChat: NO
- Weakness: year, make_model, vin, zip, delivery_date, primary_driver
