# P18.9 — Conservative AI Red Team / Risk Challenger Review

**Date:** 2026-07-04  
**Type:** 风险挑战与规避方案 — **只做 Red Team 审计，不写代码**  
**Audience:** Andy（founder）、陈总（间接 — 通过 demo 边界与产品安全）、工程、产品  
**Prerequisite（已完成）:**

- **Q0.11.1** WeCom text/click 通道稳定  
- **P18.4** CKS 商业定位  
- **P18.5** Demo Experience Plan  
- **P18.6** Demo Readiness / Cost / Smoothness Audit  
- **P18.7** End-to-End Business Flow Simulation  
- **P18.8** Implementation Asset Inventory + Risk Review  

**Purpose:** 在 implementation sprint **之前**，以 Challenger / Red Team / Risk Auditor 身份，专门挑战当前设计，找出可能导致 demo 失败、产品失败、E&O 纠纷、云事故、成本失控的重大风险，并给出**最简单、最保守、最直接**的规避方案。

**Authority:** 本文是 **Conservative AI 安全门**；不 supersede B0 Contract、ADR-001–005 或 Constitution Rule 8，但**更严厉**地解释为何必须遵守。工程 sprint 以本文 + P18.7 + P18.8 三份文档为 gate。

**Disclaimer:** 本文不构成法律、保险、合规或 E&O 建议；仅作为产品与工程风险清单。

**本文不做：** 写代码 · 部署 · 跑测试 · 改 UI · 改 schema · 调用外部 API

---

## 1. Executive Summary

### 1.1 整体判断

| 维度 | 判断 |
|------|------|
| **当前设计最大价值** | WeCom 只是 **channel**；**Case Workspace** 把碎片微信整理成 broker 30 秒可决策的结构化视图（Summary / Known / Missing / Flags / Next Action），且 **Broker Confirm** 门控后才算 Active Case — 这是 CKS 高保费 VIP 客户场景下真正的差异化，不是 chatbot。 |
| **最大风险** | **AI 或 demo 叙事越界** — 客户或陈总误以为系统会「自动报价 / 自动理赔 / 自动恢复 coverage / 已经加好了」；其次是 **Raw Event 丢失或 Case View 静默覆盖** 导致纠纷时无 timeline；第三是 **Q0.11.1 通道回归** 或 **Cloud 网络/queue 配置失误** 导致 live demo 崩盘。 |
| **最可能导致 demo 或产品失败的风险** | ① Workbench 无 screen-proof，陈总只看到微信 bubble；② Premium/Claim live 时 Workbench 空白；③ Coverage/Claim 场景 AI 说了不该说的话；④ live 发图片无反应且未提前声明；⑤ 混合业务并行深处理导致 case 混乱；⑥ demo 现场 debug WeCom / deploy。 |
| **必须在 implementation sprint 前用规则消除的风险** | Generic → 误建 Draft；AI 承诺报价/理赔/coverage；Conflict 静默覆盖；Multi-flow 并行；Confirm 前 Active Case；WeCom path 启用 LLM/OCR；改 Q0 dedup/B0 gate；schema migration；demo 依赖 live 图片。 |
| **是否建议继续开发** | **✅ 有条件 GO** — 仅当 sprint 严格限定为 **Workbench screen-proof + seed + 三条 minimal lane + Story C live**，且 **零 LLM / 零 WeCom OCR / 零 schema migration / 零 carrier API**。任何 scope 膨胀 → **No-Go**。 |
| **继续开发前必须锁定的 Conservative AI 规则** | 见 §2 全文 + §15 十条铁律；最小集合：**Raw Event 不丢 · Case View 可改但留痕 · Conflict 必 flag · One Business Flow · High-risk Manual Handle · AI never final action · Broker Confirm before Done**。 |

### 1.2 我们首先要做到的是什么

**不是**做到 AI 自动办完所有事。

**是**做到：

```
客户信息不丢  →  Raw Event Log 完整；每条文字/点击/图片占位可追溯
case 不乱     →  One Business Flow；Start Card gate；Draft ≠ Active
风险不漏      →  Coverage / Injury / Claim / Conflict flags 进 Workbench
broker 最后确认 →  Confirm / Manual Handle 门控；Done Card 仅 broker 动作后
```

若 demo 只能证明这四件事，比证明「AI 很聪明」更有商业价值、更低 E&O 风险。

---

## 2. Conservative AI 总原则

系统最保守规则定义如下。任何 implementation 决策与此冲突时，**以本节为准**。

### A. Raw Event 永久优先

客户发来的每条 **文字、图片、点击事件**（以后 **语音**），都应作为 **Raw Event** 记录。

- Raw event **不应**被 AI summary 覆盖或删除。  
- Summary / Known Facts 是**解释层**，不是原始证据。  
- 纠纷、投诉、监管问询时，**Raw Event Log** 是第一证据源。

**当前缺口（Red Team）：** WeCom path 对 text 有 `record_messages` / `evidence_events` 轻量写入；**图片/语音为零实现** — 存在「客户发了图，系统里什么都没有」的 demo 与合规双重风险。

### B. Case View 是可变解释层

AI 提取的 VIN、车辆、日期、保费、事故地点等，是 **当前理解（Case Current View）**，不是最终事实。

- 可以更新 operational field（如 premium 从 12000 → 15500）。  
- **必须**保留历史来源：哪条 Raw Event、哪次 OCR、哪次 broker 确认。  
- Workbench 显示的是 **「系统当前认为」**，不是 **「保单事实」**。

### C. Conflict 不隐藏

客户改口、信息矛盾、OCR 不确定 — **都不能静默覆盖**。

- 必须产生 **Conflict Flag** 或 **needs broker confirmation**。  
- Broker 未确认前，conflict field 不得进入「已确认 facts」区。  
- 客户侧可 ack「已更新为 X」，但 Workbench 必须同时显示 **was Y**。

