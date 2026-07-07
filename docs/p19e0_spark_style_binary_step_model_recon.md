# P19E-0 — Spark-style Binary Step Model for Add Vehicle Flow

**Date:** 2026-07-06  
**Type:** Product / architecture recon — **documentation only**  
**Audience:** Andy, Chen Kui demo team, P19E implementation agents  
**Prerequisite:** P19D-4A (H5 continuous photo flow) ✅ · P19D-4B (WeCom Start/End Card completion loop) ✅ · P19D-4B.1 (End Card live send + restart flow) ✅  
**Related:** `p19d_core_step_by_step_evidence_capture_doctrine.md`, `p19_guided_workflow_start_end_card_recon.md`, `p19d4b_wecom_start_end_card_ux_recon.md`

**This loop:** No code. No deploy. No WeCom / H5 / Workbench changes.

---

## 1. Executive Summary

P19D-4A/B closed the **operational loop**: WeCom → H5 三步照片 → 回微信 → 自动确认消息 → Workbench 可见附件 → 「重新加车」可开新 flow。

Andy 最新产品判断：闭环已通，但存在 **方向性 UX 问题** — 当前 WeCom 消息在语义上混用了「完成 ✅」与「还差 3 项」，让用户无法二元判断「我到底完成了没有」。

| Question | Answer |
|----------|--------|
| 核心问题是什么？ | **End Card 命名与语义过早** — 「照片已收到 ✅」+「还差 3 项」在同一消息里，造成「结束 vs 未结束」的认知冲突 |
| 应改什么？ | 把 P19D-4B 的 `E2-photo End Card` **重命名/重语义** 为 **Stage Complete Card（第 1 阶段完成）** + **Next Step Card（当前动作）** |
| Add Vehicle 应拆几个 phase？ | **3 个 customer-facing phase**：照片收集 → 文字信息补齐 → 经纪人确认 |
| 真正 End Card 何时出现？ | Phase 3 broker review 完成后（或 Phase 2 资料收齐转 broker queue 时发 E1），**不是** Phase 1 照片完成时 |
| 是否进入 P19E-1？ | **GO** — P19E-1 Text Field Collection Loop 是最小下一 increment |
| P19E-0 代码变更？ | **无** |

**Binary step doctrine (carry forward):**

```text
每一步 = 一个明确任务
每一步 = done / not done（无二义）
完成一步 → 明确下一步（不混合「完成了」和「还差」）
用户永远只看到一个「当前动作」
```

---

## 2. Current UX Problem

### 2.1 What shipped (P19D-4A/B truth)

| Layer | Current behavior | Status |
|-------|------------------|--------|
| WeCom 入口 | 「我要加车」/ 「重新加车」→ H5 Start Card | ✅ |
| H5 | VIN → registration → insurance/skip → 成功页 | ✅ |
| H5 成功页 | 「照片已收到 ✅」+ 返回微信 + 文字字段提示 | ✅ |
| WeCom 自动消息 | `build_h5_photo_phase_complete_reply()` — 代码注释仍称 **E2-photo End Card** | ✅ 功能通，❌ 语义错 |
| Workbench | `source=h5_task` 附件可见 | ✅ |
| 重新加车 | 开新 case + 新 H5 flow | ✅ |
| 文字字段收集 | 用户可打字，但 **无 Stage Complete 闭环** | ❌ gap |
| Broker review End | B0 `DONE_CARD_TEXT` — broker Confirm 后才发 | ✅ 但未与 phase model 对齐 |

### 2.2 The directional problem

P19D-4B 解决了 **「H5 完成后微信里没有消息」** 的信任阻断（P0）。  
P19E-0 解决的是 **「消息到了，但用户不知道这意味着什么」** 的心智负担（P0→P1 升级，但直接影响 pilot 演示质量）。

当前 shipped copy（`services/fiqa_api/wecom/reply.py`）：

```text
【加车资料】照片已收到 ✅

我们已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片

还差 3 项，请在本聊天打字：
1. 提车日期
2. 停放 ZIP
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
资料齐全后我们会再通知您。
```

