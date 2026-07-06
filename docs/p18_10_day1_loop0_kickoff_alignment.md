# P18.10 — Day 1 Loop 0: Implementation Sprint Kickoff Alignment

**Date:** 2026-07-05  
**Type:** 开工前对齐 — **不写代码、不改文件、不部署、不测试**  
**Audience:** Andy、工程  
**Prerequisite:** P18.5 · P18.6 · P18.7 · P18.8 · P18.9 · Q0.11.1 evidence · B0 Contract  

**Purpose:** 在今天正式 coding 前，确认 implementation sprint 的边界、顺序、风险、验收标准和不该碰的地方。

**Authority:** 本文是 Day 1 coding 的 **Loop 0 gate**；不 supersede B0 Contract、ADR-001–005、P18.7 行为 spec。

---

## 1. 今日总目标

今天 **不是** 做完整产品，而是做一个 **可 demo、可恢复、可解释、保守安全** 的版本。

### 1.1 核心方向

| 原则 | 含义 |
|------|------|
| **Workbench-first** | 陈总价值必须在 Broker Workbench **屏幕上** 可见；不能先堆 invisible backend |
| **Conservative AI** | AI 只做 intake / organize / flag；高风险场景 **Manual Handle** |
| **AI prepare, Broker confirm** | AI 整理案子；报价、理赔、改保单 **仍由陈总决定** |
| **WeCom = channel** | 微信客服是入口，不是产品本身 |
| **Case Workspace = product** | 每一次诉求是有身份、有记忆、有缺口、有下一步的 Case |
| **One Business Flow at a Time** | 同一时刻只处理一个 active flow；第二话题 → flag only |
| **Raw events should not be lost** | 客户原话进 timeline / evidence；summary 是解释层，不覆盖 raw |
| **High-risk always Manual Handle** | 理赔、受伤、停保、coverage、报价、保单变更 → broker review |

### 1.2 一句话 North Star

> **客户还是发微信；CKS 办公室得到的是 Case，不是聊天记录；AI 备案，陈总拍板。**

### 1.3 今日不做

- 完整产品 / carrier 对接 / CRM / multi-tenant  
- Schema migration / WeCom OCR / per-message LLM  
- 自动报价 / 自动理赔 / 自动改保单 / coverage 判断  
- 重构 Q0.11.1 WeCom pipeline  

---

## 2. 今日 Loop 顺序

今天按以下 4 个 loop 推进。**每个 loop 完成后必须停下来报告，不自动进入下一 loop。**

---

### Loop 1: Workbench screen-proof + demo seed/reset

| 维度 | 内容 |
|------|------|
| **目标** | 陈总打开 Workbench 能在 **30 秒内** 看懂：这是谁、什么类型、急不急、缺什么、下一步做什么 |
| **允许做什么** | 扩展 `BrokerWorkbenchTab.tsx` 布局；读 `structured_payload` / `extra` JSON 显示 tags/flags；新建 `seed_chen_kui_demo` + `reset_chen_kui_demo` 脚本；规则 summary（非 LLM） |
| **不允许做什么** | Schema migration；Premium/Claim WeCom lane 后端；OCR/LLM；改 `slice.py` 核心逻辑；动 Cloud SQL / VPC / NAT |
| **验收标准** | 打开 4 个 seed case，30 秒 broker 测试通过（type / VIP / missing / next action）；§5 布局字段全部可见；reset 一条命令可复现 |
| **最小测试/检查** | 本地 Workbench 打开 seed cases；`reset_chen_kui_demo` 后 cases 重现；**不跑** WeCom live（Loop 1 仅 screen-proof） |
| **完成后** | **STOP — 报告 §8 格式，等确认再进 Loop 2** |

---

### Loop 2: Premium Review minimal + Claim Lite minimal

