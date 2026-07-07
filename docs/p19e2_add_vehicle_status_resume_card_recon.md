# P19E-2 — Add Vehicle Status / Resume Card Best Practice Recon

**Date:** 2026-07-06  
**Type:** Product / architecture recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19E implementation agents  
**Prerequisite:** P19E-1.5 (Phase 2 text collection + Postgres read facade) ✅ · P19E-0 (3-phase binary step model) ✅  
**Related:** `p19e0_spark_style_binary_step_model_recon.md`, `p19e1_add_vehicle_case_state_machine_event_pipeline.md`

**This loop:** No code. No deploy. No WeCom / H5 / Workbench changes.

---

## 1. Executive Summary

P19E-1.5 closed the **data loop**: WeCom → H5 photos → Phase 2 text extraction → Stage Complete S2 → `guided_workflow_state = ready_for_broker_review` → Workbench shows collected fields.

Andy 手机测试确认链路通，但暴露 **状态感（status awareness）** 缺口：用户中断后回来，不知道自己在哪一步、该不该继续、还是已经交给陈总。

| Question | Answer |
|----------|--------|
| 核心问题是什么？ | **无统一「当前任务」入口** — 聊天里没有常驻进度视图；`你好` 仍可能落到主菜单，打断进行中的加车 case |
| 最佳 MVP 形态？ | **WeCom Status Card + CTA（方案 2 + 方案 4 轻量混合）** — 不是纯 Resume Card，也不是独立 H5 首页 |
| 推荐产品名称？ | 对外 **「加车资料进度」**；对内 **`AddVehicleProgressCard`**（Status / Progress Card，非 Resume Card） |
| `你好` 有 active case 时？ | **YES — 优先返回 Progress Card**，不显示普通主菜单 |
| `进度 / 继续 / 还差什么`？ | **YES — 强制走 status route**（高置信 status intent） |
| Phase 2 complete / broker review？ | **YES — 明确告知「不需要补资料，等待陈总」** |
| 多 open case？ | **One-flow-at-a-time** — 展示最新一笔；多笔时加一句转人工 |
| P19E-2 最小开发？ | WeCom routing + `build_add_vehicle_progress_card()` + status intent markers + pytest |
| 本轮代码变更？ | **无** |

**Verdict:** GO for P19E-2 implementation — smallest increment that fixes Andy 实测的「忘了自己在哪」问题，无需 App 首页或 H5 状态页。

---

## 2. Current UX Gap

### 2.1 What works (P19E-1.5 truth)

| Layer | Behavior | Status |
|-------|----------|--------|
| H5 三步照片 | VIN → registration → insurance/skip → 成功页 | ✅ |
| Stage Complete S1 | H5 `flow_complete` 后自动发 Phase 1 完成卡 | ✅ |
| Phase 2 字段提取 | `delivery_date` / `zip` / `phone` 写入 case | ✅ |
| Current Step Card | 部分字段收到后回进度 | ✅ |
| Stage Complete S2 | 三字段齐 → `ready_for_broker_review` | ✅ |
| Workbench | 附件 + collected fields 可见 | ✅ |
| 「重新加车」 | 显式开新 flow | ✅ |

### 2.2 What fails (Andy 实测 + 代码路径审计)

| 用户行为 | 当前系统行为 | 用户感受 |
|----------|--------------|----------|
| Phase 1 进行中，说「你好」 | `unclear` → **普通主菜单** | 「我还在上传照片吗？系统怎么让我选理赔？」 |
| Phase 1 进行中，说「继续」 | 同上（无 status intent） | 「继续什么？链接在哪？」 |
| Phase 2 进行中，说「你好」 | Phase 2 handler → **格式提示**（未识别字段） | 比主菜单好，但**没有总进度 framing**，像被骂格式不对 |
| Phase 2 完成 / broker review，说「你好」 | **普通主菜单** | 「是不是已经交给陈总了？为什么还要我选加车？」 |
| Phase 2 完成，说「进度 / 还差什么」 | **普通主菜单** 或无关回复 | 「我明明都交了，系统还说要选事项」 |
| 用户忘记 H5 链接 | 无统一「继续上传照片」入口（除非再说「我要加车」且 high-confidence） | 摩擦高 |
| 多个 open add_car case | `find_open_add_car_case` 返回**第一笔**（列表顺序依赖） | 可能看错 case |

