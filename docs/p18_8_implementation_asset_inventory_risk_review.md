# P18.8 — Implementation Asset Inventory + Risk Review

**Date:** 2026-07-04  
**Type:** 实施前资产清点 + 风险勘查 — **只做审计与计划，不写代码**  
**Audience:** Andy（founder / demo 主讲）、工程、陈总（间接 — 通过 demo 结果）  
**Prerequisite（已完成）:**

- **Q0.11.1** WeCom 技术通道 PASS — WeCom → Cloud Run → Cloud SQL private IP → inbox/outbox → WeCom reply；`message_processed` / `sync_cursor` 防历史 replay；generic 消息不误建 Draft  
- **P18.4** CKS 商业定位  
- **P18.5** Demo Experience Plan  
- **P18.6** Demo Readiness / Cost / Smoothness Audit  
- **P18.7** End-to-End Business Flow Simulation  

**Purpose:** 在进入 3–4 天 Chen Kui demo implementation sprint **之前**，围绕 7 个 sprint 功能做全面资产清点与风险勘查，避免重复 Neon / Postgres / Cloud Run 网络类隐藏风险。

**Related:** `docs/p18_7_end_to_end_business_flow_simulation.md` · `docs/p18_6_demo_readiness_cost_smoothness_audit.md` · `docs/p18_5_chen_kui_demo_experience_plan.md` · `docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md` · `docs/evidence/wecom_q0_11_1_resmoke_2026-07-04.md`

**Authority:** 本文是 sprint 前的 **asset + risk gate**；不 supersede B0 Contract 或 ADR-001–005。工程实现以本文 + P18.7 行为 spec 为准。

**Disclaimer:** 本文基于代码清点与既有文档推断；不构成法律、保险或合规建议。

**本文不做：** 写代码 · 部署 · smoke · 改 UI · 改 schema · migration

---

## 1. Executive Summary

### 1.1 是否建议进入 implementation sprint？

**结论：✅ GO — 有条件立即开工。**

| 维度 | 判断 | 一句话 |
|------|------|--------|
| 技术通道 | **Ready** | Q0.11.1 PASS；text/click path 可靠 |
| 核心闭环（Add Vehicle） | **Mostly ready** | B0 Start → Draft → merge → Confirm → Done Card 已有代码与测试 |
| Workbench 展示 | **Gap（P0）** | 有 list/detail/confirm，缺 P18.7 §10 intelligence 区块与 VIP badges |
| Premium / Claim lanes | **Gap（P0）** | intent 已有；WeCom case creation **未 wired** |
| Demo 运维 | **Partial** | drain 成熟；CKS-specific seed/reset、fallback recording **待建** |
| WeCom 图片 | **Not ready** | 代码确认：**零实现**；demo 只做 placeholder |

**条件 Go 含义：** Day 1 **必须先 Workbench screen-proof + seed**，不能先堆 invisible backend。Q0.11.1 已 PASS 路径 **不可回归**。

---

### 1.2 最大可复用资产

| 资产 | 复用价值 | 证据 |
|------|----------|------|
| **WeCom text pipeline** | callback → inbox queue → worker → sync_msg → intent → reply outbox → send | Q0.11.1 PASS；17+ test files |
| **B0 Add Vehicle 全路径** | Start Card → Draft → merge → Confirm → Done Card | `active_case_bridge.py`, `test_wecom_active_case.py` |
| **规则 intent 分类** | add_car / claim_intake / policy_review — **无 LLM** | `wecom/intent.py` |
| **字段提取器** | phone / VIN / ZIP / delivery_date / primary_driver | `wecom/identity.py` |
| **Case 持久化** | Postgres `service_records` + JSON `structured_payload` | Cloud SQL private IP PASS |
| **Broker Workbench 骨架** | list / detail / confirm / collected+still_needed / manual_followup | `BrokerWorkbenchTab.tsx` |
| **Policy Review 正式上传路径** | OCR + trust_checks + readiness（**网页版**，非 WeCom） | `policy_review/handler.py` |
| **Claim intake triage 规则** | collected/still lists、安全模板 | `inbox_triage/triage.py` |
| **Ops：manual drain** | `wecom_drain_queues.py` + admin endpoints | evidence docs |

---

### 1.3 最大新建缺口

| 缺口 | 影响 Story | 新建范围 |
|------|-----------|----------|
| **Premium Review WeCom minimal lane** | A | 高置信 `policy_review` → stub case + merge + Workbench 可见 |
| **Claim Lite WeCom minimal lane** | B | 高置信 `claim_intake` → stub case + urgent flags + Manual Handle CTA |
| **Workbench intelligence 区块** | A/B/C | Summary / Known / Missing / Flags / Next Action 布局对齐 P18.7 §10 |
| **VIP / channel / case type badges** | A | Header tags — 当前 UI 未 wired |
| **Coverage Risk flag** | C6 | WeCom slice 无专用 flag；triage 有 `payment_lapse` 但未接 WeCom lane |
| **CKS demo seed/reset** | 全局 | 现有 seed 是 founder demo mix，非陈总三 story |
| **Fallback recording + rehearsal script** | 全局 | P18.6 标注待建 |

---

### 1.4 最大技术风险

| 风险 | 严重度 | 说明 |
|------|--------|------|
| **Q0.11.1 路径回归** | 🔴 高 | 改 `slice.py` / dedup / B0 gate 可能破坏 generic safety 或 Draft merge |
| **Schema migration 影响生产** | 🔴 高 | Cloud SQL 表已 live；migration 需 downtime / 回滚计划 |
| **WeCom queue flags 未入 deploy bundle** | 🟡 中 | `WECOM_INBOX_QUEUE` / `WECOM_REPLY_OUTBOX` 需 manual `gcloud` update |
| **broker_confirmed_at 仅 JSON** | 🟡 中 | 未 mirror 到 PG `extra`；跨实例读可能不一致 |
| **双 Workbench UI** | 🟡 中 | `BrokerWorkbenchTab` vs `DocumentIntakeInboxPage` — demo 只用前者 |

---

### 1.5 最大 demo 风险

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| **陈总看不到 screen-proof 价值** | 🔴 高 | Day 1 Workbench + seed 优先 |
| **Premium/Claim live 时 Workbench 空白** | 🔴 高 | minimal lane 必须同日可见 |
| **现场 debug WeCom** | 🔴 高 | fallback recording + freeze 规则 |
| **Add Vehicle 第二次失败** | 🟡 中 | reset + rehearsal ×2 |
| **live 发图片无反应** | 🟡 中 | **不 live 发图**；seed `photos_pending` |

---

### 1.6 最大成本风险