| 维度 | 内容 |
|------|------|
| **目标** | Story A/B：WeCom 高置信 intent → stub case → Workbench 可见 intelligence 区；Claim 有 Manual Handle CTA |
| **允许做什么** | `slice.py` **最小扩展**：`policy_review` / `claim_intake` → stub case create；规则 merge + safe reply 模板；`service_lane` 新字符串值（无 migration）；Workbench lane-specific CTA label |
| **不允许做什么** | Start Card parity for Premium/Claim；OCR；自动报价/理赔建议；FNOL；改 B0 Start Card gate；大规模 refactor `slice.py` |
| **验收标准** | WeCom 发涨价消息 → Premium case + VIP tags；发「刚撞了」→ Claim case + Urgent + Manual Handle；Workbench intelligence 区完整 |
| **最小测试/检查** | `test_wecom_slice.py` / `test_wecom_active_case.py` 回归；generic hello → 无 Draft（Q0.11.1）；`guardrail_inbox_triage.sh` 若 touched backend |
| **完成后** | **STOP — 报告 §8 格式，等确认再进 Loop 3** |

---

### Loop 3: Add Vehicle polish + Coverage Risk flag

| 维度 | 内容 |
|------|------|
| **目标** | Story C full live 可重复；C6 停保场景 → Coverage Risk flag + 谨慎 reply；UI polish（WeCom tag、Draft badge） |
| **允许做什么** | `BrokerWorkbenchTab` Draft/WeCom badges；keyword detector → `coverage_suspended_mentioned_at` + `risk_flags[]`；cautious reply 模板；`human_confirmation_fields` 冲突显示 |
| **不允许做什么** | 重构 `active_case_bridge` 核心；改 Start Card gate；generic no-merge 逻辑；自动恢复 coverage；说「应该可以开」 |
| **验收标准** | Add Vehicle live ×1：Start → Draft → merge → Confirm → Done Card；C6 seed/keyword → Coverage Risk 可见 + 谨慎 reply；Q0.11.1 generic safety 仍 PASS |
| **最小测试/检查** | `test_wecom_active_case.py` 全量；Add Vehicle rehearsal ×1；C6 scenario manual walkthrough |
| **完成后** | **STOP — 报告 §8 格式，等确认再进 Loop 4** |

---

### Loop 4: Rehearsal + fallback recording / runbook

| 维度 | 内容 |
|------|------|
| **目标** | Andy 可独立完成 8–12 min demo script；live 失败 60 秒内切 fallback；ops checklist 就绪 |
| **允许做什么** | 录屏 3 clips（A/B/C）；撰写 `chen_kui_demo_runbook.md`；扩展 `demo_pre_checklist.sh`；rehearsal notes |
| **不允许做什么** | Demo 当天新 deploy；现场改 Cloud Run env；依赖 live 图片 path |
| **验收标准** | Full script rehearsal <12 min；fallback 切换 <60s；边界话术 6 条各至少说 1 次；Must-have ≥7/9 PASS |
| **最小测试/检查** | `demo_pre_checklist.sh`；`wecom_drain_queues.py` empty queue；seed reset → full walkthrough |
| **完成后** | **STOP — 最终 sprint 报告 + demo-ready 判断** |

---

## 3. Loop 1 详细任务边界

Loop 1 是今天 **最重要** 的第一步。

### 3.1 目标

让 Broker Workbench 屏幕上能 **证明系统价值** — 即使 backend lane 尚未 live，seed case 也必须 screen-proof。

### 3.2 Workbench 至少显示

**Header / Identity 区：**

- Customer identity（姓名 / 电话）
- Known / New / Possible Match
- VIP tag
- WeCom channel
- Case Type（Premium Review / Claim Lite / Add Vehicle）
- Status（Draft / Needs Info / Ready for Broker / Manual Handle / Done）

**Case Intelligence 区：**

- Summary（2–4 句 broker-readable 中文）
- Known Facts
- Missing Fields
- Risk Flags
- Broker Next Action

**Context / Action 区：**

- Timeline / latest message（至少 1–3 条）
- Confirm / Manual Handle CTA

### 3.3 Demo seed/reset 至少准备

