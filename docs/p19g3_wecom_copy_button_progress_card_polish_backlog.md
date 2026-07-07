# P19G-3 — WeCom Copy / Button / Progress Card Polish Backlog

**Date:** 2026-07-07  
**Type:** UX / copy polish backlog — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19G+ implementation agents  
**Prerequisite:** P19G-2 One-page Proposal + Demo Script ✅ (`91e9e39`)  
**Related:** `p19g2_one_page_proposal_demo_script.md` · `p19e3_channel_strategy_wecom_h5_miniprogram_recon.md` · `p19d4b_wecom_start_end_card_ux_recon.md` · `p19e2_add_vehicle_status_resume_card_recon.md`

**This loop:** No code. No deploy. No config change. No OCR. No mini program. No H5 implementation.

**Code truth source:** `services/fiqa_api/wecom/reply.py` · `ui/src/pages/H5SingleSlotUploadPage.tsx` · `services/fiqa_api/inbox_triage/h5_task_upload.py`

---

## 1. Executive Summary

P19G-2 已把产品定位和 demo 脚本定稿。P19G-3 聚焦 Andy 的核心判断：**微信端体验是 paid pilot 成败关键之一** — 目标不是「AI 聊天机器人」，而是像 Walmart Spark Driver 一样：当前任务清楚、当前步骤清楚、按钮清楚、不让客户迷路、最少动作把 case build 好、减少陈总反复追问。

| Question | Answer |
|----------|--------|
| **本轮做什么？** | 只做 UX/copy polish backlog 文档 |
| **功能是否已通？** | **是** — Start Card → H5 → S1 → Phase 2 → S2 → Progress Card → Workbench 全链路 live |
| **主要缺口在哪？** | 文案偏长、中英混杂、「完成」易误解、按钮不统一、部分卡仍像系统菜单 |
| **是否应马上改文案？** | **是，但先做 P0 copy constants** — 低风险、高 demo 价值 |
| **实现方式？** | 主要是 `reply.py` + H5 页面 copy constants；不改路由逻辑 |
| **本轮代码变更？** | **无** |

**一句话结论：**

> 功能已够 demo；下一轮用 1–2 天统一微信文案和按钮，把 Spark Driver 的「清楚感」和陈总助理的「人味」合在一起 — 先 recon/backlog（本文），再小步实现。

---

## 2. Current WeCom UX Inventory

### 2.1 端到端卡片流（Add Vehicle）

```text
客户：「我要加车」
    ↓
[H5 Start Card] — 主按钮「开始上传照片」
    ↓
H5 WebView — VIN → 行驶证 → 保险卡（可跳过）
    ↓
H5 成功页 —「第 1 阶段完成 ✅」+「返回微信」
    ↓
[Stage Complete S1] —「【第 1 阶段完成 ✅ · 照片资料】」
    ↓
客户在微信打字 — 提车日期 / ZIP / 电话
    ↓
[Stage Complete S2] —「【第 2 阶段完成 ✅ · 文字信息】」
    ↓
客户问「进度」→ [Progress Card] —「【加车资料进度】」
    ↓
陈总 Workbench 审阅
```

### 2.2 十项核心触点清单