H5 成功页 headline 同样是「照片已收到 ✅」，副标题「此照片上传流程已完成」—— 比 WeCom 稍好，但仍缺 **总进度 framing**。

### 2.3 User mental model failure modes

| 用户困惑 | 根因 |
|----------|------|
| 「我到底完成了没有？」 | ✅ 与「还差 3 项」同屏出现 |
| 「这个 End Card 是结束，还是没结束？」 | 产品内部称 End Card，用户读成「流程结束」 |
| 「是加车完成，还是照片阶段完成？」 | 无 phase 编号 / 总进度条 |
| 「我现在该等，还是该继续输入？」 | 没有单一 **当前动作** CTA |
| 「陈总收到了吗？」 | P19D-4B 已解决 — 但确认消息的 framing 仍模糊 |

---

## 3. Why Current End Card Causes Ambiguity

### 3.1 Naming collision

| Term (internal) | User reads as | Actual meaning |
|-----------------|---------------|----------------|
| **End Card** | 整个加车结束 | 仅 Phase 1（照片）完成 |
| **照片已收到 ✅** | 全部资料 OK | 仅 photo slots complete |
| **资料齐全后我们会再通知您** | 我现在不用做了 | 实际还需打字 3 项 |
| **E2-photo End Card** (code comment) | — | 准确是 partial complete，不是 terminal |

P19B-0 recon 早已定义 End Card 类型矩阵（§2.1）：

- **E1 — Materials complete** → 真正资料收齐
- **E2 — Partial complete** → 还缺项
- **E7 — Broker confirmed** → B0 Done Card

P19D-4B 实现的 `build_h5_photo_phase_complete_reply()` 本质是 **E2 partial**，却被命名为 **End Card**。这是 **taxonomy 错误**，不是 copy 微调问题。

### 3.2 Violation of binary step principle

Spark / DoorDash / KYC 的共同规则：

> **Never say "done" and "still needed" in the same breath for the same scope.**

当前消息结构：

```text
[SCOPE A: photos]  DONE ✅
[SCOPE B: text fields]  NOT DONE — 还差 3 项
```

两个 scope 混在一条「End Card」里。用户无法回答二元问题：「照片步骤完成了吗？」→ 是；「加车资料收集完成了吗？」→ 否 — **但文案没有帮用户区分这两个 scope**。

### 3.3 Should it still be called End Card?

| Candidate name | Fit | Verdict |
|----------------|-----|---------|
| End Card | Implies terminal | ❌ 过早 |
| Photo Stage Complete Card | Phase 1 done, explicit | ✅ **推荐** |
| Next Step Card | Emphasizes forward action | ✅ 可作为同一条消息的 **下半段** |
| Phase Transition Card | Accurate, slightly jargon | ✅ 内部 / Workbench 用语 |
| Current Step Card | For in-progress, not post-complete | 用于 Phase 2 进行中 |

**结论：** P19D-4B 产物应 **降级/重命名** 为 **Stage Complete Card (Phase 1)** | S1-Done)**，不是 End Card。

### 3.4 When should the true End Card appear?

| Trigger | Card type | Customer message essence |
|---------|-----------|--------------------------|
| H5 `flow_complete` | **Stage Complete S1** — NOT End | 「第 1 阶段完成：照片 ✅ → 下一步：补文字」 |
| All text fields collected | **Stage Complete S2** + E1 handoff | 「第 2 阶段完成：文字 ✅ → 已转陈总确认」 |
| Broker Confirm (B0) | **True End Card E7** | 「陈奎团队已收到您的请求，我们会跟进后续步骤」 |
| Broker requests more info | **Recovery Card** | 「陈总还需要：{missing} — 请回复」 |
| Broker closes / manual handle | **True End Card variant E3** | 「已转人工处理，会电话/微信跟进」 |

**Invariant:** True End Card = **no further customer action expected** OR **broker has acknowledged receipt at case level**. Photo complete alone does not qualify.

