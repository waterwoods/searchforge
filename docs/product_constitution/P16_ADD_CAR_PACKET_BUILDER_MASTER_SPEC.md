# P16 Add-Car Packet Builder Master Spec

## 1. Product Definition
**One-sentence definition:** P16 Add-Car Packet Builder 是一个“上传即整理”的智能工具，将客户零散的加车材料转化为办公室可直接用于报价的标准化资料包 (Quote-Ready Packet)。

**What problem it solves:** 解决 Broker 办公室在处理加车请求时，需要反复在微信中翻找、确认、拼凑零碎文件和信息的痛点，消除 5-10 分钟的 re-reading 和 re-assembly 时间。

**Who pays:** 保险经纪公司 (Brokerage / Agency)。
**Who benefits:** 
- 办公室操作员 (如 Wu Xiaojie)：免去整理资料的痛苦，直接拿到结构化数据。
- 销售/经纪人 (如 Chen Kui)：减少跟进客户要资料的时间。
- 客户 (Customer)：体验现代化的上传流程，无需填写繁琐表单。

**Why customers would use it instead of WeChat:** 客户只需像发微信一样上传手头现有的文件，系统会自动提取信息并让他们确认，体验类似 TurboTax 的智能引导，比在微信里一来一回被追问更清晰、专业。

**Why Chen Kui would use it daily:** 告别“客户发来一堆乱七八糟的截图，我还得自己看缺什么”的窘境。一键发链接给客户，收回来的就是完整的 Packet。

**Why Wu Xiaojie would trust it:** 系统不会自作主张猜测不确定的信息 (No silent guessing)。所有提取的数据都经过客户 review 和 confirm，并且附带原始凭证 (Source evidence) 供随时核对。

---

## 2. Golden Business Principles
1. **Upload-first, not chat-first:** 核心交互是“上传证据”，而不是“开放式对话”。
2. **Customer submits evidence, system builds packet:** 客户提供原材料，AI 负责组装，客户只做选择题和确认题，不做填空题。
3. **AI extracts but customer confirms:** AI 提取的任何字段，必须经过客户的显式确认 (Explicit Confirmation) 才能进入最终的 Packet。
4. **One add-car request = one vehicle:** 保持业务逻辑极简，每次流程只处理一辆车的添加请求。多车请发起多次请求。
5. **Office sees packet, not raw chat:** 办公室的交付物是结构化的 Quote-Ready Packet，而不是冗长的对话记录。
6. **Uncertain facts must be flagged, not guessed:** AI 置信度低或冲突的信息必须标记为 Conflict/Needs Confirmation，绝不替客户做决定。
7. **Every feature must reduce follow-up, re-reading, or re-assembly:** 任何不能减少这三项成本的功能都不做。

---

## 3. Data Model
保持轻量级，避免过度设计。如果现有代码使用 `case_id`，在后端可以继续映射，但前端面向客户的语言必须是 "Request" 或 "Add-Car Request"。

- **Request (Add-Car Request):** 核心实体，对应一次加车请求。包含状态、关联的客户信息、车辆信息等。
- **Person:** 客户基本信息 (Name, Phone)。
- **Evidence:** 客户上传的原始文件/图片 (URL, Type, Upload Timestamp)。
- **ExtractedFact:** AI 从 Evidence 中提取的结构化字段 (Key, Value, Confidence, Source Evidence ID)。
- **MissingField:** 必需但尚未提取到的字段。
- **Conflict:** 提取到的冲突信息 (例如两份文件中 VIN 不一致)。
- **QuoteReadyPacket:** 最终生成的、供办公室使用的标准化数据包。

---

## 4. State Machine
极简的状态机设计，不引入 Temporal/Camunda。

- `draft_upload`: 客户正在上传文件阶段。(Customer sees)
- `extracting`: AI 正在处理和提取信息。(Customer sees progress)
- `needs_confirmation`: AI 提取完毕，等待客户 review、解决冲突和补充缺失信息。(Customer sees)
- `submitted_to_office`: 客户已确认并提交，办公室收到 Packet。(Office sees)
- `office_working`: 办公室正在处理报价。(Office sees)
- `closed`: 流程结束。(Office sees)

---

## 5. Conflict Handling
- **Duplicate same value:** 自动合并 (Merge)，记录多个 Source evidence。
- **Duplicate different value:** 标记为 Conflict，在 Confirmation 页面要求客户二选一或手动输入。
- **Low confidence:** 标记为 Needs Confirmation，要求客户确认。
- **Missing required field:** 标记为 Still Needed，在 Confirmation 页面要求客户补充填写或上传新文件。
- **Unrelated document:** 忽略提取，但在 Packet 中展示给办公室以防万一。
- **Second vehicle detected:** 阻断当前提取逻辑，提示客户 "Please complete this request for one vehicle first, then start a new request for the second vehicle."

---

## 6. Quote-Ready Packet Definition
办公室看到的最终交付物格式：

**Quote-Ready Packet**
- **Customer:** Name, Phone
- **Vehicle:** Year, Make, Model, VIN
- **Policy Context:** ZIP / Garaging ZIP, Existing policy info (if available)
- **Dates:** Delivery / Effective date
- **Driver:** Primary driver
- **Missing Items:** [List of any fields customer couldn't provide]
- **Conflicts/Notes:** [Any unresolved issues or customer notes]
- **Source Evidence:** [Thumbnails/Links to uploaded files]
- **Suggested Next Action:** e.g., "Ready to quote in AMS", "Call customer to clarify garaging ZIP"
