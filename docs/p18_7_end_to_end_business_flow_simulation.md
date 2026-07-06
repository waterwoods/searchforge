# P18.7 — End-to-End Business Flow Simulation（端到端业务流程仿真）

**Date:** 2026-07-04  
**Type:** 业务流程仿真 — **不是**技术实现文档  
**Audience:** Andy（founder）、陈总（CKS broker owner）、吴小姐（办公室操作员）、产品 / 工程（implementation sprint 直接输入）  
**Prerequisite:**

- Q0.11.1 WeCom 技术通道可靠性验证 ✅  
- P18.4 CKS 商业定位 ✅  
- P18.5 Demo Experience Plan ✅  
- P18.6 Demo Readiness / Cost / Smoothness Audit 进行中或已完成  

**Purpose:** 在 implementation sprint 写代码前，用 **真实客户对话** 模拟完整业务闭环，发现流程漏洞、体验不丝滑、重复提问、误判、Workbench 缺字段等问题。本文 **直接指导** 接下来的 implementation tasks。

**Related:** `docs/p18_4_cks_business_positioning_and_demo_strategy.md` · `docs/p18_5_chen_kui_demo_experience_plan.md` · `docs/p18_6_demo_readiness_cost_smoothness_audit.md` · `docs/p18_1_chen_kui_business_workflow_simulation.md` · `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`

**Authority:** 本文定义 **业务行为预期**；不 supersede ADR-001–005 或 B0 Contract。工程实现以本文 + B0 Contract 为准。

**Disclaimer:** 仿真基于 CKS 公开业务线索、陈总口述与既有产品决策做 **流程推断**；不构成法律、保险或合规建议。

---

## 1. 文档目标

### 1.1 这份文档解决什么问题

| 问题 | 本文如何回答 |
|------|-------------|
| 客户从 WeCom 进来后，AI **到底** 该做什么？ | 每条 story 逐步列出 Customer message → AI behavior → Case state → Workbench → Broker → Customer reply |
| 何时建 Case？何时 **不** 建？ | 明确 normal / ambiguity / generic 路径 |
| 改口、补充、说错、混合话题怎么处理？ | correction / mixed-topic / manual-handle 路径 |
| Broker Workbench **必须** 显示什么？ | §10 从仿真归纳最小信息模型 |
| 客户 **应该** 收到什么？什么 **不能** 承诺？ | 每条 story 的 Customer-facing reply + Notes / risk |
| Sprint 先做什么？ | §13 Demo implementation priority |

### 1.2 仿真范围

**在范围内：**

- WeCom 作为 **channel**（入口 + 回复）  
- Case 作为 **核心对象**（Premium Review / Claim Lite / Add Vehicle）  
- AI **prepare**，Broker **confirm** / **Manual Handle**  
- 三条主线 + 异常分支 + 跨天 continuity  

**不在范围内（本文不写代码、不部署、不测试）：**

- 具体 API / schema 设计  
- UI 像素级 spec  
- Carrier 对接、自动报价、自动理赔、自动改保单  

### 1.3 核心产品原则（全文约束）

```
WeCom = channel
Case   = 产品核心对象
AI     = prepare（intake、整理、标注、追问下一个最重要问题）
Broker = confirm / manual handle（报价、理赔建议、改保单仍由 broker 决定）

不是 chatbot · 不是自动报价 · 不是自动理赔 · 不是自动改保单
One Business Flow at a Time
Generic / unclear message → 不建 Draft Case
客户自然聊天，不强迫填长表
客户改口、补充、说错 → 进入 timeline + case update
```

### 1.4 输出物

Implementation sprint 应能从本文直接提取：

1. 三条 **case lane** 的行为 spec  
2. Workbench **字段清单**  
3. 客户侧 **reply 模板** 边界  
4. **Must have / Nice to have / 不做** 优先级  
5. **Acceptance criteria**（§14）

---

## 2. 仿真总规则

### 2.1 每一步的标准字段

所有 simulation step **必须** 覆盖以下七列（表格或等价结构）：

| 字段 | 说明 |
|------|------|
| **Customer message** | 客户原话（中文为主，可含英文术语） |
| **AI / system behavior** | 意图识别、是否建/更新 Case、提取字段、发什么 reply、设什么 flag |
| **Case state** | Case Type、Status、collected / missing、active flow |
| **Workbench display** | Broker 打开 case 时应看到什么 |
| **Broker action** | Confirm / Manual Handle / 回电 / 补问 / 无动作 |
| **Customer-facing reply** | 客户在微信侧收到的下一条消息 |
| **Notes / risk** | 边界、不能承诺的事、Rule 8、E&O 风险 |

### 2.2 路径类型定义

| 路径类型 | 定义 | 典型触发 |
|----------|------|----------|
| **normal path** | 意图清晰 → 建 Case → 逐步收集 → Ready for Broker → Broker 处理 → 客户 ack | Story A/B/C 主流程 |
| **correction path** | 客户改口、更正金额/日期/VIN 等 → timeline 保留旧值 + case update + Conflict Flag | A3、B2、C2、C3 |
| **ambiguity path** | 信息不足、generic、unclear → **不建 Draft** 或仅 intelligence stub → guide menu / 单问澄清 | A1、B1 |
| **mixed-topic path** | 当前 active flow 内出现第二业务 → **ack + flag**，**不** 并行第二 flow（Rule 8） | A4、B5、C5 |
| **manual-handle path** | 高风险 / 法律敏感 / 停保 / 伤亡变化 → Urgent + Manual Handle，AI 不做决定 | B2、B4、C6 |

### 2.3 Case 终态定义

每个 flow 结束时 Case 应处于以下 **之一**：