---

## 4. Spark / DoorDash / KYC Binary Step Principles

### 4.1 Reference model

| Principle | Spark Driver | DoorDash / Flex | Jumio KYC | 微保理赔 | CaseIQ target |
|-----------|--------------|-----------------|-----------|----------|---------------|
| 每步是明确任务？ | ✅ scan barcode / verify item | ✅ upload doc type X | ✅ scan front / back | ✅ 按清单逐步 | ✅ 当前 slot / 当前字段 |
| 每步有 done/not done？ | ✅ checklist ✓/○ | ✅ onboarding step status | ✅ pass/fail/retry | ✅ 材料状态 | ✅ phase + step status |
| 完成后自动进下一步？ | ✅ in-app advance | ✅ in-app advance | ✅ wizard next | ✅ 小程序下一步 | ✅ H5 in-session; WeCom for text |
| 避免「完成+还差」同屏？ | ✅ milestone 分开发 | ✅ modular onboarding | ✅ per-part result | ✅ 分材料确认 | ❌ **当前违反** → P19E fix |
| 异常状态？ | Reject + retake reason | Re-upload doc | REJECT_VIEW | 补传入口 | Recovery Card + resume link |
| 中断后恢复？ | Same batch resume | Continue onboarding | Same session token | 案件进度页 | H5 resume + WeCom「继续加车」 |
| 完成后 confirmation？ | Push + in-app badge | Email milestone | Server-side notify merchant | 进度推送 | WeCom Stage Complete（权威） |

### 4.2 Spark Driver checklist anatomy (borrow)

```text
Overall: Add Vehicle to Policy (3 phases)

Phase 1 — Photos          [====------]  IN PROGRESS → DONE
  Step 1.1 VIN photo      ✓
  Step 1.2 Registration   ✓
  Step 1.3 Insurance card ○ skipped

Phase 2 — Text info       [----------]  NOT STARTED
  Step 2.1 Delivery date  ○
  Step 2.2 ZIP            ○
  Step 2.3 Phone          ○

Phase 3 — Broker review   [----------]  LOCKED
```

Spark 从不把 Phase 1 done 说成「onboarding complete」。CaseIQ 应对齐。

### 4.3 Binary state machine rule (formal)

For every customer-facing message `M` at time `t`:

1. **Current action** `A(t)` — exactly one primary verb phrase（「请上传 VIN」「请回复提车日期」）
2. **Scope completion** `C(scope)` — boolean; if true, message must not use ambiguous「完成」without scope label
3. **Next action** `A(t+1)` — always stated when `C(current_scope)` is true
4. **Forbidden:** `C(phase) = false` AND headline contains ✅ +「已收到」without phase qualifier

---

## 5. Recommended Add Vehicle Phase Model

### 5.1 Three-phase transaction split

| Phase | Customer-facing name | Start | Done (binary) | Next |
|-------|---------------------|-------|---------------|------|
| **Phase 1 — 照片资料收集** | 第 1 步：上传照片 | Start Card → H5 | 3 photo slots submitted (insurance optional/skipped) | 回微信 → Stage Complete S1 |
| **Phase 2 — 文字信息补齐** | 第 2 步：补充文字信息 | Stage Complete S1 的 Next Step | delivery_date + zip + phone all received | Stage Complete S2 → broker queue |
| **Phase 3 — 经纪人确认** | 第 3 步：陈总人工确认 | E1 handoff message | Broker Confirm / manual handle / closed | True End Card E7/E3 |

**Verdict:** 三 phase 拆法 **合理且必要**。与 P19B-0 canonical flow（Start → slots 1–3 → text → broker → End）一致，只是把 **customer-facing framing** 从 implicit checklist 升级为 **explicit phase boundaries**。

### 5.2 Phase 1 internal steps (H5 — already shipped)

| Step | Slot | Required | Binary done |
|------|------|----------|-------------|
| 1.1 | `vin_photo` | Yes | attachment `received` |
| 1.2 | `registration_photo` | Yes | attachment `received` |
| 1.3 | `insurance_card_photo` | Optional | `received` OR `skipped` |

