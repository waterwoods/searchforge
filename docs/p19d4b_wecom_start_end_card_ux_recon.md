# P19D-4B — WeCom Start / End Card UX Best Practice Recon

**Date:** 2026-07-06  
**Type:** UX recon + product design — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19D implementation agents  
**Prerequisite:** P19D-4A (H5 continuous photo flow) deployed + Andy live smoke feedback  
**Related:** `p19d35`, `p19d15`, `p19_guided_workflow_start_end_card_recon.md`, `p19d_core_step_by_step_evidence_capture_doctrine.md`

**This loop:** No code. No deploy. No callback / H5 / Workbench changes.

**Andy feedback (P19D-4A live smoke):**

| ✅ Working | ❌ UX gaps |
|-----------|-----------|
| H5 连续拍照丝滑：WeCom → H5 → VIN → registration → insurance/skip → Workbench | **问题 1：** 入口混淆 — 四选项菜单像机器人 IVR，不像任务入口 |
| 后台能看到上传照片 | **问题 2：** H5 点「返回微信」后，微信里没有自动 completion / confirmation message |

---

## 0. Executive Summary

| Question | Answer |
|----------|--------|
| 大厂共识：H5 完成后是否应自动发聊天确认？ | **是** — 聊天线程是用户心智中的「家」；H5 成功页 alone 不够 |
| Start Card 应长菜单还是短任务入口？ | **短任务入口** — 一次只推一个 lane 的 Start Card；四 lane 菜单仅用于首次路由 |
| 按钮 + 打字双入口如何避免混淆？ | **等价收敛** — 两条路径必须在 1 条消息内到达同一 Start Card |
| Add Vehicle 最推荐方案？ | 缩短 greeting 菜单 → 专用 H5 Start Card → H5 完成 → **自动发 E2-photo End Card**（含 checklist + 文字字段提示） |
| 是否建议开发 P19D-4B？ | **是** — Andy 实测的两个痛点都是 P0 信任/闭环问题，改动面小、价值高 |
| P19D-4B 最小范围？ | ① H5 `flow_complete` 触发 WeCom 自动消息 ② Start Card + greeting 菜单文案 ③ H5 final page 微调 |

---

## A. 大厂 / 成熟流程共识

### A.1 研究对象与模式归纳

| 参考对象 | 聊天角色 | 任务流角色 | 完成后回聊天 |
|----------|---------|-----------|-------------|
| **Walmart Spark Driver** | Push 通知 only | App 内连续任务壳 — 从不逐步回聊天 | App 内 checklist 更新；email on milestone |
| **DoorDash / Amazon Flex / Instacart** | SMS/email 仅作 deep link 入口 | App 内 sequential doc capture + preview confirm | Onboarding checklist 自动更新；**不逐步发聊天** |
| **Jumio / Onfido / 银行 KYC H5** | 客服仅 failure 时介入 | H5/SDK 连续 wizard；ReturnUrl 回跳 | **服务端查结果 + 商户发确认**（不信任前端 alone） |
| **腾讯微保 / 平安车险** | 企微/小程序客服 = 入口 + 帮办 | 小程序材料清单 wizard | **案件进度推送** + 材料 checklist ✓/○ |
| **支付宝实名 / 微信支付绑卡** | 腾讯客服公众号异步答复 | H5 核身 → redirect 回商户页 | **落地页展示结果** + 可选公众号消息 |
| **中小经纪 SaaS（行业常态）** | 企微客服 | H5 收资料链接 | **客服消息确认已收到** — 标准 80% 方案 |

### A.2 跨行业 12 条共识

