# P16 Unified Framework Simulation V1

**日期：** 2026-06-19  
**Sprint：** P16 Final Framework Simulation Before Build  
**SSOT 上游：** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**状态：** SIMULATION ONLY — 无代码，无 DB 设计，无 API 实现  
**语言：** 中文为主，中英混合  
**目的：** 在正式写代码前，最后一次验证统一框架是否稳定、简单、可扩展

---

## 北极星（再次确认）

```
Customer Request
→ Readiness
→ Broker Ready Request
```

**统一流程：**

```
Intent → Upload → Extract → Readiness → Missing Items → Broker Ready Request → Broker Result
```

**信息三桶：**

```
Driver | Vehicle | Policy Details
```

**V1 候选 Request Types：**

1. Add Vehicle（加新车）
2. Switch Insurance（换保险公司）
3. Renewal / Quote Shopping（续保/比价）
4. Replace Vehicle（换车）

---

---

# PART 1 — Customer Journey Simulation

## 闭环 A：Add Vehicle（加新车）

**客户为什么来？**  
买了一辆新车（从经销商/二手市场），需要在已有保险 policy 上加这辆车，否则无法上路。

**客户最终想得到什么结果？**  
新车被加到 policy 上，收到保险公司确认，能安全上路。时间敏感：通常有 dealership 交车日期。

**客户第一步应该看到什么？**  
极简 intent 选择：「我买了一辆新车 — 需要加到保险上」。下面提示：「请提供您的姓名、电话、停车地址邮编」。语言：中英双语。

**客户需要上传什么？**  
- 新车 purchase agreement（购车合同）— 最重要，包含 VIN
- 新车 registration（车牌注册）— 可选但有用
- 当前保险卡（insurance card）— 可选，帮助确认现有 policy

**AI 应该提取什么？**  
- Vehicle：VIN、Year、Make、Model、garaging ZIP
- Policy Details：Effective date、lienholder（如有贷款）
- Driver：Primary driver（如无则默认为客户姓名，标黄确认）

**Readiness 应该显示什么？**  
```
✅ VIN: 5UXZV4C56BL402905 (from: purchase_agreement.pdf)
✅ Year/Make/Model: 2024 Tesla Model Y
✅ Garaging ZIP: 91101
⚠️ Primary Driver: Andy Li (defaulted from customer name — confirm)
❌ Lienholder: MISSING
```

**缺什么时，客户怎么补？**  
系统显示："您的 Lienholder（贷款机构）是什么？（例如：Toyota Financial, Bank of America）"。客户可以直接输入文字，不需要上传文件。

**Broker 看到什么？**  
Trusted Packet：VIN + vehicle info + source attribution + warnings + copy-ready fields。时间戳 + case ID。

**Broker 最后给客户什么结果？**  
Quote approval + 新车被加进 policy。通知客户生效日期。

**商业价值？**  
极高。这是 broker 每天重复做的工作。每次 ~10 分钟 → ~2 分钟。Chen Kui pilot 直接针对这个场景。**已验证：CK-DRY-01 PASS。**

**四天内该不该做？**  
**✅ 已经在做。核心产品，继续。**

---

## 闭环 B：Switch Insurance（换保险公司）

**客户为什么来？**  
当前保险到期，或保险公司涨价，想换一家更便宜的。通常是 policy renewal 前 30-60 天触发。

**客户最终想得到什么结果？**  
收到新保险公司的 quote，并能顺利过渡——旧保险取消，新保险生效，保险不中断。

**客户第一步应该看到什么？**  
「我想换一家保险公司」→「请上传您当前的 Declaration Page（保险声明页）」。中文解释：「就是保险公司每年寄给您的那张单页表格，上面列出所有车辆和驾驶人」。

**客户需要上传什么？**  
- Declaration Page（dec page）— 包含 current carrier、policy number、所有车辆、所有驾驶人、coverage limits、premium
- 各车辆 registration（如 dec page 信息不完整）
- 各驾驶人 driver license（如需要）

**AI 应该提取什么？**  
这里与 Add Vehicle **根本不同**：

| 字段 | Add Vehicle | Switch Insurance |
|------|------------|-----------------|
| VIN | 新车 VIN | 所有现有车辆 VIN（可能 2-5 辆）|
| Driver | 1 人默认 | 所有驾驶人（可能 3-5 人）|
| Coverage | 无（broker 决定）| 当前 coverage limits（需要 port over）|
| Carrier | 无 | 当前 carrier + policy number |
| Premium | 无 | 当前 premium（broker 要比价）|

**Schema 挑战：**  
Switch Insurance 需要提取 **多辆车 + 多位驾驶人 + 当前 coverage**，这比 Add Vehicle 的 schema 复杂 3-5 倍。