| Case | Type | Status | 关键 flags |
|------|------|--------|-----------|
| VIP Premium Review | `policy_review` | Needs Info / Ready | VIP, Uber Black, High Premium, Retention Risk, Price Sensitive |
| Claim Lite | `claim_lite` | Manual Handle | Urgent, Needs Fast Response |
| Add Vehicle Draft | `add_car` | Draft | WeCom, missing ZIP |
| Add Vehicle Ready | `add_car` | Ready for Broker | 全字段 minus confirm |
| Coverage Risk example | overlay on Add Vehicle | Manual Handle facet | Coverage Risk, Coverage Suspended Reminder |

### 3.4 实现约束

| 约束 | 说明 |
|------|------|
| 尽量复用 `BrokerWorkbenchTab.tsx` | 扩展布局，不新建 tab/page |
| 尽量复用 `service_records` / `structured_payload` / `extra` JSON | VIP → `extra.demo_flags` 或 `workbench_tags[]`；flags → `structured_payload.risk_flags[]` |
| **不做 schema migration** | 所有新 tags/flags 走 JSONB |
| **不做 OCR** | photos_pending via seed |
| **不做 LLM summary** | 规则截断 `source_text` 或 `demo_summary` |
| **不碰 Cloud SQL / VPC / NAT config** | 应用层 only |
| **不破坏 Q0.11.1 text/click path** | Loop 1 不改 `slice.py` |

### 3.5 Loop 1 数据来源映射（无 schema change）

| 显示项 | 数据来源 |
|--------|----------|
| Customer identity | `customer_name`, `customer_phone`, `extra.wecom_external_userid` |
| Known/New/Possible Match | `structured_payload.identity_state` 或 seed |
| VIP / segment tags | `extra.demo_flags` 或 `workbench_tags[]` |
| WeCom channel | `extra.wecom_external_userid` 存在 → tag |
| Case type | `service_lane` → label map |
| Summary | `source_text` 规则摘要 或 `demo_summary` |
| Known / Missing | `collected_fields` / `still_needed_fields` |
| Risk flags | `structured_payload.risk_flags[]` |
| Next action | `broker_next_step` |
| Manual Handle | Relabel Manual Promote + `manual_followup_needed` |

---

## 4. 不可违反的红线

以下红线 **已确认**，任何 loop 均不可违反：

| # | 红线 | 原因 |
|---|------|------|
| 1 | **不做 schema migration** | Cloud SQL live；JSONB 足够 demo；migration 回归风险 |
| 2 | **不做 WeCom image OCR** | `sync_msg.py` 仅 text；media path 零实现（P18.8 §4） |
| 3 | **不做 automatic quote** | ADR-003；E&O；陈总边界话术 |
| 4 | **不做 automatic claim advice** | 「报不报」必须 broker；法律敏感 |
| 5 | **不做 automatic policy change** | Confirm 后办公室按现有流程进 carrier |
| 6 | **不判断 coverage active/inactive** | 仅 flag + Manual Handle；不说「能开」 |
| 7 | **不做 per-message LLM** | 成本失控；WeCom path 当前零 LLM |
| 8 | **不重构 Q0.11.1 WeCom pipeline** | dedup / sync_cursor / generic safety 已 PASS |
| 9 | **不破坏 generic hello → no Draft** | Q0.11.1 核心验收；`slice.py` open-Draft merge fix |
| 10 | **不破坏 Add Vehicle Start Card gate** | B0 Contract step 3–5；未点 Start 无 Draft |
| 11 | **不现场依赖 live image path** | 图片 → seed `photos_pending` / verbal fallback |

---

## 5. 模块化要求

实现时必须保持模块边界清晰。短期可以简单，但 **边界要清楚**。

