# Add-Car Transaction Clarity Sprint — Final Report

**Sprint:** Add-Car Transaction Clarity (Current title + closure / handoff finish)  
**Date:** 2026-03-22  
**Scope:** Chen Kui Unified Entry — Add-Car only

---

## 1. Sprint theme

- **Evaluated/fixed:** Customer-facing transaction identity (“当前办理：加车报价”) and handoff closure (“已提交办公室 / 正在处理”) so Add-Car reads as a bounded business request, not open-ended chat.
- **Why now:** Functionality was strong; the remaining maturity gap was **semantic framing** — users and brokers still perceived a chat thread more than a formal add-car transaction with a clear finish.

## 2. Document set created

| Artifact | Path |
|----------|------|
| Blueprint | `docs/sprints/ADD_CAR_TRANSACTION_CLARITY_SPRINT/01_BLUEPRINT.md` |
| Current transaction title spec | `02_CURRENT_TRANSACTION_TITLE_SPEC.md` |
| Progress / handoff / closure spec | `03_PROGRESS_HANDOFF_CLOSURE_SPEC.md` |
| Customer transaction UX spec | `04_CUSTOMER_TRANSACTION_UX_SPEC.md` |
| Broker workbench clarity spec | `05_BROKER_WORKBENCH_CLARITY_SPEC.md` |
| Execution outline | `EXECUTION_OUTLINE.md` |
| Acceptance criteria | `ACCEPTANCE_CRITERIA.md` |
| Founder inspection notes | `FOUNDER_INSPECTION_NOTES.md` |
| Founder scenario pack | `founder_scenario_pack.json` |
| Scenario runner | `scripts/run_add_car_transaction_clarity_scenarios.py` |
| Final report | `FINAL_REPORT.md` (this file) |

## 3. Baseline audit (required questions)

1. **Where Add-Car still felt like “chat”?** Generic hero + chat bubbles + “整理中” without a persistent **transaction name**; handoff panel led with the draft only, without a **closure headline** or **boundary** line.
2. **Did the customer know they were in Add-Car?** Partially — hybrid block and tags helped, but there was no always-on **当前办理** strip during the thread.
3. **Did they know when the office had taken over?** Partially — `handoff_phrases` mentioned office, but UI did not separate **“submitted / processing”** from the conversational reply.
4. **Visual/text difference collecting vs quote-ready vs handoff?** Collecting vs quote-ready existed in tags; **handoff finish** was not visually distinct enough from mid-thread messages.
5. **Clear enough finish?** Weak — success toasts could stack; closure copy lived only inside the draft paragraph.
6. **New issue after Add-Car?** “提交新问题” existed but **why** was under-explained.

**Biggest weaknesses**

- **Transaction identity:** No persistent Add-Car title ribbon; progress card title was generic.
- **Closure:** No layered closure (headline + reply + processing + boundary); duplicate toasts.
- **Broker cleanliness:** Case sheet did not state **add-car transaction** alignment with customer entry.
- **Safest high-value fix:** Config-driven copy + structured handoff card + ribbon (UI + phrase file), small triage copy alignment for special add-car branches.

## 4. Founder scenario pack

- **Count:** 8 scenarios (`ATC-01` … `ATC-08`).
- **Coverage:** Full handoff, partial completion, correction, materials sent, quote-ready dense turn, mixed follow-up, coverage side question, closure/boundary inspection.
- **Use:** Automates triage/draft checks; founder still validates **UI ribbon + handoff card** manually (`FOUNDER_INSPECTION_NOTES.md`).

## 5. Iteration loop 1 — Title / transaction identity

- **Changed:** Customer entry **Add-Car ribbon** (`add_car_transaction_title` / `subtitle`); progress card title **`加车报价 · 进度`**; composer **当前办理：加车报价** + boundary hint; lifecycle tag text **资料已齐 · 待办公室** (when shown); `model` included in structured-field inference for early turns; triage field set helper `triageResultLooksLikeAddCar` / `customerEntryIsAddCarActive`.
- **Why:** Highest leverage for “这不是闲聊” without touching rules engine.
- **Improvement:** Stronger **transaction frame** for the whole thread.
- **Worth it:** Yes.

## 6. Iteration loop 2 — Closure / handoff finish

- **Changed:** Handoff **closure headline** + boxed **办公室回复摘要** + **processing** line (Add-Car) + **boundary hint**; **single consolidated toast** when `case_id` + `handoff_ready` (Add-Car uses `add_car_handoff_toast`); `handoff_phrases.json` **add_car** zh/en; `triage.py` doc-clarification suffix, coverage handoff suffix, materials-sent handoff copy.
- **Why:** Finish must read as **office ownership**, not assistant sign-off.
- **Improvement:** Clearer **submitted / processing** and **next request** semantics.
- **Worth it:** Yes.

## 7. Iteration loop 3 — Scenario test + product judgment

- **Tested:** `scripts/run_add_car_transaction_clarity_scenarios.py` (8/8), `bash scripts/guardrail_inbox_triage.sh` (PASS), `cd ui && npm run build` (PASS).
- **Improved:** Transaction language in drafts (e.g. 本次加车报价…提交办公室); materials and coverage branches aligned.
- **Still weak:** Mixed-intent second questions may still **hand off** inside the same thread (ATC-06 documents this — future work: stricter secondary-issue separation).
- **More mature?** Yes, for **framing and closure**; not a full ticketing story.
- **Worth it:** Yes.