**Readiness 应该显示什么？**  
```
✅ 当前保险：Progressive, Policy #123456
✅ Vehicle 1: 2019 Toyota Camry (VIN: 4T1...)
✅ Vehicle 2: 2022 Honda CR-V (VIN: 5J6...)
⚠️ Driver 2: DOB missing — confirm
❌ Coverage limits: MISSING from dec page image quality
```

**缺什么时，客户怎么补？**  
更复杂：缺某位驾驶人的 DOB、缺某辆车的 garaging ZIP、dec page 模糊需要重新上传。问题数量是 Add Vehicle 的 2-4 倍。

**Broker 看到什么？**  
包含所有车辆 + 所有驾驶人 + 当前 coverage 的 packet → broker 用来向多个 carrier 报价比较。

**Broker 最后给客户什么结果？**  
多家 carrier 报价表 + 推荐方案 + 过渡时间表。

**商业价值？**  
极高。Switch Insurance 是 broker 每季度/每年的核心收入来源。

**四天内该不该做？**  
**❌ 不该做。** 原因：
1. Schema 完全不同，需要 `all_vehicles[]` + `all_drivers[]` + `current_coverage` 数组 — 单 bucket 升级不够
2. Dec page 图片质量问题比 purchase agreement 严重得多
3. 多辆车 / 多驾驶人场景在 UI 上需要全新组件
4. 四天内写不完。推到 V2。

---

## 闭环 C：Renewal / Quote Shopping（续保/比价）

**客户为什么来？**  
收到续保通知，发现保费涨了，想看看别的公司价格。或者主动要求 broker 做年度检查。

**客户最终想得到什么结果？**  
在 renewal date 前收到最优价格方案，顺利续保（可能换 carrier，也可能留原 carrier）。

**关键发现：Renewal 的触发模型是错的**

Add Vehicle 模型假设：**客户主动发起，上传文件**。  
Renewal 的现实是：**Broker 主动发起**（因为 carrier 会寄 renewal notice 给 broker，不是给客户）。

即使客户主动来说"我要续保"，他们上传的文件是 renewal notice（看起来像 dec page），而不是新车文件。处理逻辑和 Switch Insurance 几乎完全相同。

**与 Switch Insurance 重叠程度：**  
~85%。区别仅在于 renewal date 驱动的 urgency，以及客户不一定想换 carrier。

**商业价值？**  
高，但和 Switch Insurance 同等复杂度。

**四天内该不该做？**  
**❌ 不该做。与 Switch Insurance 合并到 V2。**  
如果要做，直接复用 Switch Insurance 的 schema + flow，加一个 `renewal_date` 字段即可。但不在四天内。

---

## 闭环 D：Replace Vehicle（换车）

**客户为什么来？**  
卖了/报废了旧车，买了新车。需要在保险上移除旧车、加入新车，确保保险连续不中断。

**客户最终想得到什么结果？**  
新车有保险，旧车从 policy 上移除，不多付旧车保费。

**客户第一步应该看到什么？**  
「我换了一辆新车（旧车已卖/报废）」→「请上传新车的购车合同」。附加选项：「如果需要，也可上传旧车信息」。

**客户需要上传什么？**  
- 新车 purchase agreement（必须）
- 旧车 registration 或 insurance card（可选 — 帮助确认要移除的车辆）

**AI 应该提取什么？**  
- 新车：VIN、Year、Make、Model、garaging ZIP（与 Add Vehicle 完全相同）
- 旧车：如果上传了旧车文件，提取旧车 VIN（存入 `related_vehicle`）

**Readiness 应该显示什么？**  
```
✅ 新车 VIN: JN1AZ4EH9GM932xxx (from: purchase_agreement.pdf)
✅ 新车: 2024 Nissan Maxima
⚠️ 旧车待移除: BMW 5UXZV... (from: old_insurance_card.png)
   → Broker 需确认移除
```

**缺什么时，客户怎么补？**  
与 Add Vehicle 完全相同。唯一额外问题：「您是否知道旧车的 VIN 或车牌号？（Broker 需要这个来移除）」

**Broker 看到什么？**  
新车 Trusted Packet + 警告条："⚠ 客户表示将换车。请确认移除旧车 [VIN/年份/型号]，并在 AMS 中更新。"

**Broker 最后给客户什么结果？**  
新车加入 policy，旧车移除确认，保险连续。

**商业价值？**  
高。Chinese 客户家庭汽车换代频率高，这是高频场景。

**四天内该不该做？**  
**✅ 应该做。** 原因：
1. 与 Add Vehicle 代码重叠 ~80%
2. 唯一新增：`related_vehicle` 字段 + Packet 中的旧车移除警告行
3. 不需要新 UI 组件，只需参数化
4. 已经有 P16_CASE_SCENARIO_SIMULATION.md 中完整的业务规则（SB-2）

