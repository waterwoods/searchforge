# Queue Preview Chinese + Workbench Language Consistency Report

**Sprint:** Queue Preview Chinese + Workbench Language Consistency Sprint  
**Completed:** 2026-03-20

---

## 1. Sprint theme

- **What was chosen:** Queue Preview Chinese + Workbench Language Consistency — high-ROI wording polish for Chen Kui Insurance Unified Entry.
- **Why now:** Product credibility has improved (customer entry, Add-Car, handoff). Remaining mixed language and internal wording weaken polish and trust. Brokers notice queue preview, case labels, and structured fields most.

---

## 2. Document set created

| Doc | Path |
|-----|------|
| Queue Preview Chinese Consistency Blueprint | `01_QUEUE_PREVIEW_CHINESE_CONSISTENCY_BLUEPRINT.md` |
| Workbench Language Audit Spec | `02_WORKBENCH_LANGUAGE_AUDIT_SPEC.md` |
| Chinese Product Wording Spec | `03_CHINESE_PRODUCT_WORDING_SPEC.md` |
| Execution Outline | `04_EXECUTION_OUTLINE.md` |
| Acceptance Criteria | `05_ACCEPTANCE_CRITERIA.md` |
| Founder Inspection Notes | `06_FOUNDER_INSPECTION_NOTES.md` |
| Final Report | `07_FINAL_REPORT.md` (this file) |

---

## 3. Baseline language audit

**Strongest current wording areas:**
- Section headers: 已收集, 还缺, 您的下一步, 跟进
- Due tags: 已逾期, 今日到期, 明日到期
- Attention labels: 已结案, 立即处理, 待您处理, 尽快跟进
- Case status options: 新建, 处理中, 等客户, 已完成
- Waiting-on options: 无阻塞, 客户, 经纪人/办公室, 保险公司, 核保

**Biggest inconsistency:**
- Queue readiness labels returned English (Ready to act, Needs more info) while status legend used Chinese (可行动, 需更多信息). Cards showed mixed vocab.

**Biggest broker-facing weakness:**
- Compact queue preview: "Collected: Year, Make/Model · Missing: VIN" — all English. First thing broker sees when scanning queue.

**Biggest internal/demo wording trace:**
- Success messages: "Case saved to recent cases", "Follow-up plan saved"
- Copy-case-snapshot output: Case:, Next move:, Collected:, Still needed:, Draft:

---

## 4. 10–20 point breakdown

1. **Mixed language hurts polish** — Broker sees queue cards in mixed English/Chinese; feels unfinished.
2. **Queue preview matters** — Highest scan frequency; broker decides what to open.
3. **Structured field labels matter** — 已收集/还缺 field names (Year, Make/Model) felt engineering-heavy.
4. **Office-oriented wording** — 已收集, 还缺, 下一步, 跟进, 在等, 今日到期, 可行动, 需更多信息.
5. **Internal wording still felt** — Same-day action, Verify receipt, Quote-ready, Collecting.
6. **Fixed first** — getQueueReadinessLabel, getCompactQueuePreview, case focus display, getCaseReportOneLiner, humanizeStructuredField.
7. **Stayed as-is** — Demo queue behavior, backend, API; FOUNDER_DEMO_QUEUE / QUICK_FILL_EXAMPLES labels (internal).
8. **Broker trust** — Consistent Chinese in queue cards and case detail improves product trust.
9. **Product feel** — Less prototype, more office tool.
10. **Deferred** — SimulationAssistant wording (broker rarely sees); conversation_summary backend strings (Collected:/Still needed:).
11. **Founder inspect** — Queue cards, compact preview, case detail labels, copy snapshot output.
12. **Future sprints** — Backend conversation_summary strings; example/demo labels if broker-facing.

---

## 5. Iteration loop 1