| # | 共识 | 证据 |
|---|------|------|
| 1 | **聊天 = 信任锚点 + 通知 + 文字采集**；结构化拍照 = App/H5/小程序 | Spark/Flex/微保均不在聊天里逐步导航照片 |
| 2 | **Start 应是「任务邀请」不是「IVR 菜单」** — 主按钮 1 个，文案 ≤2 行 | 企微模板卡片：核心信息 ≤3 项；主 CTA 一个 |
| 3 | **双入口（点按钮 / 打字）必须等价收敛** — 同一意图 → 同一下一张卡 | DoorDash「Already started signing up」= 文字路径等价于 App 入口 |
| 4 | **H5/任务流完成后，聊天里必须有确认消息** — 最佳 ≤3s | P19D-15 recon SSOT；KYC 均服务端反查后发确认 |
| 5 | **End 消息 = 已收到 + 还缺什么 + 下一步 + 人工门控** — 不是「已完成业务」 | 微保案件进度；银行不说「开户成功」直到人工/系统终审 |
| 6 | **Checklist 在 End 消息里列出已收项** — 降低「我到底交成功了吗」焦虑 | Uber Documents ✓/○；微保材料清单 |
| 7 | **分阶段 End Card** — 照片阶段结束 ≠ 全资料收齐 | DoorDash modular onboarding：每 major step 有 status，不是一次「全过」 |
| 8 | **H5 成功页与聊天 End 分工** — H5 = 操作完成 + 引导返回；聊天 = 权威确认 + 后续指令 | KYC ReturnUrl 页 + 后端通知双轨 |
| 9 | **禁止在 End 里承诺业务结果** — 不说已加车、已报价、OCR 结果 | 全行业合规 intake 一致 |
| 10 | **「返回微信」按钮 alone 不够** — 用户 swipe back 后空窗 = 最高困惑点 | P19D-15 §3.1 lost-in-journey map 第 4 格 |
| 11 | **自动消息不稳定时的兜底** — H5 页内写清「回到微信会看到确认消息」+ 延迟重试 + 「没收到？回复 已提交」 | 腾讯客服「留意公众号消息」模式 |
| 12 | **Greeting 路由菜单与 Lane Start Card 是两层 UI** — 不应混在一张卡里 | Spark 先选任务类型，再进任务壳 |

### A.3 对我们产品原则的映射

```text
WeCom  = 入口、通知、人工沟通、文字字段
H5     = 连续 guided upload（照片）
Workbench = broker review

禁止：OCR 已完成 / VIN 已识别 / 保单已修改 / 加车已完成 / 报价承诺
只能说：资料已收到，陈总会人工确认
```

这与 A.2 第 9 条完全一致，且比大厂更保守（broker-reviewed insurance）。

---

## B. 当前 CaseIQ 流程的问题

### B.1 问题 1 — 入口混淆（Start / Greeting 层）

**现状（代码 truth）：**

| 用户行为 | 系统响应 | 问题 |
|----------|---------|------|
| 打招呼 / 意图不清 | `build_guided_menu_payload()` — 4 个双语长按钮 | 像呼叫中心 IVR，不像「我要办一件事」 |
| 直接打「我要加车」 | `build_h5_vin_start_card_payload()` — H5 Start Card | ✅ 正确路径 |
| 点菜单「Add Vehicle / 加车」 | `menu_selection` → 仍可能再走路由 | 与打字路径不完全等价（依赖后续 intent） |

**Greeting 菜单当前文案**（`services/fiqa_api/wecom/reply.py`）：

```text
Head: Thanks. I can help you review your request. To make sure we route this correctly...
Buttons: Add Vehicle / 加车 | Claim / Accident / 事故理赔 | Policy Review / 保单检视 | Other / 其他
Tail: Tap a topic above, or reply with a short phrase...
```

**痛点分析：**

1. **双语并列 + 英文放前** — 华人客户读起来像系统菜单，不像陈总助理说话。
2. **四个平级选项** — 无视觉层级；「任务入口」感应是 **动词短语**（「加一台车」「查续保」），不是名词标签。
3. **Head 太长** — 用户还没进入任务，先读 4 行说明。
4. **与 H5 Start Card 风格断裂** — Greeting 是 routing menu；Add Vehicle 是 task card。用户不知道「点加车」和「打我要加车」是不是同一条路（实际 high-confidence 会收敛，但 UX 不透明）。

### B.2 问题 2 — H5 完成后无 WeCom 确认（End 层）

**现状（P19D-4A truth）：**