**四天内 Replace Vehicle = Add Vehicle + 一行警告 + related_vehicle 字段。**

---

---

# PART 2 — Request Lifecycle Simulation

## 完整生命周期走一遍（以 Add Vehicle 为例）

---

**Step 1：创建新 Request**

客户打开 `/add-car`（或未来的 `/request`）。  
选择 Intent："我买了一辆新车"。  
填写：姓名 + 电话 + 停车邮编。  
点击继续 →  
**系统：** CASE_CREATED。case_id = `CK-001`。state = `NEW`。  
**存储：** phone = primary key。此时 VIN 未知。

---

**Step 2：上传资料**

客户拖拽或选择文件（PDF / JPG / PNG / HEIC）。  
可以上传 1-10 个文件。  
每个文件上传后：DOCUMENT_UPLOADED 事件写入 timeline。  
点击「Continue →」→ 进入提取状态。

---

**Step 3：提取字段**

Gemini Flash 2.5 处理所有上传文件。  
AI_EXTRACTED_PACKET 事件写入（含 model_used、fields_extracted 数量）。  
VIN_VALIDATED 事件写入（valid/invalid）。  
如 primary driver 缺失 → PRIMARY_DRIVER_DEFAULTED 事件（黄色，需确认）。  
如字段缺失 → MISSING_ITEM_DETECTED 事件（红色）。  
State 更新：PACKET_BUILT 或 MISSING_ITEMS。

---

**Step 4：显示 Readiness**

Screen 4（Trusted Packet）显示：  
- 警告（在上方，红色）
- VIN pill + source attribution（`from: purchase_agreement.pdf`）
- Vehicle fields（Year / Make / Model）
- Driver section（如 primary driver 需确认 → 黄色标注）
- Lienholder（如缺失 → 红色标注）
- Timeline（收起，可展开）
- Copy Packet 按钮

**Readiness 指标（非数字分数，避免混淆）：**
- ✅ 可提交（所有必填字段完整）
- ⚠️ 需确认（软警告，broker 需手动核实）
- ❌ 缺少必要信息（无法生成完整 packet）

---

**Step 5：补缺失项**

如果有 ❌ 缺失字段，系统显示具体问题：  
「您的 Lienholder 贷款机构是什么？」→ 客户输入文字。  
「请上传新车购车合同来获取 VIN」→ 客户上传文件。  
填完后系统自动更新 Readiness。  
**不需要重新走全流程。**

---

**Step 6：重新上传文件**

客户回到 Upload Step，上传新文件。  
系统：`find_active_add_car_case_by_phone()` 找到现有 case。  
VIN 匹配 → Append 到现有 case。  
新的 DOCUMENT_UPLOADED 事件 → 重新提取 → 更新 packet。  
**不创建新 case。**

---

**Step 7：修改错误字段**

V1：**不支持客户直接编辑字段。**  
理由：客户编辑会污染 source attribution（字段来自哪里就不清楚了）。  
处理方式：  
- Soft fields（primary_driver）：显示"默认值，请确认"，broker 最终确认
- Hard fields（VIN 错误）：客户需重新上传正确文件，系统重提取  
V2 再考虑 customer-editable fields。

---

**Step 8：Broker Ready**

Packet state = `READY_FOR_QUOTE`。  
Timeline 最后一条：PACKET_READY（绿色）。  
Broker 收到通知（V1：邮件或 broker 访问 dashboard；V2：push notification）。  
Trusted Packet 对 broker 显示所有字段 + source + warnings。

---

**Step 9：Broker 复制 Packet**

Broker 点击「Copy All Fields」。  
剪贴板获得：
```
ADD-CAR PACKET

Customer: Andy Li · 626-555-xxxx · ZIP 91101
Vehicle: 2024 Tesla Model Y · VIN: 5YJ3E...
Driver: Andy Li (confirm)
Lienholder: Toyota Financial (from: purchase_agreement.pdf)
Effective: 2026-06-15

Sources:
  purchase_agreement.pdf → vin, year, make, model, lienholder
  intake_form → customer_name, phone, garaging_zip
```
Broker 粘贴进 AMS / carrier portal。完成。

---

**Step 10：Request 完成 / 关闭**

V1：Broker 手动关闭（或忽略，case 保持 READY_FOR_QUOTE 状态）。  
V2：Broker 有关闭按钮 → `CASE_CLOSED` 事件 → case_status = closed。  
关闭后的 case：**不再接受新文档 append**（现有 guardrail 行为）。  
关闭后还能看到吗？**可以（只读）**。不能修改。

---

**Step 11：客户几天后回来继续**