### 2.3 Root cause (architecture)

```text
Today:
  WeCom routing = intent-first (add_car / claim / unclear)
                  → active case is a side effect, not the default "home"

Spark / gig apps:
  App open     = active task first
  Chat open    = (we don't have this layer)

Missing layer:
  "What is my current add_vehicle task state?" → single Progress Card builder
  invoked BEFORE generic greeting menu when open add_car case exists
```

**关键代码事实（P19E-2 不改，仅引用）：**

- `你好` → `intent.py` `_GENERIC_VAGUE_MARKERS` → `unclear` / `low` → `build_guided_menu_payload()`（`slice.py` L753–801）
- Phase 2 handler **仅在** `should_handle_phase2_incoming_text()` 为 true 时拦截；broker review 后 `phase2_text_is_complete` → **不拦截**
- 「我要加车」high-confidence 在 photo complete 时会走 `_build_add_car_h5_start_menu` → 重发 S1，**不是**统一进度卡
- 已有卡片是 **事件驱动**（S1/S2/Current Step），不是 **查询驱动**（用户问「进度」）

### 2.4 Questions A — 当前应如何回答

| # | 问题 | 推荐行为 |
|---|------|----------|
| A1 | 有 active add_car case 时说「你好」 | **返回 Progress Card**，不显示主菜单 |
| A2 | 说「进度 / 继续 / 还差什么 / 我现在到哪了」 | **强制 status route** → 同一 Progress Card（可略详） |
| A3 | Phase 2 complete / broker review | **明确：不需要补资料，陈总确认中** |
| A4 | Phase 1 complete, Phase 2 incomplete | **列出已收 / 还差字段 +「请在本聊天打字」** |
| A5 | Phase 1 incomplete | **列出还差照片 slot +「继续上传照片」按钮（H5 link）** |
| A6 | 多个 open add_car case | **展示最新一笔** + 文案「如有多台车在办理，请联系陈总」 |

---

## 3. Big-company Best Practice

### 3.1 Gig / delivery apps (Spark, DoorDash, Uber Eats, Instacart, Amazon Flex)

| Pattern | What they do | Relevance to CaseIQ |
|---------|--------------|---------------------|
| **Active task banner** | App 首页顶部常驻当前 batch / delivery | 我们没有 App → **WeCom 聊天 = 首页** |
| **Step checklist** | ✓ 已取货 → ▶ 配送中 → ○ 完成 | 映射到 **3-phase checklist**（照片 / 文字 / 陈总） |
| **Resume without restart** | Spark: 关闭 shopping list 可 reopen 继续 | 映射到 **Progress Card + H5 deep link** |
| **Binary step state** | 每步 done / not done，不同时说完成和还差 | P19E-0 已采纳；Progress Card 延续 |
| **Primary CTA** | 每屏一个主动作（Navigate / Complete delivery） | Phase 1 → 继续上传；Phase 2 → 打字；Phase 3 → 无需操作 |
| **Completed task** | 只读摘要 +「No action needed」 | broker review 状态 |
| **Multi-task** | 通常一次一个 active gig；历史在 Earnings | **One-flow-at-a-time** 足够 pilot |

**Spark Driver 要点（官方 FAQ）：** 用户可关闭 shopping list 后 **reopen and pick up where you left off**；设备重启不丢 trip progress。本质是 **session + state rehydration on demand** — 我们应在 WeCom 用 **on-demand Progress Card** 模拟，而非要求用户记 H5 链接。

### 3.2 KYC / 银行开户 / 驾照验证

| Pattern | Example | Our mapping |
|---------|---------|-------------|
| Progress dashboard | 「3/5 已完成」 | 3 customer-facing phases |
| Section lock | 未完成的步骤可点，已完成灰显 | ✓ 第 1 步 / ▶ 第 2 步 |
| Resume CTA | 「继续验证」 | 「继续上传照片」/「继续补充文字」 |
| Submitted / pending | 「审核中，无需操作」 | Phase 3 broker review |
| Resubmit | 「请重新上传模糊照片」 | V1.1 broker Recovery Card |

### 3.3 微信生态（小程序 / 微保 / 平安）