Phase 1 done = `h5_photo_flow_is_complete(case) == true` (existing).

### 5.3 Phase 2 fields (WeCom chat — P19E-1 target)

| Field | Extract | Required for Phase 2 done |
|-------|---------|---------------------------|
| `delivery_date` | `extract_delivery_date_from_text` | Yes |
| `zip` | zip extractor | Yes |
| `phone` | phone extractor (may need add) | Yes — **pilot MVP** |

**Note:** B0 draft path also tracks `vin`, `primary_driver`, `year`, `make_model`. For **H5-first Add Vehicle path**, Phase 2 MVP scope should be **exactly the 3 fields promised in Start Card tail** — not expand silently to full draft checklist. Broker can request more via Recovery Card.

**Phase 2 done** = all 3 fields in `collected_fields` AND none in `still_needed_fields` for `{delivery_date, zip, phone}`.

### 5.4 Phase 3 (Workbench — mostly exists)

| Broker action | Customer message | `guided_workflow_state` |
|---------------|------------------|-------------------------|
| Opens case | (optional) 「陈总正在查看」| `broker_reviewing` |
| Confirm (B0) | True End E7 | `confirmed` |
| Mark manual handle | E3 | `manual_handle` |
| Request clearer photo | Recovery Card | `needs_customer_input` |

---

## 6. Card Taxonomy

Replace monolithic「End Card」with six card types:

### 6.1 Start Card

**When:** User says「我要加车」/ taps 加车 / 「重新加车」  
**Purpose:** Open flow; show **total progress overview**; one primary CTA  
**NOT:** Imply any step is done

```text
【加车资料收集】

进度：
① 上传照片  ← 当前
② 补充文字信息
③ 陈总人工确认

请点下方按钮，按顺序上传 3 张照片…
[开始上传照片]  [稍后]  [联系经纪人]
```

### 6.2 Current Step Card

**When:** Mid-flow nudge (optional P19E+); Phase 2 partial progress  
**Purpose:** One action only; show ✓/○ for **current phase** sub-steps

```text
【加车资料 · 第 2 步】

请补充文字信息（还差 2 项）：
✓ 提车日期 — 7月10日
○ 停放 ZIP — 请回复
○ 联系电话 — 请回复

直接在本聊天打字即可。
```

### 6.3 Stage Complete Card

**When:** A **phase** reaches done; NOT whole transaction  
**Purpose:** Celebrate scoped completion; **separate block** from next action  
**Structure:** Two visual blocks (or two messages — see §7)

```text
【第 1 阶段完成 ✅】
照片资料已收到：
✓ VIN 照片
✓ 行驶证照片
○ 保险卡 — 可稍后补

──────────
【下一步 · 第 2 步】
请在本聊天打字发送 3 项：
1. 提车日期
2. 停放 ZIP
3. 联系电话
```

**Key change from P19D-4B:** Headline is **「第 1 阶段完成」**, not「照片已收到 ✅」alone as pseudo-end.

### 6.4 Next Step Card

**When:** Bundled with Stage Complete (MVP) or sent as follow-up if user idle  
**Purpose:** Single forward CTA — what to do **now**

Can be §6.3 lower block. Separate message only if UX testing shows users skip lower block.

### 6.5 True Final End Card

**When:** Phase 3 complete OR Phase 2 complete + E1 broker handoff (customer waiting)  
**Purpose:** Terminal or waiting-terminal; no「还差」

**E1 — Materials complete (pre-broker action):**

```text
【加车资料 · 已全部收齐 ✅】

我们已收到您的照片和文字信息，已转陈总人工确认。
不会自动修改您的保单。
确认后我们会通过微信或电话跟进。
```

**E7 — Broker Confirm (B0 existing):**

```text
陈奎团队已收到您的请求，我们会跟进后续步骤。
```

### 6.6 Error / Recovery Card