| 风险 | 严重度 | 说明 |
|------|--------|------|
| **per-message LLM** | 🔴 高 | WeCom path 当前零 LLM；切 LLM intent/summary 会失控 |
| **OCR / Vision scope creep** | 🔴 高 | 网页版 policy_review OCR 存在；**demo WeCom 路径禁止启用** |
| **固定云成本** | 🟢 低 | Cloud SQL + NAT + static IP ~$15–30/月 baseline |
| **变动云成本** | 🟢 低 | demo 流量 <100 msg/天；Run 可忽略 |

---

### 1.7 WeCom path 可靠性声明（代码确认）

| Path | 状态 | 代码依据 |
|------|------|----------|
| **Text ingress/egress** | ✅ **可靠** | Q0.11.1 PASS；`sync_msg` 拉 text；`send_msg` 发 text/menu |
| **Click / menu / Start Card / Done Card** | ✅ **可靠** | `reply.py` + `active_case_bridge.py`；B0 tests |
| **Image / media** | ❌ **不可靠 / 未实现** | `sync_msg.py` L110: `msgtype != "text"` 直接 skip；无 `media_id`、无 download、无 GCS |

**图片 demo 策略（强制）：**

- 若客户发 renewal notice / 事故照片 → **仅** `document_received` / `photos_pending` placeholder（seed 或规则 flag）  
- **不做 OCR**  
- **不 live 依赖图片 path**  
- script 可说：「下一版可自动保存图片」

---

## 2. Current Asset Inventory

### A. WeCom Channel Layer

| 组件 | 路径 | 当前支持 | Tested | Q0.11.1 Deployed | 复用到 Premium/Claim/Coverage |
|------|------|----------|--------|------------------|------------------------------|
| **Callback route** | `routes/wecom_kf_callback.py` | GET verify + POST decrypt/ack；queue mode enqueue-only | ✅ `test_wecom_kf_callback.py` | ✅ rev `fiqa-api-00142-kwq` | ✅ ingress 通用 |
| **Inbox queue** | `wecom/inbox_queue.py` | `wecom_inbox_events`；dedup key；pending→processing→processed | ✅ `test_wecom_inbox_queue.py` | ✅ `WECOM_INBOX_QUEUE=1` | ✅ |
| **Inbox worker** | `wecom/inbox_worker.py` | SKIP LOCKED claim；stale reclaim；max 3 attempts | ✅ `test_wecom_inbox_worker.py` | ✅ | ✅ |
| **Reply outbox** | `wecom/reply_outbox.py` | `wecom_reply_outbox`；text + msgmenu only | ✅ `test_wecom_reply_outbox.py` | ✅ `WECOM_REPLY_OUTBOX=1` | ✅ |
| **Reply sender** | `wecom/send_msg.py` | `kf/send_msg`；`WECOM_SLICE_SEND_REPLY=1` gate | ✅ mocked in slice tests | ✅ | ✅ |
| **Reply templates** | `wecom/reply.py` | `build_slice_reply`：add_car/claim/policy/unclear；guided menu；Start Card；Done Card | ✅ `test_wecom_reply.py` | ✅ | ⚠️ claim/policy reply 有；lane-specific summary **待扩展** |
| **message_processed** | `wecom/message_processed.py` | `claim_message_processed` 防 replay | ✅ `test_wecom_message_processed.py` | ✅ | ✅ |
| **sync_cursor** | `wecom/sync_cursor.py` | watermark 增量 sync | ✅ 同上 | ✅ | ✅ |
| **Slice orchestrator** | `wecom/slice.py` | 全流程编排；B0 gate；generic no-merge fix | ✅ `test_wecom_slice.py` | ✅ Q0.11.1 fix | ⚠️ 仅 add_car 建 case |
| **Reply dedup** | `wecom/reply_dedup.py` | per-msg send choke | ✅ `test_wecom_reply_dedup.py` | ✅ | ✅ |
| **Queue admin** | `routes/wecom_queue_admin.py`, `wecom/queue_admin.py` | drain/status/repair-stale | ✅ admin route tests | ✅ manual token | ✅ ops |
| **Active case bridge** | `wecom/active_case_bridge.py` | Draft create/merge；Confirm→Done Card | ✅ `test_wecom_active_case.py` | ✅ | ⚠️ 仅 add_vehicle path |

**Schema（WeCom 专用）：**

- `db/schema/wecom_inbox_events.sql`
- `db/schema/wecom_reply_outbox.sql`
- `db/schema/wecom_message_processed.sql`（runtime ensure + tests）
- `db/schema/wecom_sync_cursors.sql`

**Feature flags 摘要：**

| Env | 作用 | Deploy bundle |
|-----|------|---------------|
| `WECOM_INBOX_QUEUE=1` | Callback enqueue-only | ❌ manual post-deploy |
| `WECOM_REPLY_OUTBOX=1` | Reply 异步发送 | ❌ manual |
| `WECOM_SLICE_SEND_REPLY=1` | 实际发 WeCom | ✅ in `deploy_cloud_run_core.sh` |
| `WECOM_B0_ACTIVE_WORKSPACE=1` | Start Card / Draft / Done Card | ✅ |
| `WECOM_QUEUE_ADMIN_TOKEN` | Admin drain 鉴权 | ❌ manual |

---

### B. Business Logic / Case Layer

| 组件 | 路径 | 能力摘要 |
|------|------|----------|
| **intent.py** | `wecom/intent.py` | Rule-based：`add_car`, `claim_intake`, `policy_review`, `unclear`, Start Card clicks |
| **identity.py** | `wecom/identity.py` | phone, VIN, ZIP, delivery_date, primary_driver 正则提取 |
| **slice.py** | `wecom/slice.py` | sync → intent → reply → bridge；B0 vs Track A 分支 |
| **active_case_bridge.py** | `wecom/active_case_bridge.py` | Draft/Active ingest；Confirm；Done Card |
| **case_truth_repository.py** | `inbox_triage/case_truth_repository.py` | Read facade（JSON + PG） |
| **case_store.py** | `inbox_triage/case_store.py` | Write：collected/still_needed, broker_next_step, evidence_events |
| **service_record_repository.py** | `db/service_record_repository.py` | PG：service_records, record_messages, structured_record_data |
| **active_case_resolver.py** | `inbox_triage/active_case_resolver.py` | VIN conflict → BROKER_REVIEW |
| **intake_service_lanes.py** | `inbox_triage/intake_service_lanes.py` | `add_car`, `policy_review` — **无 claim lane 常量** |
| **policy_review/handler.py** | `policy_review/handler.py` | 网页上传 OCR → case（`service_lane=policy_review`） |
| **policy_review/trust_checks.py** | `policy_review/trust_checks.py` | name conflict, needs_verification |
| **policy_review/readiness.py** | `policy_review/readiness.py` | ready/needs_info/broker_review + opportunity signals |
| **triage.py** | `inbox_triage/triage.py` | 全量 triage；claim collected/still；payment_lapse templates |