| Pattern | Example | Our mapping |
|---------|---------|-------------|
| 待办卡片 | 服务通知 +「继续办理」 | WeCom Progress Card + view button |
| 进度页 H5 | 保单服务「办理进度」 | **V1.1** — pilot 先用聊天卡 |
| 一步一屏 | 表单 wizard | 已有 H5 photo wizard |
| 完成后只读 | 「已提交，1-3 工作日」 | S2 + broker review copy |

### 3.4 Synthesis — 6 场景的通用规则

| Scenario | Best practice |
|----------|---------------|
| 中断后回来 | **Rehydrate state before menu** — 先展示任务，再提供 escape（联系经纪人 / 其他事项折叠在 tail） |
| 忘记步骤 | **Checklist + current step marker (▶)** |
| 点击「继续」 | **Same as status query** — 一条路由 |
| 已完成又打开 | **Read-only summary + no CTA**（或仅「联系陈总」） |
| 多任务 | **One primary + human escalation** for edge cases |
| 错误恢复 | **Scoped message** — 只说当前 phase 缺什么，不重置整个 flow |

---

## 4. Resume Card vs Status Card vs Task Home

### 4.1 方案对比

| 维度 | 方案 1 Resume Card | 方案 2 Status + CTA | 方案 3 Task Home H5 | 方案 4 Hybrid |
|------|-------------------|---------------------|---------------------|---------------|
| 用户问「进度」 | ✅ | ✅ | ✅（需打开链接） | ✅ |
| Phase 1 继续照片 | ⚠️ 仅文字 | ✅ H5 按钮 | ✅ | ✅ |
| broker review 等待态 | ⚠️ 名称误导 | ✅ | ✅ | ✅ |
| 开发量 | 小 | 小–中 | **大**（新 H5 页） | 中 |
| 符合 paid pilot 约束 | ✅ | ✅ | ❌ 本轮禁止 H5 表单/首页 | ✅ |
| 聊天内闭环 | ✅ | ✅ | ❌ 跳出 | ✅ |
| Spark 级状态感 | 中 | **高** | 最高 | 高 |

### 4.2 命名判断

| 名称 | 问题 | Verdict |
|------|------|---------|
| **Resume Card** | 暗示「中断后继续」；broker review / done 不是 resume | ❌ 作总称不准确 |
| **Status Card** | 准确但缺动作感 | ⚠️ 可作一半 |
| **Progress Card / 进度卡** | 覆盖查询、继续、等待 | ✅ **推荐对外** |
| **Status / Progress Card** | 内部统称 | ✅ **推荐工程名** |

### 4.3 Paid pilot 推荐

**选方案 2 + 4 轻量混合：**

- **默认载体：** WeCom `【加车资料进度】` Progress Card（text 或 msgmenu）
- **结构化动作：** Phase 1 用现有 H5 view button；Phase 2 用「请直接打字」；Phase 3 无按钮或仅「联系经纪人」
- **不做：** 独立 Persistent Task Home H5（留给 V1.1）

**理由：** 在「不写 H5 表单 / 不做小程序」约束下，WeCom Progress Card 是 **ROI 最高的状态层**；H5 继续只做照片 capture，不抢「首页」职责。

---

## 5. Recommended MVP

### 5.1 设计原则（继承 P19E-0）

1. **先任务，后菜单** — 有 open add_car case 时，status 查询优先于 generic greeting
2. **一张卡回答五个问题** — 当前任务 / 当前步骤 / 已完成 / 下一步 / 要不要我操作
3. **每 phase 一个 primary CTA** — 无 CTA 时显式写「目前不需要您操作」
4. **与 S1/S2/Current Step 共存** — Progress Card 是 **查询视图**，不替代事件驱动的 Stage Complete 消息
5. **不重复刷屏** — 同一 msg_id dedup；用户 5 分钟内重复问可回短版（V1.1）

### 5.2 路由优先级（P19E-2 建议插入点）

```text
1. Start Card clicks
2. Premium / Claim / Coverage minimal lanes
3. Phase 2 text collection（含可解析字段的消息 — 保持 P19E-1 行为）
4. ★ NEW: Status / Progress inquiry OR (active add_car + vague greeting)
      → build_add_vehicle_progress_card()
5. Draft merge / add_car H5 Start
6. Generic greeting menu（仅当 no active add_car case）
```

