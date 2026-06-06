# P16-M Phase 2 — Delete-First Review (Top 100)

**Date:** 2026-06-01  
**Question asked:** What can be removed? (Not: what should be added?)  
**Goal:** Reduce visible UI 30–50% without changing capability scope  
**Rank buckets:** Must delete · Hide by default · Collapse · Keep

---

## Must Delete (1–25) — Zero broker/customer value in trial

| # | Element | Screen | Rationale |
|---|---------|--------|-----------|
| 1 | Tab suffix — 加车旗舰路径 · 与客户报送同一服务记录 | Global tabs | Internal sprint language |
| 2 | Tab 场景仿真 | Global | Engineering tool; not product |
| 3 | 场景仿真 link on customer hero | Customer | Same |
| 4 | API endpoint label (`数据接口` + URL) | Broker queue | Engineer chrome |
| 5 | PG 镜像 tags + trust line | Broker queue/detail | "Product unfinished" signal |
| 6 | 路由/指标 debug tag | Broker queue | Engineering |
| 7 | Segmented filter 镜像异常 / 旧识别 | Broker queue | QA-only |
| 8 | KPI cards row (4-up stats) | Broker | Dashboard cosplay |
| 9 | Collapse 测试管理与图例 | Broker queue | Runbook content in UI |
| 10 | Collapse 演示与运营信号 intro text | Broker dev | Paragraph noise |
| 11 | Pilot intro Alert wall (value/does/doesNot tags) | Global full UI | Replace with one trust line |
| 12 | 显示产品说明 link | Global | Orphan control |
| 13 | English nav label "Unified Intake" | Sidebar dev | Unprofessional |
| 14 | Sub-caption under 整理结果一眼 | Case detail | Redundant instruction |
| 15 | Label 粘贴您收到的客户消息 | Broker paste | Duplicates card title |
| 16 | Secondary paste helper paragraph (product_only) | Broker | Placeholder suffices |
| 17 | Customer timing footnote (UTC 戳的本地显示…) | Customer result | Engineer honesty → tooltip |
| 18 | Bubble-level tags (跟进/需核对) on every turn | Customer thread | Move to result card |
| 19 | AddCarFlowExplanation block | Customer | Tutorial in product |
| 20 | person_link_key monospace + confidence % | Case detail | Identity stub debug |
| 21 | boundary_reason monospace line | Case detail | Internal |
| 22 | quote_ready_status English raw fallback | Tags | Never show raw enum |
| 23 | conversation_summary regex "Collected:" lines | Case detail | Duplicate of structured fields |
| 24 | getResponseWindow urgency footnote | Case detail | Redundant with urgency tag |
| 25 | Duplicate append UI (reopened card + dev card) | Case detail | One surface only |

---

## Hide by Default (26–50) — Valid but not first-screen

| # | Element | Screen | Show when |
|---|---------|--------|-----------|
| 26 | Card 快速体验（可选） | Broker | Empty queue + first session |
| 27 | 加载演示队列 button | Broker | Empty state link |
| 28 | 3 practice scenario buttons | Broker | Inside demo collapse |
| 29 | Tab 客户报送 | Global trial | Separate customer URL only |
| 30 | Tab 我的办理 | Global trial | Customer URL |
| 31 | Queue card entire section | Broker | When cases exist OR collapsed strip |
| 32 | 刷新列表 + timestamp row | Broker | Hover/focus on queue |
| 33 | Short case ID monospace | Case detail | Copy affordance only |
| 34 | Dropdown 状态 | Case detail | More menu |
| 35 | 结构化字段明细 collapse | Case detail | Always collapsed |
| 36 | 更多状态标签 collapse | Case detail | Always collapsed |
| 37 | 完整对话/原文 collapse | Case detail | Always collapsed |
| 38 | 记录管理/镜像/车道 | Case detail dev | Never in product_only |
| 39 | 报送与时间戳说明 | Case detail | Collapsed; broker ask |
| 40 | 客户可准备 card | Case detail dev | Merge into glance |
| 41 | 跟进此 case block | Case detail | Day-7+ power |
| 42 | 经纪人备注 / 操作记录 | Case detail | Day-7+ power |
| 43 | Attachment upload | Case detail | Add-car cases only |
| 44 | 加车报价·结构化报送 collapse | Customer empty | Collapsed default ✓ |
| 45 | Light identity WeChat strip | Customer | After formal submit opt-in |
| 46 | Resume multi-case hint | Customer | Only when ≥2 in progress |
| 47 | IntakeFlowStepTrack | Customer | After first button click |
| 48 | 其他事项 dropdown | Customer | After primary two buttons |
| 49 | Collapse 展开报送原文 | Customer post-handoff | Already collapsed ✓ |
| 50 | Dark app header (title duplicate) | Global | Merge into white card |