**When:** Upload fail, End Card send fail, mid-flow abandon, broker re-request  
**Purpose:** Explain what happened + one recovery action

```text
【需要您补充】
陈总查看后还需要：
· 更清晰的 VIN 照片

请点下方重新上传，或直接发新照片。
[重新上传 VIN]  [联系经纪人]
```

**H5 fallback (existing):** 「若 10 秒内没有看到确认消息，请回复：已提交」

---

## 7. Recommended Customer Flow

### 7.1 End-to-end (recommended)

```text
WeCom: 用户「我要加车」
  → Start Card（总进度 ①②③，当前=①）
  → H5: 三步照片（每步 binary done）
  → H5 成功页: 「第 1 阶段完成」 framing（非「加车完成」）
  → 用户点「返回微信」
  → WeCom: Stage Complete S1 + Next Step（第 2 步文字）
  → 用户打字: 「提车 7/10，ZIP 92705，电话 949-xxx」
  → WeCom: Stage Complete S2 + E1 handoff（第 3 步等待 broker）
  → Workbench: broker review
  → WeCom: True End E7（broker Confirm 后）
```

### 7.2 Is this optimal?

**Yes**, for paid pilot constraints:

| Criterion | Assessment |
|-----------|------------|
| Binary clarity | ✅ Each phase has one done state |
| Minimal channel switches | ✅ H5 only for photos; WeCom for text (industry norm) |
| No schema migration | ✅ Uses existing `collected_fields`, `h5_photo_flow_state`, `guided_workflow_state` JSON |
| Broker gate preserved | ✅ No auto policy change language |
| Builds on shipped code | ✅ P19D-4B send path reused; copy + phase detection added |

**Alternative considered:** In-H5 form for text fields (date picker, ZIP input). **Rejected for MVP** — adds form UX, duplicates chat value, breaks「聊天=文字采集」channel split established in P19D-15.

**Alternative considered:** Three separate WeCom messages for S1 done + next step. **Optional V1.1** — test whether one structured message suffices.

---

## 8. Recommended WeCom Copy

### 8.1 Start Card (updated — add progress header)

```text
【加车资料收集】

进度：① 上传照片 → ② 补充文字 → ③ 陈总确认
当前：第 1 步 · 上传照片

请点下方按钮，按顺序上传 3 张照片：
1. VIN 照片
2. 行驶证 / registration
3. 保险卡（可选）

大约 2 分钟，不用填长表格。

[开始上传照片]  [稍后]  [联系经纪人]

照片在页面里上传；提车日期、ZIP、电话在第 2 步回微信打字。
陈总会人工审核，不会自动修改您的保单。
```

### 8.2 Stage Complete S1 (replaces P19D-4B End Card)

```text
【第 1 阶段完成 ✅ · 照片资料】

已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片
（或 ○ 保险卡 — 可稍后补）

──────────
【下一步 · 第 2 步：补充文字信息】
请直接在本聊天打字：
1. 提车日期（例：7月10日）
2. 车辆停放 ZIP（例：92705）
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
```

### 8.3 Current Step Card — Phase 2 partial (P19E-1)

```text
【加车资料 · 第 2 步进行中】

已收到：
✓ 提车日期 — 7月10日
✓ 停放 ZIP — 92705

还差 1 项：
○ 联系电话 — 请直接打字回复
```

### 8.4 Stage Complete S2 + E1 handoff

```text
【第 2 阶段完成 ✅ · 文字信息】

已收到：
✓ 提车日期
✓ 停放 ZIP
✓ 联系电话

──────────
【下一步 · 第 3 步：陈总人工确认】
资料已全部收齐，已转陈总审核。
不会自动修改您的保单。
确认后我们会通过微信或电话跟进，请留意消息。
```

### 8.5 True End E7 (B0 — unchanged)

```text
陈奎团队已收到您的请求，我们会跟进后续步骤。
```

### 8.6 Recovery — End Card not received

```text
【确认收到】
您的照片资料我们已收到（第 1 阶段完成 ✅）。
若上方没有看到完整提示，请继续补充：提车日期、ZIP、联系电话。
```