```
┌─────────────────────────────────────────────────────────────┐
│  Channel Adapter                                             │
│  WeCom / Web / future SMS                                    │
│  → ingress, egress, dedup, reply templates                   │
├─────────────────────────────────────────────────────────────┤
│  Raw Event / Message Layer                                   │
│  record_messages / inbox events / evidence_events / timeline │
│  → append-only; 不被 summary 覆盖                            │
├─────────────────────────────────────────────────────────────┤
│  Case Engine                                                 │
│  case type, known facts, missing fields, risk flags, status  │
│  → 业务逻辑核心；不依赖特定 channel                          │
├─────────────────────────────────────────────────────────────┤
│  Extraction Layer                                            │
│  rules / OCR / LLM — optional and replaceable                │
│  → demo: rules only; OCR/LLM 不 wired 进 WeCom path          │
├─────────────────────────────────────────────────────────────┤
│  Workbench View                                              │
│  display-only view model, not business logic core            │
│  → 读 case JSON；不做 carrier/quote 决策                     │
├─────────────────────────────────────────────────────────────┤
│  Broker Action                                               │
│  Confirm / Manual Handle / Done                              │
│  → 唯一可改变 case 终态的人类门控                            │
└─────────────────────────────────────────────────────────────┘
```

**要求：** 不要把 WeCom / GCP / OCR / LLM 逻辑写死进核心 Case logic。

| 层 | 关键文件 | Sprint 策略 |
|----|----------|------------|
| Channel Adapter | `wecom/slice.py`, `reply.py`, `send_msg.py` | 扩展，不重写 |
| Raw Event | `record_messages`, `evidence_events` | text + click 写入；图片 stub |
| Case Engine | `case_store.py`, `active_case_bridge.py` | stub lane 仿 add_vehicle pattern |
| Extraction | `intent.py`, `identity.py` | rules only |
| Workbench View | `BrokerWorkbenchTab.tsx` | 读 JSON，无业务决策 |
| Broker Action | `PATCH /cases/{id}/confirm` | 已有；Manual Handle = label + flag |

---

## 6. 风险复述

今天最可能失败的 **10 个风险** 及规避方式：

| # | 风险 | 严重度 | 规避方式 |
|---|------|--------|----------|
| 1 | **Workbench 看不出价值** | 🔴 | Loop 1 硬 gate：seed 4 cases + §5 布局；30 秒 broker 测试 |
| 2 | **Q0.11.1 回归** | 🔴 | Loop 1 不改 `slice.py`；Loop 2+ 改后必跑 `test_wecom_slice.py` + generic hello 检查 |
| 3 | **slice.py 改太多** | 🔴 | 最小扩展 stub create only；不重写 orchestrator；rollback rev `fiqa-api-00142-kwq` |
| 4 | **Premium/Claim 做太深** | 🟡 | minimal stub + Workbench 可见即可；无 Start Card parity；无 OCR/FNOL |
| 5 | **Coverage Risk 回复越界** | 🔴 | 关键词 → flag only；reply 模板审查；禁止「应该可以开」 |
| 6 | **图片/OCR scope creep** | 🔴 | `photos_pending` seed only；不 live 发图；P19 defer |
| 7 | **schema migration** | 🔴 | 全部走 JSONB；任何 migration PR → HOLD |
| 8 | **seed/reset 误删数据** | 🔴 | reset 仅 `workbench_test=1` tagged cases + queue tables；**禁止** `TRUNCATE service_records` 无 WHERE |
| 9 | **live demo 无 fallback** | 🔴 | Loop 4 录屏 + runbook；live 失败 60s 切录屏，不现场 debug |
| 10 | **AI 被误解成自动报价/自动理赔** | 🔴 | Workbench Next Action =「人工比价/回电」；边界话术 6 条；禁止 reply 模板越界 |

---

## 7. Loop 1 开始前检查清单

Loop 1 coding 前，必须阅读并理解以下文件：

### 7.1 必读文件