| 环节 | 行为 | 缺口 |
|------|------|------|
| H5 最后一步 upload/skip | `flow_complete=true`；附件进 Workbench | ✅ |
| H5 成功页 | 「照片资料已收到 ✅」+「返回微信」+ 文字字段提示 | ✅ 页面内有 |
| **WeCom 自动消息** | **无** — `h5_task_upload.py` 完成时不调 KF `send_msg` | ❌ **P0 缺口** |
| B0 Done Card | 仅 broker Confirm 后发 `DONE_CARD_TEXT` | 与 H5 照片完成无关 |

**Andy 实测困惑（完全可预期）：**

- 我到底提交成功了吗？
- 陈总收到了吗？
- 下一步我要做什么？
- 还需要再发什么吗？

**根因：** H5 成功页在 WebView 里；用户 swipe 回微信后看到的是 **H5 之前的聊天历史** — 没有新消息 = 潜意识认为失败。

### B.3 架构层面：已设计但未实现

`p19_guided_workflow_start_end_card_recon.md` 已定义：

- **E1** — 资料全齐
- **E2** — 部分完成（列 missing）
- H5 完成后应发 chat ack（`p19d15` §4.3：「backend **always** sends chat ack within 3s」）

P19D-4A 实现了连续 H5 photo chain，**跳过了** WeCom completion notify — 这是已知的下一环，不是设计遗漏。

### B.4 问题优先级

| 优先级 | 问题 | 用户影响 |
|:------:|------|---------|
| **P0** | H5 完成无 WeCom End Card | 信任断裂；用户重复提交或放弃 |
| **P1** | Greeting 四选项菜单机器人感 | 首印象差；不影响已识别 add_car 路径 |
| P2 | H5 与 End Card 信息重复不一致 | 可文案统一解决 |
| P3 | 无 resume / 过期链接 End Card | P19D-4B 可不碰 |

---

## C. 推荐的 WeCom Start Card 文案

### C.1 设计原则

| 原则 | 说明 |
|------|------|
| **一张卡一件事** | Add Vehicle Start Card 不出现 Claim/Policy 选项 |
| **Head ≤2 行中文 + 1 行英文** | 中文主，英文信任补充 |
| **主 CTA 一个** | 「开始上传照片」— view button |
| **次 CTA 最多 2 个** | 稍后 / 联系经纪人 |
| **Tail = 安全边界** | 经纪人审核、不自动改保单 |
| **打字等价** | 「我要加车」「加车」「明天提车」→ 同一张 H5 Start Card（已实现，保持） |

### C.2 Greeting 路由层（首次/contact 不清意图）

**不推荐：** 继续用 4 个双语长 `msgmenu` 做主入口。

**推荐：** 短任务入口 — 中文动词优先，英文收进副标题。

**推荐 Greeting Head：**

```text
您好，我是陈奎保险服务助手。
请选您要办的事，或直接打字说明（例如：加车、事故、续保）。

Hi — pick a task below, or type a short message.
```

**推荐 Greeting 按钮（4 个，但缩短）：**

| id | 新文案 | 旧文案 |
|----|--------|--------|
| `add_vehicle` | **加车** | Add Vehicle / 加车 |
| `claim_intake` | **事故理赔** | Claim / Accident / 事故理赔 |
| `policy_review` | **保单检视** | Policy Review / 保单检视 |
| `other` | **其他** | Other / 其他 |

**推荐 Greeting Tail：**

```text
经纪人会人工处理，线上不会自动改保单。
```

**交互规则：** 用户点「加车」→ **立即发 Add Vehicle H5 Start Card**（与「我要加车」相同，不等第二轮）。

### C.3 Add Vehicle H5 Start Card（高置信 add_car 或点「加车」后）

**推荐 Head：**

```text
加车资料收集

请点下方按钮，按顺序上传 3 张照片：VIN → 行驶证 → 保险卡（可选）。
大约 2 分钟，不用填长表格。

Your broker reviews everything before anything changes.
```

**推荐按钮：**

| 类型 | 文案 |
|------|------|
| **Primary (view)** | **开始上传照片** |
| Secondary (click) | 稍后 |
| Secondary (click) | 联系经纪人 |

