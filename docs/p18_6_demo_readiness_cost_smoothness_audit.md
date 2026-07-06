# P18.6 — Demo Readiness / Cost / Smoothness Audit

**Date:** 2026-07-04  
**Type:** 实施前审计 — **只做分析，不写代码**  
**Audience:** Andy（founder / demo 主讲）、工程、陈总（间接 — 通过 demo 结果）  
**Prerequisite（已完成）:**

- WeCom 技术通道 **Q0.11.1 PASS** — inbox/outbox、`message_processed`、`sync_cursor`、generic 消息不误建 Draft  
- **P18.4** CKS 商业定位与 demo 叙事重构  
- **P18.5** 陈总 Demo 体验计划（三 story 顺序、Workbench 最低布局、话术）

**Purpose:** 在进入 3–4 天 demo implementation sprint **之前**，从 **成本可控性、工作流丝滑性、商业价值展示** 三个维度做最后一轮审计，给出明确的 Go / No-Go 与 sprint 优先级。

**Related:** `docs/p18_5_chen_kui_demo_experience_plan.md` · `docs/p18_4_cks_business_positioning_and_demo_strategy.md` · `docs/p18_chen_kui_wecom_ai_case_intake_demo.md` · `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` · `docs/evidence/wecom_q0_11_1_resmoke_2026-07-04.md`

**Authority:** 本文是 sprint 前的 **readiness gate**；不 supersede B0 contract 或 ADR-001–005。工程实现以 P18.5 §10 任务清单为准，本文补充 **成本与风险 lens**。

---

## 1. 当前准备状态判断

### 1.1 是否可以开始 implementation？

**结论：✅ 建议开始 — 但有条件 Go。**

| 维度 | 判断 | 依据 |
|------|------|------|
| 技术通道 | **Ready** | Q0.11.1 PASS；WeCom → Cloud Run → Cloud SQL private IP → inbox/outbox → reply 已验证 |
| 商业叙事 | **Ready** | P18.4 / P18.5 已定 North Star、三 story、边界话术 |
| 核心闭环（Add Vehicle） | **Mostly ready** | B0 Start Card → Draft → merge → Confirm → Done Card 已有代码与测试 |
| Workbench 展示层 | **Gap** | VIP/channel badges、Premium/Claim detail panel 尚未对齐 P18.5 §5 |
| Premium / Claim lanes | **Gap** | `intent.py` 已有 `policy_review` / `claim_intake` 分类；**独立 case lane + Workbench 展示** 待建 |
| Demo 运维 | **Partial** | manual drain 流程成熟；demo seed/reset、fallback recording **待建** |

**条件 Go 含义：** 可以立刻开工，但 **Day 1 必须先让 Workbench「看得见」**，不能先堆 backend lane 而陈总看不到 screen-proof 价值。

---

### 1.2 哪些已经 Ready

| 类别 | 已就绪项 |
|------|----------|
| **WeCom 通道** | Callback、inbox queue、reply outbox、dedup、sync cursor、guide menu、Start Card、Done Card |
| **Add Vehicle 主路径** | `active_case_bridge` Draft create/merge、`identity.py` 字段提取、Broker Confirm、`broker_confirmed_at` gate |
| **Intent 分类（规则）** | `add_car` / `claim_intake` / `policy_review` / `unclear` — **无 LLM 依赖** |
| **Case 持久化** | Postgres `service_records` + `record_messages`；Cloud SQL private IP 路径 PASS |
| **Workbench 基础** | Case list/detail、Confirm、collected/still_needed（add-car）、Manual Promote 模式可参考 |
| **商业文档** | P18.4 定位、P18.5 体验计划、demo script 初稿、边界话术 |
| **可靠性证据** | Q0.11.1 — generic 不误建 Draft；历史 replay dedup；phantom outbox 已修复 |

---

### 1.3 哪些还必须补（Sprint 阻塞项）

| # | 必须补 | 对应 Story | 阻塞原因 |
|---|--------|-----------|----------|
| 1 | Workbench **VIP / channel / case type badges** | A/B/C | 陈总「一眼看懂高价值客户」依赖 screen，不能靠口述 |
| 2 | Workbench **Summary / Known / Missing / Flags / Next Action** 布局对齐 P18.5 §5 | A/B/C | 核心价值 A/B（省时间、少出错）必须 screen-proof |
| 3 | **Premium Review minimal lane** | A | 仅有 intent 不够；需 case stub + Workbench 可打开 |
| 4 | **Claim Lite minimal lane** | B | 同上；需 Manual Handle CTA |
| 5 | **Add Vehicle polish**（Draft badge、WeCom tag、碎片 merge 演示稳定） | C | 唯一 full flow；必须 twice 无失败 |
| 6 | **Demo seed / reset** | A/B/C | 每次 rehearsal 可复现；不能靠手工清 DB |
| 7 | **Fallback recording / script** | 全局 | Live 失败时不能现场 debug |

