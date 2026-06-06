# P16-M Phase 1 — Surface Inventory

**Date:** 2026-06-01  
**Method:** Code audit of `UnifiedIntakePage`, `BrokerWorkbenchTab`, `CustomerEntryTab`, `AppLayout`, supporting components  
**Modes audited:** `product_only` (Chen Kui trial) vs full dev UI  
**Screens:** Broker Workbench · Customer Intake · Case Detail (broker)

Legend: **Remove?** / **Hide?** / **Collapse?** / **Move?** — evaluation only; no implementation in P16-M.

---

## A. Global Chrome (all Unified Intake routes)

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Dark app header — app title | Brand + context | Medium | No | product_only: yes (merge into white card) | — | Into product island |
| Dark app header — 返回工作台 link | Lab navigation | Low in trial | Yes (trial) | Already hidden product_only | — | — |
| Grey page gutter (`#e8eaed`) | Visual separation from lab shell | Low | No | — | — | — |
| White brand card — Chen Kui avatar | Trust / human broker | High for trial | No | Optional | — | Keep |
| White brand card — 金盾保险 · 陈魁团队 | Brand identity | High | No | — | — | — |
| White brand card — tagline | Product promise | High | No | — | — | — |
| Trust line (product_only) | Manual-send boundary | **Critical** | No | — | — | — |
| Pilot intro Alert (full UI only) | Scope / honesty | Medium dev; noise trial | Yes (trial) | product_only already | Default collapsed full UI | — |
| 显示产品说明 link | Re-open intro | Low | Yes | — | — | — |
| Tab bar — 客户报送 | Customer portal entry | High dev; wrong for broker trial | No | **Yes trial** | — | Separate URL |
| Tab bar — 我的办理 | Customer case list | Medium | No | **Yes trial** | — | Customer URL |
| Tab bar — 办公室工作台 | Broker surface | **Critical** | No | — | — | Default only |
| Tab bar — 场景仿真 | Engineering replay | Zero for broker | **Yes** | **Yes trial** | — | Lab-only route |
| Tab suffix text (— 加车旗舰路径…) | Internal scope note | Low; confusing | **Yes** | **Yes** | — | Docs only |

---

## B. Broker Workbench — Empty / First Visit (`product_only`)

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Page title 办公室工作台 + icon | Orientation | High | No | — | — | — |
| Subtitle (paste → review → draft) | Workflow | High | No | — | — | Merge with wayfinding |
| Secondary line (手动粘贴 · 不自动发送) | Trust | High | No | — | Merge with trust line above | — |
| Wayfinding Alert — 经纪人：请在本页粘贴 | Primary instruction | High | No | — | Merge to one line | Above paste |
| Paste card title 粘贴客户消息 | Section label | Medium | No | — | — | — |
| Paste card extra — 原样粘贴… | Expectation setting | **Critical** | No | — | — | Inside textarea hint only |
| Label 粘贴您收到的客户消息 | Redundant with title | Low | **Yes** | — | — | — |
| Textarea + placeholder | Primary input | **Critical** | No | — | — | — |
| Button 开始整理 | Primary action | **Critical** | No | — | — | — |
| Button 清空 | Reset | Medium | No | — | — | Icon-only |
| Card 快速体验（可选） | Demo onboarding | Medium Day-0; noise Day-7 | No | Defer first visit | Default collapsed | Empty-state link |
| 加载演示队列 | Demo seed | High Day-0 | No | After first case | — | — |
| Demo progress text | Prevent abandon | High | No | — | — | — |
| 3 practice scenario buttons | Playbook substitute | Medium | No | — | Inside demo collapse | — |
| Card 待处理 (queue) | Case list | High when populated | No | Empty: hide card | — | Below case detail when active |
| Queue refresh timestamp | Trust (list current) | Medium | No | — | — | Tooltip on refresh |
| Button 刷新列表 | Manual reload | Low | No | — | — | Icon-only |
| Empty queue hint text | Zero-state guidance | Medium | No | — | — | Shorter 3-step |

**Empty-state visible count (product_only, above fold): ~14–16 distinct UI objects**

---