| 终态 | 含义 | 典型 Story |
|------|------|-----------|
| **Done** | Broker Confirm 完成；客户收到 Done Card 或等价 closure ack | Add Vehicle（Story C normal） |
| **Manual Handle** | Broker 已接手；系统不自动结案；客户收到「broker 会联系」类 ack | Claim Lite（Story B normal） |
| **Needs Info** | Case 已建但缺口仍大；AI 继续单问；Broker 可先看 partial summary | Premium Review 缺 dec page |
| **Ready for Broker** | 字段足够 broker 行动；等待 Confirm / Manual Handle | 三条 story 收集中期 |

### 2.4 全局不变量

| # | 不变量 |
|---|--------|
| 1 | Generic hello / unclear → **无 Draft Case** |
| 2 | Add Vehicle → **Start Card gate** → 客户点 Start 后才建 Draft |
| 3 | Premium Review / Claim Lite → demo 可 **minimal lane**（高置信 intent 直接 stub case）；**不要求** Start Card parity |
| 4 | 同一客户同一时刻 **只有一个 active business flow** |
| 5 | 第二 topic → acknowledge + Workbench flag；**不** 切换 flow 直到当前 flow 结束或 broker 关闭 |
| 6 | 图片 → 存 evidence；demo **不 OCR**；Missing Fields 仍列「需文字 VIN / 材料说明」 |
| 7 | Broker Confirm 前 **无** Active Case（B0 Contract） |
| 8 | AI **永不** 承诺：具体保费、换公司结果、该不该报保险、保单已生效、coverage 已恢复 |

---

## 3. Story A：VIP Premium Review — 正常流程

### 3.1 场景设定

| 维度 | 值 |
|------|-----|
| 客户身份 | **Known VIP** — seed 或历史：Uber Black / TCP，年保费 ~$10k–15k |
| 渠道 | WeCom |
| 开场白 | 「陈总，我保险又涨了，有没有便宜一点？我这个 Uber Black 一年太贵了。」 |

### 3.2 逐步仿真（normal path）

| Step | Customer message | AI / system behavior | Case state | Workbench display | Broker action | Customer-facing reply | Notes / risk |
|------|------------------|---------------------|------------|-------------------|---------------|------------------------|--------------|
| **A.0** | （系统 ingress） | WeCom callback → dedup `msg_id` → inbox queue | 无 Case | — | — | — | Q0.11.1 通道 |
| **A.1** | 「陈总，我保险又涨了，有没有便宜一点？我这个 Uber Black 一年太贵了。」 | Intent = **Premium Review**（`policy_review`）；匹配 Known VIP；创建 **Premium Review Case** stub；提取：涨价关切、Uber Black、比价意向 | Type: **Premium Review** · Status: **Needs Info** · Active flow: premium_review | Header: 张先生 · **Known** · **[VIP]** · **WeCom** · **Uber Black** · **High Premium** · Case: **Premium Review** · Status: Needs Info | — | 「张先生您好，收到。我先帮您整理续保涨价的情况，陈总会人工帮您看有没有更合适的选择。」 | **不** 自动报价；**不** 说「能便宜多少」 |
| **A.2** | — | 规则提取 + seed 合并 Known Facts；计算 Missing Fields | 同上，fields 更新 | **Summary:** 客户反映 Uber Black 保费上涨，希望比价或降低保费 · **Known Facts:** 用途 Uber Black/TCP；关切涨价；segment High Premium · **Missing:** current premium、renewal date、carrier、vehicle、driver、ZIP、recent claim/ticket、dec page · **Flags:** **Price Sensitive** · **Retention Risk** · **Next Action:** 索取 renewal notice / dec page → 安排 broker 人工比价 | — | 「方便的话，请发一下您现在的 **年保费大概多少**，以及 **续保日期** 是哪天？」 | **只问下一个最重要问题**：premium + renewal date |
| **A.3** | 「现在大概 15500 一年，下个月 15 号到期，State Farm」 | Merge: premium=$15,500、renewal≈next month 15th、carrier=State Farm | Status: **Needs Info** → 部分 Ready | Known +1: premium, renewal, carrier · Missing 减：vehicle, driver, ZIP, claim history, dec page | — | 「收到，$15,500、State Farm、下月 15 号续保。请问 **车辆 VIN** 或车型年份？还有 **停放邮编 ZIP**？」 | 不重复问 premium |
| **A.4** | 「VIN 后面发，ZIP 90012，Los Angeles」 | Merge ZIP=90012；VIN pending | 同上 | Missing: VIN, driver, dec page, claim confirm · Known: LA area | — | 「收到 ZIP 90012。VIN 您方便时再发；**最近一年有没有 claim 或 ticket**？」 | VIN 可 deferred |
| **A.5** | 「没有 claim，VIN 1HGBH41JXMN109186」 | Merge VIN；claim history = none | Status: **Ready for Broker**（dec page 仍缺但可 broker 先回电） | **Next Action:** broker 人工比价 / 回电；仍 Missing: dec page（optional for first call） | 陈总打开 case，review Summary + tags | 「好的，信息我先整理给陈总。他会 **人工帮您看** 续保选项，**不会在线上直接报价**。稍后办公室联系您。」 | **Needs Info → Ready for Broker** |
| **A.6** | — | — | Status: **Manual Handle**（Premium 无 auto Done） | Flags 仍可见 | 陈总 **Manual Handle** 或口头「我会打电话比价」 | 「陈总已收到您的续保咨询，办公室会尽快联系您讨论方案。」 | 终态：**Manual Handle** / broker-led；**非** Done Card 自动报价 |

### 3.3 Story A 正常流程 — 终态总结

