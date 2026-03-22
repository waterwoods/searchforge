# Flow Productization Sprint Report

**Sprint:** Flow Productization Sprint (document-driven, ~45–90 min)  
**Scope reviewed:** Unified Intake backend (`triage.py`, `config_loader.py`, `case_store.py`, `routes/inbox_triage.py`), Chen Kui + insurance configs, Unified Intake UI client config, guardrail + scenario runners.

---

## 1. Sprint theme

- **What was reviewed:** The live Unified Intake pipeline from **API → triage engine → configs → UI copy merge → case persistence**, plus **regression orchestration** (`guardrail_inbox_triage.sh` and linked runners).
- **Why now:** The system **works** and is **scenario-hardened**, but **boundaries** between engine, industry content, client wording, and tests are **implicit**. Trial and a second broker need **legibility** and **fewer duplicate strings**, not a rewrite.

---

## 2. Document set created

All under `docs/sprints/FLOW_PRODUCTIZATION_SPRINT/`:

| # | Document |
|---|----------|
| 1 | `FLOW_PRODUCTIZATION_BLUEPRINT.md` |
| 2 | `CURRENT_ARCHITECTURE_LAYER_MAP.md` |
| 3 | `CODE_CONFIG_UI_TEST_BOUNDARY_SPEC.md` |
| 4 | `PRODUCTIZATION_TARGET_ARCHITECTURE_SPEC.md` |
| 5 | `EXTERNALIZATION_PRIORITY_SPEC.md` |
| 6 | `PORTABLE_CLIENT_INDUSTRY_PACK_CONCEPT_SPEC.md` |
| 7 | `EXECUTION_OUTLINE.md` |
| 8 | `FOUNDER_INSPECTION_NOTES.md` |
| 9 | `FINAL_REPORT.md` (this file) |

**Optional / encouraged:**

| Doc | Purpose |
|-----|---------|
| `WHAT_MOVES_NEXT_CHECKLIST.md` | Actionable externalization checklist |
| Architecture / hot-plug tables | Embedded in Blueprint + Portable Pack spec |

---

## 3. Current productization audit

### What is already product-like

- **Directory model** for `configs/industries/insurance/` vs `configs/clients/chen_kui/` vs `configs/common/`.
- **Loader** with documented merge intent (`config_loader.py` module docstring).
- **Tunable lexicon:** `markers.json` (+ document items) drives intent markers; `triage.py` falls back only if missing.
- **Client wording packs:** `handoff_phrases.json`, `ui_copy.json` served via `GET /api/inbox/client-config` and consumed in React with merged defaults (`clientConfig.ts`).
- **Industry templates:** category templates, reply templates, workflow fallbacks, add-car prompt file.
- **Strong regression culture:** guardrail script chains scenarios, persistence, backbone tests, simulations.

### What is still too code-bound

- **Orchestration and policy** in `triage.py` (thousands of lines): handoff timing, add-car exceptions, append **case boundary** graph, field extraction, LLM/rule routing.
- **Substantial customer-facing prose** inside `_apply_append_case_boundary` (continuity + “new issue” messaging).
- **Route-level** `REROUTE_MESSAGES` and `SOFT_ROUTE_STARTER_REPLIES` in `inbox_triage.py` (should live with other copy).
- **Hardcoded client merge** in `get_reply_templates()` for `reply_overrides.json` (always `chen_kui` path today).

### What is already configurable

- Insurance markers, document item labels, category templates, industry reply templates, workflow fallbacks, add-car ask strings (subset), client handoff phrases, client UI copy, quick-start definitions.

### What is still entangled

- **Same semantic content** can exist in: industry JSON, client JSON, `triage.py` fallbacks, **API routes**, and **TS `DEFAULT_UI_COPY`** — drift risk.
- **`add_car_rules.json`** includes keys (e.g. `ask_driver_only`) not loaded by `get_add_car_rules()` — **schema/engine mismatch**.

---

## 4. Current architecture layer map

| Layer | Common engine | Industry-specific | Client-specific | Config / rules | UI semantics | Regression battery |
|-------|---------------|-------------------|-----------------|----------------|--------------|---------------------|
| **Role** | Orchestration, persistence, boundary policy, LLM/rule | Markers, templates, add-car prompts | Handoff + UI + overrides | JSON files + loaders | Layout + copy merge | Scenarios + guardrail |
| **Primary artifacts** | `triage.py`, `case_store.py` | `configs/industries/insurance/*` | `configs/clients/chen_kui/*` | `config_loader.py`, `workflow_defaults.json` | `UnifiedIntakePage.tsx`, `clientConfig.ts` | `guardrail_inbox_triage.sh`, `run_*.py`, scenario JSON |

**Detail:** See `CURRENT_ARCHITECTURE_LAYER_MAP.md`.

---

## 5. Target productization architecture

**Lightweight five-pack model:**

1. **Common engine** — case/state/handoff/append/boundary **policy**, orchestration, persistence, normalization.
2. **Industry pack** — auto-insurance flows expressed as markers + templates + shared reply skeletons.
3. **Client pack** — broker tone, office naming, handoff phrases, UI strings, reply overrides.
4. **Lexicon / rule maps** — keyword lists and short prompt fragments (e.g. add-car next asks).
5. **Regression battery** — executable contracts for demos and trials.

**Detail:** `PRODUCTIZATION_TARGET_ARCHITECTURE_SPEC.md`.

---

## 6. Externalization priority

### Move next (high ROI)

- Fix **`reply_overrides`** to use active `CLIENT_ID`.
- Move **route** reroute + soft-route starter strings into config.
- Align **`add_car_rules`** JSON with the loader (or trim JSON).
- Add a **human-readable scenario index** (doc).