**非阻塞但强烈建议（P1）：**

- Identity state badge（Known / New / Possible Match）  
- Broker Next Action 字段（extra JSON 或 UI 规则）  
- WeCom-only case list filter  

---

### 1.4 哪些可以 Mock

| 能力 | Mock 方式 | Demo 可接受度 |
|------|-----------|--------------|
| VIP / segment tags | Demo seed 预置 `workbench_flags` 或 extra JSON | ✅ 高 — 展示 **概念与优先级** |
| Premium Review known facts | Seed 车辆/用途线索 + 规则提取涨价关键词 | ✅ 高 |
| Claim Intake 部分字段 | 规则提取时间/地点/是否受伤；照片标 `photos_pending` | ✅ 高 |
| Identity Known Customer | 测试 `external_userid` 绑定 seed case | ✅ 高 |
| AI Insights / opportunity | 静态 placeholder 或 verbal mention | ✅ 中 |
| Renewal reminder 自动化 | 不做；仅 tag 位 | ✅ |
| 真实 carrier 比价 | 不做；next action = 「人工比价」 | ✅ 必须 mock |
| OCR / 图片解析 | 存证 + 「稍后补文字」；不解析 | ✅ |

**Mock 原则：** Mock **数据与标签**，不 mock **工作流形态** — 陈总必须看到「消息进 → Case 出 → Workbench 整理 → broker 动作」的真实路径。

---

### 1.5 哪些不能碰（Sprint 禁区）

| 禁区 | 原因 |
|------|------|
| **自动报价 / rating engine** | ADR-003；承诺过度；demo 边界 |
| **自动理赔 filing / FNOL** | 法律与信任风险；Story B 只做 intake |
| **自动改保单 / carrier API** | 产品 invariant；Confirm 后仍由 broker 操作 |
| **LLM intent 分类替换规则** | Demo 可靠性；WeCom path 已明确 rules-first |
| **每条消息全历史 LLM 总结** | 成本与延迟；见 §3 |
| **大规模 OCR / 文档解析** | 成本不可控；非 demo 价值核心 |
| **CRM / household 模型** | 范围膨胀 |
| **Multi-topic 并行 flow** | Constitution Rule 8；claim 在 add-car 中仅 flag |
| **Scheduler / cron / Pub/Sub** | Q0 决策 — manual drain only |
| **重构 B0 / Q0 核心 dedup 逻辑** | 已 PASS；回归风险高 |
| **Timeline UI 大建** | ADR-002；demo 用 latest message 即可 |
| **Home / WC / Health / Life intake** | 分散 CKS 叙事焦点 |

---

## 2. Demo 核心价值

### 2.1 这不是什么

| 错误 framing | 为什么不行 |
|--------------|------------|
| Chatbot demo | 陈总已有吴小姐；「能回消息」不是差异化 |
| WeCom 对接秀 | 通道是前提，不是产品 |
| 加车机器人 demo | 低估 CKS 真实业务（renewal / claim 才是高价值战场） |

### 2.2 这是什么

> **AI Insurance Service Desk / AI Case Workspace demo**  
> WeCom = customer channel；Case Workspace = product；AI = prepares the case；Broker = confirms。

### 2.3 Demo 必须展示的五大价值（按 P18.5 权重）

#### A. Save broker time（节省 broker 时间）— 最高优先级

| 旧模式 | 新模式 | Demo 必须 screen-proof |
|--------|--------|------------------------|
| 翻微信 thread 10+ 分钟才进入工作状态 | Workbench 30 秒内看到 Summary + Known + Missing + Next Action | ✅ Summary 区块置顶；不必逐条读 bubble |

**Andy 锚点：** 「以前 10 分钟搞懂客户在说什么；现在打开案子 30 秒。」

#### B. Reduce missing information and errors（减少缺失信息与错误）

| 旧模式 | 新模式 | Demo 必须 screen-proof |
|--------|--------|------------------------|
| 碎片消息漏看；VIN 冲突无人标记 | **Missing Fields** 显式列表；**Conflict / risk flags** | ✅ 三 story 至少各展示一次 missing 或 flag |

#### C. Enable staff handoff（支持 staff 交接）