| 维度 | 值 |
|------|-----|
| **终态** | **Ready for Broker** → Broker **Manual Handle**（Premium Review demo 不以 Confirm+Done 为主） |
| **客户收到** | 安全 ack +「broker 会人工看」；**无** 报价数字 |
| **Broker 得到** | VIP tags + Summary + Known/Missing + Retention Risk + Next Action |
| **系统不做** | 自动比价、换 carrier、bind 新保单 |

---

## 4. Story A 异常与改口场景

### A1. 客户只说「太贵了」，没有上下文

| 维度 | 预期 |
|------|------|
| **AI 理解** | Intent = ambiguous / possible **Premium Review**；置信度 **中低** |
| **是否建 Case** | **不建 Draft Case**；可选：仅 session intelligence，或 guide menu |
| **是否切换业务流** | 无 active flow → 不切换 |
| **Workbench** | 无新 case（或 list 不出现 junk case） |
| **Customer reply** | 「您好，请问您是想 **续保涨价/比价**、**加车**、还是 **事故理赔**？您可以简单说一下情况。」 |
| **不能承诺** | 不假设是 Premium Review；不建 Add Vehicle Draft |

---

### A2. 客户后来补充「我是 Uber Black」

| 维度 | 预期 |
|------|------|
| **AI 理解** | 若 A1 已 guide → 现在 intent 升至 **Premium Review** 高置信 |
| **是否建 Case** | **此时** 创建 Premium Review Case |
| **切换业务流** | 无 prior active flow → 正常进入 premium_review |
| **Workbench** | 新建 case；tags 加 **Uber Black** · **Commercial Driver** · **High Premium** |
| **Customer reply** | 「明白，Uber Black 续保我们常见。请问现在 **年保费大概多少**？」 |
| **Notes** | 补充信息 **retroactive merge** 进 Summary；timeline 保留 A1 原话 |

---

### A3. 客户说错金额，后来改口

| 维度 | 预期 |
|------|------|
| **Customer** | 先：「现在 12000 一年」→ 后：「不对，是 15500，刚看错了」 |
| **AI 理解** | correction path；新值覆盖 operational field；旧值留 timeline |
| **是否建 Case** | 已有 Premium Review Case → **update** |
| **Workbench** | Known Facts: premium=**$15,500** · **Conflict Flag:** premium updated (was $12,000) |
| **Customer reply** | 「好的，已更新为 **$15,500/年**。请问 **续保日期**？」 |
| **不能承诺** | 不对两个金额做评论或「以哪个为准」的法律判断 — broker 可见 conflict |

---

### A4. 客户同时说「我也想加一辆车」

| 维度 | 预期 |
|------|------|
| **Customer** | （在 Premium Review flow 中）「对了，我下周还要提一辆新车，也想加上。」 |
| **AI 理解** | mixed-topic；**Rule 8** |
| **是否建 Case** | **不** 新建 Add Vehicle Draft；设 flag `add_vehicle_mentioned_at` |
| **是否切换业务流** | **不切换**；active flow 仍为 premium_review |
| **Workbench** | Banner: 「Customer also mentioned add vehicle — handle **after** premium review or broker opens second case manually」 |
| **Customer reply** | 「加车的事记下了。我们先 **把续保涨价这件办完**；加车可以之后再单独办，或您现在想 **先办加车** 请告诉我。」 |
| **Broker** | 可见 flag；可决定先回电续保或之后开 Add Vehicle |

---

### A5. 客户发 renewal notice 图片，demo 暂不 OCR

| 维度 | 预期 |
|------|------|
| **AI 理解** | evidence event；`photos_pending` / `dec_page_image_received` |
| **是否建 Case** | 已有 case → attach evidence |
| **Workbench** | Known: 「Renewal notice 图片已收到（未 OCR）」· Missing: 「dec page 关键字段文字确认（premium/renewal date）」 |
| **Customer reply** | 「收到您的续保单图片。如果方便，请 **文字发一下续保日期和保费金额**，方便陈总核对。」 |
| **不能承诺** | 不说「已读懂图片」；不自动填充 OCR 字段 |

---

### A6. 客户问「你能不能现在直接帮我换公司？」

| 维度 | 预期 |
|------|------|
| **AI 理解** | 业务边界问题；仍为 Premium Review case |
| **是否建 Case** | 已有 → 更新 Summary 含「客户希望换 carrier」 |
| **Workbench** | Next Action: **broker 人工比价 + 回电**；Flag: **Retention Risk** ↑ |
| **Customer reply** | 「换公司需要陈总 **根据您的车辆和用途人工比价**，线上不能自动办理。我先帮您整理好信息，办公室会联系您。」 |
| **不能承诺** | **绝不** 「可以现在换」「已经帮您换了」「保证更便宜」 |

---

## 5. Story B：Claim Lite — 正常流程

### 5.1 场景设定

| 维度 | 值 |
|------|-----|
| 客户 | Known 或 New（均可；VIP 可选 seed） |
| 开场白 | 「我刚刚撞车了，现在怎么办？要不要报保险？」 |

### 5.2 逐步仿真（normal path）

