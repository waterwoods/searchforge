# P18.5 — 陈总 Demo 体验计划（Demo Experience Plan）

**Date:** 2026-07-04  
**Type:** Demo 体验设计 + 商业工作流规划 — **不是**技术实现文档  
**Audience:** Andy（demo 主讲）、陈总（CKS broker owner）、吴小姐（办公室操作员）、产品 / 工程（下一 sprint 参考）  
**Prerequisite:**

- P18.4 CKS 业务定位已定：华人客户为主；TCP / Uber Black / 商业车司机为高价值 segment  
- WeCom 通道可用；Q0.11.1 通过（reliability + generic message safety）  
- 现有组件：WeCom inbox/outbox、`message_processed`、`sync_cursor`、Start Card、`active_case_bridge`、`service_records`、`record_messages`、Broker Workbench、Confirm、Done Card  

**Purpose:** 定义陈总在 demo 中 **具体看到什么、感受到什么、理解什么**——让 3–4 天 sprint 产出的演示 **商业上 impress、流程上顺畅**，且始终像 **新办公室工作流**，而非 chatbot 秀。

**Related:** `docs/p18_4_cks_business_positioning_and_demo_strategy.md` · `docs/p18_3_vip_driver_business_value_analysis.md` · `docs/p18_chen_kui_wecom_ai_case_intake_demo.md` · `docs/p18_1_chen_kui_business_workflow_simulation.md`

**Authority:** 本文定义 demo **体验与叙事**；不 supersede ADR-001–005 或 `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md`。工程实现见 §10。

---

## 1. Demo North Star

### 1.1 这不是什么

| 错误 framing | 为什么不行 |
|--------------|------------|
| 「AI 能在微信上自动回消息」 | 陈总已有吴小姐；chatbot _reply 不是差异化 |
| 「我们做了 WeCom 对接」 | 技术打通是前提，不是产品价值 |
| 「加车机器人」 | 只展示 Add Vehicle 会低估 CKS 真实业务（renewal / claim） |

### 1.2 这是什么

> **CKS 办公室获得一套新的 AI-powered service workflow（AI Insurance Service Desk）。**

```
客户（WeCom 微信客服入口）
    → AI 接收、识别、整理
    → Case Workspace 呈现 broker-ready case
    → 陈总 / staff 在 Broker Workbench review
    → Broker Confirm / Manual Handle
    → 客户收到 ack（Done Card 或安全回复）
```

| 角色 | 定义 |
|------|------|
| **WeCom** | Customer channel — 客户习惯不变，入口从个人微信变为办公室服务号 |
| **Case Workspace** | Product — 每一次诉求是有身份、有记忆、有缺口、有下一步的 Case |
| **AI** | Prepares the case — intake、organize、summarize、missing info、tags、next action |
| **Broker** | Confirms — 报价、理赔建议、改保单 **仍由陈总决定** |

### 1.3 Demo 一句话 North Star

**「客户还是发微信；CKS 办公室得到的是 Case，不是聊天记录；AI 备案，陈总拍板。」**

---

## 2. 陈总 Demo 结束时应感受到什么

Demo 结束时，陈总 **情绪上** 应接近以下六点（Andy 需在 narrative 中逐条 landing）：

| # | 陈总应感受到 | 反面（必须避免） |
|---|-------------|------------------|
| 1 | **我不必亲自记住每条微信对话** | 「还是要我翻手机找 VIN」 |
| 2 | **VIP / High Premium 客户可以被优先看见** | 「所有消息还是 FIFO 排队」 |
| 3 | **Staff 可以接手 Case** | 「只有我能答，吴小姐还得问我」 |
| 4 | **理赔和续保对话被整理成 Case** | 「事故和涨价还是混在聊天里」 |
| 5 | **系统省时间、少漏问、少出错** | 「看起来 fancy，但我更忙了」 |
| 6 | **AI 帮我管高价值客户，不是取代我** | 「AI 替我做报价 / 理赔决定」 |

### 2.1 「被 impress」的正确定义

- ✅ 「这种 Uber Black 续保涨价的客户，终于有 VIP Case 了。」  
- ✅ 「出事故时，summary 已经整理好，我打电话前先看一眼。」  
- ✅ 「加车吴小姐能接，我点 confirm 就行。」  
- ❌ 「AI 比我还懂保险。」  
- ❌ 「以后不用我管了。」  