## C. Broker Workbench — After Triage / Case Open (`product_only`)

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Case card title row — urgency + status tags | Scan priority | High | No | — | — | — |
| Short case ID (monospace) | Reference | Medium | No | — | — | Copy on hover |
| 整理结果（办公室一眼）· 三步扫读 | Primary outcome | **Critical** | No | — | — | — |
| Sub-caption (系统已把客户原文…) | Explain glance block | Low | **Yes** | — | — | — |
| ① 案子 / ② 状态 / ③ 行动 sections | Structured scan | High | No | — | ②+③ merge | — |
| 还缺什么（首要） highlight | Missing info | High | No | — | — | — |
| 跟进计划 preview in glance | Tracking | Medium | No | — | — | — |
| 客户草稿预览 (96 chars) in glance | Draft teaser | Medium | No | — | — | — |
| Card 追加客户补充 (reopened) | Follow-up intake | High | No | — | — | Above draft |
| Collapse 整理明细 | Deep detail | Medium | No | — | **Default collapsed** ✓ | — |
| Tags inside detail (事项/生命周期/…) | Engineer granularity | Low trial | **Yes** | product_only | Collapsed ✓ | — |
| 案件边界 block | Append vs new case | Medium | No | — | Collapsed | — |
| 建议人工核实 block | Risk flag | High | No | — | — | In glance |
| 结构化字段明细 collapse | Field audit | Medium | No | — | **Default collapsed** ✓ | — |
| Collapse 客户草稿（确认后再发） | Full draft | **Critical** | No | — | Default open ✓ | — |
| Tag on draft (可审核草稿 / …) | Readiness | Medium | No | — | — | — |
| Button 复制客户草稿 (header) | Primary output | **Critical** | No | — | — | Sticky |
| Dropdown 状态 | Case lifecycle | Medium | No | — | — | — |
| Collapse 完整对话/原文 | Audit trail | Medium | No | — | **Default collapsed** ✓ | — |
| Context hint when case open + paste area | Prevent double-submit | Medium | No | — | — | — |
| Queue cards (urgency + preview) | Navigation | High | No | Hide when detail focused | — | Side drawer mobile |

**Case-detail visible count (expanded draft, collapsed detail): ~18–22 objects**

---

## D. Broker Workbench — Full Dev Mode Extras (not trial)

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| 4 KPI stat cards (需立即处理/等客户/队列/高风险) | Ops dashboard | Low for broker | **Yes** | product_only ✓ | Collapsed ✓ | — |
| Segmented filters (正式/测试/旧识别/镜像异常…) | Engineering QA | Zero broker | **Yes** | product_only ✓ | — | Admin |
| API endpoint label in queue | Debug | Zero | **Yes** | product_only ✓ | — | — |
| PG mirror trust line | Infra honesty | Zero broker | **Yes** | product_only ✓ | — | — |
| Queue grouping (立即处理 / 等待或暂存) | Priority scan | Medium | No | — | — | — |
| Pagination | Scale | Medium | No | — | — | — |
| 测试管理与图例 collapse | Internal docs | Zero | **Yes** | — | — | Runbook |
| Per-card tag wall (10–15 tags) | Full metadata | Low | **Yes** | Most tags | — | Detail only |
| 复制摘要 button | Power user | Medium | No | product_only hide ✓ | — | — |
| Radio status group (inline) | Status change | Medium | No | — | — | Dropdown ✓ trial |
| Row 客户可准备 + 草稿全文 | Broker guidance | High | No | product_only: merge | Collapsed ✓ | — |
| 跟进此 case (waiting_on, dates, notes) | CRM-lite | Medium | No | product_only hidden | Collapse | — |
| 经纪人备注 / 操作记录 cards | Audit | Low Day-1 | No | product_only hidden | Collapse | — |
| Attachment upload | Add-car support | Medium | No | — | — | — |
| 记录管理/镜像/车道 collapse | Engineering | Zero | **Yes** | product_only ✓ | — | — |
| 报送与时间戳说明 collapse | Timing truth | Low | No | — | Collapsed ✓ | — |

**Full dev queue card tag count per row: up to 12 tags — primary density offender**

---