| Step | Customer message | AI / system behavior | Case state | Workbench display | Broker action | Customer-facing reply | Notes / risk |
|------|------------------|---------------------|------------|-------------------|---------------|------------------------|--------------|
| **B.0** | 「我刚刚撞车了，现在怎么办？要不要报保险？」 | Intent = **Claim Lite**；创建 **Claim Lite Case** | Type: **Claim Lite** · Status: **Needs Info** · Urgent | **WeCom** · **Claim Lite** · Tags: **Urgent** · **Needs Fast Response** · **Claim Active** | — | 「收到，请先 **确保您和人都没事**。我先帮您记录事故信息，**陈总会尽快联系您**。线上 **不能** 替您决定是否报保险。」 | **先安全回应**；**无法律/理赔判断** |
| **B.1** | — | 计算 Missing；单问 | 同上 | **Summary:** 客户刚发生事故，询问是否报保险 · **Missing:** accident time, location, vehicle, injury, other party, photos, police report, carrier contacted | — | 「请问 **事故大概什么时间、什么地点**？您人有没有受伤？」 | 一次 **2 个最相关** 问题（时间地点 + 伤亡）— 仍属「下一个最重要块」 |
| **B.2** | 「刚才 10 点左右，在 405 附近，人没事」 | Merge time≈today 10am, location=405附近, injury=no | Status: Needs Info | Known: time, location, no injury · Missing: vehicle, other party, photos, police | — | 「收到，人没事就好。请问 **您的车辆** 是哪一辆（车型或 VIN）？**对方** 有没有留信息？」 | injury=no → 仍标 Urgent 但 injury flag 低 |
| **B.3** | 「我的 BMW，对方跑了，有拍几张照片」 | Merge vehicle=BMW；other party=unknown/fled；photos=mentioned | 同上 | Missing: photos received?, police report, carrier contacted · Known: hit-and-run hint | — | 「明白。请 **把照片发过来**；如果 **已报警** 也请告诉我。」 | 照片未到 → photos pending |
| **B.4** | （发 2 张图片，无文字） | evidence only；no OCR | 同上 | Known: 「事故照片 ×2（未解析）」· Missing: other party, police report number | — | 「照片收到了。请问 **有没有报警**？有的话 **报案号** 多少？」 | demo 不 OCR 车牌 |
| **B.5** | 「还没报警，还没打保险公司」 | Merge police=no, carrier=not contacted | Status: **Ready for Broker** | **Claim Intake Summary** 完整度够 broker 回电 | 陈总打开 → **Manual Handle** | 「信息已整理给陈总。他会 **尽快打电话** 跟您说下一步。**是否报保险、怎么报，由陈总跟您说。**」 | 终态：**Manual Handle** |
| **B.6** | — | Broker 点 Manual Handle | Status: **Manual Handle** | Timeline 全可见 | 陈总电话客户 | （可选系统 ack）「办公室已接手处理，请保持电话畅通。」 | **无** Done Card 自动理赔 |

### 5.3 Story B 正常流程 — 终态总结

| 维度 | 值 |
|------|-----|
| **终态** | **Manual Handle** |
| **客户收到** | 安全 ack + broker will review + **不** 替客户决定报不报 |
| **Broker 得到** | Claim Intake Summary + Urgent + Missing + photos evidence |
| **系统不做** | FNOL、adjuster dispatch、coverage 判断、premium impact 承诺 |

---

## 6. Story B 异常与改口场景

### B1. 客户很慌，只发「撞了怎么办」

| 维度 | 预期 |
|------|------|
| **AI 该问什么** | 先安全 + 单问：「人有没有受伤？人在安全地方吗？」 |
| **是否建 Case** | 高置信 claim → **建 Claim Lite Case**（即使信息极少） |
| **Urgent** | **是** — 立即标 Urgent / Needs Fast Response |
| **Manual Handle** | Broker 应 **尽快** 看到；AI 继续 collect 但不 delay broker alert |
| **不能 AI 决定** | 报不报保险、谁的责任、会不会涨保费 |
| **Case memory** | 每条碎片 append timeline；Summary 随 merge 更新 |

---

### B2. 客户说「没有人受伤」，后来又说「脖子有点疼」

| 维度 | 预期 |
|------|------|
| **AI 理解** | **correction path** + **injury escalation** |
| **Urgent** | **升级** — Injury Flag **yes / possible**；Needs Fast Response **最高** |
| **Manual Handle** | **立即** 建议 broker 回电；AI 不再追问琐碎字段 |
| **Workbench** | **Conflict Flag:** injury status changed (no → possible neck pain) · **Risk:** possible injury · Next Action: **broker call ASAP** |
| **Customer reply** | 「收到更新。如果脖子疼，**请先考虑就医或必要时报警**。陈总会 **马上联系您**，线上不能判断伤情。」 |
| **不能 AI 决定** | 不说不报保险；不建议不就医 |

---

### B3. 客户发照片，但不说明地点

| 维度 | 预期 |
|------|------|
| **AI 该问什么** | 「照片收到了。请问 **事故地点** 大概在哪里？」 |
| **Urgent** | 有照片仍 Urgent |
| **Workbench** | Known: photos ×n · Missing: **location** |
| **Case memory** | 照片 timestamp + evidence；不假设地点 |

---

### B4. 客户问「我要不要报保险，会不会涨价」

| 维度 | 预期 |
|------|------|
| **AI 理解** | 边界问题；记录在 Summary |
| **Manual Handle** | **必须** — 这不是 AI FAQ |
| **Customer reply** | 「是否报案、对保费有什么影响，需要陈总 **看您的保单和事故情况** 才能说。我先帮您记录，他会联系您。」 |
| **不能 AI 决定** | **绝不** 「建议报/不报」「不会涨价/会涨价」 |

---

### B5. 客户同时说「我保险也快到期了」

| 维度 | 预期 |
|------|------|
| **AI 理解** | mixed-topic（Claim + Premium Review） |
| **Rule 8** | active flow = **claim**；设 `premium_review_mentioned_at` flag |
| **是否切换** | **不** 建 Premium Review Case 直到 Claim flow broker 结案或 explicit 切换 |
| **Workbench** | Banner: 「Customer also mentioned renewal — handle after claim」 |
| **Customer reply** | 「续保的事记下了。我们 **先把事故这件处理好**；续保可以之后单独跟陈总说。」 |

---

### B6. 客户明天才补对方信息