---

## 3. Value Hierarchy（价值层级）

Demo 叙事与 **屏幕展示顺序** 均按以下优先级排列。

---

### A. Save broker time（节省 broker 时间）— 最高优先级

| 维度 | 内容 |
|------|------|
| **旧 WeChat 痛点** | 每条 request：翻 thread →  mentally merge → 想 checklist → 写回复 → 再翻有没有漏；续保 / 事故单 case 常 **10+ 分钟** 才进入「能干活」状态 |
| **新 Case Workspace 改善** | 打开 Workbench → **30 秒内** 看到 Summary、Known Facts、Missing Fields、Broker Next Action；无需重读全部 bubble |
| **Demo 应展示的屏幕** | Broker Workbench case detail：**Summary** 区块置顶；**Known Facts** vs **Missing Fields** 并列；**Timeline / latest message** 可展开但不强迫 broker 逐条读 |

**Andy 话术锚点：** 「以前你花 10 分钟搞懂客户在说什么；现在打开案子 30 秒。」

---

### B. Reduce missing information and errors（减少缺失信息与错误）

| 维度 | 内容 |
|------|------|
| **旧 WeChat 痛点** | 客户分五条发 VIN / ZIP / 日期；broker 漏看一条 → 第三次追问 → 客户烦；两个 VIN 冲突无人标记 |
| **新 Case Workspace 改善** | AI 合并碎片 → **Missing Fields** 显式列出；**Conflict / risk flags** 高亮；broker 按清单补问，不凭记忆 |
| **Demo 应展示的屏幕** | **Missing Fields** 列表（Premium：缺 dec page；Claim：缺 photos / other party；Add Car：缺 ZIP）；若有冲突，**Risk Flags** 区显示（如 dual VIN hint） |

**Andy 话术锚点：** 「系统告诉你 **还缺什么**，不是猜。」

---

### C. Enable staff handoff（支持 staff 交接）

| 维度 | 内容 |
|------|------|
| **旧 WeChat 痛点** | 上下文在陈总手机与脑中；吴小姐需问「这个客户什么情况」；陈总不在 → VIP 空等 |
| **新 Case Workspace 改善** | 同一 Case 在 Workbench **全貌可见**：identity、tags、summary、timeline；staff 按 **Broker Next Action** 执行 |
| **Demo 应展示的屏幕** | Case list 吴小姐视角（或 Andy 口述切换）；detail 无需 oral transfer；**Confirm / Manual Handle** 陈总可示范授权 staff 操作（或 Chen 本人点击） |

**Andy 话术锚点：** 「你不在办公室，吴小姐打开 Workbench 就能接着办。」

---

### D. Improve VIP / high-premium customer retention（提升 VIP 留存）

| 维度 | 内容 |
|------|------|
| **旧 WeChat 痛点** | 年保费 $10k–15k 客户与普通询价混在一起；涨价不满、续保窗口 **silent churn**；响应慢 → 客户找 competitor |
| **新 Case Workspace 改善** | **VIP · High Premium · Uber Black · Retention Risk · Price Sensitive** 标签；Premium Review Case 优先进入 narrative；broker 主动看见「这单值得先回」 |
| **Demo 应展示的屏幕** | Story A Workbench：**VIP** badge + segment tags + **Retention Risk** / **Price Sensitive** flags；case type = **Premium Review** |

**Andy 话术锚点：** 「官网那种一万五 TCP 客户，值得一个 VIP Case，不是躺在聊天列表里。」

---

### E. Create future revenue opportunities（未来收入机会）— 展示位，不 deep build

| 维度 | 内容 |
|------|------|
| **旧 WeChat 痛点** | cross-sell（home）、renewal reminder、coverage gap 全靠 broker 脑子；无 systematic follow-up |
| **新 Case Workspace 改善** | Case memory + tags 为 **Renewal Soon**、future opportunity 留位；demo ** verbal + 静态 placeholder** 即可 |
| **Demo 应展示的屏幕** | Workbench 可选 **Future / Opportunity** 占位（静态「coming soon」）；或 Andy 口头：「续保提醒、house bundle 以后可以挂在这个 Case 上」 |