情景：Andy 周一上传了保险卡，周四上传了 registration。  
系统：`find_active_add_car_case_by_phone()` 找到现有 case。  
VIN 匹配 → Append 新文件 → 重提取 → 更新 packet。  
**不创建新 case。不让客户重新填个人信息。**  
Timeline 显示："周四：新增文件 registration.pdf"。

---

**Step 12：客户又开一个新 Request**

情景：Andy 的 Tesla 加好了，现在他老婆也买了辆 Honda。  
系统：`find_active_add_car_case_by_phone()` 找到 Tesla case。  
新上传文件提取出 Honda VIN → 与现有 case VIN 不匹配。  
**SB-3 规则：Two new cars = Two cases。**  
系统：创建新 case for Honda VIN。  
Broker 看到两个 case：Tesla case + Honda case。  
**不会混淆。不会合并。**

---

## 检查：关键场景

| 问题 | 答案 |
|------|------|
| 会不会产生重复 Request？ | 不会。Same phone + same VIN = append，不创建新 case |
| 同一客户多个 Request？ | 支持。不同 VIN = 不同 case。Broker 看到所有 case |
| 同一 VIN 多次上传？ | Append 到同一 case，timeline 追加事件 |
| 不同 VIN 怎么处理？ | 新建 case（SB-3）|
| Request 关闭后还能修改？ | 不能。Closed case 只读 |
| 客户会困惑的地方？ | 主要风险：客户不知道自己之前提交过，再次填写。缓解：Welcome back 提示（"您上次于 X 日提交了一辆 Tesla，继续？"）|

---

---

# PART 3 — Schema Validation

## Driver / Vehicle / Policy Details 是否足够？

### Add Vehicle

| 分类 | 字段 |
|------|------|
| **Required Fields** | VIN, year, make, model, garaging_zip, customer_name, phone |
| **Optional Fields** | lienholder, lienholder_address, effective_date |
| **Critical Fields** | VIN（精确，17位，格式验证）|
| **Customer-editable** | customer_name, phone, garaging_zip, primary_driver（确认） |
| **Document-derived** | VIN, year, make, model, lienholder, effective_date |
| **Broker-review** | VIN + source, 所有 warnings, missing items |
| **Missing Item Questions** | "贷款机构是什么？"，"请上传新车购车合同" |
| **Final Broker Output** | VIN + vehicle identity + copy-ready block |

**结论：Driver + Vehicle + Policy Details（极简）足够。** ✅

---

### Replace Vehicle

| 分类 | 字段 |
|------|------|
| **Required Fields** | 与 Add Vehicle 相同 + related_vehicle.vin（optional）|
| **Optional Fields** | related_vehicle.make, related_vehicle.model, related_vehicle.year |
| **Critical Fields** | 新车 VIN（精确）|
| **Customer-editable** | 与 Add Vehicle 相同 |
| **Document-derived** | 新车：与 Add Vehicle 相同。旧车：从旧保险卡/registration 提取 |
| **Broker-review** | 新车 packet + "旧车移除待确认" 警告 |
| **Missing Item Questions** | 与 Add Vehicle 相同。额外："旧车的 VIN 或车牌号是什么？" |
| **Final Broker Output** | 新车 packet + 旧车移除说明 |

**结论：在现有三桶基础上，只需在 `extra` JSONB 加 `related_vehicles[]`。不需要第四桶。** ✅

---

### Switch Insurance（参考 — V2）

| 分类 | 字段 |
|------|------|
| **Required Fields** | all_vehicles[]{vin, ymm}, all_drivers[]{name, dob, dl_number}, current_carrier, current_policy_number |
| **Optional Fields** | current_premium, coverage_limits{}, deductibles{} |
| **Critical Fields** | 所有车辆 VIN + 所有驾驶人 DOB（缺少任何一个都无法报价）|
| **Schema Verdict** | **三桶不够。需要 multi-vehicle array + multi-driver array + Current Policy bucket。** |

**结论：Switch Insurance 需要第四桶"Current Policy Details"，包含：**
- `current_carrier`
- `current_policy_number`  
- `all_vehicles[]`（数组，不是单辆车）
- `all_drivers[]`（数组）
- `coverage_limits{}`
- `current_premium`

**这不是 V1 scope。V2 再做。** ⛔

---

### Renewal（参考 — V2）

与 Switch Insurance schema 几乎相同，加 `renewal_date`。  
**结论：V2。同 Switch Insurance。** ⛔

---

## Schema 问题逐一判断

| 问题 | 判断 |
|------|------|
| 是否需要第四个 bucket？ | **V1 不需要。** V2 Switch/Renewal 需要 Current Policy bucket |
| Documents 要不要成为 bucket？ | **不。** Documents 是来源，不是结构化 bucket。Source Attribution 已解决这个问题 |
| Coverage 要不要独立？ | **V1 不需要。** Add/Replace 中 coverage 由 broker 决定，不是 customer input |
| Current Policy 要不要独立？ | **V2 需要**（Switch/Renewal）。V1 不需要 |
| Payment 是否永远排除？ | **是。** PCI scope，永远排除 |
| Address Change 是否 V1 排除？ | **是。** 纯文字表单，不走提取流程，V2 单独处理 |