**Add Vehicle 当前能力：**

| 模式 | 行为 | 状态 |
|------|------|------|
| **B0（demo 默认）** | 高置信 add_car → Start Card → Start click → Draft → 字段 merge → Confirm → Done Card | ✅ 主路径 |
| **Track A** | 高置信 + phone → 立即 Active case | ✅ 备用 |
| **字段** | phone, VIN, ZIP, delivery_date, primary_driver | ✅ WeCom 提取 |
| **缺** | year/make_model WeCom 提取；Draft badge UI；WeCom channel tag | ⚠️ polish 项 |

**policy_review / claim_intake intent：**

| Intent | WeCom 分类 | WeCom case 创建 | 正式路径 |
|--------|-----------|----------------|----------|
| `policy_review` | ✅ 高置信 | ❌ 仅 reply | 网页 `POST /api/intake/add-car/extract?request_type=policy_review` |
| `claim_intake` | ✅ 高置信 | ❌ 仅 safety reply | Unified Intake `triage.py` claim spine |

**service_lane 支持：**

- 已定义：`add_car`, `policy_review`
- **未定义：** `claim` / `claim_lite` — sprint 可用 `policy_review` 模式仿造或扩常量

**missing / collected / next action：**

| 存储位置 | 字段 |
|----------|------|
| JSON case | `collected_fields`, `still_needed_fields`, `broker_next_step`, `quote_ready_status` |
| PG `structured_payload` | 同上 + `case_draft`, `human_confirmation_*` |
| PG `service_records` | `current_next_action` |

**risk flags 现状：**

| Flag 类型 | 位置 | WeCom 可用 |
|-----------|------|-----------|
| `manual_followup_needed` | triage → case_store | ⚠️ 需 lane 写入 |
| `human_confirmation_fields` | triage add-car | ✅ Workbench 显示 |
| `opportunity_signals` | policy_review/readiness | 网页 policy only |
| `payment_lapse_expiration` | triage category | Unified Intake only |
| **Coverage Risk / VIP / Retention** | P18.7 spec | ❌ **未实现** |

**Broker confirm path：**

- `PATCH /api/inbox/cases/{id}/confirm` → `confirm_case_by_broker` → Done Card
- UI：`BrokerWorkbenchTab.handleBrokerConfirm`
- Guard：无 phone 时 block confirm

**Manual handle：**

- **无独立 `manual_handle` API**
- 等价：`manual_followup_needed=true` + Manual Promote（同 confirm endpoint + dialog）
- P18.7 期望的 **Manual Handle CTA** 需 UI label/flow 对齐（非新 endpoint）

---

### C. Workbench UI Layer

| 组件 | 路径 | 状态 |
|------|------|------|
| **BrokerWorkbenchTab** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | ~2674 行；主 Workbench |
| **API client** | `ui/src/api/inboxTriage.ts` | list/get/confirm/attachments/workbench flags |
| **Helpers** | `ui/src/features/intake/utils/intakePure.ts` | lane label, human confirmation, collected/still |
| **Tags** | `WorkbenchSummary.tsx`, `officeCaseBoundary.ts` | urgency, status, boundary badges |

**当前 Workbench 能显示什么：**

| 能力 | 状态 |
|------|------|
| Case list（分页 50） | ✅ |
| Case detail panel | ✅ |
| Confirm + Manual Promote | ✅ |
| `collected_fields` / `still_needed_fields` | ✅ |
| `broker_next_step` preview | ✅ |
| `manual_followup_needed` 边框/标签 | ✅ |
| `workbench_lane_kind` / `service_lane` | ✅ 部分 |
| Attachments count + upload | ✅ |
| `broker_confirmed_at` | ✅ |
| Test / archive flags | ✅ |
| human_confirmation_fields | ✅ |

**与 P18.7 §10 最小模型差距：**

| P18.7 要求 | 当前 | Gap |
|-----------|------|-----|
| **VIP** badge | ❌ | 需 seed + UI |
| **Known / New / Possible Match** | ❌ | 需 identity state |
| **WeCom channel** tag | ❌ | `wecom_external_userid` 在 extra 但未显示 |
| **Uber Black / High Premium** segment | ❌ | 需 flags |
| **Case Type**（Premium Review / Claim Lite） | ⚠️ lane label 部分覆盖 | 需明确 mapping |
| **Summary** 置顶区块 | ❌ | 无独立 Summary section |
| **Risk Flags** 区（Retention, Urgent, Coverage Risk） | ❌ | 无 dedicated flags panel |
| **Conflict flags** | ⚠️ human_confirmation only | VIN conflict 未突出 |
| **Mixed-topic flags** | ❌ | `claim_mentioned_at` 等未显示 |
| **Timeline / latest message** | ⚠️ notes/activity 轻度 | 无完整 timeline |
| **Manual Handle** 专用 CTA | ⚠️ Manual Promote 近似 | label 不对齐 Claim story |

**最小改动可 screen-proof 的项：**

1. Header row：customer name + phone + tags（VIP/WeCom/Case Type/Status）— **读 existing fields + seed JSON**
2. Intelligence card：Summary（`source_text` 截断或规则生成）+ Known/Missing 并列 — **读 collected/still**
3. Flags row：从 `structured_payload` 或 seed `demo_flags` — **无需新表**
4. Next Action：放大 `broker_next_step` — **已有数据**
5. Confirm / Manual Handle 按钮 label 按 lane 切换 — **UI only**

---

### D. Database / Schema Layer

**Cloud SQL 当前表（schema SQL 文件）：**

| 表 | 文件 | Sprint 用途 |
|----|------|------------|
| `service_records` | `stage1_service_record.sql` | Case header；`service_lane`, `current_next_action` |
| `record_messages` | 同上 | 消息时间序（WeCom path 轻用） |
| `structured_record_data` | 同上 | `structured_payload` JSONB — **demo 主战场** |
| `state_history` | 同上 | 状态变更审计 |
| `office_actions` | 同上 | ⚠️ schema only，**无 Python 写入** |
| `intake_sessions` | `intake_sessions.sql` | 网页 session（WeCom demo 次要） |
| `intake_entities` | `intake_entities.sql` | 车辆 entity memory |
| `wecom_inbox_events` | `wecom_inbox_events.sql` | Queue |
| `wecom_reply_outbox` | `wecom_reply_outbox.sql` | Outbox |
| `wecom_message_processed` | runtime DDL | Dedup |
| `wecom_sync_cursors` | runtime DDL | Watermark |