| 维度 | 预期 |
|------|------|
| **AI 理解** | deferred field；case 保持 open |
| **Status** | **Needs Info** / Ready for Broker（partial） |
| **Customer reply** | 「好的，对方信息您 **明天发** 也行，我会帮您记着。」 |
| **Case memory** | 同一 `external_userid` 明天消息 **attach 同一 Claim Case**；不新建 |
| **Broker** | Workbench 显示 Missing: other party · Last updated timestamp |

---

## 7. Story C：Add Vehicle — 正常完整闭环

### 7.1 场景设定

| 维度 | 值 |
|------|-----|
| 开场白 | 「明天提新车，帮我加到保险。」 |
| Gate | **Start Card** 必须 |

### 7.2 逐步仿真（normal path）

| Step | Customer message | AI / system behavior | Case state | Workbench display | Broker action | Customer-facing reply | Notes / risk |
|------|------------------|---------------------|------------|-------------------|---------------|------------------------|--------------|
| **C.0** | 「明天提新车，帮我加到保险。」 | Intent = add_car **高置信**；**无 Case** | 无 Draft | — | — | 发 **Start Card**（msgmenu：开始 / 咨询别的） | **未点 Start 无 Draft** |
| **C.1** | （客户点 **Start / 开始**） | `click_id=start_add_car` → 创建 **Draft Case** | Type: **Add Vehicle** · Status: **Draft** · `broker_confirmed_at=null` | Header: New/Known · **WeCom** · **Add Vehicle** · **Draft** | — | 「好的，帮您整理加车信息。请先发 **车辆 VIN**。」 | B0 gate |
| **C.2** | 「VIN 1HGBH41JXMN109186」 | Merge VIN | Draft | Known: VIN · Missing: ZIP, effective date, driver, phone | — | 「收到 VIN。请问 **车辆停放邮编 ZIP**？」 | 单问 |
| **C.3** | （2 小时后）「ZIP 90012」 | Merge ZIP | Draft | Missing 减：effective date, driver, phone | — | 「收到 90012。请问 **希望哪天生效**？您说是明天提车对吗？」 | 引用已知「明天」 |
| **C.4** | 「对，明天生效，driver 李华，电话 6265550100」 | Merge date, driver, phone；attach phone → Known Customer 可能 | Status: **Ready for Broker** | Known Facts 全 · Missing: **空或仅 optional** · Draft badge | 吴小姐/陈总 review | 「信息齐了，我先整理给办公室。**陈总确认后** 会再通知您。」 | phone required before Confirm |
| **C.5** | — | — | Ready for Broker | 全字段可见 | 陈总点 **Confirm** | — | `broker_confirmed_at` set |
| **C.6** | — | 发 **Done Card** | Status: **Done** / Confirmed | Confirmed timestamp | — | Done Card 双语：「办公室已收到并确认您的加车信息，后续会按流程处理。」 | 终态：**Done** |

### 7.3 Story C 正常流程 — 终态总结

| 维度 | 值 |
|------|-----|
| **终态** | **Done**（Broker Confirm + Done Card） |
| **唯一 full live 闭环** | Demo 必须 Story C 端到端可重复 |
| **系统不做** | 自动 bind 保单、不承诺「已经加好」 |

---

## 8. Story C 异常与改口场景

### C1. 客户先说要加车，但没有 VIN

| 维度 | 预期 |
|------|------|
| **流程** | Start Card → Start → Draft → Missing: VIN 置顶 |
| **Customer reply** | 「请先发 **VIN**（行驶证或车窗贴纸上有）。」 |
| **Workbench** | Missing Fields: **VIN** 第一行 |

---

### C2. 客户发错 VIN 后改正

| 维度 | 预期 |
|------|------|
| **AI** | correction path；新 VIN 覆盖；旧 VIN 留 timeline |
| **Workbench** | **Conflict Flag:** VIN updated · 两值均可见 |
| **Customer reply** | 「好的，VIN 已更新为 xxx。」 |
| **Broker** | Confirm 前必须看到 conflict |

---

### C3. 客户 delivery date 从明天改成后天

| 维度 | 预期 |
|------|------|
| **AI** | effective date 更新；change flag |
| **Workbench** | Known: effective=后天 · Flag: **date changed** (was 明天) |
| **Customer reply** | 「好的，生效日期已改为 **后天**。」 |
| **Notes** | timeline 保留两次说法 |

---

### C4. 客户说「driver same as before」

| 维度 | 预期 |
|------|------|
| **AI** | 若 Known Customer + 历史 case 有 driver → **Possible Match** suggestion |
| **Workbench** | Known Facts: driver=李华（**待 broker 确认**，来自历史） |
| **Customer reply** | 「明白。我先按 **上次保单的驾驶员** 记录，办公室会核对。」 |
| **不能** | 静默 auto-fill 不展示给 broker |

---

### C5. 客户问「顺便我昨天撞车了」

| 维度 | 预期 |
|------|------|
| **Rule 8** | active flow = add_vehicle；设 `claim_mentioned_at` |
| **不** | 建 Claim Case、不 pause 加车 |
| **Workbench** | Banner: claim mentioned — handle separately after add-car |
| **Customer reply** | 「事故的事记下了，**请先优先把加车信息办完**；加好后陈总可以再跟您说事故。」 |
| **Broker** | 可见 claim flag；可加急回电但 **不** 在 UI 混两个 flow |

---

### C6. 客户说之前某辆车 coverage suspended / 停保，现在要开去修车或还车

**重点仿真场景**