### D. One Business Flow at a Time

同一时间只处理 **一个 active business flow**。

- 其他话题：**记录 + flag**，不并行深处理。  
- Add Vehicle 进行中提到 claim → `claim_mentioned_at`，**不**建 Claim Case。  
- Premium 进行中提到加车 → flag only，**不**发 Start Card 打断当前 flow。

### E. High-risk always Manual Handle

以下场景 **必须 broker review**，AI 只做 intake / flag / 安全 ack：

| 类别 | 示例 |
|------|------|
| 理赔 | 报不报、私了、对方跑了、会不会涨价 |
| 受伤 | 脖子疼、送医、任何人身伤害 |
| 停保 / coverage | 停保、能不能开、先开一天、还 rental |
| coverage active/inactive | 任何「有没有保」「生没生效」 |
| 报价 / 换公司 | 便宜多少、保证降、直接换 carrier |
| 保单变更 | 加车 bind、删车、改 driver、恢复 coverage |
| 法律 / 责任 | 谁的责任、要不要报警 |

### F. AI never claims final action

AI **不说**（含变体、暗示）：

| 禁止表述 | 原因 |
|----------|------|
| 已经帮你加好了 | 保单未改；E&O |
| 保险已经生效 / 可以开车了 | coverage 状态仅 broker/carrier 可确认 |
| 一定更便宜 / 能省 $X | 未 rating；虚假承诺 |
| 应该报 / 不应该报保险 | 法律与策略敏感 |
| 这个责任是谁的 | 非 broker 法律判断 |
| 停保应该没关系 | C6 场景最高风险之一 |
| 系统已自动处理完毕 | 违背 Broker Confirm 叙事 |

**安全替代：** 「已记录 · 陈总会人工看 · 请等办公室确认 · 线上不能自动办」

---

## 3. 数据模型风险：Raw Event vs Case View

### 3.1 挑战场景

客户可能连续发：

```
T0   三段文字（碎片 VIN、ZIP、日期）
T1   两张图片（保险卡、事故照）
T2   又三段文字（改口 premium、改 delivery date）
T3   一个点击（Start / menu）
T4   第二天补信息
T5   再次改口（BMW → Toyota；VIN A → VIN B）
```

**Red Team 问题：** 若只维护一个 `structured_payload` JSON，没有 append-only Raw Log，则 **T5 覆盖 T0** 后无法证明客户最初说了什么 — 投诉时 broker 吃亏。

### 3.2 当前 schema 是否足够？

| 层 | 现有资产 | 足够？ | 缺口 |
|----|----------|--------|------|
| **Layer 1 Raw Event Log** | `record_messages`（PG）；`extra.evidence_events[]`（JSON）；`wecom_inbox_events`（queue，非 case 级） | ⚠️ **部分** | WeCom text 轻写入；**非 text 被 sync_msg skip**；evidence_events 非严格 append-only audit |
| **Layer 2 Attachment / Media** | `extra.case_attachments`；网页 upload → 本地 filesystem | ❌ **WeCom 路径不足** | 无 media_id download；无 GCS；无 OCR_status 标准字段 |
| **Layer 3 Case Current View** | `structured_record_data.structured_payload`；`collected_fields` / `still_needed_fields` | ✅ **demo 够用** | conflict 历史 weak；无 field-level provenance |
| **Layer 4 Timeline / Audit** | `state_history`（status）；`office_actions`（**无 Python 写入**）；evidence_events | ⚠️ **弱** | 无完整「customer said X → AI extracted Y → broker confirmed Z」链；ADR-002 禁 Timeline UI 但**不等于**可不要 audit 数据 |

**结论：** Demo sprint **可以**零 migration，用 JSON 补 flags；但 Red Team 必须标记：**生产 pilot 前 Layer 1 + Layer 2 对 WeCom 多媒体是 P19 硬需求**，否则「客户信息不丢」在图片/语音场景是空话。

### 3.3 什么进哪里？（推荐分工）

| 数据类型 | 进哪里 | 不进哪里 |
|----------|--------|----------|
| 客户原话 text | `record_messages.message_text` + `evidence_events`（source=wecom, msg_id） | `structured_payload` 里不要只存 summary 丢原话 |
| 点击 Start / menu | `evidence_events`（event_type=click, click_id） | 不要只改 case_status 无 event |
| 图片/文件 | Layer 2：`case_attachments` + media metadata；**先存后 OCR** | **不要** OCR 结果覆盖 raw media 引用 |
| AI 提取字段 | `structured_payload.collected_fields` + field meta `{value, source_event_id, confidence}` | 不要无 provenance 的 flat string |
| OCR 提取 | `attachment.extracted_fields` + `human_review_required=true` | **不要**直接 merge 进 collected 无 broker gate |
| 改口 / 冲突 | `structured_payload.conflict_flags[]` + timeline entry | **不要**静默 overwrite 无 flag |
| 混合话题 | `extra.*_mentioned_at` timestamps | **不要**第二 case 自动创建（Rule 8） |
| Broker 确认 | `broker_confirmed_at` + `state_history` + office_actions（未来） | Confirm 不得触发 carrier API |

### 3.4 推荐四层模型（implementation 目标态）

#### Layer 1: Raw Event Log

每条输入保存：

```
event_id / msg_id
external_userid
channel (wecom)
msg_type: text | image | click | voice | file
raw text OR media metadata (media_id, sha, size)
timestamp
dedup key (WeCom msg_id / inbox dedup)
processing_status: received | queued | processed | skipped
linked case_id if known
extraction_status: none | pending | done | failed
```

**Demo 最小：** text + click 写入 evidence_events；图片用 seed stub `document_received`。