| 旧模式 | 新模式 | Demo 必须 screen-proof |
|--------|--------|------------------------|
| 上下文在陈总手机与脑中 | 同一 Case 在 Workbench 全貌可见 | ✅ 口述吴小姐视角 + detail 无需 oral transfer |

#### D. Prioritize VIP / High Premium customers（VIP 优先可见）

| 旧模式 | 新模式 | Demo 必须 screen-proof |
|--------|--------|------------------------|
| $15k 年保费客户与普通询价 FIFO 排队 | **VIP · High Premium · Uber Black · Retention Risk** 标签 | ✅ Story A 核心展示 |

#### E. Preserve broker control with Confirm gate（broker 控制 + Confirm 门）

| 旧模式 | 新模式 | Demo 必须 screen-proof |
|--------|--------|------------------------|
| （无系统化 gate） | Add Vehicle → **Confirm** → Done Card；Claim → **Manual Handle** | ✅ 陈总或 Andy **亲手点一次** Confirm / Manual Handle |

### 2.4 价值展示 vs 技术展示

```
Demo 权重分配（implementation 决策用）

Save time + Reduce errors     ████████████████████  Workbench layout P0
Staff handoff                 ████████████████      narrative + 同一 detail 视图
VIP prioritization            ████████████████████  Story A badges P0
Broker Confirm gate           ████████████████████  Story C live P0
Future revenue opportunity    ████                  verbal / placeholder only
```

**关键原则：** Sprint 任何任务若不能帮助陈总 **在屏幕上** 感受到 A/B/D/E 之一，应降级或砍掉。

---

## 3. 成本模型分析

### 3.1 成本来源概览（宏观）

| 成本项 | Demo 阶段角色 | 典型计费模式 | Demo 阶段量级（估算） |
|--------|--------------|--------------|----------------------|
| **Cloud Run** | `fiqa-api` 单服务；callback + manual drain | 请求数 + CPU/memory 时长 + 最小实例（若有） | **低** — demo/rehearsal 日消息量 <100；无持续高 QPS |
| **Cloud SQL** | `caseiq-pilot-pg`，`db-f1-micro` zonal | 实例小时 + 存储 ~10GB | **低且固定** — 约 **$7–15/月** 量级（非 HA） |
| **Cloud NAT** | WeCom 静态出口 `8.235.43.132` | NAT gateway 小时 + 出站流量 | **中低固定** — NAT 本身有 baseline；demo 流量极小 |
| **Cloud NAT 静态 IP** | WeCom 白名单 | IP 保留费 | **低固定** |
| **VPC Direct Egress** | `all-traffic` 保 WeCom NAT | 出站流量 | Demo 可忽略 |
| **LLM token** | WeCom slice **当前无 LLM**；Unified Intake triage 可选 LLM | 按 token | **可控** — 见 §3.2 |
| **Image / document parsing** | Demo 不做 OCR | Vision / doc API | **≈ $0** — 不启用 |
| **Storage / logging** | GCS（若有附件）、Cloud Logging | 存储 + 日志 ingest | **低** — demo 数据量小 |
| **WeCom message volume** | 企业微信 API | 通常无 per-message 云费用；运维人力为主 | **低** — 三 story rehearsal 各 5–15 条消息 |

**Demo 阶段总云成本判断：✅ 可控** — 固定成本（SQL + NAT + IP）为主；变动成本（Run + LLM）在 demo 流量下可忽略，**前提是遵守 §3.3 设计原则**。

---

### 3.2 LLM 成本 — 当前架构与 Demo 策略

#### 当前事实

| 路径 | 是否调用 LLM | 说明 |
|------|-------------|------|
| WeCom `intent.py` | **否** | 明确注释：rule-based, no LLM |
| WeCom field extractors (`identity.py`) | **否** | Regex / 规则 |
| WeCom customer reply (`reply.py`) | **否** | 模板 + Start/Done Card |
| Unified Intake `triage.py` | **可选** | `OPENAI_API_KEY` 存在时 `_llm_triage`；否则 rule-based fallback |
| Policy Review doc upload | **是（若启用）** | PDF/图片 extraction — **demo 不走此路径** |
| RAG / mortgage / lab routers | 存在但 **PRODUCT_ONLY 隐藏** | Demo 不应触发 |

#### Demo 阶段 LLM 估算（若误用）