---

---

# PART 4 — UI Reuse Validation

## 现有组件能否升级为统一 Request UI？

基于 `ui/src/pages/AddCarPage.tsx` 分析：

### 组件复用评估

| 组件 | 当前状态 | 复用度 | 需要改动 |
|------|---------|--------|---------|
| **Intent Selector** | `CustomerFirstEntryScreen` 只有一个路径 | 需要改造 | 加 2-4 个 intent 选项卡 |
| **Customer Info** | `InfoStep` — name/phone/ZIP | 95% 复用 | 几乎不变 |
| **Upload Documents** | `UploadStep` — drag & drop | 98% 复用 | 不变 |
| **Extraction Progress** | `ExtractingStep` — animated steps | 100% 复用 | 不变 |
| **Field Cards** | `PacketStep` — Descriptions + Tags | 70% 复用 | 需要参数化（不同 intent 有不同字段） |
| **Readiness Checklist** | Missing items in PacketStep | 85% 复用 | 需要按 intent 配置不同必填字段 |
| **Missing Items Questions** | 尚未独立组件化 | 需新建 | 简单：一个 question list + input |
| **Broker Ready Banner** | PacketStep header "Trusted Packet" | 100% 复用 | 不变 |
| **Copy Packet** | CopyButton + copy_text | 95% 复用 | 按 intent 格式化 copy_text 即可 |
| **Source Attribution** | `from: filename.pdf` inline | 100% 复用 | 不变 |
| **Warning Panel** | Alert block before fields | 100% 复用 | 不变 |

### 复用率估计

- **现有代码复用：~80-85%**
- **需要新建的最小组件：**
  1. `IntentSelector` — 在 CustomerFirstEntryScreen 加 2 个 intent 选项（Add Vehicle / Replace Vehicle）
  2. `RequestTypeFieldConfig` — 按 request type 配置不同必填字段列表（这是 config，不是 UI 组件）
  3. `RelatedVehiclePanel` — Replace Vehicle 专用，显示旧车 VIN + 移除警告（~30行）
  4. `MissingItemsQA` — 独立化 missing items 问答（从 PacketStep 中提取，~50行）

### 不要重写的部分

- Upload Dragger（`<Dragger>`）— 完美，不碰
- Extraction animation（`ExtractingStep`）— 完美，不碰
- Copy button logic — 完美，不碰
- Source attribution inline — 完美，不碰
- VIN validation（client + server）— 完美，不碰
- Warning panel ordering — 完美，不碰

### 四天内最小改造路径

| 天 | 任务 | 范围 |
|----|------|------|
| Day 1 | 在 CustomerFirstEntryScreen 加 Intent Selector（Add / Replace 两个选项）| ~1h |
| Day 1 | 创建 `RequestTypeFieldConfig`（每个 intent 的必填字段列表）| ~2h |
| Day 2 | 参数化 PacketStep 的字段渲染（从硬编码字段 → 按 intent config 渲染）| ~3h |
| Day 2-3 | 加 RelatedVehiclePanel（Replace Vehicle 的旧车移除警告）| ~2h |
| Day 3 | 独立 MissingItemsQA 组件 | ~2h |
| Day 3-4 | Timeline + case_id wire（已有设计文档）| ~4h（参见 P16_TIMELINE_STATE_MACHINE_DESIGN.md）|

**总计：~14小时。一个工程师 4 天内可完成。**

---

---

# PART 5 — Simplicity / Zip2 Test

**假设：1 个工程师，4 天，必须做到：简单 / 手机友好 / 不吓客户 / 不让 broker 重新学习 / 陈总 5 分钟看懂价值**

---

## 应该删掉什么？

| 功能 | 删掉原因 |
|------|---------|
| Switch Insurance | Schema 复杂 3x，4 天内无法完成，V2 |
| Renewal / Quote Shopping | 同 Switch Insurance，且触发模型不匹配（broker-initiated）|
| Multi-vehicle batch（超过 1 辆新车）| 极少场景，V2 自动分拆，V1 fallback 手动 |
| Customer field editing | 污染 source attribution，broker 最终确认足够 |
| Customer dashboard / case history | 不是 CRM，pilot 不需要 |
| PDF export | Decision Freeze §4 明确排除 |
| WeChat native integration | Decision Freeze §4 明确排除 |
| Address change flow | 纯文字，不走提取，单独处理 |
| Coverage input（客户填）| Broker 决定 coverage，不是客户 |
| Lienholder auto-verification | 过于复杂，flag + broker 确认足够 |