#### Layer 2: Attachment / Media Record

```
media_id, download_status, storage_uri, mime_type, original_filename
linked case_id
OCR_status: not_started | pending | success | failed | low_confidence
extracted_fields (if any)
human_review_required: true (default for demo)
```

**Demo 最小：** `photos_pending` in still_needed + evidence stub — **不 download**。

#### Layer 3: Case Current View

```
case_type, active_flow
known_facts (operational, may change)
missing_fields
risk_flags[], conflict_flags[]
broker_next_action
status, confidence (low/med/high per field group)
```

**Demo：** 现有 `structured_payload` + JSON flags — **足够**。

#### Layer 4: Timeline / Audit

显示链：

```
customer said X  →  raw event
AI extracted Y   →  extraction event (confidence=low)
customer corrected to Z → conflict flag
broker confirmed A → broker_confirmed_at
Done Card sent   →  outbox id
```

**Demo 最小：** latest 1–3 messages + conflict flags；**不做** full Timeline panel（ADR-002），但 JSON 里应能 reconstruct。

### 3.5 Demo 先不要做深

| 项 | Demo 策略 | Defer |
|----|-----------|-------|
| WeCom 图片 download | seed `photos_pending` | P19 |
| OCR on WeCom media | 禁止 | P19+ |
| field-level provenance UI | conflict flag 即可 | post-demo |
| `p16_timeline_events` 新表 | 禁止 migration | P19 |
| voice | 不承诺 | P20+ |
| office_actions 写入 | 可选 JSON | post-demo |

---

## 4. 多模态输入风险：文字 + 图片 + 以后语音

### 4.1 Red Team 挑战

| 问题 | 挑战结论 |
|------|----------|
| WeCom 图片未实现，是否 demo blocker？ | **不是主 demo blocker** — Story C text/click live 可成立；**但是诚实边界 blocker** — 若 script 暗示「发图即可」而 live 无反应，信任崩盘。 |
| 图片若能接收，先保存还是先 OCR？ | **必须先保存 Raw Media**；OCR 异步、可失败、可跳过。 |
| OCR 看不清楚？ | `OCR_status=failed/low_confidence` → `still_needed` 保留 → broker 人工看原图。 |
| OCR VIN 错了？ | **不得**进入 confirmed facts；Conflict Flag if 与客户文字冲突。 |
| 保险卡 OCR=VIN A，文字=VIN B？ | **Conflict Flag: dual_source_vin**；Workbench 并列显示；broker 必选。 |
| 事故照片，AI 是否描述责任？ | **绝对禁止** — 最多「收到事故相关图片，已记录，陈总会联系」；**不**描述责任、不估计损失。 |
| 语音以后怎么处理？ | **先存原音** → 异步转录 → 转录标 low confidence → broker confirm；**never** 仅转录丢原音。 |

### 4.2 最保守方案（强制）

```
1. 先保存 media（metadata + storage_uri）— demo 阶段 seed stub 可接受
2. OCR 可选、异步、可失败 — WeCom demo path 禁止启用
3. OCR 结果默认 low_confidence — 必须 Broker Confirm 才进 known_facts
4. 图片不得自动决定 case facts
5. OCR vs 客户文字冲突 → Conflict Flag
6. Demo：photos_pending / document_received 标签即可
7. WeCom image path 未打通 → 不阻塞 Story C live，但必须列为 P19 HIGH PRIORITY
```

### 4.3 Demo 话术边界

**可以说：** 「图片我们会保存进案子，办公室会看；请先补文字 VIN 方便整理。」  
**不能说：** 「已从图片读出 VIN xxx。」（除非 broker 已在 Workbench 确认 OCR — demo 不做）

---

## 5. 客户改口 / 矛盾信息风险

### 5.1 六类改口 — 系统行为定义

| # | 场景 | Current fact 更新 | Old fact 保留 | Workbench | Broker 必须确认？ | 客户侧回复 | Manual Handle |
|---|------|-------------------|---------------|-----------|-------------------|------------|-----------------|
| A | BMW → Toyota | `vehicle_make_model=Toyota`（operational） | timeline: was BMW | **Conflict Flag:** vehicle changed | 建议 confirm 后再 carrier 操作 | 「好的，已更新为 **Toyota**。」 | 若已 Confirm 过 → **是** |
| B | VIN A → VIN B | operational=VIN B | was VIN A | **Conflict Flag:** VIN updated | **是** — VIN 错 = 保单错 | 「已更新 VIN。」 | **是** |
| C | 明天生效 → 后天 | effective=后天 | was 明天 | **date changed** flag | 建议 confirm before bind | 「生效日期已改为 **后天**。」 | bind 前 **是** |
| D | 没人受伤 → 脖子疼 | injury=reported | was none | **Injury Flag** + **Conflict** | **是 — 立即 Manual Handle** | 「收到，**人伤情况很重要**，陈总会尽快联系您。」 | **必须** |
| E | premium 12000 → 15500 | operational=15500 | was 12000 | **premium updated** flag | 比价前建议看一眼 | 「已更新为 **$15,500/年**。」 | Premium lane 默认 Manual Handle |
| F | OCR VIN A，文字 VIN B | **不**自动选 | 两来源并列 | **dual_source_vin** | **是** | 「收到图片和文字，办公室会核对 VIN。」 | **是** |

### 5.2 统一规则

```
更新 operational field  →  允许（客户最新意图优先）
保留 old value          →  evidence_events / conflict_flags / timeline JSON
Workbench               →  Known Facts 显示新值 + Flags 显示 was 旧值
Broker                  →  VIN / injury / coverage / post-Confirm 改口 → 必须介入
客户侧                  →  ack 更新 + 不评论哪个对
Silent overwrite        →  禁止 — Red Team 一票否决项
```