---

## 9. Recommended H5 Copy

### 9.1 Success page (flow_complete)

Replace headline「照片已收到 ✅」→ phase-aware:

```text
第 1 阶段完成 ✅
照片上传已完成

已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片（或 ○ 保险卡 — 可稍后补）

总进度：① 上传照片 ✓  →  ② 补充文字  →  ③ 陈总确认

请点「返回微信」。
回到聊天后，您会收到第 2 步指引。

[ 返回微信 ]

陈总会人工确认，不会自动修改您的保单。
若 10 秒内没有看到新消息，请回复：已提交
```

### 9.2 In-progress step pages (unchanged pattern)

Keep existing「第 X/Y 步」header — already Spark-aligned.

### 9.3 Forbidden H5 copy

| Forbidden | Why |
|-----------|-----|
| 「加车已完成」 | Policy not changed |
| 「VIN 已识别为 …」 | No OCR promise |
| 「保单即将更新」 | Broker gate |
| 「全部资料已收齐」（at H5 exit） | Text phase not done |

---

## 10. Recommended Workbench State Model

### 10.1 Dual-axis model (existing — align labels)

| Axis | Field | Purpose |
|------|-------|---------|
| Customer phase | `guided_workflow_state` + new `add_vehicle_phase` JSON | What customer sees |
| Broker queue | `case_status` | Queue position |

### 10.2 Proposed `add_vehicle_phase` (JSON on case — no migration)

| Value | Meaning | Customer card |
|-------|---------|---------------|
| `phase_1_photos_in_progress` | H5 flow open | Start / H5 |
| `phase_1_photos_complete` | `flow_complete`; text not started | Stage Complete S1 sent |
| `phase_2_text_in_progress` | 1–2 of 3 text fields | Current Step Card |
| `phase_2_text_complete` | All 3 text fields | Stage Complete S2 / E1 |
| `phase_3_broker_review` | `ready_for_broker_review` | Waiting copy |
| `phase_3_broker_done` | `confirmed` / `closed` | True End E7 |

**Implementation note:** Can derive from existing fields initially (`h5_photo_flow_is_complete` + `collected_fields` + `broker_confirmed_at`) — explicit `add_vehicle_phase` is optional denormalization for Workbench UI.

### 10.3 Workbench panel (broker-facing)

```text
Add Vehicle · Phase 2/3 — 文字已齐，待确认

Customer progress:
  [✓] Phase 1 Photos     — 3/3 slots
  [✓] Phase 2 Text       — date, zip, phone
  [○] Phase 3 Review     — awaiting broker

Attachments: [VIN] [Registration] [Insurance]
Collected: delivery 7/10 · ZIP 92705 · phone …
```

### 10.4 Timeline events (broker-readable)

| Event | Source |
|-------|--------|
| `phase_1_started` | Start Card / H5 open |
| `photo_slot_received` | H5 upload |
| `phase_1_complete` | `flow_complete` |
| `stage_complete_s1_sent` | WeCom auto message |
| `text_field_collected` | Chat extract |
| `phase_2_complete` | All 3 fields |
| `stage_complete_s2_sent` | WeCom auto message |
| `broker_confirmed` | B0 Confirm |

---

## 11. How We Can Match / Exceed Spark Driver

### 11.1 Where Spark is strong

- In-app binary checklist with locked future phases
- Zero ambiguity on step completion
- Resume from exact step
- Reject with reason → retake

### 11.2 Where we already match (post P19D-4A)

- H5 in-session multi-step with preview confirm
- Per-slot evidence binding
- Workbench attachment review
- No OCR / no auto policy change promise

### 11.3 Where we can exceed Spark