| # | 触点 | 当前作用 | 可能的问题 | Polish 方向 |
|---|------|----------|------------|-------------|
| 1 | **Greeting / main menu** | 意图不清时发 4 选项菜单 | 像 IVR 机器人；选项名偏抽象（【加车资料补充】）；head 仍偏长 | 缩短 head；动词短语按钮；中文优先；加车路径直接进 Start Card 而非再选菜单 |
| 2 | **Add Vehicle Start Card** | 引导 H5 上传 3 张照片 | 标题无【】框；含英文 `registration`；主按钮「开始上传照片」与 demo 脚本「开始上传资料」不一致；副按钮 2 个（稍后 / 联系经纪人） | 更短 checklist；统一主按钮「开始上传资料」；去掉英文 |
| 3 | **H5 final page** | 照片阶段完成 + 引导回微信 | 「第 1 阶段完成」重复出现；含「Workbench」字样（非 H5 主路径）；双按钮「返回微信」「稍后继续」可能分散 | 单主 CTA「返回微信」；与 S1 文案对齐；去掉 broker 后台术语 |
| 4 | **Stage Complete S1** | 确认照片收到 + 提示 Phase 2 | 「第 1 阶段完成」易被理解成「全部完成」；分隔线 `──────────` 偏系统感；字段提示分散 | 改为「第 1 步完成」；给固定一行例子；强调「还差文字信息」 |
| 5 | **Phase 2 text prompt** | 引导客户在微信补充 3 字段 | 有 `build_phase2_current_step_reply` 和 `build_phase2_unrecognized_fields_reply` 两套；partial 时略长 | 统一「还差 N 个」格式；始终附一行完整例子 |
| 6 | **Stage Complete S2** | 文字收齐 → 转 broker review | 「第 2 阶段完成」同样易误解；未强调「不会自动改保单」足够醒目 | 改为「第 2 步完成」；明确「等待陈总确认」；业务未完成感 |
| 7 | **Progress Card** | 回答「进度 / 还差什么 / 你好」 | 5 种状态已覆盖；「第 X 步」略机械；phase1 副按钮「联系经纪人」与主任务无关时干扰 | 更口语化步骤名；missing text 一眼 checklist；broker review 强调「不需补资料」 |
| 8 | **Restart copy** | 「重新加车」开新 case | 无确认卡 — 直接开新 flow；`restart_intro` 仅 prepend 一行 | 加确认话术（或 Progress vs Restart 分流提示）；避免误开新 case |
| 9 | **Recovery / missing info** | Phase 2 解析失败时提示格式 | 仅 `build_phase2_unrecognized_fields_reply`；无单字段 recovery | 按「还差 X 项」动态列；语气不挫败 |
| 10 | **Broker review waiting** | Progress Card phase3 + S2 tail | 与 S2 信息重复；客户仍可能问「好了吗」 | 统一 waiting copy；明确跟进渠道（微信/电话） |

### 2.3 当前文案原文（code truth）

**Greeting menu** (`reply.py`):

```text
您好，请选择您要办理的事项：

也可以直接回复：
「我要加车」/「我要理赔」/「查保单」

• 【加车资料补充】
• 【事故/理赔】
• 【保单检视】
• 【其他问题】

经纪人会审核，我们不会自动修改您的保单。
```

**H5 Start Card head:**

```text
加车资料收集

请点下方按钮，按顺序上传 3 张照片：
1. VIN 照片
2. 行驶证 / registration
3. 保险卡，可选

大约 2 分钟，不用填长表格。
```

**H5 Start Card button:** `开始上传照片`  
**H5 Start Card secondary:** `稍后` · `联系经纪人`

**Stage Complete S1 title:** `【第 1 阶段完成 ✅ · 照片资料】`

**Stage Complete S2 title:** `【第 2 阶段完成 ✅ · 文字信息】`

**Progress Card title:** `【加车资料进度】`

**Restart intro:** `好的，我们重新开始一组加车资料收集。`

**Legacy Start Card** (fallback): 仍含英文 `Start / 开始` · `Later / 稍后` · `Talk to Broker / 联系经纪人`

---

## 3. UX Principles

微信端体验原则（P19G-3 SSOT）：