---

## 6. One Business Flow at a Time 风险

### 6.1 混合话题挑战

| 客户说法 | Red Team 担心 | 正确行为 |
|----------|---------------|----------|
| 「保险涨了，顺便明天加车」 | 同时开 Premium + Add Vehicle | **Primary:** 先进入先说的 flow，或 **规则：Premium 优先**（高价值 retention）；加车 → `add_vehicle_mentioned_at` flag only |
| 「刚撞车了，保险也快到期」 | Claim + Premium 并行 | **Primary:** Claim（安全优先）→ Claim stub case；renewal → flag；**不**在 Claim case 里收 renewal 字段 |
| 「加车，停保那辆能不能开」 | Add Vehicle + Coverage Risk | Add Vehicle flow 继续；coverage → **Coverage Risk flag** + Manual Handle overlay（P18.7 C6） |
| 「便宜点，换公司，也要 ID card」 | Premium + 文档 + 多 intent | **Primary:** Premium Review；ID card → `document_received` / still_needed；换公司 → **不** promise |

### 6.2 选择 primary active flow 的规则（保守）

```
1. 安全优先：claim/injury/coverage 关键词 → 若需建 case，Claim 或 risk overlay 优先
2. 时间优先：同一消息多 intent → 第一句/main clause 定 primary
3. 已有 open Draft → 不切换，除非 broker 关闭或 flow 终态
4. secondary topics → timestamp flag only，不建第二 case（Rule 8）
5. broker 手动开第二 case → Workbench 允许，系统不自动
```

### 6.3 客户侧怎么说才不突兀

**模板方向：**

> 「您说的 **{secondary_topic}** 我先帮您 **记下来** 给陈总；我们 **先把 {primary_flow} 整理好**，免得信息乱掉。办完后办公室再跟您说 **{secondary_topic}**。」

**禁止：** 同时问 Claim 时间地点 + Add Vehicle VIN + Premium 金额。

### 6.4 是否新建 case？

| 情况 | 新建 case？ |
|------|-------------|
| 同一 session 第二 business flow（不同天 / 前 case 已 Manual Handle/Done） | **是** — 独立 service_record |
| 同一 active Draft 内第二 topic | **否** — flag only |
| Coverage risk overlay on Add Vehicle | **否** — risk_flags on same case |
| broker 强制拆分 | **是** — 人工操作 |

---

## 7. Coverage / 停保 / 保险断档风险

### 7.1 典型客户说法（全部高危）

- 「这辆车之前停保了」  
- 「我今天要开去修车」  
- 「我要还 rental」  
- 「保险先拿掉了还能不能开」  
- 「可以先开一天吗」  
- 「是别人撞我，应该没关系吧」

### 7.2 保守规则（不可谈判）

| 必须 | 禁止 |
|------|------|
| AI **不**判断能不能开 | 「应该可以开」「没关系」 |
| AI **不**说 coverage active | 「还有保」「已经生效」 |
| AI **不**自动恢复 coverage | 任何 bind/restore API |
| Workbench 显示 **Coverage Risk** | 静默合并进 Add Vehicle VIN 流程 |
| Broker next action: **check policy status / call customer before driving** | AI 给 driving advice |
| 客户侧：**请等 broker 确认，不要假设 coverage 已生效** | Done Card 暗示停保车可上路 |

### 7.3 系统行为（C6 复现）

```
1. 检测 coverage_suspended / 停保 / 能不能开 等关键词
2. 设 coverage_suspended_mentioned_at + risk_flags: Coverage Risk, Coverage Suspended Reminder
3. Add Vehicle（若在进行）继续 — 但 Risk 区 persistent
4. 客户 reply：停保车辆不能假设可合法上路，请等陈总确认后再动
5. Broker Confirm 加车 ≠ 恢复另一辆停保车 — Workbench 必须分开展示
6. Manual Handle 建议用于 coverage 部分
```

### 7.4 为什么商业价值极高

| 价值 | 说明 |
|------|------|
| **防投诉** | 客户以为「broker 系统说能开」结果无 coverage |
| **防纠纷** | 无保险上路事故 — 灾难性 |
| **防重大损失** | 单事故 liability 可远超 agency 年佣金 |
| **保护 broker** | E&O：错误 coverage 建议是第一类索赔 |
| **保护客户** | 华人客户常口语化问「能不能开」— 系统必须比 chatbot 更谨慎 |

**Red Team：** 若 demo 只展示 Add Vehicle 而不展示 C6 Coverage Risk，陈总会以为产品 **不懂 CKS 真实风险** — C6 与 Story A 同等重要。

---

## 8. Premium Review / 续保比价风险

### 8.1 挑战场景

- 「能不能便宜？」  
- 「现在能不能直接换公司？」  
- 「你保证帮我降多少？」  
- 「为什么涨价？」  
- 「我是不是应该降低 coverage？」

### 8.2 AI 可以 / 不可以

| AI 可以 | AI 不可以 |
|---------|-----------|
| 收集：当前 premium、renewal date、carrier、VIN、ZIP、用途、claim/ticket 历史 | 给出具体新保费 |
| 说：收到，陈总会 **人工比价** | 「能便宜 $2000」「保证降」 |
| 说：请发 renewal notice / dec page | 「建议换 XX 公司」 |
| 设 flags：Price Sensitive, Retention Risk, VIP | 「应该降低 coverage」（保险建议） |
| 解释：线上 **不能自动报价** | 解释 carrier 涨价原因（除非 broker 审过的模板） |

### 8.3 Workbench 显示

```
Missing: current premium, renewal date, carrier, vehicle/VIN, ZIP, driver, dec page, recent claim
Known:   从规则提取 + seed VIP 标签
Flags:   Retention Risk, High Premium, Uber Black
Next:    人工比价 / 回电 — 非 auto quote
CTA:     Manual Handle（Premium 无 auto Done）
```