| 场景 | 单次 token 粗估 | 50 条消息/天 rehearsal | 风险 |
|------|----------------|----------------------|------|
| 每条消息 full-history summarize | 2k–8k input + 256–512 output | **$0.5–5/天**（gpt-4o-mini） | 🔴 高 — 禁止 |
| 仅 case 创建时 summarize 一次 | ~500–1500 tokens | **<$0.1/天** | 🟢 可接受 |
| 纯规则 + 模板 | 0 | **$0** | 🟢 **推荐** |

**结论：** Demo sprint **默认零 LLM** 即可达成 P18.5 目标；若后续加 case summary，必须 **按 case 增量、按 lane  gated**。

---

### 3.3 成本可控设计原则（Sprint 必须遵守）

| # | 原则 | 实现含义 |
|---|------|----------|
| 1 | **普通消息尽量轻量规则 / 小模型** | WeCom path 保持 `intent.py` + `identity.py` 规则；generic → guide menu only |
| 2 | **只有进入 case 或需要摘要时才调用 LLM** | Premium/Claim case 创建后的 summary 可 **规则模板 + 关键词**；LLM 为 P2 optional |
| 3 | **图片先保存，必要时再解析** | 图片 → evidence / `photos_pending` flag；**不** 调 vision API |
| 4 | **不要每条消息都重新总结全历史** | Workbench summary 来自 `collected_fields` merge + 固定模板；非 rolling LLM |
| 5 | **Workbench 摘要按 case 状态增量更新** | 新 fact 合并 → 更新 known/missing；summary 句子可规则拼接 |
| 6 | **Claim / Premium / Add Vehicle 分 lane 控制 token** | 各 lane 独立 field set 与 reply 模板；避免通用 mega-prompt |
| 7 | **Demo 不做真实 OCR 大规模解析** | Policy Review upload flow 不进入 WeCom demo |
| 8 | **Manual drain，无 background worker 常驻** | 避免 idle Cloud Run 实例 + 定时 drain 的固定 burn |
| 9 | **Demo seed 控制 case 数量** | Reset 脚本 truncate 测试 queue 表；不累积无限 history |

---

### 3.4 哪些地方未来可能变贵

| 场景 | 变贵机制 | 缓解 |
|------|----------|------|
| 500 VIP 客户全量上线 | 消息量 × LLM summarize | 规则 first；LLM 仅 broker-open case |
| 每条消息 LLM triage | Token 线性增长 | 保持 rule gate；LLM 仅 `unclear` 且已进入 case |
| 图片 OCR 全开启 | Vision API × 照片数 | 按需 parse；broker 触发 |
| Cloud Run min instances > 0 | 固定小时费 | Demo 可接受 cold start；pilot 再评估 |
| Cloud SQL 升 tier / HA | 实例费翻倍+ | 有 revenue 后再升 |
| 全历史 embedding / RAG | Qdrant + embed API | Intake core 不依赖 vectors（CURRENT_PRODUCT_SHAPE） |
| sync_msg 大量 replay 未 dedup | CPU + DB write 放大 | Q0.10 已解决 — **不可回归** |

---

### 3.5 Demo 阶段成本结论

| 问题 | 答案 |
|------|------|
| Demo 阶段成本是否可控？ | **✅ 是** — 固定 infra ~$20–40/月 量级 + 近零变动 LLM |
| 最大成本风险是什么？ | **工程范围 creep**（OCR、LLM everywhere、新 infra）而非 demo 流量本身 |
| Sprint 成本相关 Do / Don't | **Do:** rules-first, seed/reset, manual drain · **Don't:** LLM summarize per message, OCR, min instances for demo |

---

## 4. 新工作流丝滑性审计

### 4.1 客户侧（WeCom 微信）

| 检查项 | 当前状态 | Sprint 目标 | 风险 |
|--------|----------|-------------|------|
| **能否自然微信聊天** | ✅ 文本消息 + Start Card / guide menu | 保持；不强迫表单 | 低 |
| **是否只问下一个最重要问题** | ⚠ Add-car 有 still_needed 逻辑；Premium/Claim 待建 | Claim/Premium lane 需 **单问题引导** 或 guided menu | 中 — 若无引导，客户侧体验像沉默 |
| **是否避免重复问** | ✅ merge 已有字段进 `collected_fields` | Premium/Claim 复用同一 merge 模式 | 低（Add Vehicle）；中（新 lane） |
| **能否处理客户补充信息** | ✅ 多轮 merge 已测 | 三 story rehearsal 验证 | 低 |
| **能否处理客户改口** | ⚠ 新值覆盖旧值；冲突 flag 未全面 | Demo 至少展示 **dual VIN hint** 或 verbal | 中 |
| **能否处理客户打错** | ⚠ 同改口；无 explicit 「您是指…？」 | Sprint 可 **规则纠正**（17 vs 1 位 VIN）；非必须 LLM | 低–中 |
| **能否处理中途离开后回来** | ✅ `external_userid` 绑定 open Draft | 同一客户 reopen case；seed 演示 | 低 |
| **是否明确 broker 会审核** | ✅ Start Card / Done Card 文案含 broker 语义 | Premium/Claim ack 需含 **「办公室会联系您」** | 中 — Claim 禁 auto 法律建议 |