**What was fixed:**
- getQueueReadinessLabel: all labels → 可行动, 需更多信息, 可报价, 差一点, 信息不足, 当日处理, 需核实收到
- getCompactQueuePreview: Collected:/Missing: → 已收集：/还缺：; flow names → 加车报价, 保费关注, 已报事故, 材料补交, 当日处理; English fallbacks → Chinese
- CASE_FOCUS_DISPLAY_ZH + getCaseFocusDisplayLabel: case focus tags → 加车报价, 事故报险, 保费复查, 删车, 材料补交, 付款/取消风险
- getCaseReportOneLiner: Ready for handoff/Collecting → 可交办公室/信息收集中
- humanizeStructuredField: prefer CUSTOMER_FIELD_LABELS_ZH (Chinese) for broker view
- CATEGORY_DISPLAY_LABELS: all → Chinese (取消风险, 材料补交, 核保跟进, etc.)
- getDraftReadinessLabel: Edit before sending/Ready for quick broker review → 需您修改后再发/可审核草稿
- Copy case snapshot: Case:/Next move:/Collected:/Still needed:/Draft: → 案件/下一步/已收集/还缺/草稿

**Why:** Highest visibility; queue cards and case detail are primary broker touchpoints.

**What now feels more polished:** Queue cards read naturally in Chinese; readiness tags and compact preview align with status legend; case detail field names in Chinese.

**What did not improve:** Backend conversation_summary (Collected:/Still needed:) still English when displayed; example labels (CUSTOMER_ENTRY_EXAMPLES, QUICK_FILL_EXAMPLES) remain English.

**Worth it:** Yes. Highest ROI.

---

## 6. Iteration loop 2

**What was fixed:**
- getResponseWindow: Same-day broker review / Review within 1-3 business days → 建议当日处理 / 1–3 工作日内处理 / 非紧急·常规跟进
- Broker Workbench message strings: Case saved... → case 已保存到最近列表; Case marked... → 已标记为「处理中」等; Follow-up plan saved → 跟进计划已保存; Broker note saved → 备注已保存; Attachment added → 已添加附件：…; Paste the new customer message first → 请先粘贴客户新消息; Add a short broker note first → 请先添加简短备注
- Copy draft messages: No draft to copy / Client draft copied / Copy failed → 暂无草稿可复制 / 草稿已复制 / 复制失败
- Clear button → 清空
- Example loaded → 已加载
- Status legend: 您的行动 → 待您处理 (align with getCaseAttentionState)

**Why:** Case detail and message consistency; aligns with Loop 1.

**Improved vs loop 1:** Success/error messages and small UI strings now Chinese; overall tone more consistent.

**What still remained weak:** getCaseAttentionState reason strings (internal); Customer Entry turn tags.

**Worth it:** Yes.

---

## 7. Iteration loop 3

**What was fixed:**
- Customer Entry turn tags: Ready for handoff/Collecting info → 可交办公室/信息收集中; Ready to save/Collecting → 可保存/信息收集中; Follow-up: {type} → 跟进：客户更正/称已发送
- Copy snapshot button title: focus → 案件类型
- getCaseAttentionState reason strings: all → Chinese (已标记完成…, 跟进日期已过…, 当前阻塞在经纪人行动…, etc.)

**Why:** Customer Entry is visible when broker switches tabs; reason strings may surface in tooltips.

**Improved vs loop 2:** Full consistency across Customer Entry and Workbench; no remaining high-visibility English in core flows.

**What still remained weak:** Example labels (Payment failed, Missing document) — internal/demo; conversation_summary from backend.

**Stopping now correct:** Yes. Further changes (example labels, backend strings) are lower value and/or require backend work.

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| `cd ui && npm run build` | ✓ Pass |
| Logic changes | None |
| Demo queue behavior | Unchanged |

---

## 9. Deployment / release judgment

- **Frontend changed:** Yes.
- **Redeploy needed:** Yes. Run `cd ui && vercel --prod` when ready.
- **Deployment attempted:** Command run; founder should verify deployment and production URL.