| # | 原则 | 说明 |
|---|------|------|
| 1 | **短句优先** | 每条消息 ≤6 行有效信息；checklist 用 ✓ / ○ / ▶️ |
| 2 | **中文优先** | 客户面向文案默认中文；英文仅保留合规必要处 |
| 3 | **一次只做一件事** | 每张卡一个主动作；不要同时推 3 个平行入口 |
| 4 | **不说技术词** | 禁止：OCR、backend、API、token、case、workflow、state machine |
| 5 | **不说后台词** | 禁止对客户说：Workbench、queue、ingest、slot、pipeline |
| 6 | **四问必答** | 已收到什么 · 还差什么 · 下一步做什么 · 要不要等陈总 |
| 7 | **一张卡一个主动作** | 主按钮 1 个；次要动作放 tail 或文字提示 |
| 8 | **「完成」要谨慎** | 照片完成 ≠ 全部完成；文字完成 ≠ 保单已改；只有陈总确认后才是真正完成 |
| 9 | **语气像靠谱助理** | 像吴小姐 / 陈总办公室助理，不像机器人 IVR |
| 10 | **Spark Driver 清楚感** | 当前任务 · 当前步骤 · done/not-done · 不迷路 |
| 11 | **人工门控透明** | 始终让客户知道：陈总会人工确认，不会自动改保单 |
| 12 | **少打扰** | 里程碑才发卡；重复「进度」不重复发长卡（V1.1 dedup） |

### 3.1 Spark Driver vs 保险经纪人 — 如何兼得

| Spark Driver | 我们的适配 |
|--------------|------------|
| App 内 checklist 实时更新 | WeCom Progress Card + Stage Complete 卡 |
| 每步一个 primary action | H5 每步一个上传按钮；微信每卡一个主 CTA |
| 不逐步发聊天 | 只在阶段边界发卡（S1 / S2 / 查询 Progress） |
| 无人工审核 | **加一层：陈总人工确认中** — 这是信任优势，不是弱点 |
| 冷冰冰的系统语气 | **加一层：像陈总助理说话** — 短、亲切、不承诺业务结果 |

---

## 4. Start Card Copy Polish

### 4.1 当前 vs 问题

| 项 | 现状 | 问题 |
|----|------|------|
| 标题 | `加车资料收集` | 无视觉锚点【】；与 Progress Card 标题风格不统一 |
| 清单 | 含 `registration` | 中英混杂 |
| 主按钮 | `开始上传照片` | 与 P19G-2 demo 脚本「开始上传资料」不一致 |
| 副按钮 | 稍后 + 联系经纪人 | 2 个 click 可能分散；首卡应聚焦上传 |
| Tail | 3 行说明 + 链接兜底 | 略长；可合并 |

### 4.2 推荐文案（Draft v1）

```text
【加车资料收集】

请先上传 3 类资料：
1. VIN 照片
2. 行驶证 / 登记证
3. 保险卡（没有可跳过）

点下面按钮开始上传。
```

**主按钮：** `开始上传资料`  
**Tail（可选）：** `照片在页面里上传；提车日期、ZIP、电话稍后回微信补充。陈总会人工确认。`  
**链接兜底：** `如果按钮打不开，请回复：链接`

### 4.3 副按钮策略

| 选项 | 建议 |
|------|------|
| A — 保留「稍后」「联系经纪人」 | 当前行为；适合已有焦虑客户 |
| B — 首卡只留主按钮 | 最 Spark-like；次要动作靠打字「联系经纪人」 |
| **推荐** | **A 保留，但降级为 tail 文字提示**，首卡 visual 只有 1 个主按钮 |

---

## 5. H5 Button / CTA Polish

### 5.1 当前 H5 按钮清单

| 场景 | 当前文案 | 问题 |
|------|----------|------|
| 选图 | `选择 / 拍摄照片` | ✅ 可保留 |
| 预览确认 | `确认提交` | ✅ 可保留 |
| 重选 | `重新选择` | ✅ 可保留 |
| 跳过保险卡 | `跳过此步骤 / 稍后补充` | 略长 |
| 上传中 | `上传中…` | ✅ |
| 成功页主 CTA | `返回微信` | ✅ 正确 |
| 成功页副 CTA | `稍后继续` | 与「返回微信」重复（都调 closeWindow） |
| 成功页 headline | `第 1 阶段完成 ✅`（出现 2 次） | 重复 |

### 5.2 H5 成功页推荐文案（Draft v1）

```text
【第 1 步完成 ✅】

照片已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡（或 ○ 可稍后补）

总进度：① 上传照片 ✓ → ② 补充文字 → ③ 陈总确认

请点下方按钮回到微信。
回到聊天后会收到下一步指引。
```