**JSON / metadata 已可用字段（避免 schema change）：**

`service_records.extra`：

- `wecom_external_userid`, `evidence_events`, `case_attachments`, `workbench_test`, `workbench_archived`, `merge_review_required`, `conflict_state`

`structured_record_data.structured_payload`：

- `collected_fields`, `still_needed_fields`, `broker_next_step`, `case_draft`, `human_confirmation_*`, `p16_broker_packet`

**Sprint 推荐：零 schema change**

| Demo 需求 | 存储方案 |
|----------|----------|
| VIP / segment tags | `extra.demo_flags` 或 `structured_payload.workbench_tags[]` |
| Coverage Risk flag | `structured_payload.risk_flags[]` |
| Mixed-topic flags | `extra.claim_mentioned_at` 等 timestamp（B0 已有 `claim_mentioned_at` 模式） |
| Summary | `broker_next_step` + `source_text` 规则截断；或 `structured_payload.demo_summary` |
| photos_pending | `still_needed_fields` 含 `photos`；`evidence_events` 占位 |
| Claim lane | `service_lane` 可用新字符串值（列是 text，无需 migration） |

**若必须 schema change 的风险：**

| 风险 | 影响 |
|------|------|
| Migration 失败 | Cloud SQL demo downtime |
| 列默认值 / 回填 | 旧 case 读异常 |
| Q0.11.1 regression | 改 repository 可能破坏 confirm path |
| Deploy 不同步 | schema 与 code 版本 mismatch |

**结论：demo sprint 应 **避免 migration**；用 JSONB 承载所有新 flags/tags。**

**对 Q0.11.1 已 PASS path 的影响：**

- WeCom queue 表 truncate 是 **安全** 的（evidence 已验证）  
- **不可** truncate `service_records` 在生产 demo 前无备份  
- 改 `slice.py` 逻辑需回归 `test_wecom_message_processed.py` generic safety tests

---

### E. Existing Web Upload / Document Flow

| 能力 | 路径 | 状态 |
|------|------|------|
| **Customer file upload** | `ui/src/pages/AddCarPage.tsx` | PDF/JPG/PNG/HEIC；add_car + policy_review |
| **Broker attachment upload** | `BrokerWorkbenchTab.tsx` | POST attachments |
| **Add-car extract** | `routes/add_car.py` | multipart → OCR |
| **Policy review extract** | `policy_review/handler.py` | OCR + trust + readiness |
| **Inline image OCR** | `routes/inbox_triage.py` + `image_input_pipeline.py` | base64 → Vision（可选） |
| **OCR engine** | `ocr_kill_test/` | Gemini/OpenAI |
| **Storage** | `data/unified_intake_attachments/` | **本地 filesystem** |
| **GCS** | — | ❌ **intake 路径无 GCS** |

**关键问题回答：**

| 问题 | 答案 |
|------|------|
| 网页版上传能否复用到 WeCom 图片？ | **架构上可**，但 **无 wired 代码** |
| WeCom 图片是否已实现下载？ | **否** — `sync_msg` 过滤非 text |
| media_id → download → GCS → attachment？ | **否** — 零 `media_id` 引用 |
| Demo 是否只做 placeholder？ | **是** — `photos_pending` / `document_received` via seed 或 `evidence_events` stub |
| 能否假设图片能工作？ | **绝对不能** |

---

### F. Cloud / Ops Layer

| 组件 | 路径 / 配置 | Sprint 策略 |
|------|------------|------------|
| **Cloud Run** | `scripts/deploy_cloud_run_core.sh` | 新 revision；**保留** Q0.11.1 flags |
| **Cloud SQL private IP** | `fiqa-service-record-database-url-cloudsql-private` | **不可动** 网络路径 |
| **Direct VPC all-traffic** | deploy config | **不可动** — WeCom NAT 依赖 |
| **Cloud NAT static IP** | `8.235.43.132`（evidence） | **不可动** — 白名单 |
| **Secret Manager** | DB URL, WeCom secrets |  rotate 需协调 |
| **Admin queue endpoints** | `/api/admin/wecom/queues/*` | **保留** — rehearsal drain |
| **Manual drain** | `scripts/wecom_drain_queues.py` | **保留** — 每次消息后 drain |
| **Reset scripts** | `reset_p16_supervised_demo.sh`, `prepare_unified_intake_founder_demo.py` | ⚠️ 本地 JSON；需 **CKS 版** |
| **Cloud cleanup** | `cleanup_p16_demo_queue.py` | API 侧清 junk cases |
| **Evidence docs** | `docs/evidence/wecom_q0_*.md` | 回归基准 |

**Deploy 风险：**

| 项 | 风险 | 缓解 |
|----|------|------|
| Queue flags 遗漏 | inbox/outbox 不工作 | deploy checklist 显式列 flags |
| 新 env var 未设 | feature 静默关闭 | `validate_pilot_deploy_env.py` |
| Image tag 错误 | 回滚到 `fiqa-api-00142-kwq` | evidence 记录 rollback rev |
| Schema 手动 apply | 表缺失 | deploy 前 `psql -f` checklist |

**不可动清单：**

- Cloud SQL private IP + VPC egress 拓扑  
- WeCom NAT 静态 IP 白名单  
- `message_processed` / `sync_cursor` dedup 语义  
- B0 Start Card gate（generic → 无 Draft）  
- Manual drain only（无 cron/Pub/Sub）

---

## 3. Feature-by-feature Inventory and Risk

### Feature 1: Workbench screen-proof

| 维度 | 分析 |
|------|------|
| **可复用组件** | `BrokerWorkbenchTab` list/detail；`collected_fields`/`still_needed_fields`；Confirm；`manual_followup_needed`；`broker_next_step`；`workbenchLaneLabel`；attachment count |
| **新增 UI 最小范围** | Header tag row；Intelligence card（Summary + Known + Missing + Flags + Next Action）；lane-specific CTA labels；可选 WeCom filter |
| **Schema change** | **不需要** — 用 `structured_payload` / `extra` JSON |
| **显示映射** | 见下表 |
| **最大风险** | 改 Workbench 引入 regression；陈总仍看不到 VIP — **口述代替屏幕** |
| **最小实现方案** | Day 1：读 existing case fields + demo seed 预置 tags/flags；布局对齐 P18.7 §10 ASCII；不改 API contract |
| **Demo acceptance** | 打开 seed Story A case，**30 秒内**答出：type / VIP / missing / next action |

**显示项映射：**