---

## 10. Founder inspection list

1. **Queue cards** — 办公室工作台 → 最近 case. Check readiness tags (可行动, 需更多信息, 可报价, etc.) and compact preview line (已收集：… · 还缺：…).
2. **Case focus tags** — Tags show 加车报价, 事故报险, 保费复查, 材料补交 (not Add car quote, Claim intake).
3. **Case detail** — 已收集/还缺 field names in Chinese (车型, 车架号, 年份, etc.); 可审核草稿/需您修改后再发.
4. **Copy case snapshot** — Click 复制 case 摘要. Paste. Verify: 案件：…, 下一步：…, 已收集：…, 还缺：…, 草稿：….
5. **Success messages** — case 已保存到最近列表, 备注已保存, 跟进计划已保存, etc.
6. **Overall tone** — Workbench feels more like an office tool and less like a prototype.

---

## 11. Final judgment

- **Biggest polish gain:** Queue preview and readiness labels in Chinese; brokers can scan the queue without mixed-language friction.
- **Biggest remaining weakness:** Backend conversation_summary (Collected:/Still needed:) when displayed; example labels if shown to broker.
- **Workbench now feels more commercially polished:** Yes. Language is consistent; office tone is clear.
- **Best next step:** Deploy frontend; founder inspects production; defer backend string changes to a later sprint if needed.

---

## 12. 中文宏观总结

**为什么现在做这一轮：** 产品可信度已提升，但队列预览、case 标签、结构化字段仍有中英混用，影响专业感。经纪人最常看到的就是队列卡片和 case 详情。

**主要改了什么：** 队列准备度标签（可行动、需更多信息等）、紧凑预览（已收集/还缺）、案件类型标签（加车报价、事故报险等）、结构化字段中文、一键复制摘要、成功/错误提示、草稿准备度、跟进状态原因说明。

**最大提升是什么：** 队列卡片和 case 详情全中文呈现，经纪人扫一眼即可理解，减少“半成品”感。

**还差什么：** 后端 conversation_summary 中的 Collected:/Still needed: 仍为英文；示例标签（内部用）可暂不处理。

**下一步最该做什么：** 部署前端，创始人现场验收；如需进一步 polish，再考虑后端字符串中文化。

---

## 13. COPY/PASTE FOUNDER BLOCK

**Biggest wording/polish improvement:** Queue preview and readiness labels now consistently Chinese (可行动, 需更多信息, 已收集, 还缺, 加车报价, etc.). Brokers can scan the queue without mixed-language friction.

**Biggest remaining weakness:** Backend conversation_summary (Collected:/Still needed:) when displayed from API; low priority.

**Redeploy needed:** Yes. Run `cd ui && vercel --prod`.

**What Andy should inspect first:** 办公室工作台 → 最近 case → 看队列卡片的准备度标签和紧凑预览是否全中文；打开任意 case → 复制 case 摘要 → 粘贴检查 案件/下一步/已收集/还缺/草稿 是否为中文。

---

## 14. REQUIRED SHORT OVERVIEW

### 为什么做这件事
产品已有基础可信度，但队列预览、case 标签、结构化字段仍有中英混用，削弱专业感和信任。经纪人在队列卡片和 case 详情处最易感知。

### 主要用了什么方法/技术
文档驱动：先建 Blueprint、Audit Spec、Wording Spec；三轮迭代（queue 标签→case 详情与消息→Customer Entry 与收尾）；仅改 wording，不改逻辑和 demo 队列行为。

### 这轮最大的提升
队列预览和 readiness 标签全中文化；case 类型标签（加车报价、事故报险等）和结构化字段中文；复制摘要、成功提示、草稿准备度、跟进原因说明等一致使用中文。Workbench 更像正式办公工具。

### 现在还差什么
后端 conversation_summary 中 Collected:/Still needed: 仍为英文；示例标签（内部）可暂不处理。部署后创始人验收即可。