**推荐 Tail：**

```text
照片请在页面里上传（一次一张）；提车日期、ZIP、电话稍后回微信打字即可。
经纪人会先审核，不会自动修改保单。

链接打不开？复制：
{h5_url}
```

**与现版差异：**

| 维度 | P19D-4A 现版 | P19D-4B 推荐 |
|------|-------------|-------------|
| Head 第一句 | 「开始补加车资料」 | 「加车资料收集」— 更任务化 |
| 过程描述 | 偏操作说明 | 加「大约 2 分钟」降焦虑 |
| 主按钮 | 「开始补资料 / Start guided upload」 | 「开始上传照片」— 动词明确 |
| Tail | 仅 fallback 链接 | 增加 **文字字段分流说明**（减少 H5 完成后困惑的前置铺垫） |

---

## D. 推荐的 H5 Final Page 文案

### D.1 信息分工

| 信息 | H5 成功页 | WeCom End Card |
|------|:---------:|:--------------:|
| 照片步骤完成 | ✅ 主标题 | ✅ checklist 复述 |
| 已收到哪些照片 | ✅ 简要 | ✅ 具名列表 |
| 下一步文字字段 | ✅ 列出 | ✅ 复述 + 示例 |
| 陈总人工确认 | ✅ 一句 | ✅ 主承诺 |
| 保单未修改 | — | ✅ |
| 权威「提交成功」确认 | ⚠️ 页面内 | ✅ **聊天里是权威源** |

### D.2 推荐 H5 Final Page 全文

```text
【标题】照片已收到 ✅

【正文】
您已完成加车照片步骤（共 3 步）。

我们已收到：
• VIN 照片
• 行驶证照片
• 保险卡照片（或：保险卡 — 您选择了稍后补充）

【下一步 — 重要】
请点下方按钮返回微信。
回到聊天后，您会收到一条确认消息。

请在微信里直接打字发给我们：
1. 提车日期（例如：7月10日）
2. 车辆停放 ZIP（例如：90012）
3. 联系电话

【边界】
陈总会人工查看并确认，不会自动修改您的保单。

【按钮】
[ 返回微信 ]  （主按钮，大号）
[ 稍后补充 ]  （次按钮 — 仍引导回微信看确认消息）

【兜底小字】
若回到微信后 10 秒内没看到新消息，请回复：已提交
```

**动态项：** checklist 根据实际上传 / skip 渲染（VIN ✓、行驶证 ✓、保险卡 ✓/跳过）。

**禁止出现：** 已识别、OCR、加车已完成、保费、保障。

### D.3 与现版对比

现版（`H5SingleSlotUploadPage.tsx`）已有核心元素，缺：

1. **明确承诺「回到微信会收到确认消息」** — 最关键一句
2. **已收照片 checklist** — 增强完成感
3. **兜底「回复 已提交」** — 防自动消息失败

---

## E. 推荐的 WeCom End Card 文案

### E.1 何时发、发哪种

Add Vehicle 有 **两个 End 阶段** — 不要混成一张：

| 阶段 | 触发 | Card 类型 | 目的 |
|------|------|-----------|------|
| **Phase 1 — 照片完成** | H5 `flow_complete=true` | **E2-photo**（新子类型） | 确认照片已收到 + 引导文字字段 |
| **Phase 2 — 资料全齐** | 文字字段到齐 / broker 判定 ready | **E1** | 宣布转陈总审核 |
| **Broker Confirm** | 陈总点 Confirm | **E7**（现有 B0 Done Card） | 办公室已确认收到 |

**P19D-4B MVP 只做 Phase 1（E2-photo）** — 这是 Andy 实测缺口。

### E.2 推荐 E2-photo End Card（H5 完成后自动发）

**形式：** WeCom 文本消息（MVP）或 `msgmenu`（V1.1 — 带「继续补充」按钮）。

**推荐正文：**