| 显示项 | 数据来源（无 schema change） | Mock/Seed |
|--------|------------------------------|-----------|
| Customer identity | `customer_name`, `customer_phone`, `extra.wecom_external_userid` | Seed VIP 客户 |
| Known/New/Possible Match | `structured_payload.identity_state` 或 seed | Seed Known |
| VIP | `extra.demo_flags.vip` 或 `workbench_tags` | ✅ Seed |
| WeCom channel | `extra.wecom_external_userid` 存在 → tag | Live cases |
| Uber Black / High Premium | `workbench_tags` | ✅ Seed |
| Case type | `service_lane` → label map | Seed per story |
| Status | `case_status` + `quote_ready_status` + `broker_confirmed_at` | — |
| Summary | `source_text` 规则摘要 或 `demo_summary` | 规则 + seed |
| Known facts | `collected_fields` | Live merge |
| Missing fields | `still_needed_fields` | Live merge |
| Risk flags | `structured_payload.risk_flags[]` | Seed + rules |
| Next action | `broker_next_step` | Rule-generated |
| Timeline/latest | `case_notes` / `evidence_events` / `record_messages` | Latest 1–3 |
| Confirm | 已有 button | Add Vehicle |
| Manual Handle | Relabel Manual Promote + `manual_followup_needed` | Claim/Premium |

**Stop Condition / 不该做什么：**

- ❌ 不做 full timeline panel（ADR-002）  
- ❌ 不做 CRM / household 视图  
- ❌ 不改 case list 分页架构  
- ❌ 不依赖 LLM 生成 summary  

---

### Feature 2: Demo seed/reset

| 维度 | 分析 |
|------|------|
| **当前 seed/reset** | `prepare_unified_intake_founder_demo.py`（founder mix）；`reset_p16_supervised_demo.sh`（本地 JSON）；`cleanup_p16_demo_queue.py`（Cloud API 清 junk） |
| **应 seed 的 cases** | 见下表 |
| **Reset 范围** | ✅ 可清：WeCom queue 表（inbox/outbox/message_processed/sync_cursors）；demo-tagged cases（`workbench_test=1`） |
| **不能清** | 生产 broker 真实 cases；`wecom_sync_cursors` 除非 rehearsal 全量重置；Secret/网络配置 |
| **Rehearsal 可重复** | 固定 `external_userid` + 固定 seed case_ids + queue truncate script + browser localStorage clear |
| **最大 DB 风险** | 误删非 demo `service_records`；truncate 后 sync_cursor 丢失导致历史 replay |
| **最小安全实现方案** | 新 script：`seed_chen_kui_demo.py` — 4 cases + VIP flags；`reset_chen_kui_demo.sh` — queue tables only + mark-delete demo cases by tag |
| **Demo acceptance** | 一条命令 reset 后，Workbench 显示 4 个 story cases + VIP 客户 |

**Seed cases 规格：**

| Case | Type | Status | 关键 flags |
|------|------|--------|-----------|
| VIP Premium Review | `policy_review` | Needs Info / Ready | VIP, Uber Black, High Premium, Retention Risk, Price Sensitive |
| Claim Lite | `claim_lite`（或 triage category） | Manual Handle | Urgent, Needs Fast Response, Injury optional |
| Add Vehicle Draft | `add_car` | Draft | WeCom, missing ZIP |
| Add Vehicle Ready | `add_car` | Ready for Broker | 全字段 minus confirm |
| Coverage Risk example | overlay on Add Vehicle 或独立 seed | Manual Handle facet | Coverage Risk, Coverage Suspended Reminder |

**Stop Condition：**

- ❌ 不做 `TRUNCATE service_records` 无 WHERE  
- ❌ 不 reset 生产 sync_cursor 除非明确 rehearsal mode  
- ❌ 不依赖手工 psql  

---

### Feature 3: Premium Review minimal

| 维度 | 分析 |
|------|------|
| **intent.py** | ✅ `policy_review` 已有 |
| **新 service_lane** | 可用现有 `policy_review`；无需 migration |
| **service_records** | ✅ 可复用；pattern 仿 `active_case_bridge` add_vehicle |
| **known/missing/flags/next** | `collected_fields`（premium, carrier, renewal, vehicle use）；`still_needed_fields`（dec page, VIN）；`risk_flags`（Retention, Price Sensitive）；`broker_next_step`（人工比价/回电） |
| **LLM** | **默认不需要** — 规则提取涨价关键词 + identity extractors |
| **真实报价** | **绝对不需要** |
| **图片 OCR** | **不需要** — 客户发图 → `document_received` placeholder |
| **Renewal notice 图片** | `evidence_events` stub + `still_needed_fields` 含 `declaration_page` + reply「收到图片，请补文字 confirmation」 |
| **最大风险** | 误承诺自动报价；Workbench 不可见；与网页 policy_review OCR 混淆启用 |
| **最小实现方案** | `slice.py`：高置信 `policy_review` + 无 active add_car flow → `create_premium_review_stub()`；规则 summary；safe reply 模板已有；**无 Start Card** |
| **Demo acceptance** | WeCom 发涨价消息 → case 出现 → Workbench 见 VIP tags + missing dec page |

**Stop Condition：**

- ❌ 不调用 `policy_review/handler.py` OCR on WeCom path  
- ❌ 不说「能便宜多少」  
- ❌ 不做 carrier API  
- ❌ 不改 B0 Start Card 逻辑  

---

### Feature 4: Claim Lite minimal

| 维度 | 分析 |
|------|------|
| **intent.py** | ✅ `claim_intake` 已有 |
| **新 service_lane** | 建议 `claim_lite` 字符串（无 migration）；或复用 triage `issue_category` |
| **字段收集** | 规则提取：accident time/location（文本）、injury markers、other party、police；photos → `photos_pending`；参照 `triage.py` claim collected/still lists |
| **urgent 显示** | `manual_followup_needed=true`；`risk_flags`: Urgent, Needs Fast Response, Claim Active |
| **自动理赔** | **绝对不需要** |
| **法律/责任判断** | **绝对不需要** — reply 用现有 claim safety template |
| **图片** | `photos_pending` only |
| **最大风险** | AI 给出「该不该报保险」建议；injury escalation 回复不当 |
| **最小实现方案** | 高置信 `claim_intake` → stub case；copy triage claim templates for reply；Workbench Manual Handle CTA；**无 Start Card** |
| **Demo acceptance** | 「刚撞了」→ case + urgent flags → broker Manual Handle |

**Stop Condition：**

- ❌ 不做 FNOL / adjuster dispatch  
- ❌ 不说「建议不报」「一定会赔」  
- ❌ Claim 期间不问 VIN（安全优先）  
- ❌ 不与 add_car flow 并行（Rule 8）  