- [ ] `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` — 当前 list/detail/confirm 能力；P18.7 §10 gap
- [ ] `ui/src/api/inboxTriage.ts` — list/get/confirm API contract
- [ ] `services/fiqa_api/db/service_record_repository.py` — PG read/write；`extra` / `structured_payload` 字段
- [ ] `services/fiqa_api/inbox_triage/case_store.py` — `collected_fields`, `still_needed_fields`, `broker_next_step`, flags pattern
- [ ] `services/fiqa_api/wecom/active_case_bridge.py` — add_vehicle case create/merge pattern（Loop 2 参考，Loop 1 不修改）
- [ ] `services/fiqa_api/wecom/slice.py` — Q0.11.1 generic no-merge fix 位置（**Loop 1 不修改，仅理解**）
- [ ] `services/fiqa_api/wecom/intent.py` — `policy_review` / `claim_intake` / `add_car` 分类（Loop 2 参考）
- [ ] Existing seed/reset scripts（见下）

### 7.2 现有 seed/reset 脚本（参考，非 CKS 专用）

| 脚本 | 用途 | Sprint 动作 |
|------|------|------------|
| `scripts/prepare_unified_intake_founder_demo.py` | Founder demo mix seed | 参考 pattern；新建 CKS 版 |
| `scripts/reset_p16_supervised_demo.sh` | 本地 JSON reset | 参考 pattern |
| `scripts/cleanup_p16_demo_queue.py` | Cloud API 清 junk cases | 参考 queue cleanup |
| `scripts/wecom_drain_queues.py` | Manual drain | rehearsal ops；Loop 1 不依赖 |

**待建（Loop 1 产出）：**

- `scripts/seed_chen_kui_demo.py` — 4–5 cases + VIP flags
- `scripts/reset_chen_kui_demo.sh` — queue tables + demo-tagged cases only

### 7.3 环境与证据确认

- [ ] Q0.11.1 evidence: `docs/evidence/wecom_q0_11_1_resmoke_2026-07-04.md` — PASS；rollback rev 已知
- [ ] B0 Contract: `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` — Start Card gate + Rule 8
- [ ] Demo 环境统一：Workbench 连 local 8001 还是 Cloud Run — **Loop 1 前确认**
- [ ] Demo `external_userid` 测试号 — **Loop 1 seed 前确认**（seed 可用固定值）

### 7.4 Loop 1 开工前 GO 条件

| # | 条件 | 状态 |
|---|------|------|
| 1 | P18.5–P18.9 + 本文 Loop 0 完成 | ✅ |
| 2 | Q0.11.1 PASS | ✅ |
| 3 | Schema change 决策：避免 | ✅ |
| 4 | WeCom image path：不存在，placeholder 策略 | ✅ |
| 5 | 必读文件清单已浏览 | ⬜ operator |
| 6 | Demo 环境（local vs Cloud）已确认 | ⬜ operator |

---

## 8. Loop 完成后的报告格式

每个 loop 完成后 **必须** 按以下格式报告，并 **等待确认** 再进入下一 loop：

```markdown
## Loop N Complete Report

**Loop:** N — [名称]
**Date/time:**
**Operator:**

### Changed files
- [list every file touched]

### What was implemented
- [bullet list of completed items]

### What was not implemented
- [explicit deferrals with reason]

### Any high-risk files touched
- [ ] slice.py
- [ ] active_case_bridge.py
- [ ] case_store.py
- [ ] service_record_repository.py
- [ ] wecom/sync_msg.py / message_processed.py
- [ ] BrokerWorkbenchTab.tsx
- [ ] None

### Tests/checks run
- [commands + pass/fail]

### Manual verification steps
1. [step-by-step what operator verified]

### Remaining risks
- [open risks for next loop or demo]

### Ready for next loop?
- [ ] YES — criteria met
- [ ] NO — blocker: [reason]
```

---

## 9. Final GO / HOLD 判断

### 9.1 是否建议开始 Loop 1 coding？

## ✅ **GO — 建议开始 Loop 1**