### 8.4 何时 Manual Handle

- 客户问「保证降多少」→ 立即 flag + Manual Handle  
- 客户要「今天换公司 bind」→ Manual Handle  
- dec page 收到（含图片 stub）→ broker 人工读  

### 8.5 如何避免变成自动报价

```
rules-first intent + field extract
no rating engine（ADR-003）
no carrier API
no LLM「建议方案」
Workbench Next Action = 「broker 人工比价」— 固定文案
```

---

## 9. Claim Lite / 理赔风险

### 9.1 挑战场景

| 客户说法 | 风险级别 |
|----------|----------|
| 我要不要报保险？ | 🔴 法律 + E&O |
| 会不会涨价？ | 🔴 |
| 谁的责任？ | 🔴 |
| 我要不要报警？ | 🔴 |
| 对方跑了怎么办？ | 🟡 intake OK |
| 脖子疼但不严重 | 🔴 injury |
| 能不能私了？ | 🔴 |

### 9.2 AI 可以先问什么（安全 intake）

```
1. 人有没有受伤？（优先）
2. 大致时间、地点
3. 是否涉及其他车辆/人员
4. 是否已报警（仅记录，不建议）
5. 照片「收到，请补文字说明」— 不 OCR 判责
```

**顺序：** 安全 > 位置 > 细节；**never** 第一个问题要 VIN。

### 9.3 安全回复原则

```
- 人没事最重要 / 若受伤请优先就医或 911
- 我已记录，陈总会联系您
- 是否报案、是否报保险 — 需要 broker 人工看，线上不能替您决定
- 不要讨论 fault / 保费影响 / 私了利弊
```

### 9.4 Flags 与 Manual Handle

| 触发 | Flag | Manual Handle |
|------|------|---------------|
| injury / 脖子疼 /  hospital | **Injury**, **Urgent** | **必须** |
| 「要不要报保险」 | **Claim Advice Requested** | **必须** |
| hit-and-run | **Urgent**, Needs Fast Response | **必须** |
| 仅事故时间地点 | Claim Active | 建议 Manual Handle |
| fault / 私了 / 涨价 | **Do Not Auto Reply** — 模板拒答 + Manual Handle | **必须** |

### 9.5 绝对不能回答

- 报不报保险  
- 会不会涨保费  
- 谁的责任  
- 该不该私了  
- 对方跑了能不能报  

### 9.6 Workbench 快速接手

```
Header: Claim Lite · Urgent · Injury（若有）
Summary: 2 句 — 时间地点 + 伤情
Known / Missing 并列
Risk Flags 置顶
Next Action: 回电客户 — 讨论是否 FNOL
CTA: Manual Handle（主按钮，非 Confirm）
Latest message 可见 — 不必翻微信
```

---

## 10. IT / 云架构风险

### 10.1 我们过去犯过的错（必须铭记）

| 事故类 | 症状 | 根因 |
|--------|------|------|
| Neon / Cloud SQL 跨云 | 连不上 DB、数据分裂 | 多 DB 源 |
| Cloud Run VPC + NAT + SQL connector 冲突 | 503、timeout | all-traffic egress 与 connector 路由打架 |
| WeCom Trusted IP | callback 403 / send fail | NAT IP 未白名单 |
| Cloud SQL private IP | 改 public 又破坏 WeCom | 单路径依赖 |
| Secret Manager 漏配 | 静默失败 | env 未进 deploy bundle |
| queue flags 未 deploy | inbox 堆死 | WECOM_INBOX_QUEUE 仅 manual gcloud |
| duplicate callback / replay | 重复 Draft / 重复 reply | dedup 失效 |
| outbox phantom | 客户收不到 / 收多条 | outbox 状态机 bug（Q0 已修） |
| schema migration | demo downtime | live 表已存在 |
| image storage | 本地 path Cloud Run 不可见 | filesystem vs GCS |
| logs PII | 合规/信任 | VIN/phone 明文 log |

### 10.2 当前不该碰的东西

| 禁区 | 原因 |
|------|------|
| Cloud SQL private IP 拓扑 | Q0.11.1 PASS 依赖 |
| Direct VPC all-traffic + NAT | WeCom 静态出口 |
| `message_processed` / `sync_cursor` 语义 | replay 安全 |
| inbox/outbox 架构替换 | 已验证；改=回归 |
| B0 Start Card gate | generic safety |
| schema migration | 无必要不迁移 |
| demo day deploy | 现场不可控 |
| WeCom path OCR / GCS 新桶 | 未测；权限风险 |

### 10.3 简单解决方案

```
no migration unless absolutely needed — JSON flags only
use JSON flags for demo — structured_payload / extra
manual drain only — wecom_drain_queues.py after each test message
rollback revision known — fiqa-api-00142-kwq
no live image dependency — seed photos_pending
PII masking in logs — phone/VIN 截断
deploy checklist — queue flags + WECOM_SLICE_SEND_REPLY + B0
24h freeze before demo — 零 deploy
```

---

## 11. 成本风险

### 11.1 挑战

| 成本爆炸模式 | 后果 |
|--------------|------|
| 每条消息 LLM | WeCom 碎片消息 × VIP 500 客户 = 不可控 |
| 每张图 OCR | Vision API × 事故多图 |
| 每 case 全历史 LLM summary | latency + bill |
| 大量 debug logs | Cloud Logging $ |
| Cloud SQL 升级 | 固定成本上升 |
| GCS 图片存储 | 存储 + egress |
| 500 VIP 上线 | 10× 流量假设 |

### 11.2 保守策略（强制）