**Andy 话术锚点：** 「今天先做 intake；明天这些标签能变成 renewal reminder 和 cross-sell 线索。」

---

### 价值层级总览

```
Demo 叙事权重
    A Save time          ████████████████████  必须 screen-proof
    B Reduce errors      ████████████████████  必须 screen-proof
    C Staff handoff      ████████████████      必须 narrative + screen
    D VIP retention      ████████████████████  Story A 核心
    E Future revenue     ████                  mention / placeholder
```

---

## 4. Recommended Demo Flow（8–12 分钟）

**总时长：** 8–12 分钟（含 Q&A buffer 可延至 15 分钟）  
**Story 顺序：** Premium Review → Claim Lite → Add Vehicle（与 P18.4 一致）  
**环境：** Live WeCom + Broker Workbench；Premium / Claim 可 minimal / mock-backed（见 §6）

---

### Phase 0 — Opening：Before / After（约 1.5 分钟）

| 步骤 | Andy 做什么 | 陈总看到 / 听到 |
|------|------------|----------------|
| 0.1 | 不打开系统，先讲故事 | Before：个人微信、消息散、靠记忆、VIP 与普通客户混在一起 |
| 0.2 | 对比 | After：WeCom AI Service Desk → structured cases → Broker Workbench |
| 0.3 | 定位句 | 「不是 chatbot，是 **AI Insurance Service Desk**；WeCom 是入口，**Case Workspace** 是产品。」 |
| 0.4 | 边界预告 | 「AI 做 intake 和整理；**报价、理赔、改保单还是你决定**。」 |

**可选开场问题（等陈总点头）：**

> 「你那些 Uber Black 客户续保涨价、或者出事故，是不是都在个人微信里，要靠你自己记谁更急？」

---

### Story A — VIP Premium Review（约 3–4 分钟）

**客户台词（WeCom 测试号或预录）：**

> 「陈总，我保险又涨了，有没有便宜一点？我这个 Uber Black 一年太贵了。」

| 步骤 | 系统应展示 | Andy 讲解要点 |
|------|-----------|--------------|
| A.1 | 消息进入 WeCom；**不**因 generic 误建 Add Car Draft | Q0.11.1 安全；这是 **Premium Review**，不是加车 |
| A.2 | Workbench 出现 / 打开 **Premium Review Case** | Case Type 明确 |
| A.3 | Tags：**VIP · Uber Black / Commercial Driver · High Premium · Price Sensitive · Retention Risk** | 「这种客户你会想 **先回**。」 |
| A.4 | **Summary**：客户关切涨价、想比价 | AI prepared，不是 auto quote |
| A.5 | **Known Facts**（若有 seed：车辆、用途线索） | 从碎片或 seed 来 |
| A.6 | **Missing Fields**（如 renewal notice、近期 claim 确认、里程） | 减少漏问 |
| A.7 | **Broker Next Action**：补 dec page / 安排人工比价 / 回电 | **Intake + broker review**，不承诺自动报价 |
| A.8 | Andy 示范：陈总 review，口头「我会打电话」 | Broker 控制最终决策 |

**Story A 禁止说法：** 「系统自动帮你找最便宜保险公司。」

---

### Story B — Claim Lite（约 2.5–3.5 分钟）

**客户台词：**

> 「我刚刚撞车了，现在怎么办？要不要报保险？」

| 步骤 | 系统应展示 | Andy 讲解要点 |
|------|-----------|--------------|
| B.1 | **Claim Lite Case** 创建（独立 lane，不与 Story A 混） | 一类事一个 Case |
| B.2 | Tags：**Urgent · Needs Fast Response · Claim Active** | VIP 事故应置顶 narrative |
| B.3 | AI 引导 / 收集：时间、地点、伤亡、对方、报警、照片 | 分条 intake |
| B.4 | **Claim Intake Summary** | broker 打电话前一眼看懂 |
| B.5 | **Missing accident info**（photos、other party 等） | 显式缺口 |
| B.6 | **Broker Next Action：Manual Handle** | 必须 broker 电话；**不** auto filing |
| B.7 | Andy 点 **Manual Handle**（或示范） | 无 Done Card 自动化；安全 ack 即可 |