### 5.3 `你好` 是否优先查 active case？

**YES**，条件：

- `find_open_add_car_case_by_external_userid()` 有值
- case `case_status != closed`
- 用户消息属于 **vague greeting**（`你好` / `在吗` / `hi` 等）
- **不**覆盖：显式 `重新加车`、high-confidence 其他 lane（理赔/停保优先）

**Tail 折叠菜单（可选）：** Progress Card 末尾一行「办理其他事项请回复：理赔 / 保单 / 其他」— **不**用完整 msgmenu 抢主视觉。

### 5.4 `进度 / 继续 / 还差什么` 是否强制 status route？

**YES** — 新增 `status_inquiry` intent（high confidence），markers 示例：

```text
进度, 查进度, 什么进度, 到哪了, 哪一步, 还差什么, 还差, 缺什么,
继续, 继续办, 继续上传, 还没完, 完成了吗, 好了吗, 交了吗
```

与 Phase 2 字段提取 **分流规则：**

- 消息 **仅** status marker、无可解析 date/zip/phone → Progress Card
- 消息 **同时** 含字段 + status 词 → **先提取字段**，再附短 progress 行（或仅 Current Step — 实现时二选一，推荐先提取）

### 5.5 有 active case 时是否还显示主菜单？

**NO** 作为默认回复。  
**例外：** 用户明确说「其他问题」「理赔」等 → 走对应 lane 或 secondary_topic_deferred。

---

## 6. State-to-Card Mapping

### 6.1 状态推导（无 schema migration）

从现有字段 derive，不强制新 DB 列：

| Customer state | Derive from |
|----------------|-------------|
| Phase 1 in progress | open add_car + `NOT h5_photo_flow_is_complete(case)` |
| Phase 1 complete | `h5_photo_flow_is_complete` + Phase 2 incomplete |
| Phase 2 partial | 同上 + `collected_fields` 非空子集 |
| Phase 2 complete / broker review | `phase2_text_is_complete` OR `guided_workflow_state == ready_for_broker_review` |
| Broker done | `case_status in (confirmed, closed)` OR B0 Done Card sent |
| No active case | no open add_car for external_userid |

优先使用已有 `add_vehicle_phase`（若已写）；否则 fallback derive。

### 6.2 六情况映射表

| # | State | Primary CTA | Card type |
|---|-------|-------------|-----------|
| 1 | Phase 1 photos in progress | 继续上传照片 (H5 view) | Progress + CTA |
| 2 | Phase 1 done, Phase 2 not started | 请直接打字 | Progress |
| 3 | Phase 2 partial | 请继续打字 | Progress |
| 4 | Phase 2 complete / broker review | **无** — 等待陈总 | Progress (read-only) |
| 5 | Broker done | Done 摘要 | True End / read-only |
| 6 | No active case | 主菜单 | Guided menu |

---

## 7. Recommended WeCom Copy

### 7.1 情况 1 — Phase 1 photos in progress

```text
【加车资料进度】

▶️ 第 1 步：上传照片
还差：
○ VIN 照片
○ 行驶证照片
○ 保险卡照片（可选）

请点击下方按钮继续上传。

[继续上传照片]  [联系经纪人]
```

*注：○ 项按 `_completed_h5_slots` / `_skipped_h5_slots` 动态生成；已收的改 ✓。*

### 7.2 情况 2 — Phase 1 complete, Phase 2 incomplete (zero text fields)

```text
【加车资料进度】

✅ 第 1 步：照片资料已收到
▶️ 第 2 步：补充文字信息

还差：
○ 提车日期
○ 停放 ZIP
○ 联系电话

请直接在本聊天打字回复。
```

### 7.3 情况 3 — Phase 2 partially complete

```text
【加车资料进度】

✅ 第 1 步：照片资料已收到
▶️ 第 2 步：补充文字信息

已收到：
✓ 停放 ZIP — 92705

还差：
○ 提车日期
○ 联系电话

请继续在本聊天打字回复。
```

### 7.4 情况 4 — Phase 2 complete / broker review