| Step | Customer message | AI / system behavior | Case state | Workbench display | Broker action | Customer-facing reply | Notes / risk |
|------|------------------|---------------------|------------|-------------------|---------------|------------------------|--------------|
| **C6.1** | 「我加新车。对了，我 **另一辆 BMW 之前停保了**，今天要开去修车，还能开吗？」 | mixed-topic + **coverage risk**；add_vehicle flow 继续；设 `coverage_suspended_mentioned_at` + **Coverage Risk** flag | Add Vehicle Draft **+** Risk overlay | **Risk Flags:** **Coverage Suspended Reminder** · **Coverage Risk** · vehicle may **not** have active coverage · Next Action: **check policy status / call customer before drive** | **Manual Handle** on risk facet | 「停保车辆 **不能假设还能合法上路**。我先帮您记录，**请等陈总确认 coverage 状态后再动那辆车**。」 | **系统不要自动恢复保险** |
| **C6.2** | — | 不创建「恢复保单」case；不 merge 成 add vehicle VIN | 同上 | Summary 分两段：① Add Vehicle 新车 ② **Separate risk:** suspended BMW — broker must confirm | 陈总 **call customer** + 查 carrier portal | 「新车加保信息我们继续整理。**停保那辆请暂时不要开**，直到办公室确认。」 | E&O 高风险 |
| **C6.3** | — | — | Add Vehicle 仍可 Ready for Broker（新车）；Risk 区 **persistent** | **Manual Handle** 建议用于 coverage 部分 | Broker 分别处理：Confirm 加车 **≠** 恢复停保 | — | Confirm 加车 **不** 隐含恢复另一辆 |

**C6 核心原则：**

| 必须 | 禁止 |
|------|------|
| 标注 **Coverage Risk / Coverage Suspended Reminder** | 自动 restore coverage |
| Workbench 显示 broker must confirm before customer drives | 说「应该可以开」 |
| 客户侧谨慎 ack | 把停保车 merge 进 Add Vehicle VIN 流程 |

---

## 9. Cross-story Continuity（跨 story 连续性）

### 9.1 场景：同一客户三天内三个诉求

| 天 | 客户行为 | 系统行为 |
|----|----------|----------|
| **Day 1** | Premium Review 完整交流 | Case #1 Premium Review · Status: Manual Handle / Ready |
| **Day 2** | 「昨天续保的事谢谢。今天 **刚撞车了**…」 | **新** Case #2 Claim Lite · **不** merge 进 Case #1 |
| **Day 3** | 「车修好了。明天 **提新车** 要加保。」 | **新** Case #3 Add Vehicle（Start Card → Draft） |

### 9.2 Same customer 识别

| 机制 | 说明 |
|------|------|
| **Primary** | WeCom `external_userid` |
| **Secondary** | normalized phone（客户给出后 attach） |
| **Seed** | Demo VIP 客户预置 Known identity |

### 9.3 历史 Case 保留

| 规则 | 说明 |
|------|------|
| 每个 Case 独立 `service_record` | Premium / Claim / Add Vehicle **各一条** |
| Case list 按 customer 聚合 | Broker 可看 **customer timeline**（case 级，非 infinite chat） |
| Closed / Manual Handle case **只读** | 新消息 **不** 自动 reopen 除非 broker 或规则 explicit |

### 9.4 避免混 flow（Rule 8）

| 情况 | 行为 |
|------|------|
| Day 2 Claim 时 Case #1 仍 open | **允许** 新建 Claim Case（不同 business flow）；Case #1 标「superseded by broker」或保持 open 待 broker 关 |
| Day 3 Add Vehicle 时 Case #2 open | Add Vehicle 走 **Start Card**；Claim case 仍 visible · **不** 在 Add Vehicle Draft 里 collect claim 字段 |
| 客户在 Add Vehicle 中又提 renewal | flag only — 见 A4 / B5 |

### 9.5 Broker 看到的 Customer Timeline

```
Customer: 张先生 · Known VIP · WeCom
├── Case #1  Premium Review   · Manual Handle · 2026-07-02
├── Case #2  Claim Lite       · Manual Handle · 2026-07-03
└── Case #3  Add Vehicle      · Draft → Done  · 2026-07-04
```

**Demo 最低要求：** list 能按客户看到 **≥2 个历史 case**；detail 打开 **当前 story 对应 case**。

---

## 10. Workbench 最小信息模型

从 §3–§9 仿真归纳 — **Broker Workbench / Case Workspace** 必须支持：

### 10.1 Header / Identity

| 字段 | 来源 Story | 必填 |
|------|-----------|------|
| **Customer Identity**（name / phone / external_userid） | 全部 | ✅ |
| **Known / New / Possible Match** | 全部 | ✅ |
| **VIP** tag | A | ✅（Story A demo） |
| **High Premium / Uber Black / Commercial Driver** | A | ✅ |
| **Channel: WeCom** | 全部 | ✅ |
| **Case Type**（Premium Review / Claim Lite / Add Vehicle） | 全部 | ✅ |
| **Status**（Draft / Needs Info / Ready for Broker / Manual Handle / Done / Confirmed） | 全部 | ✅ |

### 10.2 Case Intelligence

| 字段 | 说明 |
|------|------|
| **Summary** | 2–4 句 broker-readable 中文 |
| **Known Facts** | 键值对：premium, VIN, ZIP, accident time, … |
| **Missing Fields** | 动态列表；收集后减少 |
| **Risk Flags** | Price Sensitive, Retention Risk, Urgent, Needs Fast Response, Injury, **Coverage Risk**, **Coverage Suspended Reminder** |
| **Conflict Flags** | premium updated, VIN updated, date changed, injury changed, dual ZIP |
| **Broker Next Action** | 单行：补 dec page / 回电 / 人工比价 / Manual Handle / Confirm |

### 10.3 Context / Action