---

### Feature 5: Add Vehicle full polish

| 维度 | 分析 |
|------|------|
| **已有完整路径** | B0：intent → Start Card → Start click → Draft → identity merge → Confirm → Done Card |
| **还缺 polish** | 见下表 |
| **改核心 B0** | **尽量不改** — 仅 UI + 边缘 flag |
| **最大回归风险** | 改 `slice.py` open-Draft merge → 复现 Q0.11.1 generic bug |
| **最小实现方案** | UI：WeCom tag, Draft badge, missing fields 显式, Confirm readiness indicator；后端：duplicate Draft guard 已有；generic no-merge 已有；correction 用 `human_confirmation_fields` |
| **Demo acceptance** | Story C live ×2：Start → 碎片 merge → Confirm → Done Card ×2 无失败 |

**Polish 清单：**

| 项 | 现状 | Sprint |
|----|------|--------|
| WeCom tag | ❌ UI | Header badge |
| Draft badge | ⚠️ status 有 | 强化 list badge |
| Missing fields display | ✅ still_needed | 布局突出 |
| Confirm readiness | ✅ quote_ready gate | UI indicator |
| No duplicate Draft | ✅ external_userid binding | regression test |
| Generic no merge | ✅ Q0.11.1 | **不碰** |
| phone/VIN/date correction | ⚠️ human_confirmation | flag 显示 |

**Stop Condition：**

- ❌ 不重构 `active_case_bridge` 核心  
- ❌ 不改 Start Card gate  
- ❌ 不加 year/make_model WeCom extractor（nice-to-have）  

---

### Feature 6: Coverage Risk flag

| 维度 | 分析 |
|------|------|
| **触发关键词** | 停保、暂停保险、coverage removed/suspended、repair、rental、return car、drive to repair、lapse、inactive coverage — triage 有 `payment_lapse` 部分覆盖；**WeCom slice 无** |
| **新建 Case** | Demo：**不**新建 restore case；作为 **risk flag overlay** on active flow + Manual Handle |
| **Workbench 显示** | Coverage Risk · vehicle may not have active coverage · broker must confirm before customer drives · next action: check policy status / call customer |
| **客户回复** | wait for broker confirmation；do not assume coverage is active |
| **最大风险** | 法律/E&O：误导客户以为 coverage 恢复；Confirm 加车 ≠ 恢复停保车 |
| **最小实现方案** | `slice.py` 或 bridge：keyword detector → set `coverage_suspended_mentioned_at` + `risk_flags[]`；cautious reply 模板；Workbench flag 区；**不** auto restore |
| **Demo acceptance** | C6 场景：Add Vehicle 进行中 + 停保提及 → Risk flag 可见 + 谨慎 reply |

**Stop Condition：**

- ❌ 不自动恢复 coverage  
- ❌ 不说「应该可以开」  
- ❌ 不把停保车 merge 进 Add Vehicle VIN 流程  
- ❌ 不做法律判断  

---

### Feature 7: Rehearsal + fallback recording

| 维度 | 分析 |
|------|------|
| **现有 demo script** | `docs/p18_chen_kui_wecom_ai_case_intake_demo.md`；P18.5 narrative；P18.7 step tables |
| **Fallback recording** | ❌ **未建** |
| **Screen recording** | 需要 — Andy 预录 full flow + 分 story clips |
| **Live 失败切换** | 60 秒内切预录屏 + seed case 静态演示 |
| **Demo 前 24h freeze** | 无新 deploy；仅 drain + seed；代码 freeze |
| **Demo 前 2h checklist** | health + drain + seed + flags verify + Workbench smoke |
| **最大风险** | 现场 debug WeCom；网络/Cloud SQL 503 |
| **最小实现方案** | 撰写 `docs/chen_kui_demo_runbook.md`（或附录）：script + fallback 切换点 + ops checklist；录屏 3 clips（A/B/C）；`demo_pre_checklist.sh` 扩展 |
| **Demo acceptance** | Andy 完整 rehearsal 1 次 <12 min；fallback 切换 <60s |

**Stop Condition：**

- ❌ 不在 demo 当天 deploy 新 revision  
- ❌ 不在现场改 Cloud Run env  
- ❌ 不依赖 live 图片  

---

## 4. WeCom Image / Media Specific Audit

### 4.1 逐项代码确认

| 问题 | 答案 | 证据 |
|------|------|------|
| WeCom `sync_msg` 对图片返回什么字段？ | API 返回 `msgtype=image` + `image.media_id` 等（WeCom 文档）；**本代码不读取** | WeCom API spec；代码未处理 |
| 当前代码是否识别图片 `msgtype`？ | **否** | `sync_msg.py` L110: 仅 `"text"` |
| 当前代码能否拿到 `media_id`？ | **否** | 零 `media_id` 引用 in `services/` |
| 是否有 WeCom media download API？ | **否** | 无 `cgi-bin/media/get` 调用 |
| 能否存 GCS？ | **否**（WeCom path） | 无 GCS in wecom/ |
| 能否关联 service_record / record_messages？ | **仅 text** via `append_follow_up_message`；`evidence_events` filename stub | `active_case_bridge.py` |
| Workbench 能否显示附件/图片已收到？ | 网页 upload attachments ✅；**WeCom 图片 ❌** | `BrokerWorkbenchTab` attachments |
| 是否有 OCR / Vision / LLM image parsing？ | 网页/triage 有；**WeCom 无** | `image_input_pipeline.py` |

### 4.2 分类总结

| 类别 | 项 |
|------|-----|
| **已有** | Text sync/send；evidence_events text stub；网页 attachment upload；triage inline OCR（非 WeCom） |
| **没有** | Image msgtype handling；media_id；media download；GCS；photos_pending flag；Workbench WeCom image display |
| **不可假设** | 客户 live 发图会被系统接收；OCR 读出 VIN；图片触发 case update |

### 4.3 Demo 建议（强制）

**B. Media path does not exist — 采用此方案：**

- Demo **不 live 发图片**  
- 用 **seed/mock** 显示 `photos_pending` / `document_received`  
- Script：「图片已记录，下一版自动保存；今天请补文字」  
- Premium dec page、Claim accident photos 均走此路径  

**C. Do not implement media unless specifically approved.**

- Sprint **不** 做 media download  
- Sprint **不** 做 OCR on WeCom images  
- 若陈总问起：roadmap item，非本次 demo scope  

---

## 5. Cost Risk Review

### 5.1 七项功能成本矩阵