## E. Customer Intake — Empty State (full UI)

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Hero Title H2 + icon | Product identity | High customer | No | Compact when active ✓ | — | — |
| portalServiceTagline paragraph | Scope explanation | Medium | No | — | Shorten 50% | — |
| Resume in-progress hint | Continuity | Medium | No | — | — | — |
| 场景仿真 text button | Lab tool | Zero customer | **Yes** | — | — | Lab |
| IntakeFlowStepTrack (3 steps) | Progress metaphor | Medium | No | — | — | After first action |
| Empty headline + secondary | Guidance | High | No | — | — | — |
| 办理类型 label | Choice framing | Medium | No | — | — | — |
| Button 办理加车报价 (+ 推荐主路径 tag) | Primary path | High | No | — | — | — |
| Button 联系人工 | Escalation | High | No | — | — | — |
| Button 其他事项 dropdown | Secondary intents | Medium | No | — | — | — |
| Collapse 加车报价·结构化报送 | Hybrid intake | Medium | No | — | **Default collapsed** ✓ | — |
| 5 structured input fields | Faster add-car | Medium | No | — | Inside collapse ✓ | — |
| Input area + submit (when empty) | Free text | High | No | — | — | — |

**Customer empty-state count: ~16–18 objects — high for 5-second test**

---

## F. Customer Intake — Active / Post-Handoff

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Compact hero card | Context | Medium | No | — | — | — |
| Add-car transaction banner | Lane clarity | Medium | No | — | — | — |
| AddCarCaseStatusStrip chips | Status | High | No | — | — | — |
| Progress card 加车报价·进度 | Task record | High | No | — | — | — |
| AddCarRecordSummaryRail | Structured summary | High | No | — | — | — |
| Service record ID (monospace) | Reference | Medium | No | — | — | — |
| Chat thread bubbles | Conversational UX | Medium | No | — | **Collapsed post-handoff** ✓ | — |
| Bubble micro-tags (urgency, lifecycle…) | Metadata | Low customer | **Yes** | Most | — | Result card |
| Result card 受理结果卡 | Outcome | **Critical** | No | — | — | — |
| Formal submitted timestamp block | Trust | Medium | No | — | — | — |
| Timing truth footnote (UTC…) | Engineer honesty | Low customer | **Yes** | — | — | Tooltip |
| 办公室侧下一步 | Expectation | High | No | — | — | — |
| 您这边下一步 | Customer action | High | No | — | — | — |
| Append-to-same-record UI | Continuity | Medium | No | — | — | — |
| 提交新问题 boundary UI | New issue | Medium | No | — | — | — |
| Light identity / WeChat strip | Future continuity | Low v1 | No | Hide default | — | — |
| Button 查看工作台 | Broker handoff | Dev only | N/A trial | — | — | — |
| AddCarFlowExplanation | Education | Low | **Yes** | — | Collapse | — |

---

## G. Case Detail — Customer-Facing Result Card (within Customer tab)

Treat as third screen for customer mental model after formal submit.

| Visible item | Purpose | Value | Remove? | Hide? | Collapse? | Move? |
|--------------|---------|-------|---------|-------|-----------|-------|
| Eyebrow 加车报价·受理结果卡 | Type label | Medium | No | — | — | — |
| Eyebrow hint 非聊天流水 | Set expectation | Medium | No | — | — | — |
| Status strip | Phase | High | No | — | — | — |
| Grouped snapshot fields | What was captured | High | No | — | — | — |
| Closure / office reply section | Outcome | High | No | — | — | — |
| Link 我的办理 | Self-service tracking | Medium | No | Hide trial | — | — |

---

## Summary Counts

| Screen | Mode | Est. visible objects (typical) | Target after P16-M purge |
|--------|------|-------------------------------|--------------------------|
| Broker Workbench empty | product_only | 14–16 | 8–10 |
| Broker Workbench + case | product_only | 18–22 | 10–14 |
| Broker Workbench | full dev | 45–70 | 20–35 |
| Customer empty | full dev | 16–18 | 8–10 |
| Customer active | full dev | 25–35 | 12–18 |
| Case detail (broker) | product_only | 15–20 (many collapsed) | 8–12 expanded |

**Primary density offenders:** tag walls on queue cards (dev), duplicate trust/wayfinding lines, demo card above paste on repeat visits, customer empty-state choice overload, engineer timing footnotes on customer cards.

---

*End of P16-M Surface Inventory*