**主按钮：** `返回微信`  
**去掉：** `稍后继续` 第二按钮（功能重复）  
**去掉：** `陈总会在 Workbench 中人工确认` → 改为 `陈总会人工确认，不会自动修改您的保单。`

### 5.3 H5 步骤内文案（`_SLOT_COPY`）

当前已较好；微调建议：

| Slot | 当前 | 建议 |
|------|------|------|
| vin_photo | `请拍 VIN 照片` | 保留 |
| registration | `请拍行驶证 / registration` | → `请拍行驶证 / 登记证` |
| insurance | `请拍保险卡 / insurance card` | → `请拍保险卡（可跳过）` |

---

## 6. Stage Complete S1 Copy Polish

### 6.1 当前 vs 问题

- 标题 `第 1 阶段完成` → 客户可能以为「都办完了」
- 分隔线 `──────────` + 子标题 `【下一步 · 第 2 步：补充文字信息】` → 偏系统模板
- 缺一行完整例子（只有分项例）

### 6.2 推荐文案（Draft v1）

```text
【第 1 步完成 ✅】

照片资料已收到。

下一步请在微信里回复：
提车日期、停放 ZIP、联系电话。

例如：
7月10号提车，ZIP 92705，电话 2031234567

陈总会人工查看，不会自动修改您的保单。
```

**关键改动：**
- `阶段` → `步`
- 去掉分隔线
- 合并为一段「例如」整行示范
- 保留人工门控一句

---

## 7. Phase 2 Text Prompt Polish

### 7.1 三种子状态

| 子状态 | 函数 | 场景 |
|--------|------|------|
| 空 | `build_phase2_current_step_reply` (no fields) | S1 后首次 |
| 部分 | `build_phase2_current_step_reply` (partial) | 已收到部分字段 |
| 无法解析 | `build_phase2_unrecognized_fields_reply` | 自由文本解析失败 |

### 7.2 推荐文案

**空 / 首次：**

```text
【加车资料 · 第 2 步】

还差 3 个文字信息：

1. 提车日期
2. 停放 ZIP
3. 联系电话

可以直接这样回复：
7月10号提车，ZIP 92705，电话 2031234567
```

**部分收到：**

```text
【加车资料 · 第 2 步】

已收到：
✓ 提车日期 — 7月10日
✓ 停放 ZIP — 92705

还差：
○ 联系电话

请直接回复电话号码即可。
```

**无法解析（Recovery 轻量版）：**

```text
我还需要一点信息才能继续。

还差：
○ 提车日期
○ 停放 ZIP
○ 联系电话

请直接这样回复：
7月10号提车，ZIP 92705，电话 2031234567
```

---

## 8. Stage Complete S2 Copy Polish

### 8.1 当前 vs 问题

- `第 2 阶段完成` 同样误导
- `资料已基本收齐，已转陈总审核` — 好，但可更短
- 与 Progress Card phase3 内容重叠 — 需刻意一致

### 8.2 推荐文案（Draft v1）

```text
【第 2 步完成 ✅】

文字信息已收到。

目前资料已基本收齐。
下一步：陈总人工确认。

系统不会自动修改您的保单。
确认后会通过微信或电话跟进。
```

---

## 9. Progress Card Copy Polish

### 9.1 五态映射 + 推荐文案

#### State B — Phase 1 in progress（还差照片）

```text
【加车资料进度】

▶️ 第 1 步：上传照片

还差：
○ 行驶证照片
○ 保险卡照片

请点击继续上传。
```

**主按钮：** `继续上传照片`  
**Tail：** `如果按钮打不开，请回复：链接`

#### State C/D — Phase 2 incomplete / partial（还差文字）

```text
【加车资料进度】

✅ 照片资料已收到
▶️ 还差文字信息

还差：
○ 提车日期
○ 停放 ZIP
○ 联系电话

请直接在微信里回复。
```

#### State E — Broker review（陈总确认中）