| Feature | LLM | OCR/Vision | 云变动 | 风险等级 |
|---------|-----|------------|--------|----------|
| 1 Workbench screen-proof | 零 | 零 | 零 | 🟢 |
| 2 Demo seed/reset | 零 | 零 | 极低 SQL write | 🟢 |
| 3 Premium Review minimal | 零（规则） | 零（禁止 WeCom OCR） | 低 — 每 case 数条 msg | 🟢 |
| 4 Claim Lite minimal | 零 | 零 | 低 | 🟢 |
| 5 Add Vehicle polish | 零 | 零 | 低 — rehearsal 主流量 | 🟢 |
| 6 Coverage Risk flag | 零 | 零 | 零 | 🟢 |
| 7 Rehearsal + fallback | 零 | 零 | 零 | 🟢 |

### 5.2 成本风险点

| 风险 | 触发条件 | 防护 |
|------|----------|------|
| per-message LLM | 用 LLM 做 intent/summary | **禁止** — 保持 rules-first |
| OCR scope creep | 接 WeCom 图片 → policy_review handler | **禁止** — photos_pending only |
| Cloud SQL 扩容 | HA / 升 tier | Demo 保持 `db-f1-micro` |
| NAT 流量 | 大量 media download（若未来做） | 本次零 |
| Logging 膨胀 | debug logging per message | 保持 structured info level |

### 5.3 固定成本（demo 期间）

| 项 | 量级 |
|----|------|
| Cloud SQL `db-f1-micro` | ~$7–15/月 |
| Cloud NAT + static IP | ~$10–20/月 |
| Cloud Run | 按请求 — demo 可忽略 |
| Secret Manager | 极低 |

### 5.4 Demo 阶段推荐成本策略

1. **WeCom path 零 LLM** — 全部规则  
2. **零 OCR** — 图片 placeholder only  
3. **不启用** `OPENAI_API_KEY` 于 Cloud Run（或确保 triage LLM path 不被 WeCom 触发）  
4. **不升** Cloud SQL tier  
5. **不建** GCS bucket for demo  
6. Rehearsal 消息量控制在 <50/天  

---

## 6. Data Safety / Compliance / Liability Risk

### 6.1 风险矩阵

| 风险类型 | 相关 Feature | 严重度 | 现有防护 | Sprint 需补 |
|----------|-------------|--------|----------|------------|
| Insurance advice | Premium Review | 🔴 | ADR-003；reply 模板 | Workbench 不显示「建议换公司」 |
| Claim advice | Claim Lite | 🔴 | Safety reply templates | 禁止「报不报」建议 |
| Coverage active/inactive | Coverage Risk | 🔴 | triage payment_lapse 模板 | WeCom cautious reply + flag |
| Premium quote promise | Premium | 🔴 | 「人工比价」next action | UI + reply 双检 |
| Automatic policy change | Add Vehicle | 🔴 | B0 Confirm gate | Done Card 不说「已加保」 |
| Customer PII storage | 全部 | 🟡 | Cloud SQL private；API key | Demo 用测试客户 |
| Image/document storage | Premium/Claim | 🟡 | 本地 attachments | Demo 不存真实客户图 |
| Audit trail / retention | 全部 | 🟡 | state_history；evidence_events | 明确 demo data 可删 |

### 6.2 Demo-safe language（对外统一）

**EN keywords + 中文话术：**

| 原则 | 话术 |
|------|------|
| AI collects and organizes | 「我先帮您整理信息」 |
| Broker reviews | 「陈总会人工帮您看」 |
| Broker confirms | 「办公室确认后才会办」 |
| No automatic quote | 「不会在线上直接报价」 |
| No automatic claim | 「理赔决定由陈总人工处理」 |
| No automatic coverage change | 「保单变更需办公室确认」 |
| No legal determination | 「停保车辆需等陈总确认 coverage 状态」 |

### 6.3 高风险场景红线

| 场景 | 禁止用语 | 正确方向 |
|------|----------|----------|
| 客户问「能便宜多少」 | 任何数字 | 「陈总会人工比价」 |
| 客户问「要不要报保险」 | 「建议报/不报」 | 「陈总会根据情况给您建议」 |
| 停保车问「能开吗」 | 「应该可以」 | 「请等办公室确认 coverage」 |
| Confirm 加车后 | 「已经加好了」 | Done Card：「已收到信息，办公室会处理」 |

---

## 7. Implementation Order Recommendation

### Day 1: Workbench + seed/reset

| 类别 | 项 |
|------|-----|
| **必须完成** | Workbench header tags + intelligence card layout；`seed_chen_kui_demo` 4 cases；`reset_chen_kui_demo` script；30 秒 broker test on seed |
| **可选完成** | WeCom channel filter；customer grouping in list |
| **Stop condition** | 陈总能在 seed case 上看到 VIP + missing + next action；**不** 开始 Premium lane 若 Workbench 仍空白 |

### Day 2: Premium + Claim minimal lanes

| 类别 | 项 |
|------|-----|
| **必须完成** | WeCom `policy_review` → stub case；WeCom `claim_intake` → stub case；safe replies；Workbench 可见；Manual Handle label for Claim |
| **可选完成** | Live WeCom 发消息创建 case（可用 seed 代替 live） |
| **Stop condition** | Story A/B simulation 主步骤可 walkthrough；**不** 做 OCR |

### Day 3: Add Vehicle polish + Coverage Risk

| 类别 | 项 |
|------|-----|
| **必须完成** | Add Vehicle UI polish；Coverage Risk keyword + flag + reply；C6 scenario seed；rehearsal Add Vehicle ×2 |
| **可选完成** | Conflict flag UI polish；mixed-topic flag display |
| **Stop condition** | Story C live ×2 pass；C6 flag visible；**不** 改 B0 core merge logic |

### Day 4: Rehearsal + fallback

| 类别 | 项 |
|------|-----|
| **必须完成** | Full script rehearsal <12 min；fallback recordings；ops checklist；24h freeze 执行 |
| **可选完成** | Cross-story 3-day seed narrative |
| **Stop condition** | Andy 可独立完成 demo；fallback <60s；**零** 现场 deploy |

---

## 8. Go / No-Go Gate Before Coding

### 8.1 可以开始 coding 的条件

| # | 条件 | 状态 |
|---|------|------|
| 1 | Q0.11.1 PASS 证据已归档 | ✅ |
| 2 | P18.7 行为 spec 已定 | ✅ |
| 3 | 本文 asset inventory 完成 | ✅ |
| 4 | WeCom image path 已代码确认 | ✅ **不存在 — 采用 placeholder 策略** |
| 5 | Schema change 决策：**避免** | ✅ |
| 6 | Sprint 7 feature scope 已锁定 | ✅ |
| 7 | Rollback revision 已知（`fiqa-api-00142-kwq`） | ✅ |