**Story B 禁止说法：** 「AI 告诉你该不该报保险。」「系统自动理赔。」

---

### Story C — Add Vehicle full flow（约 3–4 分钟）

**客户台词：**

> 「明天提新车，帮我加到保险。」

| 步骤 | 系统应展示 | Andy 讲解要点 |
|------|-----------|--------------|
| C.1 | **Start Card**（未点 Start 无 Draft） | 成熟 gate；generic 不误建 |
| C.2 | 客户点 **Start / 开始** → **Draft Case** | 明确 consent |
| C.3 | 碎片消息：VIN、ZIP、date、driver | **Missing Fields** 动态减少 |
| C.4 | Workbench：**Known Facts** 填满 | 结构化闭环 |
| C.5 | 陈总或 Andy 点 **Broker Confirm** | Broker gate |
| C.6 | 客户收到 **Done Card** | 客户侧 closure |

**Story C 定位句：**

> 「续保和事故是 CKS 最赚钱、最建信任的场景；加车这条证明 **系统能完整跑通**，吴小姐也能接手。」

---

### Phase 4 — Closing（约 1 分钟）

- 回顾 North Star：Case Workspace，不是 chatbot  
- 回顾价值 A→D：省时间、少出错、staff 能接、VIP 能看见  
- 明确边界（§9）  
- 邀请陈总复述一句：「AI 备案，我拍板。」  

---

### 时间预算表

| 段落 | 目标时长 |
|------|----------|
| Opening Before/After | 1.5 min |
| Story A Premium Review | 3–4 min |
| Story B Claim Lite | 2.5–3.5 min |
| Story C Add Vehicle | 3–4 min |
| Closing + boundary | 1 min |
| **合计** | **8–12 min** |

---

## 5. Workbench Screen Requirements（陈总必须看到的最小布局）

以下为 **单 case detail 视图** 最低要求；list 视图需能筛/认 WeCom + case type。

### 5.1 Header / Identity 区

| 字段 | 要求 | Demo 示例 |
|------|------|-----------|
| Customer name | 姓名或「未知客户」 | 张先生 / Unknown |
| Identity state | **Known / New / Possible Match** | Known（VIP seed） |
| **VIP** tag | 醒目 badge | VIP |
| **Channel** | **WeCom** | 微信客服 |
| **Segment** | Uber Black / Commercial Driver / High Premium | 至少其一可见 |
| **Case Type** | Premium Review / Claim Lite / Add Vehicle | 随 story 变 |
| **Status** | Draft / Ready for Broker / Manual Handle / Confirmed | 随 flow 变 |

### 5.2 Case Intelligence 区

| 字段 | 要求 |
|------|------|
| **Summary** | 2–4 句 broker-readable 中文摘要 |
| **Known Facts** | 键值或 bullet：已收集事实 |
| **Missing Fields** | 明确列表；可加「仍缺」计数 |
| **Risk / Opportunity Flags** | Price Sensitive、Retention Risk、Urgent、injury hint、claim_mentioned 等 |
| **Broker Next Action** | 单行可执行建议：补料 / 回电 / 人工比价 / Manual Handle |

### 5.3 Context / Action 区

| 字段 | 要求 |
|------|------|
| **Timeline / latest customer message** | 至少最新 1–3 条；完整 thread 可折叠 |
| **Confirm** | Add Vehicle ready 时出现；触发 Done Card |
| **Manual Handle** | Claim Lite 主 CTA；Premium Review 可选 |

### 5.4 Layout 示意（ASCII）

```
┌─────────────────────────────────────────────────────────┐
│ 张先生 · Known · [VIP] · WeCom · Uber Black · High Premium │
│  Case: Premium Review          Status: Ready for Broker   │
├─────────────────────────────────────────────────────────┤
│  Summary                                                  │
│  客户反映 Uber Black 保费上涨，希望比价或换公司…              │
├──────────────────────┬──────────────────────────────────┤
│  Known Facts         │  Missing Fields                   │
│  · 用途: TCP/Uber    │  · Renewal notice                 │
│  · 关切: 涨价        │  · 近期 claim 确认                 │
├──────────────────────┴──────────────────────────────────┤
│  Flags: Price Sensitive · Retention Risk                  │
│  Next Action: 索取 dec page → 安排 broker 人工比价          │
├─────────────────────────────────────────────────────────┤
│  Timeline (latest)                                        │
│  「陈总，我保险又涨了…」                                    │
├─────────────────────────────────────────────────────────┤
│  [ Confirm ]  [ Manual Handle ]                           │
└─────────────────────────────────────────────────────────┘
```

