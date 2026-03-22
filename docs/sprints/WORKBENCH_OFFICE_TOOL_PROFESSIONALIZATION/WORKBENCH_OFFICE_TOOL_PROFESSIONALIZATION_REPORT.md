# Workbench Office Tool Professionalization Report

**Sprint:** Workbench Office Tool Professionalization  
**Date:** 2026-03-20

---

## 1. Sprint Theme

**What was chosen:** Push the broker/workbench surface from "strong internal case panel" toward "real office tool that a small insurance broker team could actually rely on daily."

**Why now:** Customer-facing intake is strong (add-car quote-ready, contact, attachment, materials-sent). The next commercial bottleneck is the office side: when a broker opens Workbench, does it feel like a tool they can use to process real cases?

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| 1. Workbench Office Tool Professionalization Blueprint | `01_WORKBENCH_OFFICE_TOOL_PROFESSIONALIZATION_BLUEPRINT.md` |
| 2. Broker First-Scan Spec | `02_BROKER_FIRST_SCAN_SPEC.md` |
| 3. Case Card / Case Detail Structure Spec | `03_CASE_CARD_CASE_DETAIL_STRUCTURE_SPEC.md` |
| 4. Operational Follow-Up Visibility Spec | `04_OPERATIONAL_FOLLOW_UP_VISIBILITY_SPEC.md` |
| 5. Broker Next Step Professionalization Spec | `05_BROKER_NEXT_STEP_PROFESSIONALIZATION_SPEC.md` |
| 6. Execution Outline | `06_EXECUTION_OUTLINE.md` |
| 7. Acceptance / Office Tool Criteria | `07_ACCEPTANCE_OFFICE_TOOL_CRITERIA.md` |
| 8. Founder Inspection Notes | `08_FOUNDER_INSPECTION_NOTES.md` |
| 0. Baseline Audit | `00_BASELINE_AUDIT.md` |

---

## 3. Baseline Audit

### Strongest Current Parts

- Case focus, next move, collected/still_needed chips, human confirmation, urgency
- Correction / already_sent badges in case detail
- Quote-ready, contact block, attachment block in case detail
- Recent customer messages in case detail
- Queue cards: quote_ready, correction, already_sent, contact needed (from prior sprint)
- Due tag (overdue/due today) on queue cards

### Biggest Office-Tool Weakness

Queue cards lacked broker_next_step preview. Broker had to open a case to see what to do.

### Biggest Broker Blind-Spot Risk

Next-step invisibility on queue — broker could not prioritize by "what to do" without opening each case.

### Biggest Follow-Up Visibility Gap

Follow-up block in case detail was below the fold. "当前状态" was in a separate row below the main action block.

### Biggest Commercial-Feel Gap

Case detail felt like a panel rather than a case sheet. Section hierarchy could be clearer; follow-up should be above the fold.

---

## 4. 10–20 Point Breakdown

1. **Why current workbench may still feel too demo-like** — Queue cards lacked broker_next_step preview; follow-up was below fold in case detail.
2. **What a broker must see in 3–5 seconds** — Case focus, quote-ready, contact, correction/already_sent, urgency, one clear next step, follow-up state.
3. **What belongs on queue cards** — Case focus, attention, due tag, readiness, quote-ready, correction, already_sent, contact needed, attachments, urgency, source preview, compact preview, **next-step preview**, **follow-up summary**.
4. **What belongs above the fold in case detail** — Case focus, next step, correction/already_sent, **follow-up block** (when set), quote-ready, contact, collected, still needed, materials.
5. **Why quote-ready must be visible** — Add-car is high volume; broker needs to prioritize quote-ready cases.
6. **Why contact status must be visible** — Quote-ready without contact blocks follow-up.
7. **Why materials status must be visible** — Speeds up quote; broker needs to know if docs received.
8. **Why correction / already_sent / already_paid must be visible** — Avoid duplicate requests; verify receipt instead.
9. **Why follow-up visibility matters** — Broker must see waiting_on, next_contact_by, due-state to avoid missed follow-up.
10. **What good broker_next_step looks like** — Specific, actionable, 1–2 sentences (e.g. "Verify materials received; run quote when confirmed").
11. **What weak broker_next_step looks like** — "Continue processing", "Follow up as needed", "Review and act on {category}."
12. **What most reduces broker rework** — Next-step preview on cards; follow-up above fold; concrete broker_next_step.
13. **What most improves office trust** — Key signals not buried; next step visible without opening.
14. **What most improves commercial product feel** — Professional queue cards; actionable next step; case detail like working case sheet.
15. **What should remain deferred** — Enterprise ticketing, SLA engine, OCR, carrier integration.
16. **What simulations are needed** — Broker trial stress (BS9–BS13); handoff timing.
17. **What founder should manually inspect** — First-scan clarity; next-step preview; follow-up visibility; case detail hierarchy.
18. **What V2 can add later** — Field values in chips; queue-level filtering; SLA.