**客户侧丝滑性总评：** Add Vehicle **较丝滑**；Premium/Claim **依赖 sprint 新建 lane 的 reply 模板质量**。建议每条 lane 最多 **1 条引导问 + 1 条 ack**，其余靠自然聊天 merge。

**客户侧 Demo 最低 bar：**

```
消息进 → 有回应（guide / Start / 单问 / ack）
       → 不沉默 >30s（manual drain 需在 demo 前 pre-drain 或 Andy 边讲边 drain）
       → 不重复已收集字段
       → 不说「系统自动理赔/报价」
```

---

### 4.2 Broker 侧（Broker Workbench）

| 检查项 | 当前状态 | Sprint 目标 | 风险 |
|--------|----------|-------------|------|
| **Workbench 是否一眼看懂** | ⚠ 有 add-car detail；信息密度高 | P18.5 §5 布局：**Summary 置顶** | 中 — UI clutter |
| **是否显示身份 / VIP / channel** | ❌ 未 wired | P0 badges | 高 — Story A 核心 |
| **是否显示 case type / status** | ⚠ 有 service_lane / status；humanize 存在 | Premium Review / Claim Lite / Add Vehicle 明确 label | 中 |
| **是否显示 known facts** | ✅ add-car `collected_fields` | Premium/Claim field set | 低–中 |
| **是否显示 missing fields** | ✅ `still_needed_fields` | 三 lane 各自 missing 集 | 低–中 |
| **是否显示 risk / opportunity flags** | ⚠ 部分 via triage flags | Retention Risk、Urgent、Price Sensitive | 中 |
| **是否显示 next action** | ⚠ `buildOfficeNextAction` 存在 | Broker Next Action 对齐 story | 中 |
| **是否有 Confirm / Manual Handle** | ✅ Confirm（add-car）；Manual Promote 可参考 | Claim → **Manual Handle** 专用 CTA | 中 |
| **是否能让 staff 接手** | ⚠ 数据在 DB；UI 未强调 handoff | 同一 detail 无需 oral context | 低（数据层 ready） |

**Broker 侧丝滑性总评：** **数据层 mostly ready，展示层是 sprint 主战场。** 若 Day 1 未达成 §5 布局，Demo 会退化为「看聊天记录的 fancy UI」—— **商业价值 FAIL**。

**Broker 30 秒测试（rehearsal 必做）：**

> 给 Andy 一个从未见过的 case id → 30 秒内说出：这是谁、什么类型、急不急、缺什么、下一步做什么。

---

### 4.3 端到端丝滑性 — 三 story 联调风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| Manual drain 延迟 | 客户发消息后 Workbench 不更新 | Demo script 标注 drain 时机；pre-drain empty queue |
| 三 story 同一测试客户 | Case 冲突 / Rule 8 | **三个 external_userid 或 sequential reset** |
| Workbench 刷新 | Andy 切屏时 case 未出现 | List auto-refresh 或 manual Reload 一次 |
| Premium 误分类为 add_car | 错误 Start Card | 强化 `policy_review` markers（涨价、便宜、续保） |
| Claim 误分类为 unclear | 只有 guide menu | Claim markers 已较全；rehearsal 验证中文「刚撞了」 |

---

## 5. 关键异常场景

Demo 至少要能 **解释、展示或 verbal fallback** 以下场景：