### 5.5 Case List 最低要求

- 每行：客户标识、Case Type、Status、Channel=WeCom、VIP 点状标记  
- 可选 demo filter：**仅 WeCom cases**  

---

## 6. Live vs Mock / Minimal（什么真跑、什么可 mock）

| 能力 | 建议模式 | 理由 |
|------|----------|------|
| **WeCom 入口 / 回复** | **Live** | Q0.11.1 已通过；demo 可信度靠真通道 |
| **inbox/outbox / dedup** | **Live** | 已验证；不需 mock |
| **Story C Add Vehicle** | **Live / Full** | 现有 flow 最强；Start → Draft → Confirm → Done Card 必须端到端 |
| **Story A Premium Review** | **Minimal 或 mock-backed Workbench case** | 分类 + 摘要 + tags + missing + next action 可见即可；可无完整 Start Card lane |
| **Story B Claim Lite** | **Minimal flow 或 mock-backed case** | Claim Intake Summary + urgent + Manual Handle；可无完整 OCR / FNOL |
| **VIP tags / AI Insights** | **Rule-based 或 demo seed / mock** | 演示 **概念与优先级**；不需 ML |
| **Identity Known/New** | **Seed data 或规则** | 测试客户预置为 Known VIP |
| **Carrier integration** | **None** | 明确不做 |
| **Premium 自动报价** | **None** | Workbench 只显示 next action: 人工比价 |
| **Claim 自动 filing** | **None** | Manual Handle only |

### 6.1 Demo 数据策略

| 策略 | 说明 |
|------|------|
| **Demo seed / reset** | 每次 demo 前重置 VIP 测试客户 + 三条 story 可复现状态 |
| **Fallback recording** | Live 失败时播放预录屏（Story A/B mock + Story C live 片段） |
| **双路径 rehearsal** | Andy 至少走通一遍 full live、一遍 mock-backed |

### 6.2 陈总应理解的诚实表述

> 「续保和事故这两条，demo 可能是 **简化版 intake**；加车是 **完整闭环**。上线后同一套 Case Workspace 会加深。」

---

## 7. Demo Script（Andy 主讲稿）

**语气：** 务实、不夸大；强调 AI = prepare，broker = decide。

---

### 7.1 开场（约 30 秒）

> 「陈总，今天不是给你看聊天机器人。  
> 你办公室现在大部分客户还在 **个人微信** 里，消息散、靠你记。尤其是 **Uber Black、保费高的客户**——续保涨价、出事故、要文件——混在一起的。  
> 我们做的是：**客户进 WeCom 办公室服务号，AI 帮你们整理成 Case，你在 **Broker Workbench** 里看摘要、缺什么、下一步做什么，**你来确认**。  
> WeCom 只是入口；**Case Workspace** 才是产品。」

---

### 7.2 Story A 旁白 — VIP Premium Review

> 「假设一个 **VIP Uber Black 客户**发微信：『保险又涨了，有没有便宜一点？』  
> 以前：这条消息埋在列表里，你要翻记录、想他是谁、缺什么材料才能比价。  
> 现在：系统建 **Premium Review Case**——你看，**VIP、High Premium、Price Sensitive、Retention Risk** 都标出来了。  
> **Summary** 告诉你他想要什么；**Missing Fields** 告诉你还要 renewal notice 还是 dec page；**Next Action** 是请你人工比价或回电。  
> **我们不会自动报价**——是把案子整理好，让你 **30 秒进入工作状态**，不是 10 分钟翻微信。」

*(切换 Workbench，指给陈总看 tags / summary / missing / next action)*

---

### 7.3 Story B 旁白 — Claim Lite