```text
【加车资料】照片已收到 ✅

我们已收到您的：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片
（动态：若跳过保险卡 → 「○ 保险卡 — 可稍后补」）

还差 3 项，请直接在本聊天里打字发给我们：
1. 提车日期（例如：7月10日）
2. 车辆停放 ZIP（例如：90012）
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
资料齐全后我们会再通知您。

---
Photos received. Still need: delivery date, ZIP, phone — please type here.
Chen will review manually; your policy is not changed automatically.
```

### E.3 推荐 E1 End Card（文字字段到齐后 — P19D-4B 可不实现，列清方案）

```text
【加车资料】已收齐，已转陈总 ✅

我们已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片（或：保险卡待补）
✓ 提车日期
✓ 停放 ZIP
✓ 联系电话

陈总会人工确认并跟进，不会自动修改您的保单。
请留意微信消息，有疑问可直接回复。

---
All materials received and forwarded to Chen for manual review.
```

### E.4 禁止用语（重申）

| 禁止 | 替代 |
|------|------|
| 加车已完成 | 资料已收到 / 已转陈总 |
| VIN 已识别为 XXX | VIN 照片 ✓ |
| OCR 已完成 | （不提 OCR） |
| 保单已更新 | 不会自动修改保单 |
| 预计保费 / 保障 | （不提） |

---

## F. End Card Checklist 设计

### F.1 Checklist 结构

```text
我们已收到您的：
✓ {slot_label}     — status = uploaded
○ {slot_label}     — status = skipped / pending
✗ {slot_label}     — 不出现（未收的不列，避免负面暗示）

还差 {n} 项：
1. {field_label}（示例：…）
```

### F.2 Add Vehicle Checklist 项

| 项 | Phase 1 (E2-photo) | Phase 2 (E1) |
|----|:------------------:|:------------:|
| VIN 照片 | ✓ 若已上传 | ✓ |
| 行驶证照片 | ✓ 若已上传 | ✓ |
| 保险卡照片 | ✓ 或 ○ 跳过 | ✓ 或 ○ |
| 提车日期 | 列在「还差」 | ✓ |
| 停放 ZIP | 列在「还差」 | ✓ |
| 联系电话 | 列在「还差」 | ✓ |

### F.3 数据来源（实现参考，本文不写代码）

| 字段 | 来源 |
|------|------|
| 照片 ✓ | case attachments `source=h5_task` + slot |
| 保险卡跳过 | `h5_photo_flow_state.skipped_slots` |
| 文字字段 | `still_needed_fields` / case JSON |

### F.4 格式选择

| 格式 | MVP | V1.1 |
|------|:---:|:----:|
| 纯文本 + ✓/○ | ✅ | |
| `msgmenu` 带「补充电话」快捷入口 | | ✅ |
| 企微模板卡片（text_notice + horizontal list） | | ✅ 需 API 升级 |

**MVP 建议纯文本** — `msgmenu` 已在 Start Card 验证；End Card 用文本更快、更稳。

---

## G. 异常 / 兜底设计

### G.1 「返回微信」后没有自动消息

| 层级 | 兜底 |
|------|------|
| **H5 成功页** | 写清「回到微信后会收到确认消息」；10 秒没收到 → 回复「已提交」 |
| **后端** | `flow_complete` 后 **同步尝试** KF send；失败 → 入重试队列（30s × 3） |
| **用户触发** | 客户发「已提交」「继续」→ 若 case 已有 H5 完成标记，**重发 E2-photo**（幂等） |
| **日志** | `h5_flow_complete_notify_sent_v1` / `h5_flow_complete_notify_failed_v1` |

### G.2 自动消息技术不稳定

| 风险 | 概率 | 兜底 |
|------|:----:|------|
| KF send API 超时 | 中 | 重试 + H5 页兜底文案 |
| 48h KF 会话窗口 | 低（用户刚互动） | 同会话内完成应仍在窗口 |
| `send_msg` 被限流 | 低 | 退避重试 |
| 用户太快 swipe back | 高 | **先 send 再让用户点返回** — H5 在 `flow_complete` 响应后 **等 500ms** 再显示成功页（可选 polish） |