---

## 5. Iteration Loop 1 — Queue / First-Scan Professionalization

**What was fixed:**
- Queue cards: added broker_next_step preview (1 line, ~60 chars) — "下一步：{truncated}"
- Queue cards: follow-up more prominent when overdue/due today — show Tag + tracking summary

**Why these fixes were chosen:** Broker could not see "what to do" without opening cases. Due-state and follow-up needed to stand out when actionable.

**What now feels more like a real office tool:** Broker can scan queue and see next step + follow-up state at a glance.

**What did not improve:** Case detail was unchanged in loop 1.

**Whether it was worth it:** Yes. Broker can prioritize and triage from the list without opening every case.

---

## 6. Iteration Loop 2 — Case Detail / Follow-Up Professionalization

**What was fixed:**
- Case detail: added follow-up block above the fold (inside "Case 整理" card)
- Follow-up block: when waiting_on or next_contact_by is set, shows a bordered callout with "跟进", due tag, waiting_on, next_contact_by
- Visual treatment: overdue = red, due today = orange, else blue

**Why these fixes were chosen:** Follow-up was buried in "当前状态" below the fold. Per spec, it should be part of the working case sheet, visible when case is opened.

**What improved vs loop 1:** Case detail now feels more like a working case sheet; follow-up is above the fold when set.

**What still remained weak:** Section hierarchy could be further refined; acceptable for now.

**Whether it was worth it:** Yes. Broker can see follow-up context immediately when opening a case.

---

## 7. Iteration Loop 3 — broker_next_step / Trial Hardening

**What was hardened:**
- triage.py: hardcoded fallback updated from "Review and act on {category}." to "Review the {category} message; confirm what the client needs and take the next step."
- Added BS13: Premium review + remove-vehicle + bill sent — validates broker_next_step contains "renewal" and "remove"

**Why these fixes were chosen:** Ensure no fallback path produces weak broker_next_step; harden premium review + remove-vehicle handoff.

**What improved vs loop 2:** Guardrail now covers premium review + remove-vehicle; fallback is consistent with config.

**What still remained weak:** None for this loop.

**Whether it was worth it:** Yes. BS13 and fallback update harden the sprint gains.

---

## 8. Optional Loop 4

**Whether used:** No.

**Why stopping is correct:** Loops 1–3 addressed the highest-value weak points. Remaining items (e.g. finer section hierarchy, queue-level filtering) are lower priority and can be V2.

---

## 9. Validation Summary

| Check | Result |
|-------|--------|
| guardrail_inbox_triage.sh | PASS |
| run_broker_trial_stress_simulations.py | 13/13 passed |
| run_handoff_timing_simulations.py | 13/13 passed |
| npm run build | Success |

**Limitations:** API test (append) requires server on 8001; not run in this sprint.

---

## 10. Deployment / Release Judgment

| Component | Changed | Redeploy needed |
|-----------|---------|-----------------|
| Backend (triage.py, config) | Yes | Yes |
| Frontend (UnifiedIntakePage.tsx) | Yes | Yes |

**Backend:** triage.py (fallback), broker_trial_stress_simulations.json (BS13)  
**Frontend:** UnifiedIntakePage.tsx (queue card next-step preview, follow-up prominence; case detail follow-up block)