| Opportunity | Spark | CaseIQ advantage |
|-------------|-------|------------------|
| **Natural language intake** | Fixed forms only | User can type「明天提车 ZIP 92705」in one message — AI extracts + confirms |
| **Chat as home** | Push-only return | WeCom thread = persistent case memory + human broker |
| **Structured + conversational** | App OR chat, not both | H5 for photos (high structure) + chat for text (low friction) + AI for questions |
| **Human review gate** | Platform auto-approves docs | Broker Workbench — no false「approved」; insurance-appropriate |
| **Evidence timeline** | Driver sees own checklist | Broker sees full timeline with attachments + extracted fields |
| **Recovery without restart** | Re-open app | 「继续加车」/ 「重新加车」/ partial field nudge — chat-native |
| **Explainability** | Generic error codes | AI can answer「为什么要 ZIP？」in context of **this case** |
| **Multi-lingual casual input** | English forms | 中文口语 + 英文混合 — broker still gets structured Workbench |

### 11.4 Differentiation thesis

```text
Spark Driver  = Task execution machine (no conversation, no human broker)
CaseIQ        = Chat + Guided Task + Human Review + Case Memory

We don't need to beat Spark at in-app polish.
We win by being the only flow where:
  - customer asks questions anytime in WeChat
  - structured capture doesn't sacrifice conversational recovery
  - broker confirms before anything touches the policy
  - every step leaves auditable evidence
```

---

## 12. MVP Implementation Plan (P19E-1)

**Sprint name:** P19E-1 — Text Field Collection Loop  
**Goal:** Close Phase 2 binary loop; rename Phase 1 message semantics

### 12.1 P19E-1 scope (minimal)

| # | Change | Layer |
|---|--------|-------|
| 1 | Rename/reframe `build_h5_photo_phase_complete_reply()` → Stage Complete S1 copy (§8.2) | WeCom `reply.py` |
| 2 | Update H5 success page headline + progress bar (§9.1) | H5 UI |
| 3 | On WeCom text message during open add_car case: extract delivery_date, zip, phone | `active_case_bridge` / slice |
| 4 | After each text field: optional Current Step Card (partial progress) | WeCom reply |
| 5 | When all 3 text fields collected: send Stage Complete S2 + E1 (§8.4) | WeCom auto send |
| 6 | Set `guided_workflow_state → ready_for_broker_review` on Phase 2 complete | case JSON |
| 7 | Derive `add_vehicle_phase` for Workbench display (read-only label) | Workbench UI optional |
| 8 | Tests: phase transitions, copy assertions, no duplicate S2 send | pytest |

### 12.2 P19E-1 explicit non-scope

- OCR / VIN recognition display
- Schema migration / new DB tables
- 小程序
- In-H5 text form
- Claim / premium / coverage lanes
- Auto broker Confirm
- Expanding Phase 2 beyond 3 promised fields (vin/driver re-collection via Recovery only)

### 12.3 Acceptance criteria (P19E-1 Done)

1. Andy phone: 加车 → H5 三步 → 回微信 → 收到 **「第 1 阶段完成」** 消息（非 ambiguous End）
2. 用户打字 3 字段 → 收到 **「第 2 阶段完成」** + broker handoff
3. Workbench shows phase label + all attachments + collected fields
4. 「重新加车」still opens new flow
5. No forbidden phrases (§Product Rules)
6. No duplicate Stage Complete messages on refresh/re-entry

**Est:** 1.5–2 dev days + 15 min phone smoke

---

## 13. V1.1 / V2 Plan

### 13.1 V1.1 (post P19E-1 polish)

| Feature | Value |
|---------|-------|
| Start Card shows live progress on re-entry | Resume clarity |
| Split S1 into two WeCom messages if A/B shows users miss Next Step | Binary block separation |
| Phone number extractor hardening | Reduce partial Phase 2 |
| Workbench「Request missing field」→ Recovery Card to customer | Broker-initiated loop |
| `insurance_card` late upload via chat/H5 single slot | Optional slot recovery |
| Nudge if Phase 2 idle 24h | E2-style reminder with Current Step Card |

### 13.2 V2 (volume / compliance)

