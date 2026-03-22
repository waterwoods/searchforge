# Commercial Product Framework Overview

**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Purpose:** 创始人级产品框架概览，便于决策与 ChatGPT 复用  
**Created:** 2026-03-19 — Commercial Product Framework Overview Sprint

---

## 1. 产品定位

本产品是面向加州车险经纪人的 **Trusted Assistant**：把客户发来的 messy 消息整理成结构化 case，有下一步动作、收集了什么、还缺什么、草稿回复。经纪人确认后再发，不自动发送。**不是** 通用 AI 聊天机器人、不是完整 CRM、不是自动化外发系统。目标用户：服务华语客户的加州车险小办公室（1–5 人），以 WeChat/email 为主要渠道。

---

## 2. 现在已经做出来的核心能力

| 能力 | 状态 |
|------|------|
| **Unified Intake** | 一贴即结构化 triage；多轮收集；handoff 到 Workbench |
| **Broker Workbench** | 队列、case card、Collected/Still needed chips、broker_next_step、follow-up memory、reopen context |
| **Add-Car 旗舰场景** | 多轮收集 year/model/zip；quote-ready 可见性；concrete vehicle 在 broker_next_step；coverage/garaging 旁问处理 |
| **Quote-ready visibility** | quote_ready / almost_ready / need_more；与 attachment 分离 |
| **Identity/contact layer** | customer_name、customer_phone 提取；Contact block 可见；quote-ready 时 contact 仍可 still_needed |
| **Attachment-ready lite** | case_attachments、上传 API、Workbench 可见；optional 不阻塞 |
| **Client-aware config** | 按 client 的 handoff phrases、templates；client_id 持久化 |
| **Scenario Logic Center** | 规则在 config；detect → ask → enough? → handoff；5 层架构（rules / knowledge / client / state / tests） |
| **Simulation / guardrail / handoff timing** | 64/64 guardrail、41/41 multi-turn、12/12 handoff timing；founder demo queue、SIM1–SIM15；billing route、mixed-intent、correction/already_sent 加固 |

---

## 3. 现在最有商业价值的部分

经纪人愿意用，因为：**省时间**（一贴即 triage，不用手动读/分）、**少重复解释**（草稿可编辑，不用从零写）、**少漏跟**（urgency + escalation 浮出 same-day action）。办公室直接价值：Collected chips 避免重复问、Still needed 明确下一步、broker_next_step 一句话可执行、follow-up memory（waiting_on、next_contact_by）不丢单。已有 7 场景标准包（add-car、missing doc、cancellation risk、premium review、billing、claim、talk-to-agent）。

---

## 4. 和通用平台相比，我们的差异化

与 Zendesk / Intercom / Shopify Inbox 相比：**垂直专精**（加州车险 + 华语客户）、**部署更快**（无 enterprise 配置）、**配置更少**（规则 + retrieval + human-backed，非通用 workflow 搭建）、**保险专用 handoff/intake 逻辑**（add-car 多轮、quote-ready、cancellation  urgency、missing doc 验证）。通用平台需大量定制；我们开箱即用。

---

## 5. 现在最大的不足

UI/product polish 不足，尚非「大公司产品」观感。**无真实 quote engine**（只到 quote-ready，不报价）。**无 OCR / extraction**（附件可见但无 AI 解析）。**无真实 broker trial 证据**（trial-ready 但尚未执行）。部分 handoff 细节仍在改进（correction/already_sent 可见性、billing 路由、field values in chips）。无 inbox sync、无 carrier API。

---

## 6. 下一步最该加力的方向

| 优先级 | 方向 |
|--------|------|
| **1** | **Trial 执行 + fix-next 加固** — 运行真实 trial；修复 billing 路由；加固 Workbench handoff（correction/already_sent）；捕获观察；填 fix-now queue |
| **2** | Add-car 旗舰强化 — 已有 excellence；可继续 HT12、coverage 等 refinement |
| **3** | UI productization — 观感提升；大公司产品感 |
| **4** | Template/config 复用 — 为 client B/C 准备；时机在首 pilot 之后 |

**明确 defer：** OCR / AI 辅助提取（陷阱：成本高、风险大、无 trial 前证据）。Config 扩展（有价值但首 pilot 后做）。

---

*End of Commercial Product Framework Overview*