```text
【加车资料进度】

✅ 第 1 步：照片资料已收到
✅ 第 2 步：文字信息已收到
▶️ 第 3 步：陈总人工确认中

目前不需要您补充资料。
陈总会人工查看，不会自动修改您的保单。
确认后我们会通过微信或电话跟进。
```

### 7.5 情况 5 — Broker done

复用 B0 Done Card（`陈奎团队已收到您的请求…`）或：

```text
【加车资料进度】

✅ 您的加车请求陈总已确认收到
我们会跟进后续步骤，请留意微信或电话。

如有新问题，可直接回复「我要加车」开始新的资料收集。
```

### 7.6 情况 6 — No active case

现有 guided menu（不变）：

```text
您好，请选择您要办理的事项：
…
```

### 7.7 Status inquiry 与 greeting 的统一

**同一张卡** — `进度` 与 `你好`（有 active case）输出一致，避免两套 copy 漂移。

---

## 8. H5 / Workbench Implications

### 8.1 H5（本轮最小）

| Item | P19E-2 | V1.1 |
|------|--------|------|
| 新状态页 | ❌ | 可选「查看进度」静态页 |
| 成功页 progress bar | 已有 P19E-0 建议 | 保持 |
| H5 reopen 同一 case token | ✅ 复用 `mint_h5_add_vehicle_photo_flow_link` | — |
| 「返回微信」后提示 | 可加一句「回聊天说「进度」可随时查看」 | copy only |

### 8.2 Workbench（本轮禁止大改）

| Item | P19E-2 | V1.1 |
|------|--------|------|
| Broker 看 customer phase | 已有 `add_vehicle_phase` / collected_fields | 可选只读 badge |
| 「发给客户进度卡」按钮 | ❌ | broker 触发 Recovery / Progress |
| Timeline event `progress_card_sent` | 可选 log | 正式 event |

### 8.3 与现有卡片关系

```text
Event-driven (keep):
  S1 on H5 complete
  Current Step on each Phase 2 field
  S2 on Phase 2 complete
  Done on broker Confirm

Query-driven (new):
  Progress Card on greeting / status inquiry / (optional) 「我要加车」when case exists
```

**不重复发 S1：** Progress Card 在 broker review 状态 **不得** 再触发 `try_send_h5_photo_flow_end_card`。

---

## 9. Edge Cases

| Edge | Handling |
|------|----------|
| Phase 2 进行中用户说「你好」 | Progress Card（情况 2/3），**不是** format hint |
| Phase 2 进行中用户说「你好，ZIP 92705」 | 先字段提取 → Current Step（P19E-1 优先） |
| Photo 未完成用户说「进度」 | 情况 1 + H5 CTA |
| `重新加车` | **不**走 Progress Card；现有 new case + Start Card |
| 用户说「我要加车」且已有 open case | **Progress Card** 或 S1 重发 — **推荐 Progress Card**（避免 S1 刷屏） |
| 多 open add_car | 展示 **newest** `created_at`；tail：「多台车同时办理请联系陈总」 |
| stale binding / Postgres miss | 保持 P19E-1.5 read facade；miss 时 honest「未找到进行中资料」+ 主菜单 |
| broker 要求补件（未来） | V1.1 Recovery Card；Progress Card 显示 broker-requested gaps |
| 用户连发 3 次「进度」 | MVP：同内容；V1.1：短版「仍在第 X 步，无需重复提交」 |
| Phase 3 用户问「还差什么」 | 「目前不需要补充；陈总确认中」 |
| coverage_risk 与 add_car 并存 | coverage_risk lane **优先**（安全） |

---

## 10. MVP Implementation Plan

**Sprint name:** P19E-2 — Add Vehicle Progress Card  
**Est:** 1–1.5 dev days + 15 min phone smoke

### 10.1 In scope

| # | Change | Layer |
|---|--------|-------|
| 1 | `derive_add_vehicle_customer_phase(case)` | `add_vehicle_phase2.py` 或新 `add_vehicle_progress.py` |
| 2 | `build_add_vehicle_progress_card(case)` — 6 状态 copy + dynamic slots/fields | `reply.py` |
| 3 | Phase 1 CTA: msgmenu with `mint_h5_add_vehicle_photo_flow_link` | `reply.py` + `slice.py` |
| 4 | `status_inquiry` intent markers | `intent.py` |
| 5 | Routing: before generic greeting; active case + vague greeting | `slice.py` |
| 6 | `should_handle_phase2`: vague-only messages → **false**（改由 Progress Card 处理） | `add_vehicle_phase2.py` |
| 7 | pytest: 6 states × copy + routing priority | `tests/` |