> 「第二条：客户说 **『刚撞车了，怎么办，要不要报保险？』**  
> 这种消息最急、最碎——时间、地点、照片、对方信息，分好几条发。  
> 系统开 **Claim Lite Case**，标 **Urgent、Needs Fast Response**。AI 收集到的放在 **Claim Intake Summary**；还缺的列在 **Missing Fields**。  
> 你点 **Manual Handle**——意思是 **必须你来打电话**，系统 **不会** 自动理赔，也 **不会** 告诉客户该不该报。  
> 目的是：你打给客户之前，**summary 已经准备好了**。」

*(示范 Manual Handle)*

---

### 7.4 Story C 旁白 — Add Vehicle

> 「第三条证明 **系统能完整跑通**：客户说 **『明天提新车，帮我加保险。』**  
> 先收到 **Start Card**——不点开始，不会乱建案子。客户点 **开始**，才建 **Draft Case**。  
> VIN、邮编、日期、司机，分几条发都行；**Known Facts** 会合并，**Missing Fields** 会更新。  
> 你在 Workbench **Confirm** 之后，客户收到 **Done Card**。  
> 这条 **吴小姐也能接**——你不在，她看同一个 Case 就能跟进。  
> 续保和事故是 **最赚钱、最建信任** 的场景；加车是证明 **办公室日常变更也能走同一套 Case Workspace**。」

*(走 live Confirm → 展示 Done Card)*

---

### 7.5 Closing pitch（约 30–45 秒）

> 「总结一下：  
> 第一，这不是 chatbot，是 **CKS 办公室的新工作流**。  
> 第二，**高保费 Uber Black 客户**可以被标 VIP、优先看见。  
> 第三，**涨价续保**和**事故**都能变成 Case，不是散在微信里。  
> 第四，**staff 能接手**，不用读你的个人微信。  
> 第五，**AI 备案，你拍板**——不自动报价、不自动理赔、不自动改保单。  
> 今天 demo 里，加车是完整闭环；续保和事故是 intake 优先。下一步可以把你的 **500 核心司机客户** 逐步迁到这套 Service Desk 上。」

---

## 8. Success Criteria（Demo 成功标准）

Demo 结束后，陈总 **能用自己的话** 说出以下六点（Andy 可当场轻问确认）：

| # | 陈总应能说出 | 验证方式 |
|---|-------------|----------|
| 1 | 「这不是 chatbot，是 **Case Workspace / Service Desk**。」 | 开场 + closing 复述 |
| 2 | 「**高价值司机客户**可以被优先、被标 VIP。」 | Story A tags 记忆 |
| 3 | 「**涨价续保**和**事故**可以变成 Case。」 | Story A + B |
| 4 | 「**Staff 能帮忙**，不用读我个人微信。」 | Story C + handoff narrative |
| 5 | 「**加车**能 end-to-end，我 **Confirm**。」 | Story C live |
| 6 | 「**AI 整理案子，最后我决定**。」 | Boundary language |

### 8.1 加分项（非必须）

- 陈总主动问：「我的老客户能不能批量标 VIP？」  
- 陈总对吴小姐说：「以后你可以在这个上面看。」  
- 陈总提到官网 TCP case：「这种客户就该这样管。」  

### 8.2 失败信号（需 fallback narrative）

- 陈总只说：「哦，就是个微信机器人。」→ 回到 North Star，重讲 Before/After  
- Live WeCom 超时 → 切预录屏 + Workbench mock case，**不** 现场 debug  

---

## 9. Risk and Boundary Language（Andy 必须明确说出的边界）

以下句子 **建议在 Opening 或 Closing 各说一次**，中间 story 按需重复：

| # | 必须说出的边界 | 推荐中文表述 |
|---|---------------|-------------|
| 1 | 不做自动报价 | 「我们 **还没有自动报价**；Premium Review 是把材料和信息整理好，**比价还是你来做**。」 |
| 2 | 不做自动理赔 filing | 「我们 **不会自动报保险、不会自动理赔**；事故 case 是 **intake summary + 你来 Manual Handle**。」 |
| 3 | 不做自动改保单 | 「**不会自动改保单**；Confirm 之后办公室按现有流程进 carrier。」 |
| 4 | 不替代 broker 判断 | 「**不替代你的专业判断**——该不该换公司、该不该报，都是你来定。」 |
| 5 | 产品定义 | 「这是 **AI intake and case workspace**，不是 CRM 替换，也不是 carrier 系统。」 |
| 6 | 不做法律 / 合规结论 | 「AI **不会** 做法律或合规判断。」 |
| 7 | Demo 诚实 | 「续保和事故 demo 可能是 **简化 intake**；加车是 **完整闭环**。」 |