| 字段 | 说明 |
|------|------|
| **Timeline** | 客户消息时间序；含改口前后 |
| **Latest Message** | 最近 1–3 条 |
| **Mixed-topic flags** | add_vehicle_mentioned, claim_mentioned, premium_review_mentioned, coverage_suspended_mentioned |
| **Confirm** | Add Vehicle Ready 时 |
| **Manual Handle** | Claim 主 CTA；Premium / Coverage Risk 亦可用 |
| **Done / Follow-up** | Done timestamp；Follow-up placeholder |

### 10.4 Layout 参考（与 P18.5 一致）

```
┌─────────────────────────────────────────────────────────────┐
│ 张先生 · Known · [VIP] · WeCom · Uber Black · High Premium   │
│  Case: Premium Review              Status: Ready for Broker  │
├─────────────────────────────────────────────────────────────┤
│  Summary · Known Facts · Missing Fields · Flags · Next Action│
├─────────────────────────────────────────────────────────────┤
│  Timeline (latest) · Mixed-topic banner if any               │
├─────────────────────────────────────────────────────────────┤
│  [ Confirm ]  [ Manual Handle ]                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. 客户侧体验规则

从仿真总结的 **AI 回复规则**（WeCom outbound）：

| # | 规则 | 反例（禁止） |
|---|------|-------------|
| 1 | **不要一次问太多** — 下一条只问 **下一个最重要** 的 1 个（或紧密相关的 2 个，如时间+地点） | 「请提供 VIN、ZIP、日期、driver、phone、dec page」 |
| 2 | **不重复问已知信息** | 已有 VIN 再问 VIN |
| 3 | **客户改口时 acknowledge update** | 静默覆盖 |
| 4 | **客户不清楚时 guide menu** | 乱猜 intent 建 Draft |
| 5 | **高风险场景提醒 broker review** | 「您应该可以开车」 |
| 6 | **不承诺报价** | 「能便宜 2000」 |
| 7 | **不承诺理赔结果** | 「建议不报」「一定会赔」 |
| 8 | **不承诺改保单 / 已生效** | 「已经帮您加好了」 |
| 9 | **明确 broker 会审核** | 「系统已自动处理完毕」 |
| 10 | **Claim 先安全** | 直接问 VIN |
| 11 | **Generic 不建 Draft** | 「你好」→ Add Vehicle Draft |
| 12 | **Add Vehicle 必须 Start Card** | 听到加车就建 Draft |
| 13 | **混合话题：ack + defer（Rule 8）** | 同时开两个 flow |
| 14 | **图片：收到 + 请补文字** | 「已 OCR 读出 VIN」 |
| 15 | **停保 / coverage：谨慎 + 等 broker** | 「停保应该没事」 |

### 11.1 语气模板（示例）

| 场景 | 模板方向 |
|------|----------|
| Premium 收集 | 「收到。请问 **年保费大概多少**？」 |
| Claim 安全 | 「人没事最重要。请问 **时间地点**？」 |
| Add Vehicle Start 后 | 「请先发 **VIN**。」 |
| 改口 ack | 「好的，已更新为 **{new_value}**。」 |
| 边界 | 「这个需要陈总 **人工看**，线上不能自动办。」 |
| Done Card | 「办公室已确认收到您的加车信息…」 |

---

## 12. 流程漏洞与实现建议

从 simulation 输出的 **implementation 输入**：

### 12.1 需要新增 / 明确的 case lanes

| Lane | 创建触发 | Gate | 终态 CTA |
|------|----------|------|----------|
| **Premium Review** | `policy_review` 高置信 | 无 Start Card（minimal） | Manual Handle |
| **Claim Lite** | claim markers 高置信 | 无 Start Card（minimal） | Manual Handle |
| **Add Vehicle** | `add_car` 高置信 | **Start Card 必须** | Confirm → Done Card |

### 12.2 需要的 tags / flags

| Tag / Flag | Story |
|------------|-------|
| VIP, High Premium, Uber Black, Commercial Driver | A |
| Price Sensitive, Retention Risk | A |
| Urgent, Needs Fast Response, Claim Active, Injury | B |
| Coverage Risk, Coverage Suspended Reminder | C6 |
| claim_mentioned_at, add_vehicle_mentioned_at, premium_review_mentioned_at, coverage_suspended_mentioned_at | mixed-topic |
| Conflict flags（premium, VIN, date, injury, ZIP） | correction |

### 12.3 Mock vs Live vs Manual

| 能力 | Mock / Seed | Live | 必须人工 |
|------|-------------|------|----------|
| WeCom ingress/egress | — | ✅ | — |
| VIP Known identity | ✅ seed | 可选 | — |
| Premium field merge | 规则 + seed | ✅ minimal | 比价、换公司 |
| Claim field merge | 规则 | ✅ minimal | 报不报、电话 |
| Add Vehicle full flow | reset fixture | ✅ **必须** | Confirm |
| OCR / 图片解析 | photos_pending | log only | broker 读图 |
| Coverage 恢复 | flag only | — | **必须** broker |
| 报价 / carrier | — | — | **必须** broker |

### 12.4 需要测试的场景（QA 清单）

| # | 场景 |
|---|------|
| 1 | Generic hello → 无 Draft |
| 2 | Story A normal + A1 ambiguity |
| 3 | A3 premium correction conflict |
| 4 | A4 mixed add vehicle flag |
| 5 | Story B normal + B2 injury escalation |
| 6 | B4 不报保险边界 reply |
| 7 | Story C full Start → Confirm → Done ×2 |
| 8 | C2 VIN conflict |
| 9 | C5 claim mentioned during add-car |
| 10 | C6 coverage suspended — **no auto restore** |
| 11 | Cross-story 三天三 case |
| 12 | dedup / 不重复 outbox |

### 12.5 不该在 3–4 天 demo 做

| 项 | 原因 |
|----|------|
| Real OCR | 成本；photos_pending 足够 |
| Carrier API / 实时 quote | ADR-003 |
| FNOL / adjuster | Claim Lite = intake only |
| Multi-flow 并行 | Rule 8 永久不做 |
| Full timeline UI | ADR-002；latest 1–3 条够 |
| CRM / household | 超出 intake MVP |
| 自动 renewal reminder | Value E — verbal |
| LLM 长 summary | 规则 summary 够 demo |

### 12.6 仿真发现的流程漏洞（需在 sprint 关闭）

| 漏洞 | 影响 | 建议 |
|------|------|------|
| Premium/Claim **无 WeCom lane** | Story A/B 无法 live | Day 2 minimal stub + merge |
| Workbench **无 intelligence 区块** | 陈总看不到 Service Desk | Day 1 布局 + seed |
| **Manual Handle** UI 弱 | Story B 无法闭环 | Day 2–3 CTA |
| mixed-topic **仅 add-car 有 flag** | A4/B5/C5 不一致 | 统一 `*_mentioned_at` 模式 |
| C6 coverage risk **无专用 flag** | E&O 风险 | 加 Coverage Suspended Reminder |
| Cross-story **customer 聚合** | 留存叙事弱 | list 按 customer 分组 demo seed |

---

## 13. Demo Implementation Priority（3–4 天 sprint）

与 P18.5 §10、P18.6 §7 对齐，经 **本仿真强化**：

### 13.1 Must Have

| # | 项 | 仿真依据 |
|---|-----|----------|
| 1 | **Add Vehicle full live**（Start → Draft → merge → Confirm → Done ×2） | §7 — 唯一 full proof |
| 2 | **Premium Review minimal**（intent → stub case → tags → summary → missing → next action） | §3–§4 |
| 3 | **Claim Lite minimal**（intent → stub → urgent → summary → Manual Handle） | §5–§6 |
| 4 | **Coverage Risk / Coverage Suspended reminder**（flag + Workbench + 谨慎 reply） | §8 C6 — high-value insight |
| 5 | **Workbench tags + Known/Missing/Flags/Next Action** | §10 |
| 6 | **Demo seed / reset**（VIP 客户 + 三 story 可复现） | §9 |
| 7 | **Script / fallback recording** | P18.6 |
| 8 | **Rule 8 mixed-topic flags**（至少 claim_mentioned + add_vehicle_mentioned） | §4 A4, §6 B5, §8 C5 |
| 9 | **Conflict flags**（VIN / premium / date / injury） | correction paths |
| 10 | **Generic safety**（Q0.11.1 不回退） | §2 |

### 13.2 Nice to Have

| 项 |
|----|
| Image parsing |
| Real OCR |
| Automated renewal reminder |
| Real quote integration |
| Real carrier integration |
| Full customer timeline panel |
| LLM-generated summary |
| Identity Possible Match UI polish |

### 13.3 建议 sprint 日程

| 天 | 焦点 | 仿真验收 |
|----|------|----------|
| **Day 1** | Workbench §10 布局 + seed + badges | 用 seed 打开 Story A/B/C case，30 秒答 type/missing/next |
| **Day 2** | Premium + Claim minimal lane + reply 模板 | 跑通 §3.2 + §5.2 主步骤 |
| **Day 3** | Add Vehicle polish + Manual Handle + conflict/mixed flags | 跑通 §7.2 + C2/C5/C6 flag |
| **Day 4** | Rehearsal + fallback + cross-story seed | §9 三天三 case 可见 |

---

## 14. Acceptance Criteria（本文档验收标准）

本文档 **完成** 当且仅当满足：

| # | 标准 | 章节 |
|---|------|------|
| 1 | 模拟 **三条主线** 完整闭环（Premium Review / Claim Lite / Add Vehicle） | §3, §5, §7 |
| 2 | 包含 **正常、改口、错误、混合话题、停保风险** 场景 | §4, §6, §8（含 C6 重点） |
| 3 | 明确 **Workbench 应显示什么** | §3–§8 每步 + §10 |
| 4 | 明确 **客户应收到什么** | 每步 Customer-facing reply |
| 5 | 明确 **AI 不应该承诺什么** | Notes / risk + §11 |
| 6 | 直接给 **implementation sprint 优先级** | §12, §13 |
| 7 | 遵守 **WeCom=channel, Case=core, AI prepare, Broker confirm** | §2.4 |
| 8 | 遵守 **One Business Flow at a Time** | §4 A4, §6 B5, §8 C5, §9 |
| 9 | **Generic 不建 Draft**；**Add Vehicle 有 Start gate** | §2, §7, §8 C1 |
| 10 | **Cross-story continuity** 有明确规则 | §9 |

---

## 附录 A — 三 Story 终态对照表

| Story | 正常终态 | 客户收到 | Broker CTA | 禁止 |
|-------|----------|----------|------------|------|
| **A Premium Review** | Ready for Broker → Manual Handle | 安全 ack；broker 会联系 | 人工比价 / 回电 | 自动报价、换公司 |
| **B Claim Lite** | Manual Handle | 安全 ack；broker 会尽快联系 | Manual Handle | 报不报建议、自动理赔 |
| **C Add Vehicle** | Done（Confirm + Done Card） | Done Card | Confirm | 自动加保、已生效承诺 |

---

## 附录 B — 与上游文档的关系

```
P18.4 商业定位（CKS 是谁、VIP 为何重要）
    ↓
P18.5 Demo 体验（陈总看到什么、8–12 分钟 flow）
    ↓
P18.6 Readiness Audit（成本、丝滑度、Go/No-Go）
    ↓
P18.7 本文 — 逐步对话级仿真 → implementation tasks 输入
    ↓
Implementation sprint（3–4 天）→ 陈总 demo
```

---

*End of P18.7 — End-to-End Business Flow Simulation*