```text
【加车资料进度】

✅ 照片资料已收到
✅ 文字信息已收到
▶️ 陈总人工确认中

目前不需要您补资料。
确认后会通过微信或电话跟进。
```

#### State F — Broker done

```text
【加车资料进度】

✅ 照片资料已收到
✅ 文字信息已收到
✅ 陈总已处理

请留意微信或电话。
如需办理其他事项，直接回复即可。
```

### 9.2 Progress Card polish 要点

| 项 | 改法 |
|----|------|
| `第 X 步：上传照片` | 可保留；或简化为 `▶️ 还差照片` |
| 已收到字段带值 | partial 时保留 — 减少客户重复输入 |
| 多车 tail | 保留 `如果您同时办理多台车，请联系陈总。` |
| H5 fallback | `请回复：重新加车 重新开始，或联系经纪人。` |

---

## 10. Restart / Recovery Copy Polish

### 10.1 Restart — 当前行为

- 客户发 `重新加车` → 立即新 case + Start Card
- `restart_intro` prepend：`好的，我们重新开始一组加车资料收集。`

### 10.2 Restart 推荐文案（Draft v1）

**方案 A — 确认分流（P1，需路由改动）：**

```text
您要重新开始一辆车的资料收集吗？

如果是，请回复：
重新加车

如果只是查看进度，请回复：
进度
```

**方案 B — 保持即时 restart，优化 intro（P0 copy only）：**

```text
好的，我们为您开始一辆新车的资料收集。

【加车资料收集】
…（标准 Start Card）…
```

**推荐：** P0 用方案 B；P1 评估方案 A 是否降低误触。

### 10.3 Recovery — 单字段缺失

```text
我还需要一点信息才能继续。

还差：
○ 联系电话

请直接回复电话号码即可。
```

### 10.4 Recovery — 照片相关问题（P2）

当前无专用 Recovery Card。Broker 在工作台发现照片不对时，仍靠人工微信 — 试点可接受。

---

## 11. Broker Review / Waiting Copy Polish

### 11.1 客户等待期核心焦虑

| 客户心里话 | 文案应答 |
|------------|----------|
| 好了吗？ | Progress Card：`陈总人工确认中` |
| 还要我做什么？ | `目前不需要您补资料` |
| 多久能好？ | `确认后会通过微信或电话跟进`（不承诺时效） |
| 保单改了吗？ | `系统不会自动修改您的保单` |

### 11.2 Broker Done Card（`DONE_CARD_TEXT`）

当前：

```text
陈奎团队已收到您的请求，我们会跟进后续步骤。
```

**建议微调（P1）：**

```text
陈总已收到并处理您的加车资料。

后续步骤我们会通过微信或电话告知。
如有疑问，直接回复即可。
```

注意：Done Card 仅在 broker Confirm 后发送 — 语气可更具体，但仍不能说「保单已修改」。

---

## 12. Human Tone Guidelines

### 12.1 像助理，不像机器人

| ✅ 推荐 | ❌ 避免 |
|---------|---------|
| 照片资料已收到 | 您的资料已成功提交至系统 |
| 还差 3 个文字信息 | Phase 2 text collection pending |
| 陈总人工确认中 | Case status: broker_review |
| 请直接在微信里回复 | 请在当前 channel 输入字段 |
| 例如：7月10号提车… | 请按 schema 格式填写 |

### 12.2 称谓与签名

- 用「陈总」— 客户认识经纪人
- 不说「AI」「机器人」「智能客服」
- 可用「我们」指办公室，不用品牌英文名做主语

### 12.3 长度预算

| 卡类型 | 目标行数 |
|--------|----------|
| Start Card head | ≤8 行 |
| Stage Complete | ≤12 行 |
| Progress Card | ≤10 行 |
| Recovery | ≤6 行 |

---

## 13. Button / CTA Guidelines

### 13.1 原则

| # | 原则 |
|---|------|
| 1 | 主按钮最多 1 个 |
| 2 | 按钮文字 ≤8 字 |
| 3 | 动词开头 |
| 4 | 不用技术词 |
| 5 | 不同时出现多个平行入口 |
| 6 | view 按钮（H5 链接）优先于 click 按钮 |
| 7 | 中英文不并列 — 中文为主 |