```
rules-first — intent.py / identity.py 已验证，保持
LLM only on explicit broker action or scheduled case summary refresh — demo: 零 LLM
OCR async and optional — WeCom demo: 零 OCR
no per-message LLM
no full-history resummarization every turn — 规则截断 source_text 即可
keep images stored but parse on demand — 甚至 demo 不 store
cost tags / metrics in future — 先 design hook，不实现
```

**Red Team：** 若有人提议「加 LLM 让 summary 更聪明」— **No**，除非同时提交 $/case 上限与 fallback 规则。

---

## 12. Demo 风险

### 12.1 挑战清单

| 风险 | 严重度 |
|------|--------|
| Workbench 无 screen-proof | 🔴 |
| live WeCom 出错 | 🔴 |
| Add Vehicle 第二次失败 | 🟡 |
| Premium/Claim 口头无 case | 🔴 |
| live 发图无反应 | 🟡 |
| 陈总以为自动报价/理赔 | 🔴 |
| 陈总以为只是 chatbot | 🔴 |
| Demo >15 min | 🟡 |
| 无 fallback | 🔴 |

### 12.2 最简单解决方案

```
Workbench-first — Day 1 必须 screen-proof
seed/reset — CKS 三 story 可复现
Story C live — Add Vehicle 唯一 full live path
Story A/B minimal or seed-backed — 打开即有 case
no live image dependency
fallback recording — <60s 切换
boundary language — 开场白 30 秒讲清「不是自动报价/理赔」
8–12 min only — 宁可少讲一个 feature
demo 前 24h freeze — 零 deploy、零 schema
manual drain after each live message
```

### 12.3 Demo 叙事 Red Team

**陈总脑中的两个失败模式：**

1. 「又一个 chatbot」→ 必须用 Workbench 30 秒 scan 反制  
2. 「会自动帮我办事」→ 必须用 Broker Confirm + 边界话术反制  

**Andy 必须在 demo 前 60 秒说清：**

> 「AI 整理案子，**您点 Confirm 才算数**；报价、理赔、能不能开，**都是您定**。」

---

## 13. 商业流程风险

### 13.1 挑战

| 风险 | 说明 |
|------|------|
| 99% 华人客户，中英混杂 | intent 规则必须覆盖中文关键词 + 英文 VIN/State Farm |
| VIP 要更快响应 | FIFO list 抹杀商业价值 — **VIP tag 必须可见** |
| 普通 vs VIP 混排 | Workbench sort/filter by VIP — demo seed 演示 |
| staff 接手困难 | 同一 Case 全貌 — 禁 oral transfer |
| 客户投诉/误会 | 无 timeline → 无法自证 |
| 公开差评 | 「系统说能开」类 — C6 级 |
| 陈总要系统干完 | 产品叙事必须持续 **Broker Confirm** |

### 13.2 规则

```
VIP prioritization — tag + sort，非 auto SLA bot
timeline audit — evidence_events 最小保留，future full audit
broker confirm gate — Done Card 仅 confirm 后
staff handoff view — Workbench detail 自给自足
no auto final decision — 铁律
customer-facing wording conservative — 模板审阅，禁 fault/coverage/quote
Mixed language — 提取器支持中文日期/金额/「停保」「理赔」
```

---

## 14. Red Team 风险表