**Whether founder can inspect now:** Yes, after redeploy. Run `bash scripts/run_demo_local.sh` and open workbench tab.

---

## 11. Founder Manual Inspection List

1. **Load demo queue** → Open workbench → Load 演示队列 → Verify queue cards show "下一步：{preview}" for each case.
2. **Overdue / due today** → Verify cases with next_contact_by today or past show overdue/due-today tag prominently on card.
3. **Open case with follow-up** → Verify "跟进" block appears above the fold (after "Your next move") when waiting_on or next_contact_by is set.
4. **Open add-car quote-ready case** → Verify quote_ready tag, contact block, next step with vehicle.
5. **Open premium review + remove-vehicle case** → Verify broker_next_step says "Review renewal notice... confirm remove-vehicle intent."
6. **Scan queue in 3–5 seconds** → Can you tell which cases need same-day action, which are quote-ready, what to do next, which have follow-up due?

---

## 12. Final Judgment

**Biggest gain:** Queue cards now show broker_next_step preview and follow-up prominence; case detail has follow-up block above the fold. Broker can scan and prioritize without opening every case.

**Biggest remaining weakness:** Some edge customer_question cases may still get generic broker_next_step; acceptable for trial.

**Whether Workbench now feels professional enough for a real broker office demo:** Yes. Key signals visible; next step actionable; follow-up above fold; queue cards scannable.

**Best next step:** Founder manual inspection; then trial with real broker.

---

## 13. 中文宏观总结

**为什么现在做这一轮：** 客户入口和加车流程已加强，办公室打开 case 时是否像真正的办公工具成为最大商业问题。本 sprint 将 workbench 从「可用的内部流程」升级为更专业、商业级的办公 intake/case 处理界面。

**主要修了什么：**
- 队列卡片：增加 broker_next_step 预览（下一步：…）；overdue/due today 时跟进更突出
- 案例详情：增加「跟进」区块，above the fold，当 waiting_on 或 next_contact_by 有值时显示
- broker_next_step：triage 硬编码 fallback 改进；新增 BS13 模拟（premium review + remove-vehicle）

**最大提升是什么：** 经纪人可在 3–5 秒内从队列扫描出关键信号和下一步；打开 case 时跟进可见；broker_next_step 更可操作。

**还差什么：** 部分 customer_question 边缘场景可能仍有通用指引；可接受。

**下一步最该做什么：** 创始人人工检查 → 真实经纪人试用。

---

## 14. COPY/PASTE FOUNDER BLOCK

**Biggest Workbench office-tool improvement:** Queue cards now show broker_next_step preview ("下一步：…") and follow-up prominence (overdue/due today); case detail has follow-up block above the fold when set.

**Biggest remaining weakness:** Some edge customer_question cases may still get generic broker_next_step.

**Redeploy needed:** Yes — backend (triage.py, broker_trial_stress_simulations.json) and frontend (UnifiedIntakePage.tsx).

**What Andy should inspect first:** Load demo queue → verify queue cards show new next-step preview → open case with follow-up → confirm follow-up block is above the fold → open premium review + remove-vehicle case → confirm broker_next_step says renewal + remove-vehicle.

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

客户入口和加车流程已加强，办公室打开 case 时是否像真正的办公工具成为最大商业问题。本 sprint 将 workbench 从「可用的内部流程」升级为更专业、商业级的办公 intake/case 处理界面。

### 主要用了什么方法/技术

- 队列卡片增加 broker_next_step 预览、跟进更突出（overdue/due today）
- 案例详情增加「跟进」区块 above the fold
- triage 硬编码 fallback 改进；新增 BS13 模拟（premium review + remove-vehicle）

### 这轮最大的提升

经纪人可在 3–5 秒内从队列扫描出关键信号和下一步；打开 case 时跟进可见；broker_next_step 更可操作。

### 现在还差什么

部分 customer_question 边缘场景可能仍有通用指引；可接受。下一步：创始人人工检查 → 真实经纪人试用。