---

## 应该保留什么？

| 功能 | 保留原因 |
|------|---------|
| Add Vehicle 完整流程 | 已验证，核心产品 |
| Replace Vehicle（bolt-on）| 80% 复用，高频场景 |
| Trusted Packet + Copy All | 这是 broker 的钱 moment |
| Source Attribution（always visible）| 建立 broker 信任的核心 |
| VIN Validation | 防止 broker 报错 |
| Timeline（collapsed）| 给 broker 看历史，不干扰主流程 |
| Bilingual labels（中英）| 手机友好，客户不困惑 |
| Primary Driver defaulted 提示 | 软警告，避免空字段，不阻断流程 |

---

## 应该推迟什么？

| 功能 | 推迟理由 |
|------|---------|
| Switch Insurance | V2，不同 schema |
| Renewal | V2，与 Switch 合并 |
| Broker dashboard / case list | 10-case gate 后再做 |
| Customer accounts / login | 决策冻结排除 |
| PDF generation | 决策冻结排除 |
| Customer confirmation screen | 决策冻结排除 |
| Advanced state machine UI（broker side）| V2 |
| Full `p16_timeline_events` table | V2，MVP 用 JSONB 即可 |

---

## 哪个 demo 闭环最惊艳？

**Replace Vehicle > Add Vehicle。**

原因：  
Add Vehicle 是 "我买了新车，帮我加"——合理但普通。  
Replace Vehicle 是 "我换了车，AI 自动知道旧车要移除，新车要加"——这才是智能的体现。  

**最惊艳 demo 脚本：**  
1. 客户说"我换了辆新车"，上传一份购车合同 + 一张旧车保险卡
2. AI 提取出新车 VIN，同时识别旧车 VIN（来自保险卡）
3. Trusted Packet 显示："新车已准备好 ✅" + "旧车待移除 ⚠️（请 broker 确认）"
4. Broker 一键 Copy，粘贴进 AMS

陈总 5 分钟内看到：一份文件 → 两个动作清楚呈现。**这就是价值。**

---

## 哪个功能最容易让陈总愿意试用？

**Copy All → 粘贴进 AMS 这个动作。**  

不是 UI，不是 AI，是那次粘贴。  
当陈总第一次粘贴 packet 进保险系统，看到所有字段整齐排列，他会说：  
**"这个以前要我自己整理 10 分钟"。**  

这就是付费意愿的来源。

---

---

# PART 6 — Risks

| 风险 | 最简单规则 |
|------|-----------|
| **客户选错 intent** | 只提供 2 个 intent（Add Vehicle / Replace Vehicle）。少即是多。不要超过 3 个选项（V1）。 |
| **客户上传错文件** | 不要拒绝上传。提取什么算什么，缺什么就问。错的文件比没有文件好（至少有 partial data）。 |
| **客户不知道字段意思** | 所有字段标签双语（中英）。"Lienholder" → "贷款机构（如：Toyota Financial, Bank of America）"。 |
| **缺资料后不知道怎么补** | Missing items 直接说中文具体问题："请问您的 VIN（车辆识别号）是什么？可在购车合同首页找到。"不要只显示字段名。 |
| **VIN 冲突** | VIN_CONFLICT_FLAGGED 规则已实现。规则：Never silently overwrite. Always flag. Broker decides. |
| **Switch / Renewal schema 太复杂** | 直接排除出 V1。不要用一个 "通用 schema" 同时处理 Add Vehicle 和 Switch Insurance，必然两边都做不好。 |
| **UI 复杂度变高** | 硬性规则：5个 Screen 不变。Intent Selector 在 Screen 1 之前或作为 Screen 0。不新增 screen 数量。 |
| **Broker 不信任 AI** | Source attribution 永远可见（不能藏在 toggle 后）。每个字段旁边必须显示 `from: filename`。不猜，不静默。 |
| **Scope creep** | 四天内一个人只做 Add Vehicle + Replace Vehicle 的统一化。Switch 和 Renewal 物理隔离在 TODO 文档里，不进入当前 sprint。 |
| **四天内做太多** | Day 4 必须留给：真实文件测试 + 干跑 + bug fix。不要让 Day 4 变成 feature day。 |

---

---

# PART 7 — Final Freeze Recommendation

---

## 输出文件

**FILES_CREATED:**  
`docs/p16/P16_UNIFIED_FRAMEWORK_SIMULATION_V1.md`（本文件）

**FILES_UPDATED:**  
无。建议在 Andy 批准后，向 `P16_DECISION_FREEZE_V1.md` §14 追加以下决策：  
- Replace Vehicle 作为 V1 第二 request type（bolt-on to Add Vehicle）  
- Switch Insurance / Renewal 明确推至 V2  
- Intent Selector 作为 Screen 0 加入统一流程  