| # | 场景 | 期望行为 | 当前能力 | Sprint 动作 |
|---|------|----------|----------|-------------|
| 1 | **客户说不清楚** | Guide menu 或单问澄清；**不**建 Draft | ✅ unclear → guide menu | Rehearsal 验证 |
| 2 | **客户发错信息** | Merge 进 case；broker 在 Workbench 看见 | ✅ merge | 可选 conflict flag |
| 3 | **客户改日期 / 改 VIN** | 新值覆盖；旧值可留 timeline | ⚠ 覆盖无 history diff | Verbal：「timeline 有完整记录」 |
| 4 | **客户同时提到 claim 和 renewal** | **Rule 8：** 一 flow 一次；第二个 topic flag 或 guide 选 lane | ⚠ add-car 内 claim → flag only | Premium open 时 claim → **新 case 或 verbal** 说明 v2 |
| 5 | **客户发图片但暂不解析** | 存 evidence；Missing = photos；**不** OCR | ✅ B0 scope：log only | Workbench 显示 `photos_pending` |
| 6 | **停保 / coverage suspended 后又要开车** | 识别 urgency；**不** auto 法律结论；Manual Handle | ⚠ triage 有 payment_lapse 模板；WeCom lane 未专建 | Story B 可 verbal + urgent flag；或 seed |
| 7 | **历史消息 replay 不重复处理** | dedup + watermark | ✅ Q0.10/Q0.11.1 PASS | **不可回归** |
| 8 | **Generic hello 不误建 Draft** | guide menu only | ✅ Q0.11.1 PASS | Opening demo 可展示 |

### 5.1 异常场景 Demo 策略

| 策略 | 说明 |
|------|------|
| **Live 展示（优先）** | #7 generic hello、#1 unclear、#5 图片存证 |
| **Script 口述 + Workbench 静态** | #3 改 VIN、#6 停保 |
| **Explicitly defer to v2** | #4 双 topic 并行 — Andy 说「同一时刻只办一件事，另一个先 flag」 |

---

## 6. 三条 Demo Story 的 Readiness

### Story A: VIP Premium Review

| 维度 | 评估 |
|------|------|
| **需要展示什么** | VIP/Uber Black/High Premium tags；Premium Review case type；Summary（涨价、比价意向）；Missing（dec page、renewal notice）；Flags（Price Sensitive、Retention Risk）；Next Action（人工比价/回电） |
| **哪些可以 minimal/mock** | Known facts 可 seed；无真实 dec page 解析；无 carrier quote；ack 模板回复即可 |
| **是否需要真实报价** | **❌ 不需要** |
| **必须有的 Workbench 信息** | Header: VIP + WeCom + Premium Review · Intelligence: Summary + Known + Missing + Flags + Next Action |
| **Backend readiness** | `intent.py` 有 `policy_review`；triage 有 premium_review 模板；**WeCom case lane 未建** |
| **Readiness 评分** | **🟡 40%** — intent ready，case + UI 待 sprint |

**Minimal 实现路径：** 高置信 `policy_review` intent → 创建 `service_lane=premium_review` stub → 规则 summary + seed VIP flags → Workbench 展示。**无需 Start Card gate**（与 P18.5 一致）。

---

### Story B: Claim Lite

| 维度 | 评估 |
|------|------|
| **需要展示什么** | Claim Lite case；Urgent / Needs Fast Response tags；Claim Intake Summary；Missing（photos、other party）；**Manual Handle** CTA |
| **哪些可以 minimal/mock** | 字段规则提取；照片「稍后发」；无 FNOL；无 adjuster |
| **是否自动理赔** | **❌ 不需要 / 禁止** |
| **必须有的 urgency/missing info** | Urgent flag visible；missing: 时间/地点/对方/照片 至少列 2–3 项 |
| **Backend readiness** | `intent.py` claim markers 较全；**claim case lane + merge 未建** |
| **Readiness 评分** | **🟡 35%** — 分类 ready，lane + UI 待 sprint |

**Minimal 实现路径：** Claim 高置信 → claim stub case（或 Claim Start Card 简化版）→ 多轮 merge accident fields → Manual Handle status。**禁止** Done Card 自动化。

---

### Story C: Add Vehicle

| 维度 | 评估 |
|------|------|
| **需要展示什么** | Start Card → Draft → 碎片 VIN/ZIP/date/driver → Known/Missing 动态更新 → Broker Confirm → Done Card |
| **哪些必须 live/full** | **全流程必须 live** — 这是「系统成熟度」唯一 proof |
| **当前已有组件能否支持** | **✅ 大部分** — B0 contract steps 1–11；tests 存在 |
| **还缺什么 polish** | Draft list badge；WeCom channel tag；rehearsal 稳定性；demo reset；phone-required-before-confirm guard |
| **Readiness 评分** | **🟢 75–80%** — sprint 以 polish + rehearsal 为主 |

**Story C 是 sprint 的「可靠性锚点」** — 若 C 失败，整个 demo 可信度崩塌；A/B 可 mock，C 不可。

---

### 三 Story Readiness 总览