---

## Collapse (51–75) — Keep capability, hide depth

| # | Element | Screen | Default state |
|---|---------|--------|---------------|
| 51 | 整理明细 | Case detail | Collapsed ✓ |
| 52 | 客户草稿 full text | Case detail | Open (primary output) |
| 53 | 完整对话 | Case detail | Collapsed ✓ |
| 54 | 结构化字段 | Case detail | Collapsed ✓ |
| 55 | 案件边界 block | Case detail | Collapsed |
| 56 | 建议人工核实 | Case detail | Inline in glance only |
| 57 | 跟进计划 in glance | Case detail | One line; detail collapsed |
| 58 | Queue tag wall (dev) | Broker list | Max 2 tags visible |
| 59 | AddCarCaseStatusStrip on list cards | Broker dev | Hide on list; show detail |
| 60 | Service record ID on list cards | Broker | Detail only |
| 61 | Broker next preview on list cards | Broker | Detail only |
| 62 | Follow-up tracking on list cards | Broker | Icon/badge only |
| 63 | Example cases panel | Broker dev | Collapsed |
| 64 | Demo queue progress tag | Broker | During load only |
| 65 | Customer chat thread pre-handoff | Customer | Collapsed add-car ✓ |
| 66 | Customer chat thread post-handoff | Customer | Collapsed ✓ |
| 67 | Progress card secondary sections | Customer | Primary rail only |
| 68 | 已记录要点 / 仍缺 tags | Customer generic | Inside progress card |
| 69 | Formal timestamp block | Customer | One line in result card |
| 70 | Wayfinding Alert body | Broker | Title only; drop description |
| 71 | Page subtitle + trust line | Broker | Single merged line |
| 72 | Paste card extra subtitle | Broker | Into placeholder |
| 73 | Context hint (已打开的记录…) | Broker paste | Toast once |
| 74 | 整理结果 ①②③ numbering | Case detail | Visual hierarchy without numbers |
| 75 | Empty queue hint paragraph | Broker | 3-step bullets |

---

## Keep (76–100) — Core product contract

| # | Element | Screen | Why keep |
|---|---------|--------|----------|
| 76 | Brand card (avatar + team + tagline) | Global | Trust |
| 77 | Trust line 不自动对外发送 | Global | **Constitution** |
| 78 | Paste textarea | Broker | Primary input |
| 79 | 开始整理 | Broker | Primary action |
| 80 | 复制客户草稿 | Case detail | Primary output |
| 81 | 整理结果一眼 (glance summary) | Case detail | Core value |
| 82 | 还缺什么 highlight | Case detail | Action clarity |
| 83 | 主行动（办公室） line | Case detail | Next step |
| 84 | Urgency tag | Case/queue | Priority |
| 85 | Loading 首次分析约30秒 | Broker | Prevents abandon |
| 86 | 追加客户补充 | Case reopened | Follow-up intake |
| 87 | Queue row (urgency + preview) product_only | Broker | Navigation |
| 88 | Demo queue (Day-0 only) | Broker | Trial kickoff |
| 89 | Wayfinding one-liner | Broker | Front door |
| 90 | Customer 办理加车报价 CTA | Customer | Secondary capability |
| 91 | Customer 联系人工 | Customer | Escalation |
| 92 | Result card 受理结果卡 | Customer | Outcome |
| 93 | 办公室侧下一步 (customer) | Customer | Expectation |
| 94 | AddCarRecordSummaryRail | Customer | Structured clarity |
| 95 | Status strip chips | Both | Phase communication |
| 96 | Error Alert | Both | Failure recovery |
| 97 | 清空 | Broker | Escape hatch |
| 98 | Case status (simple) | Case detail | Workflow |
| 99 | 正式提交办公室 CTA | Customer add-car | Handoff moment |
| 100 | Empty-state paste placeholder examples | Broker | Reduces blank-page fear |

---

## Reduction Math

| Surface | Current visible (est.) | After Must delete + Hide + Collapse | Reduction |
|---------|------------------------|---------------------------------------|-----------|
| Broker product_only empty | 15 | 8 | **47%** |
| Broker product_only + case | 20 | 11 | **45%** |
| Broker full dev | 55 | 28 | **49%** |
| Customer empty | 17 | 9 | **47%** |
| Customer active | 30 | 16 | **47%** |

**Verdict:** Delete-first plan hits **30–50% target** without removing any capability output (triage, draft, case ID, queue).

---

*End of P16-M Top 100 Deletions*
