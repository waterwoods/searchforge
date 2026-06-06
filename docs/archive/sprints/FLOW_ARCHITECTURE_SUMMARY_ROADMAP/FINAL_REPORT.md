# Flow Architecture Summary + Roadmap Report

**Sprint:** Flow Architecture Summary + Roadmap  
**Product:** SearchForge → Chen Kui Insurance Unified Entry  
**Date:** 2026-03-22  

---

## 1. Sprint theme

- **What was reviewed:** Unified Intake end-to-end — orchestration in `triage.py`, config loading, FastAPI routes, case persistence, React UI, and the guardrail / simulation / battery test spine.
- **Why now:** The product is **stronger but denser**; the founder needs a **reviewable map** of where the “flow brain” lives, what is config vs code, and what to refactor **next** without a framework rewrite.

---

## 2. Document set created

All under `docs/sprints/FLOW_ARCHITECTURE_SUMMARY_ROADMAP/`:

| # | File |
|---|------|
| 1 | `01_FLOW_ARCHITECTURE_BLUEPRINT.md` |
| 2 | `02_CURRENT_FLOW_SYSTEM_MAP.md` |
| 3 | `03_ADD_CAR_FLOW_DEEP_DIVE.md` |
| 4 | `04_UI_BACKEND_CONFIG_TEST_SPLIT_SPEC.md` |
| 5 | `05_CONCENTRATION_VS_SCATTER_ANALYSIS_SPEC.md` |
| 6 | `06_REFACTOR_EXTERNALIZATION_ROADMAP_SPEC.md` |
| 7 | `07_EXECUTION_OUTLINE.md` |
| 8 | `08_FOUNDER_INSPECTION_NOTES.md` |
| 9 | `FINAL_REPORT.md` (this file) |
| Optional | `FLOW_DIAGRAM_AND_TABLE.md` |

---

## 3. Current flow system map

- **Major layers:** Browser UI → FastAPI inbox routes → **`triage.py` orchestration** → JSON configs (industry + client) → optional **`case_store`** persistence → **`scripts/` regression** layer.
- **What each layer does:** See `02_CURRENT_FLOW_SYSTEM_MAP.md` (layer diagram + responsibility table).
- **How they connect:** UI posts `conversation_turns` + optional `soft_route`; API calls `triage_conversation`; result drives UI and optional case save; configs influence markers/templates/handoff/add-car asks; guardrail scripts lock behavior.

---

## 4. Where the current flow logic lives

### Main questions 1–5 (explicit)

1. **Where does the current flow logic mainly live?**  
   **`services/fiqa_api/inbox_triage/triage.py`**, especially **`triage_conversation`**. Routes add HTTP glue; config shapes wording and markers.

2. **What exactly does `triage.py` handle today?**  
   Turn merging (`[客户]`/`[系统]`), talk-to-agent shortcut, **LLM vs rule** (with fast path), **handoff vs next-ask**, **add-car / remove-car / claim / missing-doc / cancel** structured extraction, **handoff reply** assembly + many **commercial patches** (doc clarification, coverage side-question, materials sent, correction lead-ins, etc.), **broker_next_step** tailoring, **append** flow via `triage_for_append` + **case boundary** classification, conversation summary / secondary intent hints, human-confirmation signals.

3. **What is already moved into config / rule files?**  
   **`configs/industries/insurance/markers.json`**, **`category_templates.json`**, **`reply_templates.json`**, **`add_car_rules.json`**, **`configs/common/workflow_defaults.json`**, **`configs/clients/chen_kui/handoff_phrases.json`**, **`reply_overrides.json`**, **`ui_copy.json`** (allowlisted keys). Loader: **`config_loader.py`**.

4. **What is handled in frontend UI logic?**  
   **`ui/src/pages/UnifiedIntakePage.tsx`**: conversation UX, **`soft_route`** from quick-start, when to show add-car **transaction chrome**, **handoff** toasts/panels, **post-handoff** same-request vs new-issue UX, helpers like **`triageResultLooksLikeAddCar`**, case one-liner display. **`clientConfig.ts`** + **`inboxTriage.ts`**: fetch client copy and call APIs.

5. **What is handled in regression batteries / simulation runners?**  
   **`scripts/guardrail_inbox_triage.sh`** orchestrates scenario runners, multi-turn/adversarial packs, case persistence checks, workflow backbone tests, case boundary battery, simulation assistant, broker trial stress, handoff timing, client handoff A/B, client identity append, etc. Add-car-specific: **`scripts/run_add_car_*.py`**. Scenario JSON: **`configs/inbox_triage_scenarios.json`**, various `configs/*simulations*.json`, sprint **`scenario_battery.json`** files under `docs/sprints/`.

### Concentration vs scatter (preview — full detail in §6)

6. **Too concentrated:** Mostly **`triage.py`** (orchestration + policy + extraction + many edge cases in one module).  
7. **Too scattered:** **Customer-facing strings** split across config files, **`routes/inbox_triage.py`**, and **inline Python**; scenario assets split across **configs** and **docs/sprints**.  
8. **Externalize next:** **Phrase inventory** + align **`add_car_rules`** loader with every key triage consumes (**`ask_driver_only`** if product-owned); optionally move **route-level** reroute/starter strings to client config.  
9. **Stay in code for now:** **Handoff vs collect policy**, **append boundary graph**, **slot extraction heuristics**, **LLM/fast-path routing** — all proven under test; moving to DSL is **not** the next ROI.  
10. **Heavier framework?** **Not needed now** — complexity is **domain branching**, not generic graph mechanics. Prefer **docs + optional file split** over LangGraph.