### Move later

- Boundary **paragraph** templates (keep logic in code).
- Optional workflow **timing** knobs once a second customer needs them.

### Keep in code for now

- Append boundary **classification**, handoff **gating**, extraction **heuristics**, LLM merge, case validation enums.

**Detail:** `EXTERNALIZATION_PRIORITY_SPEC.md` + `WHAT_MOVES_NEXT_CHECKLIST.md`.

---

## 7. Hot-plug / portability judgment

### What becomes easier

- **Same industry, new broker:** swap `configs/clients/<id>/` + `CLIENT_ID` once template overrides path is fixed; tune words without touching engine.
- **Explaining the product:** client JSON is a **wording appendix** for review.

### What remains hard

- **New industry:** `triage.py` and scenario suites are insurance-shaped; expect a **major** engine and test rebuild, not a JSON swap.

### What the architecture already makes easy / hard

- **Easy:** client-visible copy, handoff phrases, marker tuning, industry template edits.
- **Hard:** changing **when** we hand off or **how** we split cases without scenario work.

**Detail:** `PORTABLE_CLIENT_INDUSTRY_PACK_CONCEPT_SPEC.md`.

---

## 8. Reporting / customer-review value

- **Founder understanding:** `FOUNDER_INSPECTION_NOTES.md` gives a 30-minute path through configs before code.
- **Customer review:** Client pack JSON is reviewable **business surface**; industry pack is **defaults**.
- **Reporting / walkthroughs:** Show UI copy + handoff phrases + “guardrail green” as **evidence** of controlled change.
- **Safer change management:** Boundary spec + externalization priorities reduce **silent drift** (same string edited in three files).
- **Team onboarding:** Layer map answers “where do I change a button vs. a rule?”

---

## 9. Final judgment

1. **Are you productized enough for this stage?** **Yes, for a focused paid pilot / trial** — configs and guardrails are ahead of typical early-stage demos. **No**, if the bar is “second broker in a day with zero code” — one loader bug (`reply_overrides`) blocks that.
2. **Biggest productization gap today:** **String ownership drift** + **hardcoded client template path** + **schema mismatch** on add-car rules.
3. **Single best next productization move:** Fix **`get_reply_templates()`** to load `reply_overrides` from **`configs/clients/{CLIENT_ID}/`** and move **route-level** Chinese copy into config — small diff, high portability ROI.
4. **What should definitely not be done yet?** JSON-driven boundary graphs, LangGraph, multi-tenant platform work, or “general workflow DSL.”
5. **Is a heavy framework needed now?** **No.** Clarity, loader fixes, and copy consolidation beat framework churn.
6. **Lightweight architecture for the next 1–3 weeks:** Follow **`EXECUTION_OUTLINE.md`**: loader fix → route copy externalization → add-car schema alignment → scenario index doc → optional boundary template JSON.

---

## 10. 中文宏观总结

- **现在 flow 哪些已经像产品了：** 行业配置（`markers`、模板、`add_car_rules`）和客户配置（`handoff_phrases`、`ui_copy`）分层清晰；前端已走后端 `client-config` 拉文案；有一套 guardrail + 多脚本场景回归，属于可对外讲“可控迭代”的形态。
- **哪些还太依赖代码：** 多轮编排、何时 handoff、追加消息时的 **case boundary** 判定与长篇回复、字段抽取与 LLM/规则路由，都集中在 `triage.py`；`routes` 里还有一段与业务相关的软路由文案；`reply_overrides` 仍写死 `chen_kui` 路径。
- **哪些应该先外置：** 立刻值得做的是 **按 CLIENT_ID 加载 reply_overrides**、把 **路由层 reroute/starter 文案** 收进配置、把 **`add_car_rules.json` 与 loader 对齐**（避免 JSON 里有字段但代码不读）。
- **热插拔以后大概怎么做：** 同一行业换经纪楼 = 换 `configs/clients/<新客户>/` + 环境变量 `CLIENT_ID`（并修好 overrides 路径）；跨行业 ≠ 换配置文件夹就能搞定，需要重写意图/抽取与场景包，但 **“行业包 + 客户包 + 引擎”** 的分工仍然成立。
- **现在最值的一步：** **修 `get_reply_templates()` 的客户端路径 + 外置 routes 里的业务文案** —— 改动小、直接提升“可移植/可运营”，且不触碰核心状态机与安全边界逻辑。

---

## Main questions (explicit index)

| # | Question | Short answer |
|---|----------|----------------|
| 1 | What is already product-like? | Industry/client JSON split, UI copy API, markers, guardrails. |
| 2 | What is too code-bound? | Orchestration, boundary policy, extraction, long embedded copy. |
| 3 | What is already configurable? | Markers, templates, handoff, UI copy, fallbacks, partial add-car prompts. |
| 4 | What should remain in code for now? | Handoff policy, boundary classification, extraction, LLM merge, case invariants. |
| 5 | What to externalize next? | Client-scoped overrides path, route copy, add-car schema alignment, scenario index. |
| 6 | Lightweight hot-pluggable architecture? | Env-selected `CLIENT_ID` + `configs/industries|clients|common` + stable loader; no new framework. |
| 7 | Engine vs industry vs client pack? | See §5 and Target Architecture spec. |
| 8 | Easier customer migration? | Fix overrides + single-source strings + document scenarios. |
| 9 | Easier customer review? | Treat client JSON as wording appendix + show regression evidence. |
| 10 | What not to over-engineer? | JSON state machines, multi-tenant platform, LangGraph — premature now. |