| 条件 | 状态 | 依据 |
|------|------|------|
| 商业叙事清晰 | ✅ | P18.4 / P18.5 North Star + 三 story 顺序 |
| 技术通道可靠 | ✅ | Q0.11.1 PASS；text/click path；rollback rev 已知 |
| 行为 spec 已定 | ✅ | P18.7 逐步仿真 + Workbench §10 字段清单 |
| 资产清点完成 | ✅ | P18.8 复用/缺口/红线明确 |
| Conservative AI gate | ✅ | P18.9 十条铁律 + scope 锁定 |
| Schema 策略 | ✅ | 零 migration；JSONB only |
| 最大瓶颈已识别 | ✅ | Workbench 展示层 — Loop 1 直接对准 |

**条件 Go 含义：** 可以立刻开工 Loop 1，但 **Loop 1 必须先 screen-proof**，不能跳过 Workbench 直接做 backend lane。

### 9.2 如果 GO — Loop 1 第一步应该改什么

**推荐顺序（最小风险）：**

1. **先读** `BrokerWorkbenchTab.tsx` — 定位 detail panel 渲染区，对照 P18.7 §10 ASCII 找 gap  
2. **先建** `scripts/seed_chen_kui_demo.py` — 4–5 cases 写入 `structured_payload` / `extra` JSON（VIP Premium、Claim Lite、Add Vehicle Draft/Ready、Coverage Risk overlay）  
3. **再改** `BrokerWorkbenchTab.tsx` — Header tag row + Intelligence card（Summary / Known / Missing / Flags / Next Action）读 seed 数据  
4. **再建** `scripts/reset_chen_kui_demo.sh` — demo-tagged cases + queue tables only  
5. **验收** — 30 秒 broker 测试 on seed Story A case → **STOP 报告**

**Loop 1 第一步具体文件：** `scripts/seed_chen_kui_demo.py`（先让数据存在，再改 UI 读它）。

**Loop 1 不应第一步改：** `slice.py`、`active_case_bridge.py`、任何 WeCom pipeline 文件。

### 9.3 如果 HOLD — 缺什么信息

当前 **无阻塞性 HOLD 项**。以下需在 Loop 1 前由 operator 确认（不阻塞开工，但影响 seed 与 rehearsal）：

| 项 | 影响 | 默认 |
|----|------|------|
| Demo 环境：local 8001 vs Cloud Run | seed 写入目标 DB | local 8001 + `run_demo_local.sh` |
| 测试 `external_userid` | seed VIP Known identity | 沿用 Q0.11.1 smoke 测试号或固定 demo ID |
| Cloud Run queue flags 当前值 | Loop 2+ live WeCom | deploy 前 `gcloud run services describe` 核对 |

### 9.4 No-Go 触发条件（任一即停 sprint）

- Q0.11.1 generic safety **回归**（hello → Draft）  
- Sprint scope 膨胀到 OCR / carrier API / LLM intent / schema migration  
- Cloud SQL 连接失败且无 rollback  
- Loop 1 结束 Workbench 仍无 VIP + intelligence 区  

---

## 附录 A — 文档关系

```
Q0.11.1 PASS
    ↓
P18.5 Demo 体验 → P18.6 成本审计 → P18.7 逐步仿真 → P18.8 资产清点 → P18.9 Red Team
    ↓
P18.10 本文 — Loop 0 Kickoff Alignment
    ↓
Loop 1 → Loop 2 → Loop 3 → Loop 4 → 陈总 demo
```

---

## 附录 B — Must-have 验收对照（全 sprint）

| # | Must-have | 负责 Loop |
|---|-----------|-----------|
| 1 | WeCom entry live | Loop 2–3 |
| 2 | Workbench case list + detail | Loop 1 |
| 3 | VIP / channel / case type badges | Loop 1 |
| 4 | Premium Review minimal case | Loop 2 |
| 5 | Claim Lite minimal case | Loop 2 |
| 6 | Add Vehicle full flow live ×2 | Loop 3 |
| 7 | Confirm gate | Loop 3 |
| 8 | Demo seed / reset | Loop 1 |
| 9 | Fallback recording / script | Loop 4 |

---

*End of P18.10 — Day 1 Loop 0 Kickoff Alignment*