## 8. Optional loop 4

- **Not used.** Remaining gap (mixed intent / secondary case) is **not** a one-line fix; stopping avoids scope creep.

## 9. Validation summary

| Check | Result |
|-------|--------|
| `scripts/run_add_car_transaction_clarity_scenarios.py` | 8/8 passed |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | PASS |
| Regressions observed | None in guardrail |

## 10. Deployment / release judgment

- **Backend:** **Redeploy recommended** if production serves `triage.py` / `config_loader.py` / `handoff_phrases.json` from the repo — handoff text and doc/coverage/materials branches changed.
- **Frontend:** **Redeploy recommended** — `UnifiedIntakePage.tsx` and `clientConfig.ts` changed; new `ui_copy` keys must be loaded via API after backend deploy.
- **Live inspection:** Founder can inspect **locally** with `bash scripts/run_demo_local.sh` after pull; **cloud** inspection requires the above deploys.

*This sprint did not run a remote deploy from this environment.*

## 11. Rule-brain / product-semantics summary

| Concern | Where controlled |
|---------|-------------------|
| **Transaction title / ribbon / progress title / handoff UI shell** | `ui/src/pages/UnifiedIntakePage.tsx` + optional `configs/clients/chen_kui/ui_copy.json` (via `get_ui_copy` / `mergeUiCopy`) |
| **Default UI strings (fallback)** | `ui/src/api/clientConfig.ts` → `DEFAULT_UI_COPY` |
| **API exposure of ui_copy keys** | `services/fiqa_api/inbox_triage/config_loader.py` → `get_ui_copy` |
| **Standard Add-Car handoff reply** | `configs/clients/chen_kui/handoff_phrases.json` → `handoff.add_car` |
| **Special branches** (doc clarification suffix, coverage combo, materials sent) | `services/fiqa_api/inbox_triage/triage.py` |
| **Next-step asks (collecting)** | `configs/industries/insurance/add_car_rules.json` (+ Rules Center) |
| **Workbench transaction line** | `UnifiedIntakePage.tsx` → `BrokerWorkbenchTab` Case 整理 |

**How “transaction feel” is assembled:** Soft route + triage structured fields set **Add-Car context** → UI shows **ribbon + progress title** → rules/config drive **collecting copy** → when `handoff_ready`, **phrases + triage branches** produce **office-submitted draft** → UI adds **closure headline, processing, boundary** around that draft.

## 12. Final judgment

- **Biggest gain:** Combined **visible transaction identity** + **layered handoff closure** with config-controlled copy.
- **Biggest remaining weakness:** **Secondary / mixed intent** after quote-ready can still hand off in one thread — boundary copy helps, but **case separation** is not fully enforced in rules.
- **Serious business flow?** **Closer** — especially on the customer finish screen and default handoff wording.
- **Best next step:** Optional sprint on **mixed-intent → secondary case** when user explicitly asks a non-add-car question post-handoff (keep Add-Car bounded).

## 13. 中文宏观总结

- **为什么做：** 加车流程能力已够，但“像聊天”的余味还在；要用**事务标题**和**收尾结构**把体验拉齐到**正式服务请求**。
- **主要强化：** 客户侧 **当前办理：加车报价** 条、**加车报价 · 进度**、交办公室后的**分层收尾**与**新问题边界**；办公室侧 **加车报价事务** 提示；配置与话术里明确 **提交办公室 / 跟进**。
- **事务感：** 明显更强（条带 + 进度卡标题 + 输入区文案）。
- **收尾感：** 更强（标题 + 摘要框 + 处理说明 + 边界提示 + 合并 toast）。
- **统一入口成熟度：** 更接近**平台化受理**（有事务框、有结束态），但仍非工单系统。
- **继续打磨：** 混合意图时是否**强制新开请求**；英文客户全链路 parity；必要时把部分 UI 句柄迁入 Rules Center。

## 14. COPY/PASTE FOUNDER BLOCK

- **最大事务清晰度提升：** 对话进行中持续显示 **当前办理：加车报价** + **加车报价 · 进度**，输入区用 **当前办理** 框定事务。
- **最大收尾提升：** 交办公室后出现 **closure 标题**、**办公室回复摘要**、**处理中说明**，并提示 **无关问题请提交新问题**；加车 handoff **toast** 合并为更强的一句。
- **最大残留弱点：** 客户在加车流程里**顺带问别的**时，规则仍可能 **同一轮就 handoff**，需要后续专门做**二次议题分流**。
- **是否要重新部署：** **要** — 改了后端 triage/配置加载与 handoff 话术，以及前端统一入口页与客户配置类型。
- **Andy 现在能验吗：** **本地**拉代码跑 `run_demo_local.sh` 即可验；**线上**需按上面完成前后端发布后再验。

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

把加车从“聪明聊天”推进到“**有名字的正式业务**”，并在交办公室时给出**可信赖的结束态**。

### 主要用了什么方法/技术

文档驱动 sprint；**客户配置（ui_copy + handoff_phrases）** + **Unified Intake UI 分层收尾** + **triage 特殊分支文案对齐**；自动化脚本做 **8 条 founder pack** 与现有 **guardrail**。

### 这轮最大的提升

**事务身份**与**办公室接手**在 UI 和话术上同时变清晰，且可配置。

### 现在还差什么

**混合意图 / 第二议题**的硬边界仍在产品层未完全解决；上线需 **deploy** 才能在云环境看到完整效果。