**行业做法：** KYC 不信任前端 alone — **服务端 send 是 source of truth**；H5 页是辅助。

### G.3 其他异常路径

| 场景 | End / 回复 |
|------|-----------|
| H5 中途退出（1/3 照片） | 不发 End Card；用户回聊天发「继续」→ 重发 H5 link（同 token resume） |
| 重复点「返回微信」 | 幂等 — 不重复发 End（或 5min 内去重） |
| 用户先打字再拍照 | 接受文字；End Card checklist 反映混合进度 |
| 用户问「陈总收到了吗」 | 若有 H5 完成 → 重发 E2-photo |
| 自动消息全失败 | Workbench 仍可见；broker 可手动发确认（ops fallback） |

### G.4 入口混淆兜底

| 场景 | 行为 |
|------|------|
| 用户打招呼后打字「加车」 | 跳过 greeting 菜单 → 直接 H5 Start Card |
| 用户点「加车」后又打「我要加车」 | 复用 open draft case；不重复建 case |
| 用户点「事故」 | Claim lane Start（P19D-4B 范围外） |

---

## H. MVP 版本怎么做（P19D-4B 建议范围）

### H.1 必做（P0）

| # | 改动 | 文件/区域 | 估时 |
|---|------|----------|:----:|
| 1 | H5 `flow_complete` → 调 WeCom KF 发 **E2-photo** 文本 | `h5_task_upload.py` + 新 `build_h5_photo_complete_reply()` in `reply.py` | 0.5d |
| 2 | Checklist 动态生成（3 照片 + 3 文字字段状态） | 同上 + case read | 0.25d |
| 3 | 发送失败重试 + 日志 | wecom send helper | 0.25d |
| 4 | H5 final page 文案更新（承诺聊天确认 + checklist + 兜底） | `H5SingleSlotUploadPage.tsx` | 0.25d |
| 5 | 测试：flow_complete → mock KF send asserted | pytest | 0.25d |

**不做：** OCR、schema migration、小程序、Claim/Premium flow、broker Done Card 改动。

### H.2 应做（P1，同 sprint 可并入）

| # | 改动 |
|---|------|
| 6 | Greeting 菜单缩短为中文动词（§C.2） |
| 7 | Add Vehicle H5 Start Card 文案更新（§C.3） |
| 8 | 点「加车」菜单 → 直接 H5 Start Card（与打字等价） |

### H.3 明确不做（P19D-4B）

- E1 全资料收齐自动 End（等文字字段 ingest 逻辑稳定）
- 企微模板卡片 upgrade
- Workbench UI 变更
- WeCom callback 架构改动
- 「已提交」重发幂等 handler（可 V1.1）

---

## I. V1.1 以后怎么增强

| 增强 | 价值 |
|------|------|
| **E1 自动触发** — 文字字段到齐后发第二段 End | 完整闭环 |
| **`msgmenu` End Card** — 「补充电话」快捷按钮 | 减少打字摩擦 |
| **企微 `text_notice` 模板卡片** — 品牌感 + 结构化 checklist | 对标微保案件进度 |
| **「已提交」/「继续」幂等重发** | 自动消息失败自愈 |
| **Start Card 模板卡片**（非 msgmenu） | 更高打开率 |
| **H5 → 小程序** — `openCustomerServiceChat` 一键回聊天 | 消除 swipe back |
| **24h E2 nudge** — 照片完成但文字未补 | 降低 broker 等待 |
| **Premium / Claim lane Start Card 统一风格** | 全 lane 一致 |

---

## J. 是否应该进入开发 P19D-4B

### J.1 建议：**GO — 进入 P19D-4B**

| 维度 | 评估 |
|------|------|
| Andy 实测痛点 | 2/2 被本文覆盖 |
| 用户信任风险 | **高** — 「没收到确认 = 以为失败」可导致重复提交或流失 |
| 技术风险 | **低** — 在现有 `flow_complete` 钩子加 send；无 schema 变更 |
| 与产品原则对齐 | ✅ WeCom=通知；不说 OCR/加车完成 |
| 依赖 | P19D-4A H5 chain 已上线 |
| 范围可控 | MVP ≤1.5 dev day |

