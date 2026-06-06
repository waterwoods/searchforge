# Today Commercial Progress Master Summary

**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Audience:** Founder / internal strategy  
**Date:** 2026-03-20  
**Mode:** Document-driven synthesis — no new build in this sprint

---

## 1. 我们现在这个产品到底是什么

我们在做的是面向加州车险小办公室（尤其服务华语客户）的 **Unified Entry**：客户 messy 消息一贴，系统做多轮收集与 triage，产出结构化 **case**、可执行的 **broker_next_step**、**Collected / Still needed**、可编辑的 **client reply draft**，再 handoff 到 **Broker Workbench** 做队列与跟进记忆；**不自动外发**，经纪人确认后再发。**不是** 通用聊天机器人、完整 CRM、inbox 全渠道同步、报价引擎或 carrier 集成。**价值**在于省掉反复读贴、分类、从零写回复的时间，把「办公室下一步该干什么」说清楚。

---

## 2. 今天和最近几轮最重要的推进

最近几轮的主线，是把产品从「能 demo」推进到「办公室愿意每天打开」。**Unified Intake UI** 做了专业化：版式、层次、关键字段更像正经 **B2B tool**，而不是临时页面。**Add-Car** 仍是旗舰：多轮问法更贴近真实微信对话。**quote-ready / almost_ready / need_more** 与「要不要附件」拆开，办公室不会被 UI 误导。**Identity / contact-lite** 让 case 更像真人客户，而不是匿名测试串。**attachment-ready lite** 覆盖「客户甩图 / PDF」：能传、能看、默认不挡主流程。**Materials-sent、already-sent** 与 **billing** 相关路径在规则与场景里加固，减少「客户说过了但系统不知道」类 handoff 事故。**Workbench** 继续往 **office tool** 收：队列、urgency、跟进与重开上下文更一致。**中文** 在 queue 预览与 Workbench 用语上做了对齐，降低华语经纪人的认知摩擦。**Persistence** 被写成明确架构结论：当前是 **JSON + 本地附件** 的轻量层，并标出与未来商用存储的边界。**成熟骨架**（Stripe/Page、Amazon/Flow、Intercom/Handoff、Zendesk/State）被写进文档，方便全员用同一套语言讨论产品成熟度（见下一节）。

---

## 3. 成熟骨架总纲

**Mature reference mix（最终参照组合）：**

- **Stripe** 管 **Page**：页面信息架构、信任感、关键 CTA 与层次 — 让人一眼知道在哪、下一步点哪。
- **Amazon-style** 管 **Flow**：步骤清晰、少迷路、每步可完成 — 用户一步一步怎么走，不依赖经纪人脑内流程图。
- **Intercom** 管 **Handoff**：从「对话/收集」到「交给正确的人」时，上下文与下一步不丢 — 办公室接手时知道发生了什么、要回什么。
- **Zendesk** 管 **State**：ticket/case 生命周期、状态、字段 — 现在进行到哪一步、谁在等什么。

**Four Backbones（创始人语言）：**

- **Page**：页面长什么样 — 专业度、可读性、关键信息是否一眼可见。
- **Flow**：用户一步一步怎么走 — intake 多轮、quote-ready 门槛、材料路径是否自然。
- **State**：现在进行到哪一步 — case 状态、队列、跟进记忆、重开是否可信。
- **Handoff**：交给办公室时带什么信息 — broker_next_step、Collected/Still needed、草稿、urgency、修正/已发送等上下文。

**应借鉴的：** 清晰的 IA、步骤化 flow、handoff 包裹完整上下文、case 状态可运营。**必须垂直专精的：** 加州车险规则、华语客户话术、add-car / billing / materials-sent 等 **broker-grade** 业务逻辑 — 通用工单平台换皮做不出来。

---

## 4. 我们现在最像商业产品的地方