---

## 评分

| 维度 | 分数 | 说明 |
|------|------|------|
| **FRAMEWORK_SCORE** | 8.5 / 10 | 统一流程稳定。Driver + Vehicle + Policy Details 对 V1 够用。Switch/Renewal 需要升级才能支持。 |
| **CUSTOMER_FLOW_SCORE** | 8.5 / 10 | Add Vehicle 已验证。Replace Vehicle 流程清晰。客户混淆风险低（只有 2 个 intent 选项）。 |
| **SCHEMA_SCORE** | 7.5 / 10 | Add + Replace 够用。Switch/Renewal 需要 Current Policy bucket + 数组字段。V1 暂不需要。 |
| **UI_REUSE_SCORE** | 9 / 10 | 80-85% 代码复用。新组件 < 5 个。现有骨架完全保留。 |
| **FOUR_DAY_FEASIBILITY_SCORE** | 7.5 / 10 | 仅限 Add + Replace。包含 Switch/Renewal 则降至 4/10。 |

---

## 核心决策

**BEST_V1_REQUEST_TYPES:**  
Add Vehicle + Replace Vehicle

**WHAT_TO_BUILD_IN_4_DAYS:**  
1. Intent Selector（CustomerFirstEntryScreen → 支持 Add / Replace 两个 intent）  
2. RequestTypeFieldConfig（配置文件，不是新组件）  
3. 参数化 PacketStep（按 intent 渲染不同字段集）  
4. RelatedVehiclePanel（Replace Vehicle 的旧车警告，~30行）  
5. Timeline wire（`save_case()` + `timeline_events` 返回 + UI `<Timeline>` 组件）  
6. MissingItemsQA（独立组件，missing fields 的中文具体问题）  

**WHAT_TO_EXCLUDE_FROM_4_DAYS:**  
- Switch Insurance  
- Renewal / Quote Shopping  
- Multi-vehicle batch automation  
- Customer field editing  
- Broker dashboard  
- Customer accounts  
- PDF export  
- Coverage input  

**WHAT_TO_FREEZE_NOW:**

```
FROZEN FLOW:
Intent Selector (Add / Replace)
→ Customer Info (name, phone, ZIP)
→ Upload Documents
→ AI Extraction
→ Trusted Packet + Readiness
→ Missing Items Q&A
→ Broker Ready
→ Copy All → Broker Action

FROZEN SCHEMA (V1):
Vehicle: VIN, year, make, model, garaging_zip, lienholder
Driver: primary_driver (default from customer name, confirm)
Policy Details: effective_date
Related Vehicle (Replace only): related_vin, relationship, pending_action

FROZEN CASE IDENTITY:
(phone, new_vehicle_VIN) = one case
Same phone + same VIN = append
Different VIN = new case
Replace = one new case + related_vehicle flagged
```

---

## 最佳设计决策

**BEST_CUSTOMER_FLOW:**

```
Screen 0: Intent（Add Car / Replace Car）— 2 个选项，中英双语，30 秒
Screen 1: Your Info（姓名 / 电话 / 停车邮编）— 1 分钟
Screen 2: Upload（拖拽或选择文件）— 2 分钟
Screen 3: AI 正在读取您的文件...（动画，30-60秒）
Screen 4: Trusted Packet（警告 + VIN + 字段 + Copy 按钮）
```

**BEST_BROKER_FLOW:**

```
Notification → 打开 Packet → 查看警告（5 秒）→ 核对 VIN + Source（10 秒）
→ Copy All → 粘贴进 AMS（5 秒）→ 完成
总计 broker 时间：< 2 分钟
```

**BEST_SCHEMA:**

```
For V1 (Add + Replace):
  Vehicle: {vin, year, make, model, garaging_zip, lienholder?}
  Driver: {primary_driver (with needs_confirmation)}
  Policy: {effective_date}
  Related: {related_vehicles[]: [{vin, relationship, pending_action}]}

For V2 (Switch + Renewal, add):
  Current Policy: {carrier, policy_number, premium, expiry_date}
  All Vehicles: {vehicles[]: [...]}
  All Drivers: {drivers[]: [{name, dob, dl_number, dl_state}]}
  Coverage: {limits{}, deductibles{}}
```

**BEST_READINESS_MODEL:**

```
三级显示（不用数字分数）：
✅ 就绪 — 所有必填字段已提取，broker 可直接操作
⚠️ 需确认 — 有软警告（primary driver defaulted, date conflict）
❌ 缺少必要信息 — 有必填字段缺失，需客户或 broker 补充

不用 "Readiness: 73%" — 数字会让 broker 问"为什么不是 100%？我要等吗？"
```

**BEST_DEMO_LOOP:**