### J.2 不做 P19D-4B 的风险

- 每次 H5 完成都制造「提交幻觉」
- Andy / 陈总 pilot 演示时客户困惑
- Workbench 有数据但客户不知道 — 增加 broker 解释成本

### J.3 验收标准（P19D-4B Done）

1. Andy 手机：我要加车 → H5 完成 3 步 → 点返回微信 → **10 秒内收到 E2-photo 消息**
2. E2-photo 含 ✓ checklist + 3 个文字字段提示 + 人工门控
3. H5 成功页含「回到微信会收到确认消息」
4. 无禁止用语（OCR / 加车已完成 / 保单已改）
5. 回归：greeting 菜单、Claim/Premium lane 不受影响

---

## STOP — 最终推荐文案与决策

### 1. 推荐 Start Card 最终文案

**Add Vehicle H5 Start Card：**

```text
【Head】
加车资料收集

请点下方按钮，按顺序上传 3 张照片：VIN → 行驶证 → 保险卡（可选）。
大约 2 分钟，不用填长表格。

Your broker reviews everything before anything changes.

【Primary button】开始上传照片

【Secondary】稍后 | 联系经纪人

【Tail】
照片请在页面里上传（一次一张）；提车日期、ZIP、电话稍后回微信打字即可。
经纪人会先审核，不会自动修改保单。
```

**Greeting 路由（首次不清意图）：**

```text
【Head】
您好，我是陈奎保险服务助手。
请选要办的事，或直接打字（例如：加车、事故、续保）。

【Buttons】加车 | 事故理赔 | 保单检视 | 其他

【Tail】
经纪人会人工处理，线上不会自动改保单。
```

---

### 2. 推荐 End Card 最终文案（E2-photo — H5 完成后自动发）

```text
【加车资料】照片已收到 ✅

我们已收到您的：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片
（若跳过保险卡 → 「○ 保险卡 — 可稍后补」）

还差 3 项，请直接在本聊天里打字发给我们：
1. 提车日期（例如：7月10日）
2. 车辆停放 ZIP（例如：90012）
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
资料齐全后我们会再通知您。
```

---

### 3. 推荐 H5 Final Page 文案

```text
照片已收到 ✅

您已完成加车照片步骤。

我们已收到：
• VIN 照片
• 行驶证照片
• 保险卡照片（或：保险卡 — 您选择了稍后补充）

请点下方按钮返回微信。
回到聊天后，您会收到一条确认消息。

请在微信里打字发给我们：
1. 提车日期（例如：7月10日）
2. 车辆停放 ZIP（例如：90012）
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。

[ 返回微信 ]  [ 稍后补充 ]

若 10 秒内没看到新消息，请回复：已提交
```

---

### 4. 是否建议下一步开发 P19D-4B

**建议：是 — 立即进入 P19D-4B。**

理由：Andy 实测的两个 UX 问题中，**无 WeCom 确认消息是 P0 信任阻断**；Start Card 文案是 P1 但可同 sprint 低成本修复。改动面小、无 schema/OCR/小程序依赖，与 paid pilot 目标直接对齐。

---

### 5. 若开发，最小改动范围

| 层 | 最小改动 |
|----|---------|
| **Backend** | `ingest_h5_slot_upload` / `skip_h5_flow_slot` 在 `flow_complete` 时调用 WeCom KF send E2-photo（含动态 checklist） |
| **Copy** | `reply.py` — 新 `build_h5_photo_phase_complete_reply(case)` + 更新 Start Card / greeting 文案 |
| **H5** | `H5SingleSlotUploadPage.tsx` — 成功页文案 + checklist 展示 + 「会收到确认消息」 |
| **Tests** | `test_h5_add_vehicle_photo_flow.py` + wecom send mock |
| **不改** | WeCom callback 路由、Workbench、OCR、schema、小程序、Claim/Premium flow |

**估时：** 1–1.5 dev day + Andy 手机复测 15 min。

---

*P19D-4B recon complete. No code. No deploy. Awaiting Andy GO for implementation.*