**Intake → case → Workbench** 闭环已经像一条真实产品线，而不是单次 demo 脚本。**标准场景包**（含 add-car、缺件、账单、理赔初响等）有可对外复述的 **package** 叙事。**Guardrail / simulation / handoff timing** 一类脚本把「别在 trial 现场翻车」做成了可重复检查，这是 **paid-trial** 级交付心态。**经纪人价值**直接可讲：少读贴、少重复问、少漏跟、handoff 带齐下一步。

---

## 5. 我们现在还不够商业化的地方

**生产级 infra** 仍是单租户、轻部署思路。我们不是多区域、SLA、可观测性拉满的平台型团队交付物。**Persistence** 是本地 JSON + 磁盘附件。它 **不是** 托管 DB、权限隔离、备份恢复完备的 **data layer**。**没有 quote engine / carrier API**。产品停在 **quote-ready** 与办公室下一步，不产出可绑单的费率。**无 OCR / 结构化抽取**。附件可见，但不会自动回填字段。UI 与部分 handoff 仍有 **polish gap**：细看能挑出不一致或解释成本。**真实经纪人 trial 的量化证据**偏少。文档与 guardrail 已 ready，但 **paid story** 还需要现场摩擦数据支撑。

---

## 6. 我们离「真正能上线收钱的平台」还有多远

用五档描述：

| 阶段 | 含义 |
|------|------|
| **Demo-like** | 能讲清故事，路径脆，不宜收钱 |
| **Pilot-ready** | 可约真实经纪人试用，已知边界 |
| **Paid-trial ready** | 可标价短试用，有检查清单与修复闭环 |
| **Commercial v1 ready** | 稳定计费、数据与合规基线、可续费 |
| **Scaled product ready** | 多客户、多租户、深度集成、平台运营 |

**诚实判断：整体在 Pilot-ready 与 Paid-trial ready 之间。** 场景深度、Workbench、规则与 guardrail 已能支撑 **短周期收费试用** 的对外说法。**我们还没到 Commercial v1**：没有自动计费集成，也没有企业级数据与合规基线。**要升到 Commercial v1**，至少需要：可重复的 **trial 证据**、明确的 **数据驻留与恢复** 策略、以及「客户愿意续费」的信号。**进入下一阶的最短路径** 仍是：跑完至少一轮 **真实 trial**，把摩擦收进 **fix-now / fix-next**。**Handoff 与 billing 路由** 应随真实对话继续加固。**Persistence** 是否在 pilot 期升级，应只由 **数据丢失风险** 与 **部署形态** 驱动，不必为「好看」提前上重型 DB。**Scaled product** 需要多租户、深度 inbox、carrier 等 — 与当前目标不同。**暂不应做：** 无 trial 证据前预建 OCR、carrier、全渠道 inbox — ROI 差、分散焦点。

---

## 7. 现在最值得继续做的三件事

1. **Trial 执行 + 观察闭环** — 启动陈奎侧真实使用，按 trial 文档采集摩擦，固化「修什么、defer 什么」。  
2. **Handoff / office 信任加固** — correction、already_sent、账单类路由与 Workbench 一致性，确保「交给办公室」这一 backbone 不输 Intercom 叙事。  
3. **Paid-trial 交付包** — 一页 offer、检查脚本、证据截图/日志模板，让 **manual 收款** 路径极短、极清晰。

---

## 8. 明确不要现在做的东西

除非 trial 强烈证明否则 **defer**：**OCR / AI 抽取**（成本、错误类型、责任边界未验证）；**carrier API / 真报价**（合同与集成量级远超当前阶段）；**完整 enterprise ticketing**（我们已有垂直 case 模型，不必复刻 Zendesk 全家桶）；**多通道 inbox 实时同步**；**多租户 auth / Stripe**（与 paid pilot 目标文档一致：首单可手工收款）。优先用 **垂直规则 + 人工确认** 换确定性与速度。

---

*End of Today Commercial Progress Master Summary*