```
Story A Premium Review   🟡 40%   mock/minimal OK — UI + stub lane 是瓶颈
Story B Claim Lite       🟡 35%   mock/minimal OK — Manual Handle UI 是瓶颈
Story C Add Vehicle      🟢 80%   must live full — polish only
WeCom 通道               🟢 95%   Q0.11.1 PASS
Workbench 展示           🟡 50%   badges + layout 是瓶颈
Demo 运维                🔴 30%   seed/reset/fallback 待建
```

---

## 7. Must-have vs Nice-to-have

### 7.1 Must Have（3–4 天 sprint — 完不成则 No-Go demo）

| # | 项 | Story | 验收 |
|---|-----|-------|------|
| 1 | WeCom entry live | 全局 | 消息进 → drain → reply |
| 2 | Workbench case list + detail | 全局 | 三 case 可打开 |
| 3 | VIP / channel / case type badges | A/C | Story A 必见 VIP |
| 4 | Premium Review minimal case | A | Workbench 完整 intelligence 区 |
| 5 | Claim Lite minimal case | B | Urgent + Manual Handle |
| 6 | Add Vehicle full flow | C | Start → Confirm → Done Card ×2 无失败 |
| 7 | Confirm gate | C | Andy/陈总亲手 Confirm |
| 8 | Demo seed / reset | 全局 | <10 min 恢复到 demo 初始状态 |
| 9 | Fallback recording / script | 全局 | Live 失败 60 秒内切录屏 |

---

### 7.2 Nice-to-have（明确不阻塞 demo）

| 项 | 原因 defer |
|----|------------|
| Image parsing / OCR | 成本 + 范围；photos_pending 足够 |
| Real customer matching | Seed Known 即可 |
| Advanced AI insights | 静态 placeholder |
| Renewal reminder automation | Value E — verbal only |
| Coverage gap scoring | 未来 opportunity |
| Carrier integration | ADR-003 |
| Identity Possible Match UI | P1；Known/New 二态可先 |
| WeCom-only list filter | P2 |
| Conversation full thread panel | latest 1–3 条足够 |
| LLM case summary | 规则 summary 足够 demo |

---

### 7.3 建议 3–4 天优先级（与 P18.5 §10.1 对齐）

| 天 | 焦点 | Must-have 覆盖 |
|----|------|----------------|
| **Day 1** | Workbench badges + detail panel（§5 布局）+ seed data | #2 #3 #8（seed 初版） |
| **Day 2** | Premium Review lane + Claim Lite lane（minimal backend + UI） | #4 #5 |
| **Day 3** | Add Vehicle polish + Manual Handle + internal rehearsal ×2 | #6 #7 |
| **Day 4** | Andy script rehearsal + fallback recording + dry run | #9 + 全流程 |

**Day 1 结束时验收：** 用 **mock/seed** _cases，陈总布局（§5 ASCII）在 Workbench **可见** — 即使 backend lane 未 live。

---

## 8. Demo 成功标准

Demo 结束后，陈总 **能用自己的话** 说出以下六点（P18.5 §8 扩展）：

| # | 陈总应能说 | 对应价值 | 验证 |
|---|-----------|----------|------|
| 1 | 「这不是普通 chatbot，是 **Case Workspace / Service Desk**。」 | 产品定义 | Opening + Closing |
| 2 | 「**高价值客户**可以优先、标 VIP。」 | D — VIP | Story A tags |
| 3 | 「**涨价 / 理赔 / 加车**都能变成 case。」 | 商业覆盖 | Story A+B+C |
| 4 | 「**Staff 能接手**，不用读我个人微信。」 | C — handoff | Story C narrative |
| 5 | 「**AI 整理案子，最后我 Confirm**。」 | E — broker control | Story C Confirm |
| 6 | 「这个系统能 **减少漏事、错误和客户流失**。」 | A + B | Missing fields + VIP |

### 8.1 加分项

- 陈总问：「老客户能不能批量标 VIP？」  
- 陈总对吴小姐说：「以后你可以在这个上面看。」  
- 陈总联想到官网 TCP $15,500 case  

### 8.2 失败信号（需 immediate fallback）

| 信号 | 响应 |
|------|------|
| 「哦，就是个微信机器人。」 | 停 demo，重讲 Before/After + Workbench |
| Live WeCom 超时 / 双回复 | 切 fallback recording；**不** 现场 debug |
| Workbench 空白 / 无 VIP | 切 seed mock case；口述布局 |
| 陈总追问自动报价 | 边界话术 §9 P18.5 |

---

## 9. Go / No-Go 判断

### 9.1 是否建议开始 implementation sprint？

## ✅ **GO — 建议立即开始 3–4 天 sprint**