| Risk ID | 风险描述 | 类型 | 严重度 | 触发例子 | 最简单规避方案 | Demo 前必须？ | Defer？ |
|---------|----------|------|--------|----------|----------------|---------------|---------|
| R01 | AI 承诺具体保费或「能便宜 X」 | AI/Legal | **High** | 「保证降 2000」 | 固定拒答模板 + Manual Handle | **是** | 否 |
| R02 | AI 建议报/不报保险 | AI/Legal | **High** | 「要不要报？」 | 拒答 + Claim flag + Manual Handle | **是** | 否 |
| R03 | AI 判断 coverage / 能否开车 | AI/Legal | **High** | 「停保还能开吗」 | Coverage Risk flag +  cautious reply | **是** | 否 |
| R04 | AI 判断事故责任 | AI/Legal | **High** | 「对方全责吧？」 | 不回答 fault；记录 + Manual Handle | **是** | 否 |
| R05 | Raw Event 丢失（尤其图片） | Data | **High** | 客户发图无记录 | seed stub + P19 media path；demo 禁 live 图 | **部分** | 媒体全链路 defer |
| R06 | Conflict 静默覆盖 | Data/Workflow | **High** | VIN A→B 无 flag | conflict_flags JSON + Workbench 显示 was | **是** | 否 |
| R07 | Generic hello 误建 Draft | Workflow | **High** | 「你好」→ Draft | B0 gate + Q0.11.1 回归测试 | **是** | 否 |
| R08 | Multi-flow 并行深处理 | Workflow | **High** | 加车+理赔同时问 | Rule 8 flag only | **是** | 否 |
| R09 | Confirm 前 Active Case | Workflow | **High** | 未 Confirm 就 Done Card | broker_confirmed_at gate | **是** | 否 |
| R10 | Done Card 暗示保单已改 | Business/Legal | **High** | Confirm 加车文案过度 | Done Card 仅「broker 已审核」 | **是** | 否 |
| R11 | Injury 未升级 Manual Handle | AI/Workflow | **High** | 「脖子疼」 | Injury flag + urgent + Manual Handle | **是** | 否 |
| R12 | OCR 错 VIN 自动入库 | OCR/Data | **High** | 保险卡 OCR 错一位 | Demo 禁 WeCom OCR；low_confidence gate | **是** | 全 OCR defer |
| R13 | OCR vs 文字 VIN 冲突未标记 | OCR/Data | **High** | 图 A 文 B | dual_source_vin flag | **是** | 否（flag 逻辑） |
| R14 | Q0.11.1 dedup 回归 | Cloud/Workflow | **High** | 改 slice.py | 不改 dedup；跑 generic safety tests | **是** | 否 |
| R15 | Queue flags 未开 inbox/outbox | Cloud | **High** | deploy 漏 flag | deploy checklist + describe 核对 | **是** | 否 |
| R16 | Demo 现场 deploy | Cloud/Demo | **High** | 现场改 code | 24h freeze + fallback video | **是** | 否 |
| R17 | Workbench 无 screen-proof | Demo/Business | **High** | 陈总只看微信 | Day 1 Workbench + seed | **是** | 否 |
| R18 | Premium/Claim live 无 case | Demo | **High** | 说 Premium 无 Workbench | minimal stub lane + seed | **是** | 否 |
| R19 | 陈总误解为 chatbot | Business/Demo | **High** | 无 Workbench 演示 | Workbench-first narrative | **是** | 否 |
| R20 | per-message LLM 引入 | AI/Cost | **High** | 「summary 用 GPT」 | 禁止 WeCom path LLM | **是** | 否 |
| R21 | schema migration 破坏 live DB | Cloud/Data | **High** | 加 column | JSON only；no migration | **是** | 否 |
| R22 | Cloud SQL / VPC 改动 | Cloud | **High** | 改 NAT/connector | do-not-touch 清单 | **是** | 否 |
| R23 | PII 进 logs | Cloud/Legal | **Medium** | log 全 VIN | mask phone/VIN | **是** | 部分 |
| R24 | live 发图无反应 | Demo/OCR | **Medium** | demo 发保险卡 | 不 live 图；script 声明 | **是** | 媒体 defer |
| R25 | Add Vehicle 第二次失败 | Demo/Workflow | **Medium** | reset 不干净 | seed/reset script + rehearsal ×2 | **是** | 否 |
| R26 | broker_confirmed_at 仅 JSON 不同步 PG | Data | **Medium** | 跨实例读不一致 | demo 单实例；mirror extra 可 defer | 否 | **是** |
| R27 | 无 staff handoff 视图 | Business | **Medium** | 吴小姐看不懂 | Workbench detail 自给自足 | **是** | UI polish defer |
| R28 | VIP 与普通 FIFO | Business | **Medium** | $15k 客户排队 | VIP tag + seed sort | **是** | 自动 SLA defer |
| R29 | 中英混杂 intent miss | AI | **Medium** | 「续保」「claim」混说 | 扩展关键词规则 | **是** | 否 |
| R30 | outbox phantom 复发 | Cloud | **Medium** | 重复 Done Card | 不改 outbox 核心；reply_dedup | **是** | 否 |
| R31 | 本地 attachment path 上 cloud 失败 | Cloud | **Medium** | 网页 upload 在 Run | demo 不依赖网页 upload | 否 | **是** |
| R32 | Vision API 成本 | Cost/OCR | **Medium** | policy_review OCR 误开 WeCom | WeCom path 禁 OCR | **是** | 否 |
| R33 | 全历史 resummary 成本 | Cost/AI | **Medium** | 每 turn summary | 规则截断 only | **是** | 否 |
| R34 | office_actions 空表无 audit | Data | **Low** | broker 动作无 PG audit | JSON evidence + state_history | 否 | **是** |
| R35 | Timeline UI 范围 creep | Demo | **Low** | 做 full timeline | ADR-002 禁止 | **是** | full UI defer |
| R36 | Cross-story case 合并错误 | Workflow | **Medium** | Day2 claim merge Day1 premium | 独立 case per flow per day | **是** | 否 |
| R37 | Confirm 加车自动恢复停保车 | Legal/Workflow | **High** | C6 未分开展示 | Risk overlay + 文案分离 | **是** | 否 |
| R38 | 私了建议 | AI/Legal | **High** | 「能私了吗」 | 拒答 + Manual Handle | **是** | 否 |
| R39 | 降级 coverage 建议 | AI/Legal | **Medium** | 「该降 coverage 吗」 | 拒答；broker only | **是** | 否 |
| R40 | replay 历史 WeCom 消息 | Cloud/Data | **High** | cursor 回退 | 不改 sync_cursor 语义 | **是** | 否 |

**统计：** 40 条重大风险（超过最低 25 条要求）；其中 **Demo 前必须解决或显式 mitigated：32 条**；**可 defer：8 条**（媒体全链路、broker_confirmed PG mirror、office_actions、GCS、Timeline UI、自动 VIP SLA 等）。

---

## 15. 10 条不可违反的 Product Safety Rules

以下十条为 **Conservative AI 铁律**。违反任一条 → sprint 应 Stop。

| # | 铁律 | 含义 |
|---|------|------|
| **1** | **Raw event never lost** | 每条客户输入必须可追溯；不得仅用 summary 替代 |
| **2** | **AI never overwrites without timeline** | Case View 更新必须留痕；改口 → Conflict Flag |
| **3** | **One active business flow at a time** | 第二 topic 仅 flag，不并行深处理 |
| **4** | **High-risk always manual handle** | Claim/coverage/injury/quote/bind → broker |
| **5** | **No automatic quote** | 无数字、无 guarantee、无 carrier 推荐 |
| **6** | **No automatic claim advice** | 不报/报、不 fault、不私了、不涨价预测 |
| **7** | **No automatic policy change** | 无 bind/endorsement/restore API |
| **8** | **No coverage active/inactive assertion** | 不说「能开」「有保」「已生效」 |
| **9** | **OCR low confidence until broker confirms** | Demo：WeCom 无 OCR；任何 OCR 默认待确认 |
| **10** | **Broker confirm before Done** | Done Card / Active Case 仅 broker 动作后 |

---

## 16. 最小实现建议

**原则：不要深做。** 以下路线与 P18.8 一致，Red Team 从**风险**角度再次收紧。