### 13.2 推荐按钮文案

| 场景 | 推荐 |
|------|------|
| 开始加车 flow | `开始上传资料` |
| H5 继续上传 | `继续上传照片` |
| 查进度 | `查看加车进度`（若需按钮；目前靠打字「进度」） |
| 联系人工 | `联系经纪人` |
| 重新开始 | `重新开始加车` |
| 回微信 | `返回微信` |
| H5 选图 | `选择 / 拍摄照片` |
| H5 确认 | `确认提交` |

### 13.3 不推荐

| 文案 | 原因 |
|------|------|
| Open H5 | 英文 + 技术 |
| Upload task | 系统用语 |
| Case detail | 后台用语 |
| Submit workflow | 技术 |
| Finalize request | 误导「已完成业务」 |
| Start / 开始 | 中英并列 |
| Later / 稍后 | 中英并列 |

---

## 14. Priority Backlog

### P0 — 现在最值得做（demo 前 / demo 中）

| # | Item | Value | Effort | Risk | Timing |
|---|------|-------|--------|------|--------|
| 1 | **Start Card copy 更短** | 首印象专业；demo 第一屏 | S — `reply.py` constants | 低 | 下一轮 sprint 第 1 天 |
| 2 | **S1 / S2 避免「完成」误解** | 减少客户以为保单已改 | S — title + body strings | 低 | 同上 |
| 3 | **Progress Card 更短、更像用户状态** | 核心卖点「进度清楚」 | S — `build_add_vehicle_progress_card` | 低 | 同上 |
| 4 | **Phase 2 prompt 固定例子** | 减少格式猜测、减少追问 | S — phase2 reply functions | 低 | 同上 |
| 5 | **按钮统一** | 「开始上传资料」「继续上传照片」 | S — constants + tests snapshot | 低 | 同上 |
| 6 | **去掉客户可见英文** | 华人客户信任感 | S — grep + replace | 低 | 同上 |
| 7 | **H5 成功页去重 + 去 Workbench 词** | 与 S1 一致；不暴露后台 | M — `H5SingleSlotUploadPage.tsx` | 低 | P0 后半 |

**P0 预估：** 1–2 人天 · 仅 copy constants + snapshot tests · 无路由变更

### P1 — paid pilot 前

| # | Item | Value | Effort | Risk | Timing |
|---|------|-------|--------|------|--------|
| 1 | **Recovery copy（单字段 / 多字段）** | 减少挫败感 | S | 低 | Pilot week 1–2 |
| 2 | **Restart confirmation** | 避免误开新 case | M — 可能需 intent 分流 | 中 | Pilot week 2 |
| 3 | **Broker waiting copy 统一** | S2 + Progress phase3 + Done Card 一致 | S | 低 | Pilot week 1 |
| 4 | **多 case 提示优化** | 多台车场景 | S | 低 | 有实测后再调 |
| 5 | **Claim lane switch copy** | 加车中途问理赔 | S — `_SECONDARY_TOPIC_DEFERRED` | 低 | Pilot 中按需 |
| 6 | **Greeting menu 缩短** | 非加车路径首印象 | S | 低 | Pilot 前 |
| 7 | **Progress Card dedup** | 重复「进度」不刷屏 | M — routing/dedup | 中 | V1.1 |

### P2 — 以后

| # | Item | Value | Effort | Risk | Timing |
|---|------|-------|--------|------|--------|
| 1 | **OCR pending copy** | 未来 OCR 时客户预期管理 | M | 高（合规） | Post-pilot |
| 2 | **Broker asks more info loop** | 陈总退回补资料 | L — 新卡类型 | 中 | V1.1 |
| 3 | **H5 Task Home copy** | 只读进度页 | M | 低 | After Progress Card 稳定 |
| 4 | **Mini program copy** | 新 channel | L | 高 | 量触发后 |
| 5 | **Bilingual mode** | 英文客户 | M | 低 | 有需求再做 |
| 6 | **照片重传按钮** | 发错图恢复 | M | 中 | 看 pilot 比例 |