| 条件 | 状态 |
|------|------|
| 技术通道可靠 | ✅ Q0.11.1 PASS |
| 商业叙事清晰 | ✅ P18.4 + P18.5 |
| 核心闭环可演示 | ✅ Add Vehicle ~80% |
| 成本可控 | ✅ §3 — rules-first, 无 OCR |
| 范围可收敛 | ✅ Must-have 清单明确 |
| 主要风险可缓解 | ✅ fallback recording + seed/reset |

**No-Go 触发条件（若出现则 pause sprint）：**

- Q0 dedup / phantom outbox **回归**  
- Cloud SQL private IP path **不可用**  
- 陈总 meeting **<48h** 且 Day 1 Workbench 布局未可见 — 改 mock-only dry run  

---

### 9.2 前两天先做什么

| 优先级 | Day 1 | Day 2 |
|--------|-------|-------|
| **P0** | Workbench §5 布局 + VIP/channel/case type badges | Premium Review minimal lane end-to-end |
| **P0** | Demo seed fixtures（三 story 初始态） | Claim Lite minimal lane + Manual Handle |
| **P1** | Summary / Known / Missing / Flags / Next Action 区块 | Premium/Claim reply 模板（单问 + ack） |
| **P1** | Internal review：30 秒 broker 测试 | Cross-story reset 流程 |

**Day 1 红线：** 不开始复杂 backend refactor；**先让屏幕像 Service Desk**。

**Day 2 红线：** Premium/Claim **不要求** Start Card 完整 parity；**要求** Workbench intelligence 区完整。

---

### 9.3 最后一天验证什么

| 验证项 | 方法 | Pass 标准 |
|--------|------|-----------|
| Full live run | Andy 完整 8–12 min script | 三 story 顺序无 block |
| Story C twice | 重复 Add Vehicle | 无 manual DB fix |
| 30 秒 broker 测试 | 随机 case | Andy 答出 type/urgency/missing/next |
| Fallback path | 模拟 WeCom 失败 | 60 秒内切 recording |
| 边界话术 | Andy 自评 | 6 条边界各至少说 1 次 |
| 成本 spot check | Cloud Console + 无 LLM key 误用 | 无 unexpected API call |

---

### 9.4 什么时候必须停止加功能，转为 rehearsal

| 时间点 | 规则 |
|--------|------|
| **Sprint Day 3 结束** | **Feature freeze** — 只允许 bugfix + copy polish |
| **Demo 前 24h** | **Rehearsal only** — 不加新 lane、不改 intent 规则 |
| **Demo 前 2h** | **Ops only** — seed reset、empty drain、queue 检查 |
| **Demo 现场** | **零 deploy** — 任何 live 问题 → fallback recording |

**停止加功能的信号：**

- Must-have 9 项中 **≥7 项 PASS**  
- Story C **连续 2 次** full live PASS  
- Andy 能在 **无笔记** 情况下讲完 8 min script  

---

### 9.5 最终结论摘要

| 问题 | 答案 |
|------|------|
| 成本可控吗？ | **✅ 是** — infra 固定低位；遵守 rules-first、无 OCR、无 per-message LLM |
| 工作流丝滑吗？ | **⚠ 部分** — Add Vehicle 较 ready；Premium/Claim 依赖 sprint UI+lane；**Workbench 是瓶颈** |
| Demo 能展示商业价值吗？ | **✅ 能** — 若按 P18.5 价值层级实现 §5 布局 + 三 story；否则退化为 chatbot |
| 建议行动 | **GO** — Day 1 Workbench first；Day 2 lanes；Day 3–4 polish + rehearsal |
| 最大风险 | Live 失败无 fallback；Workbench 信息不足；范围 creep（OCR/LLM/carrier） |
| 最大缓解 | Seed/reset + fallback recording + rules-first + Story C live anchor |

---

## Acceptance Checklist（本文档验收）

| 标准 | 状态 |
|------|------|
| 回答可否开始 implementation | ✅ §1 + §9 |
| 明确 Demo 核心价值（非 chatbot） | ✅ §2 |
| 宏观成本模型 + 可控策略 | ✅ §3 |
| 客户侧 + broker 侧丝滑性审计 | ✅ §4 |
| 关键异常场景 | ✅ §5 |
| 三 story readiness 评估 | ✅ §6 |
| Must-have vs nice-to-have | ✅ §7 |
| Demo 成功标准 | ✅ §8 |
| Go / No-Go + sprint 节奏 | ✅ §9 |
| 无 code、deploy、test run、UI change | ✅ 仅分析 |

---

*End of P18.6 — Demo Readiness / Cost / Smoothness Audit*