**禁止用语清单：**

- ❌ 「AI 帮你找到最便宜保险」  
- ❌ 「系统自动处理理赔」  
- ❌ 「以后你不用再管微信了」  
- ❌ 「AI 比 broker 更懂」  

---

## 10. Implementation Implications（下一任务清单 — 仅列出，不实施）

以下为实现本 Demo Experience Plan 的 **likely next tasks**；**本文档不包含代码、部署或 UI 变更**。

| # | 任务 | 优先级 | 对应 Demo 段落 |
|---|------|--------|----------------|
| 1 | **Workbench：VIP / channel / customer badges** | P0 | §5 Header；Story A VIP |
| 2 | **Premium Review minimal case lane** | P0 | Story A；intent + case stub + Workbench summary |
| 3 | **Claim Lite minimal case lane** | P0 | Story B；`SERVICE_LANE_CLAIM_INTAKE` + summary panel |
| 4 | **Workbench case detail panel 补全** | P0 | §5 Summary / Missing / Flags / Next Action / Timeline |
| 5 | **Demo seed / reset 脚本或 fixture** | P0 | §6 可复现三条 story |
| 6 | **Add Vehicle full flow polish** | P0 | Story C live；Draft badge、WeCom tag |
| 7 | **Identity state：Known / New / Possible Match** | P1 | §5 Identity |
| 8 | **Broker Next Action 字段（extra JSON 或 UI 静态规则）** | P1 | Story A/B/C |
| 9 | **Risk / Opportunity flags UI** | P1 | Retention Risk、Price Sensitive、Urgent |
| 10 | **Manual Handle CTA（Claim 专用，无 Done Card）** | P0 | Story B |
| 11 | **Chen Kui demo script 定稿**（本文 §7 扩展版 + 双语 customer cues） | P1 | 主讲 |
| 12 | **Fallback recording plan** | P1 | Live 失败备用 |
| 13 | **WeCom-only case list filter** | P2 | Demo 整洁 |
| 14 | **Future opportunity placeholder** | P2 | Value E mention |

### 10.1 建议 sprint 顺序（3–4 天）

| 天 | 焦点 | 产出 |
|----|------|------|
| **Day 1** | Workbench badges + detail panel + seed data | 陈总能在 Workbench **看见** §5 布局（mock Premium/Claim 亦可） |
| **Day 2** | Premium Review minimal lane + Claim Lite minimal lane | Story A/B **minimal live or seed-triggered** |
| **Day 3** | Add Vehicle polish + Manual Handle + internal rehearsal | Story C **full live** 两次无失败 |
| **Day 4** | Andy script rehearsal + fallback recording + dry run with Wu | Demo-ready |

### 10.2 与现有组件映射

| 现有组件 | Demo 用途 |
|----------|-----------|
| WeCom inbox/outbox | 三 story 客户消息入口 |
| `message_processed` + `sync_cursor` | Live 可靠性；可向陈总简述「不会重复处理」 |
| Start Card + `active_case_bridge` | Story C |
| `service_records` + `record_messages` | Case + timeline |
| Broker Workbench + Confirm + Done Card | Story C + detail 布局 |
| **待建** Premium / Claim lanes | Story A / B |

---

## Acceptance Checklist（本文档验收）

| 标准 | 状态 |
|------|------|
| Demo 像 **新办公室工作流**，不是 chatbot | ✅ §1 North Star |
| 清楚解释 time saving、error reduction、staff handoff、VIP retention、future revenue | ✅ §3 Value Hierarchy |
| 三 story 顺序：Premium Review → Claim Lite → Add Vehicle | ✅ §4 |
| 定义 live vs mock/minimal | ✅ §6 |
| 含实用中文 demo script | ✅ §7 |
| 无 code、deploy、UI change、test run | ✅ 仅规划 |

---

*End of P18.5 — 陈总 Demo 体验计划*