### 8.2 必须先查清楚的问题

| 问题 | 结论 | 阻塞？ |
|------|------|--------|
| WeCom image/media path 是否必须先确认？ | **已确认：不存在** | **不阻塞** — GO with placeholder |
| Cloud Run queue flags 当前值？ | 需 deploy 前 `gcloud run services describe` 核对 | ⚠️ Day 0 ops check |
| Demo 用哪个 `external_userid`？ | 需 operator 确认测试号 | ⚠️ Day 1 seed |
| Workbench 连 Cloud Run 还是 local？ | 需统一 demo 环境 | ⚠️ Day 1 |

### 8.3 最终判断

**✅ GO — 图片 path 不完整仍 GO**

- Text/click path 可靠  
- 图片只做 `photos_pending` / `document_received` placeholder  
- **不实现** media download in this sprint  
- Day 1 Workbench screen-proof 是 hard gate  

**No-Go 触发条件（任一即停）：**

- Q0.11.1 generic safety regression  
- Cloud SQL 连接失败且无 rollback  
- Sprint scope 膨胀到 OCR / carrier API / LLM intent  

---

## 9. Final Checklist

可复制清单 — implementation sprint 启动前逐项勾选：

### Assets confirmed

- [ ] Q0.11.1 evidence: `docs/evidence/wecom_q0_11_1_resmoke_2026-07-04.md`
- [ ] WeCom text pipeline files mapped（§2A）
- [ ] B0 Add Vehicle path tested locally
- [ ] Workbench `BrokerWorkbenchTab.tsx` gap list understood（§2C）
- [ ] Cloud SQL tables inventoried — **no migration planned**（§2D）
- [ ] WeCom image path: **confirmed NOT implemented**（§4）

### Reuse list

- [ ] `wecom/slice.py` orchestrator — extend, don't rewrite
- [ ] `wecom/intent.py` — policy_review + claim_intake
- [ ] `wecom/reply.py` — safe reply templates
- [ ] `wecom/active_case_bridge.py` — case create/merge/confirm pattern
- [ ] `wecom/identity.py` — field extractors
- [ ] `inbox_triage/case_store.py` — collected/still/flags in JSON
- [ ] `BrokerWorkbenchTab.tsx` — layout extend
- [ ] `scripts/wecom_drain_queues.py` — ops drain
- [ ] `PATCH /api/inbox/cases/{id}/confirm` — broker gate

### New build list

- [ ] Workbench intelligence layout（Summary/Known/Missing/Flags/Next）
- [ ] VIP / channel / case type header badges
- [ ] Premium Review WeCom stub lane
- [ ] Claim Lite WeCom stub lane
- [ ] Coverage Risk keyword + flag + cautious reply
- [ ] `seed_chen_kui_demo` + `reset_chen_kui_demo` scripts
- [ ] Demo runbook + fallback recordings
- [ ] Manual Handle CTA label alignment

### Mock list

- [ ] VIP / Uber Black / High Premium tags — seed
- [ ] Known customer identity — seed `external_userid`
- [ ] photos_pending / document_received — seed + evidence stub
- [ ] Premium known facts partial — seed merge
- [ ] Cross-story 3 cases — seed
- [ ] AI Insights / opportunity — verbal or static placeholder

### Live list（必须真实）

- [ ] WeCom text ingress/egress
- [ ] Add Vehicle full flow（Start → Draft → merge → Confirm → Done）
- [ ] Broker Confirm click
- [ ] Cloud SQL case persist
- [ ] Manual drain post-message

### Risk list

- [ ] Q0.11.1 regression on `slice.py` edits
- [ ] Schema migration temptation — **reject**
- [ ] LLM/OCR scope creep — **reject**
- [ ] Coverage/legal advice in replies — review templates
- [ ] Live image dependency — **reject**
- [ ] Demo day deploy — **reject**
- [ ] Queue flags missing post-deploy — checklist

### Do-not-touch list

- [ ] Cloud SQL private IP / VPC / NAT topology
- [ ] `message_processed` + `sync_cursor` semantics
- [ ] B0 Start Card gate + generic no-Draft rule
- [ ] `deploy_cloud_run_core.sh` network config
- [ ] `policy_review/handler.py` OCR on WeCom path
- [ ] `office_actions` table
- [ ] Multi-flow parallel（Rule 8）
- [ ] Carrier API / rating / FNOL

### Demo acceptance criteria

- [ ] **Story A:** VIP Premium case — 30s broker test pass（type/VIP/missing/next）
- [ ] **Story B:** Claim case — urgent flags + Manual Handle visible
- [ ] **Story C:** Add Vehicle live ×2 — Done Card both times
- [ ] **C6:** Coverage Risk flag + cautious reply — no auto restore
- [ ] **Generic:** hello → guide menu, no Draft（Q0.11.1）
- [ ] **Fallback:** recording switch <60s
- [ ] **Cost:** zero LLM/OCR on WeCom path during rehearsal
- [ ] **Image:** no live image dependency; photos_pending via seed/mock

---

## 附录 A — 关键文件索引

| 层 | 文件 |
|----|------|
| WeCom callback | `services/fiqa_api/routes/wecom_kf_callback.py` |
| WeCom slice | `services/fiqa_api/wecom/slice.py` |
| WeCom sync（text only） | `services/fiqa_api/wecom/sync_msg.py` |
| Intent | `services/fiqa_api/wecom/intent.py` |
| Case bridge | `services/fiqa_api/wecom/active_case_bridge.py` |
| Reply | `services/fiqa_api/wecom/reply.py` |
| Workbench UI | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` |
| Case store | `services/fiqa_api/inbox_triage/case_store.py` |
| PG repo | `services/fiqa_api/db/service_record_repository.py` |
| Policy review | `services/fiqa_api/policy_review/handler.py` |
| Triage | `services/fiqa_api/inbox_triage/triage.py` |
| Deploy | `scripts/deploy_cloud_run_core.sh` |
| Drain | `scripts/wecom_drain_queues.py` |
| Seed（待扩展） | `scripts/prepare_unified_intake_founder_demo.py` |

---

## 附录 B — 文档关系

```
Q0.11.1 WeCom 通道 PASS
    ↓
P18.4 商业定位 → P18.5 Demo 体验 → P18.6 成本/丝滑审计 → P18.7 逐步仿真
    ↓
P18.8 本文 — 资产清点 + 风险勘查 → Go/No-Go
    ↓
Implementation sprint（3–4 天）→ 陈总 demo
```

---

*End of P18.8 — Implementation Asset Inventory + Risk Review*