### Day 1 — Workbench + seed（不写复杂 AI）

| 必须 | 避免 |
|------|------|
| Workbench intelligence 布局（Summary/Known/Missing/Flags/Next） | LLM summary |
| VIP / WeCom / Case Type header badges | Timeline panel |
| `seed_chen_kui_demo` 三 story cases | 改 slice dedup |
| 30 秒 broker scan rehearsal | Premium/Claim WeCom lane |
| 边界话术文档 | schema migration |

**Day 1 Stop Condition：** 陈总视角打开 seed case **30 秒内**答 type/VIP/missing/next — 否则 **No-Go Day 2**。

### Day 2 — Premium / Claim stub + safe reply

| 必须 | 避免 |
|------|------|
| `policy_review` / `claim_intake` → stub case + Workbench 可见 | 自动报价/理赔回复 |
| safe reply 模板审阅（§8、§9） | LLM intent |
| Manual Handle CTA label（Claim/Premium） | Confirm on Claim |
| Injury / Coverage 关键词 → flags | OCR on WeCom |
| seed + optional minimal live | live 图片 |

### Day 3 — Add Vehicle polish + Coverage Risk

| 必须 | 避免 |
|------|------|
| Story C live ×2 rehearsal | 改 B0 Start gate |
| C6 Coverage Risk flag + reply | auto restore coverage |
| conflict flag（VIN/premium/date） | multi-flow parallel |
| mixed-topic flags 显示 | carrier API |
| claim_mentioned during add-car |  deep Claim lane 打断加车 |

### Day 4 — Rehearsal + fallback

| 必须 | 避免 |
|------|------|
| Full script **8–12 min** | >15 min feature tour |
| fallback recording <60s | demo day deploy |
| ops checklist + drain | 新 env 实验 |
| 24h freeze 执行 | Cloud SQL / VPC 改动 |
| Andy solo run ×2 | 依赖未测 image path |

---

## 17. Go / No-Go

### 17.1 明天能不能开始 coding？

**✅ 可以 — 条件极严：**

```
GO 当且仅当：
  - Day 1 = Workbench + seed ONLY
  - 接受 WeCom 图片 zero implementation
  - 接受 zero LLM / zero WeCom OCR / zero migration
  - 接受 Story C 唯一 full live path
  - 接受 C6 Coverage Risk 为 demo 必演场景
  - rollback rev fiqa-api-00142-kwq 已知
```

**No-Go 触发（任一即停）：**

- 有人提议 sprint 内做 WeCom OCR / GCS / media download  
- 有人提议 LLM intent 或 per-message summary  
- 有人提议 schema migration「小改一下」  
- Q0.11.1 generic safety 测试失败  
- Day 1 结束仍无 Workbench screen-proof  

### 17.2 哪些规则必须先写进 docs 或 tests？

| 优先级 | 规则 | 形式 |
|--------|------|------|
| **P0** | 10 条 Product Safety Rules（§15） | 本文 + Constitution 引用 |
| **P0** | B0 Start Card gate + generic no-Draft | 已有 tests — **不可回归** |
| **P0** | Claim/Coverage 禁答清单 | reply 模板 + test assert forbidden phrases |
| **P0** | Rule 8 mixed-topic flag | test: claim during add-car → no second case |
| **P1** | Conflict flag on VIN/premium/date/injury | unit test on merge logic |
| **P1** | C6 Coverage Risk keywords → flag | slice/identity keyword test |
| **P2** | VIP tag visible on Workbench | UI smoke / seed fixture |

### 17.3 哪些可以 defer？

| Defer 项 | 最早时机 |
|----------|----------|
| WeCom image download + GCS | P19 |
| WeCom OCR | P19+ |
| Full Timeline UI | post-demo（audit JSON 先存） |
| `p16_timeline_events` 表 | P19 |
| office_actions PG 写入 | post-demo |
| broker_confirmed_at PG mirror | post-demo |
| voice pipeline | P20+ |
| LLM case summary on broker click | pilot phase |
| VIP auto-SLA / routing | pilot phase |
| carrier API / rating | **永不**（ADR-003） |

### 17.4 哪些一定不能在这次 demo 做？

```
❌ 自动报价 / rating engine
❌ 自动理赔 filing / FNOL
❌ 自动改保单 / bind / restore coverage
❌ LLM 替换 rules intent
❌ 每条消息 LLM summary
❌ WeCom live 图片依赖
❌ WeCom path OCR / Vision API
❌ schema migration
❌ demo day deploy / VPC 改动
❌ multi-flow 并行
❌ Timeline 大 UI
❌ CRM / household 模型
❌ 「AI 已帮你办好」类文案
```

---

## 附录 A — 与前置文档关系

| 文档 | P18.9 关系 |
|------|------------|
| P18.7 | 业务行为 spec — 本文挑战其**风险边界**是否足够严 |
| P18.8 | 资产清单 — 本文不重复 inventory，只加 **Challenger lens** |
| B0 Contract | Implementation 真相 — 本文 **更保守** 解释 Rule 8 / Confirm |
| Constitution Rule 8 | One Business Flow — 本文 §6、§15 强化 |
| ADR-002 | No Timeline UI — demo 可不做 UI，**不可**不做 audit 数据意识 |
| ADR-003 | No Carrier API — 本文 §8、§15 重申 |

---

## 附录 B — Red Team 最终一句话

> **宁可 demo 少展示一个「智能」功能，也不可展示一个「替 broker 做决定」的幻觉。**  
> Conservative AI 的胜利标准：**信息不丢、case 不乱、风险不漏、broker 确认** — 不是 **消息回得快**。

---

*Document version: P18.9 v1 · 2026-07-04 · Red Team gate only — no code*