---

## 5. Add-Car flow deep dive

- **Start:** Add-vehicle intent from **markers** + `_is_add_vehicle_request`, or UI **`soft_route: "add_car"`** (with possible reroute in routes).  
- **Extraction:** `_extract_add_car_fields` and related helpers on **`[客户]`** text only; corrections via `_is_add_car_vehicle_correction_signal` / `_extract_add_car_vehicle_concrete`.  
- **State progression:** Derived per request (**no separate engine**): slot completeness, `_add_car_enough_for_handoff`, customer turn count, `_get_next_ask_draft` / `_get_next_ask_for_add_car`; exposed as **`collected_fields`**, **`still_needed_fields`**, **`quote_ready_status`**, **`lifecycle_status`**, **`follow_up_type`**.  
- **Reply generation:** Base draft from rule/LLM triage; when collecting, **ack + config ask**; when handing off, **handoff phrase** from **`handoff_phrases.json`** with **code fallbacks** and **patch blocks** for special mixes (doc Q + quote, coverage Q, materials sent, correction).  
- **Handoff:** **`handoff_ready`** true; customer line from config; **`broker_next_step`** rewritten for quote/materials/contact.  
- **Post-handoff:** **`triage_for_append`** + **`case_boundary`** rules; UI shows same-request / new-issue hints from **`ui_copy.json`**.

*(Full narrative: `03_ADD_CAR_FLOW_DEEP_DIVE.md`.)*

---

## 6. Concentration vs scatter analysis

### Too concentrated

- **`triage.py`**: single home for orchestration + most commercial policy — **high** maintenance cost, **low** deployment risk.
- **`triage_conversation`**: long ordered chain of decisions — **high** cognitive load when debugging “who wins.”

### Too scattered

- **Copy** across config, routes, and Python — **medium** product friction.
- **Tests** across many scripts — **medium** discoverability (mitigated by guardrail).

### What matters now vs later

- **Now:** Map + phrase inventory + avoid untested edits to `triage_conversation`.  
- **Later:** Mechanical split into submodules; optional declarative layer only if flow count grows.

*(Detail: `05_CONCENTRATION_VS_SCATTER_ANALYSIS_SPEC.md`.)*

---

## 7. Roadmap

- **Near-term:** This doc set; phrase map; **`ask_driver_only`** loader alignment if needed; optional comment/doc link from `triage_conversation` to add-car spec; consider moving route reroute/starter copy to config.  
- **Mid-term:** Extract `add_car_flow.py` / `append_boundary.py` (behavior-neutral); clarify client pack checklist; index all `run_add_car_*.py` purposes.  
- **Later / optional:** Stronger workflow engine **only** if multi-tenant / long-running human workflows demand it.

*(Detail: `06_REFACTOR_EXTERNALIZATION_ROADMAP_SPEC.md`.)*

---

## 8. Final architecture judgment

1. **Is the current architecture still enough for this product stage?** **Yes.**  
2. **Biggest architecture risk today?** **Unbounded growth of `triage_conversation` branches** without a **visible decision order** or **module boundaries** — regression risk is managed by tests, but **human reasoning cost** rises.  
3. **Single best next improvement?** **Keep behavior, add structure:** phrase inventory + documented patch order + optional **file split** of add-car and append logic.  
4. **What not to do yet?** Full **graph-framework rewrite**; **single giant JSON** for all copy without tooling.  
5. **Hot-pluggable expansion mindset:** New flows should add **markers + structured fields + scenario pack + config hooks** in **one PR story**; resist one-off `if` blocks without a **named policy** and **test**.

---

## 9. 中文宏观总结

- **现在 flow 主脑在哪？** 主要在 **`triage.py`** 里的 **`triage_conversation`**：多轮合并、分类（规则/LLM）、加车收资、是否交办公室、客户回复草稿、以及大量「商业细节」补丁（材料已发、条款追问、改车型等）。  
- **哪些在 config？** 行业 **`markers.json`**、**`add_car_rules.json`**（问客户下一句话的文案）、**`handoff_phrases.json`**（交办公室时给客户的话）、**`ui_copy.json`**（前台/事务条/结案卡片等展示文案）、以及 **`category_templates` / `reply_templates` / `workflow_defaults`** 等模板与兜底。  
- **哪些在前端？** **`UnifiedIntakePage.tsx`**：对话体验、快捷入口 **`soft_route`**、加车事务视觉、handoff 后的面板与提示；**`clientConfig.ts`** 拉取 **`ui_copy`**。前端**推断**「像不像加车」只为展示，**真相仍以 API 返回为准**。  
- **哪些在测试包？** **`guardrail_inbox_triage.sh`** 串起主回归；另有 **多轮/对抗/边界/交办公室时机** 等脚本；加车有 **`run_add_car_*.py`** 与 sprint 的 **`scenario_battery.json`**。  
- **现在要不要上更重 framework？** **不需要。** 难点在 **保险场景分支与话术策略**，不在「图遍历」本身；用 **文档 + 分层/拆文件 + 继续用测试锁住行为** 更划算。  
- **下一步最值的整理动作是什么？** 做一份 **话术/策略清单**（哪句在哪个文件/哪段代码），并在工程上 **明确 `triage_conversation` 里补丁的先后顺序**；可选把 **加车 / append 边界** 从 `triage.py` **原样挪到子模块**（不改行为）以降低认知负担。