---

## 15. Final Recommendation

### 15.1 七个明确回答

| # | Question | Answer |
|---|----------|--------|
| 1 | **现在是否应该马上改微信文案？** | **是** — 功能已通，文案是 demo → pilot 最低成本提升项 |
| 2 | **哪些文案最先改？** | Start Card → S1/S2 标题 → Progress Card → Phase 2 例子 → 按钮统一 |
| 3 | **是否会影响现有功能？** | **不会** — 仅字符串替换；路由/state machine 不变 |
| 4 | **是否需要代码实现，还是 copy constants？** | **主要是 copy constants** — `reply.py`（~80%）+ H5 页面（~20%）；测试更新 snapshot |
| 5 | **是否应该先做 recon/backlog，再下一轮实现？** | **是** — 本文即 recon/backlog；下一轮直接按 P0 清单改 |
| 6 | **是否应该避免过度频繁发卡打扰客户？** | **是** — 只在阶段边界 + 客户主动查询时发卡；V1.1 加 Progress dedup |
| 7 | **如何保持 Spark 清楚感 + 经纪人的人味？** | Spark 结构（步骤/checklist/单 CTA）+ 陈总助理语气（短中文、不承诺、人工门控透明） |

### 15.2 实现顺序建议（下一轮 P19G-3.1）

```text
Day 1 AM  — reply.py: Start Card + S1 + S2 + Progress Card
Day 1 PM  — reply.py: Phase 2 prompts + button labels
Day 2 AM  — H5SingleSlotUploadPage.tsx: success page + slot labels
Day 2 PM  — pytest snapshot update + demo_pre_checklist + Andy phone smoke
```

### 15.3 不建议现在做的

- 不改 WeCom 路由优先级
- 不加新卡类型（Recovery Card 路由）
- 不做 OCR copy
- 不做小程序
- 不做 Greeting menu 结构改版（P1）

---

## 16. Appendix — Copy Diff Summary

| 位置 | 当前关键词 | 推荐关键词 |
|------|------------|------------|
| Start title | `加车资料收集` | `【加车资料收集】` |
| Start button | `开始上传照片` | `开始上传资料` |
| S1 title | `第 1 阶段完成` | `第 1 步完成` |
| S2 title | `第 2 阶段完成` | `第 2 步完成` |
| Progress phase3 | `第 3 步：陈总人工确认中` | `陈总人工确认中`（可去「第 3 步」） |
| H5 registration | `行驶证 / registration` | `行驶证 / 登记证` |
| Legacy buttons | `Start / 开始` | `开始`（legacy path 清理） |

---

## 17. Final STOP Report

| # | Item | Value |
|---|------|-------|
| 1 | **Document path** | `docs/p19g3_wecom_copy_button_progress_card_polish_backlog.md` |
| 2 | **Main UX principle** | 短句中文 · 一次一事 · 四问必答 · 「完成」谨慎 · 像陈总助理不像机器人 |
| 3 | **Top 5 copy polish items** | ① Start Card 更短 ② S1/S2 去「阶段完成」误解 ③ Progress Card 状态化 ④ Phase 2 固定例子 ⑤ 按钮统一 |
| 4 | **Recommended button labels** | 开始上传资料 · 继续上传照片 · 返回微信 · 联系经纪人 · 重新开始加车 |
| 5 | **P0/P1/P2 backlog** | P0: 7 项 copy/button（1–2 天）· P1: 7 项 pilot 前 · P2: 6 项 post-pilot |
| 6 | **Immediate implementation recommended?** | **Yes for P0** — after this doc; not in this loop |
| 7 | **Code changed?** | **No** |
| 8 | **Deploy happened?** | **No** |
| 9 | **STOP** | **P19G-3 documentation complete — ready for P19G-3.1 implementation** |

---

*P19G-3 loop closed. Next: P19G-3.1 copy constants implementation (separate PR).*