```
Replace Vehicle 闭环（最惊艳）：
1. 客户上传：新车购车合同 + 旧车保险卡
2. AI：提取新车 VIN + 识别旧车（old insurance card）
3. Packet：新车 ✅ + 旧车移除 ⚠️
4. Broker：Copy All → 粘贴进 AMS → 加新车 + 确认移除旧车
5. 陈总看到：一次上传，两个动作，0 个微信来回
```

---

## Top 5 Risks

1. **Scope creep（最大风险）** — 统一框架思维会驱动工程师在 4 天内同时做 4 个 intent。规则：Intent Selector 只上线 2 个选项（Add / Replace），Switch 和 Renewal 在 UI 上不显示，即使后端有代码骨架。
2. **Switch Insurance schema 被提前实现** — 工程师"顺手"把 dec page 提取加进来。规则：只在 Switch Insurance 开 feature flag，pilot 期间不开放。
3. **Broker 不信任 primary driver defaulted** — 黄色警告让 broker 以为有问题。规则：文案改为"默认使用客户姓名，如有不同请告知 broker"，不是"警告"，是"提示"。
4. **Replace Vehicle 的 related_vehicle 警告太显眼** — 旧车移除警告占据 packet 太多空间。规则：旧车警告用一行 info banner，不要用红色 Alert，颜色用 #faad14（黄色）。
5. **四天内 Timeline + Replace Vehicle + 参数化 UI 全部完成** — 每个都单独可以，但叠加后 Day 3-4 容易崩。规则：Timeline 是 must-have，Replace Vehicle 是 should-have，参数化 UI 是 nice-to-have。如果时间不够，Day 3 只做 Timeline wire，Replace Vehicle 的 Intent 选项加进去但 Packet 显示与 Add Vehicle 相同，下个 sprint 再做 related_vehicle panel。

---

## Top 5 Simplifications

1. **V1 只有 2 个 Intent 选项**（Add Vehicle / Replace Vehicle）。不要 4 个。Switch / Renewal 等到真实 broker 要求再加。
2. **Replace Vehicle = Add Vehicle + 一行旧车警告**。不要设计新的 state machine，不要创建新 case，不要新的 broker 确认 workflow。一行警告足够。
3. **Primary Driver 默认规则已经解决了最大 UX 痛点**（保险卡不含驾驶人，但系统不报红）。保留并推广这个规则，不要撤销。
4. **Trusted Packet = 已完成。不要再改 PacketStep 的骨架**。只参数化字段集，不改渲染逻辑。
5. **Broker "钱 moment" = Copy All 那一下**。确保在 Demo 中这个动作永远最后一个、最大、最突出。所有改动不能让 Copy All 变小或变不突出。

---

## 最终裁决

**GO_OR_NO_GO_FOR_BUILD:**  
**✅ GO — 条件是 scope 限定为 Add Vehicle + Replace Vehicle**

如果包含 Switch Insurance 或 Renewal：**NO-GO — 4 天内无法完成到 demo 标准**

---

**ONE_SENTENCE_RECOMMENDATION:**

> 四天内只做 **Add Vehicle + Replace Vehicle**，共享同一个 5-step 统一流程，Replace 在现有 Add Vehicle 代码上加 `related_vehicle` 字段 + 一行旧车警告，其余全复用，Day 4 留给真实文件测试和 broker walkthrough。

---

## 最终问题：明天第一步应该改什么？

**明天第一步（按优先级）：**

**第一步（30 分钟）：** 在 `CustomerFirstEntryScreen` 加 Intent Selector。

改动极小：
- 现有 `CustomerFirstEntryScreen` 只有一个"加新车"入口
- 加两个选项卡或两个大按钮：
  - 「我买了一辆新车」（Add Vehicle）
  - 「我换了一辆新车，旧车要移除」（Replace Vehicle）
- 两个选项选完后，后续 5 个 step **完全相同**，只是 `requestType` 参数不同
- PacketStep 根据 `requestType === 'replace'` 决定是否显示 RelatedVehiclePanel

**为什么这是第一步：**  
不改任何 extraction logic。不改任何 schema。只是在 UI 上宣告"我们支持两种 Request"。整个统一框架的 demo 从这一行 UI 改动开始可见。

**第二步（与第一步并行，或第一步之后 1 小时）：** Wire `save_case()` into `add_car.py`。

这是 Timeline 的前置条件，也是让每次提取都有 `case_id` 的关键。没有 `case_id`，broker 看到的 packet 是无法追溯的。

---

*Simulation 完成于 2026-06-19。无代码写入。SSOT: `docs/p16/P16_DECISION_FREEZE_V1.md`。*  
*建议 Andy 批准后，向 Decision Freeze V1 §14 追加 Replace Vehicle + Intent Selector 决策。*