| Feature | Trigger |
|---------|---------|
| 微信小程序 | Link trust complaints |
| OCR draft (broker-only) | P19C+ |
| primary_driver / VIN text cross-check | Carrier requirement |
| Full checklist sidebar in H5 | Multi-vehicle batch |
| Customer-facing case status query「查进度」 | >20 cases/week |

---

## 14. Risks / Open Questions

| Risk | Mitigation |
|------|------------|
| User sends all 3 fields in one message | Extract all; send single S2 — **preferred UX** |
| User sends fields before H5 complete | Route to H5 Start Card first; don't collect text for incomplete Phase 1 |
| Duplicate Stage Complete on H5 re-open | Existing dedup `end_card_sent_at`; add `stage_s2_sent_at` |
| Phone extraction fails on Chinese formats | Explicit Recovery prompt; broker manual entry in Workbench |
| Conflict: B0 draft checklist has 5+ fields vs Phase 2 promise of 3 | **Decision:** H5 path Phase 2 = 3 fields only; expand only via broker Recovery |
| Two-message vs one-message S1 | Default one message with visual separator; A/B in pilot |
| `重新加车` mid Phase 2 | Already opens new case — document in Start Card tail |

**Open for Andy:**

1. Phase 2 是否 strictly 3 字段，还是加 `primary_driver`？
2. Phase 2 部分完成时是否每条消息都回 Current Step Card，还是仅 at milestones？
3. Broker Confirm 前是否发 E1「已转陈总」—— 还是仅 Phase 2 Stage Complete 即 enough？

**Recommendation:** Strict 3 fields for pilot; Current Step Card on every field ack (low cost, high clarity); E1 bundled in S2 (same message).

---

## 15. Final Recommendation: GO for P19E

| Decision | Verdict |
|----------|---------|
| P19E-0 recon complete? | ✅ |
| Rename End Card → Stage Complete Card? | **YES** — semantic fix, not cosmetic |
| 3-phase model? | **YES** |
| Enter P19E-1? | **GO** |
| HOLD reasons? | None — no schema/OCR/小程序 blockers |

---

## Product Rules (Hard Constraints)

Write these into all P19E+ implementation PRs:

1. **「照片已收到」≠ 整个 Add Vehicle 完成** — it is Phase 1 complete only
2. **Do not use End Card before Phase 3 or full materials handoff** — use Stage Complete Card
3. **User sees one current action at a time** — primary CTA or primary instruction
4. **Every step is binary:** done / not done — no「半完成」headlines
5. **After done → state next step explicitly** — never leave user guessing wait vs continue
6. **Never say OCR completed / VIN recognized / policy modified / add-car completed**
7. **Only say:** 资料已收到 · 等待人工确认 · 陈总会审核
8. **Do not combine scoped ✅ with unscoped「还差」in the same headline**
9. **H5 = structured photo capture; WeCom = text + notifications + conversation**
10. **Broker Confirm (B0) is the only True End Card trigger for policy-adjacent closure**

---

## Appendix A — Mapping from P19B End Card types to P19E taxonomy

| P19B type | P19E card | When |
|-----------|-----------|------|
| E2 partial | Stage Complete S1 or Current Step | Phase 1 or 2 partial |
| E1 materials complete | Stage Complete S2 + handoff | Phase 2 done |
| E3 broker handoff | True End variant | Manual handle |
| E7 broker confirmed | True Final End | B0 Confirm |
| E6 declined | (unchanged) | Later tap |

## Appendix B — Code touchpoints (reference for P19E-1 — do not change in P19E-0)

| File | Current role |
|------|--------------|
| `services/fiqa_api/wecom/reply.py` | Start Card + `build_h5_photo_phase_complete_reply()` |
| `services/fiqa_api/wecom/h5_photo_end_card.py` | End Card send + dedup |
| `services/fiqa_api/wecom/slice.py` | Routing + `photo_flow_complete_followup` |
| `services/fiqa_api/wecom/active_case_bridge.py` | Text field extraction |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | `flow_complete` trigger |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | Success page copy |

---

*P19E-0 — documentation only. No code. No deploy. STOP.*