### 10.2 Explicit non-scope（本轮禁止）

- OCR / VIN 识别展示
- 小程序
- H5 状态首页 / H5 表单
- claim / premium / coverage flow 改造
- schema migration / Cloud config
- Workbench 大改
- 24h 自动 reminder
- 多 case 选择 UI

### 10.3 Acceptance criteria

1. Andy：Phase 1 半途 → 「你好」→ 进度卡 + 继续上传按钮（**非**主菜单）
2. Andy：Phase 2 半途 → 「还差什么」→ 列出已收/还差（**非**格式报错）
3. Andy：S2 后 → 「进度」→ 陈总确认中、无需补资料
4. Andy：无 case → 「你好」→ 原主菜单
5. 「重新加车」行为不变
6. 不重复发送 S1/S2

---

## 11. V1.1 / V2

### 11.1 V1.1

| Feature | Value |
|---------|-------|
| H5 轻量「查看进度」静态页（只读，无表单） | 链接可放进 Progress Card tail |
| Progress Card 短版 dedup（5 min 内重复查询） | 减噪 |
| Phase 2 idle 24h nudge | 运营 |
| Broker「请补 XX」→ Recovery Card | 双向 loop |
| Workbench 一键「发送进度给客户」 | broker 工具 |
| insurance_card 晚补 slot | 单 slot H5 |

### 11.2 V2

| Feature | Trigger |
|---------|---------|
| 微信小程序任务首页 | 链接信任 / 规模 |
| 多车并行 case picker | >N 多车家庭 |
| 客户 case ID / 手机号查进度 | 无 WeCom 历史 |
| OCR draft（broker-only） | P19C+ |
| 全 lane Progress Card | claim / premium 统一状态层 |

---

## 12. Final Recommendation

| Decision | Verdict |
|----------|---------|
| Resume Card 是最佳 MVP 吗？ | **概念上接近，但名称用 Progress Card；形态是 Status + CTA，不是纯 Resume** |
| 推荐名称 | 对外 **「加车资料进度」**；对内 **`AddVehicleProgressCard`** |
| 最推荐方案 | **方案 2 + 4 混合** — WeCom Progress Card + Phase 1 H5 button |
| 「你好」先查 active case？ | **YES** |
| 「进度 / 继续 / 还差什么」 | **强制 status route** → 同一 Progress Card |
| 有 active case 还显示主菜单？ | **NO**（默认）；其他事项走 tail 或显式 intent |
| 比 Resume Card 更丝滑？ | 长期：**H5 只读进度页 + 小程序**；pilot 内 **WeCom Progress Card 已足够** |
| P19E-2 最小范围 | §10.1 七项 |
| 本轮代码 | **无** |

---

## Appendix A — Current vs Target Routing (ASCII)

```text
TODAY (simplified):
  你好 + open add_car (Phase 1) ──→ [主菜单]  ✗
  你好 + open add_car (Phase 2)   ──→ [格式提示] △
  你好 + broker review            ──→ [主菜单]  ✗

TARGET (P19E-2):
  你好 / 进度 / 继续 + open add_car ──→ [Progress Card + CTA?]
  你好 + no case                    ──→ [主菜单]
  重新加车                          ──→ [新 Start Card]  (unchanged)
```

## Appendix B — Code touchpoints (reference for P19E-2 — do not change in this recon)

| File | Role |
|------|------|
| `services/fiqa_api/wecom/slice.py` | Insert Progress route before greeting |
| `services/fiqa_api/wecom/intent.py` | `status_inquiry` markers |
| `services/fiqa_api/wecom/reply.py` | `build_add_vehicle_progress_card()` |
| `services/fiqa_api/wecom/add_vehicle_phase2.py` | Phase derive helpers; adjust `should_handle_phase2` |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | `h5_photo_flow_is_complete`, slot sets |
| `services/fiqa_api/wecom/active_case_bridge.py` | `find_open_add_car_case_by_external_userid` |

---

*P19E-2 recon complete. Ready for implementation sprint.*
