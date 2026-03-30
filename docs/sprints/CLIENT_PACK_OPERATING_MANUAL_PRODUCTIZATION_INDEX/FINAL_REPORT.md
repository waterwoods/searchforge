# Client-Pack Operating Manual / Productization Index Report

## 1. Sprint theme

- **Reviewed / organized:** Unified Intake stack — `triage.py`, `config_loader.py`, inbox routes, case store, insurance + client + common configs, Unified Intake UI + client config API, `guardrail_inbox_triage.sh`, scenario and A/B runners, second broker pack (`socal_precision`).
- **Why now:** The engine is strong but dense; the founder needs a **compact operator map** (layers, hot-plug, validation) without adding code complexity.

---

## 2. Document set created

All under `docs/sprints/CLIENT_PACK_OPERATING_MANUAL_PRODUCTIZATION_INDEX/`:

| Doc | File |
|-----|------|
| READ THIS FIRST | `READ_THIS_FIRST.md` |
| Productization Index | `PRODUCTIZATION_INDEX.md` |
| Client-Pack Operating Manual Blueprint | `CLIENT_PACK_OPERATING_MANUAL_BLUEPRINT.md` |
| Current Architecture Module Guide | `MODULE_ARCHITECTURE_GUIDE.md` |
| File / Folder Responsibility Map | `FILE_FOLDER_RESPONSIBILITY_MAP.md` |
| Same-Industry Migration Checklist | `SAME_INDUSTRY_MIGRATION_CHECKLIST.md` |
| Validation / Regression Checklist | `VALIDATION_REGRESSION_CHECKLIST.md` |
| Execution Outline | `EXECUTION_OUTLINE.md` |
| Founder Inspection Notes | `FOUNDER_INSPECTION_NOTES.md` |
| Final Report (this file) | `FINAL_REPORT.md` |
| Glossary | `GLOSSARY.md` |
| Important vs less important | `IMPORTANT_VS_NOT_IMPORTANT.md` |
| Safe vs risky changes | `SAFE_VS_RISKY_CHANGES.md` |

---

## 3. Productization index

- **Major layers:** UI (React) → FastAPI inbox routes → triage engine (`triage.py`) → config loader → JSON packs (`common` / `industries/insurance` / `clients/<id>`) → regression batteries (`configs/inbox_triage_scenarios.json` + `scripts/`).
- **Reading order:** `READ_THIS_FIRST.md` → `PRODUCTIZATION_INDEX.md` → `MODULE_ARCHITECTURE_GUIDE.md` → migration + validation checklists → `AGENTS.md` / `STANDARD_SCENARIO_PACKAGE.md` for run commands.
- **Repo navigation summary:** Use `CLIENT_ID` to select `configs/clients/<id>/`; change **copy** in JSON first; run **`bash scripts/guardrail_inbox_triage.sh`** before calling a change “done.”

---

## 4. Current architecture module guide

| Module | Role | Why it matters |
|--------|------|----------------|
| `triage.py` | Classification, drafts, workflow, add-car, append/boundary | Core product behavior |
| `config_loader.py` | Loads and merges configs; `CLIENT_ID` | Defines isolation and overrides |
| `routes/inbox_triage.py` | HTTP API, persistence, soft-route wiring | UI/engine contract |
| `case_store.py` | JSON cases for demo/workbench | Continuity + office tools |
| Client / industry JSON | Lexicon + templates + UI strings | Hot-plug broker voice |
| `UnifiedIntakePage.tsx` | Customer + broker UX | Founder-visible product |
| `clientConfig.ts` | Fetch/merge `ui_copy` | Typing + defaults |
| Guardrail + scripts | Regression + A/B isolation | Safe migration |

*(Plain-language detail: `MODULE_ARCHITECTURE_GUIDE.md`.)*

---

## 5. File / folder responsibility map

- **Categories:** engine (`services/fiqa_api/inbox_triage/*.py`, routes), industry pack (`configs/industries/insurance/`), client pack (`configs/clients/<id>/`), common (`configs/common/`), UI (`ui/src/pages/…`, `ui/src/api/clientConfig.ts`), regression (`configs/inbox_triage_scenarios.json`, `scripts/*`), infra (env `CLIENT_ID`, deploy).
- **Safe vs risky:** Summarized in `SAFE_VS_RISKY_CHANGES.md` and expanded in `FILE_FOLDER_RESPONSIBILITY_MAP.md`.

---

## 6. Same-industry migration checklist

- **Process:** Pick `client_id` → copy pack folder → fill `ui_copy.json`, `handoff_phrases.json`, `reply_overrides.json` → set `CLIENT_ID` → run cross-client A/B scripts + full guardrail → optional browser smoke → define success (green tests + correct `client-config` + no wrong-broker phrases).
- **What matters most:** Client JSON completeness + isolation tests + guardrail PASS.
- **Success criteria:** See checklist section 10 in `SAME_INDUSTRY_MIGRATION_CHECKLIST.md`.

---

## 7. Validation / regression checklist

- **Must-run:** `bash scripts/guardrail_inbox_triage.sh`.
- **Optional:** API test with live server; add-car batteries when touching add-car.
- **UI checks:** Refresh + quick-start + handoff cards after `ui_copy` changes.
- **A/B / isolation:** `run_cross_client_ab_scenarios.py`, `run_append_boundary_ab_scenarios.py`, `run_residual_copy_ab_scenarios.py` (inside guardrail).
- **Blocks release:** Any guardrail **FAIL**.

---

## 8. Important vs less important guide

- **Focus first:** `CLIENT_ID`, client pack JSON, guardrail, A/B scripts.
- **Can wait for migration:** Engine refactors, new API surface, large UI rewrites.
- **Risky:** `triage.py`, `config_loader.py`, `case_store.py`, global `markers.json` without scenario review.

---

## 9. Founder architecture explanation

### 中文说明（给创始人）

你现在可以把它想成四层叠在一起：

1. **门面（网页）** — `UnifiedIntakePage.tsx`：客户怎么输入、有哪些快捷按钮、办公室工作台长什么样。很多**可见文案**来自后端下发的 `ui_copy.json`，但前端也有一套**默认文案**（目前偏 Chen Kui），所以新客户要记得把 JSON 写全，避免“看起来像默认样板”。

2. **API 前台** — `routes/inbox_triage.py`：所有 `/api/inbox/...` 请求在这里进门，负责把会话、案件、软路由（快捷意图）交给引擎。

3. **主脑（引擎）** — `triage.py`：真正决定“这是什么类型的问题、紧不紧急、下一句问什么、什么时候移交办公室、加车流程走到哪”。这里是**最高风险**的代码区：改一句逻辑可能影响很多场景。**如果只是改口吻，优先改 JSON，不要先改这里。**

4. **装载层** — `config_loader.py`：从磁盘读 `configs/`，按规则合并：**行业默认 + 客户覆盖**；并且对关键客户字段**不做跨客户兜底**，避免 A 经纪人的话术跑到 B 身上。

**目录分工（最好记的版）：**

- `configs/industries/insurance/`：**车险行业共用** — 关键词库（markers）、行业回复模板、分类说明、加车追问文案。
- `configs/clients/<客户id>/`：**这家办公室专用** — 页面标题/按钮（`ui_copy.json`）、移交客户时的话（`handoff_phrases.json`，含可选 `stitched` 细调）、对行业模板的**局部覆盖**（`reply_overrides.json`）。
- `configs/common/`：**跨客户默认** — 例如软路由的转场话术（`soft_route_inbox.json`）、一些 workflow 兜底。

**`configs/inbox_triage_scenarios.json` 和 `scripts/` 里的一串 runner：** 可以理解为**回归题库 + 自动化考卷**；`guardrail_inbox_triage.sh` 是**总开关**，要通过才算“这轮改动没把底子打穿”。其中 **cross-client A/B** 专门盯：**两个经纪人的话术不能串台**。

**切换同类新客户时：** 先新建 `configs/clients/新id/`，配齐 JSON，部署时设好 `CLIENT_ID`，再跑 guardrail。不要一上来就改 `triage.py`。

### English summary (short)

Unified Intake is **UI → FastAPI → `triage.py` → configs**. Broker-specific voice lives in **`configs/clients/<client_id>/`**; shared auto-insurance behavior lives in **`configs/industries/insurance/`**. The guardrail script is the **practical quality gate**; A/B runners prove **client isolation**. Prefer **JSON** for wording; touch **`triage.py`** only when behavior must change.

---

## 10. Final judgment

1. **Usable client-pack operating manual?** **Yes** — blueprint + migration + validation + responsibility map are enough to operate and onboard a second same-industry broker at the **config + env** level.
2. **Repo easier to understand?** **Yes** — this sprint adds a navigable index and module guide without changing code.
3. **Founder could guide same-industry migration?** **Reasonably yes**, if they follow the checklists and treat guardrail + A/B scripts as non-optional.
4. **Still confusing or risky?** Engine size (`triage.py`); LLM vs rule-mode drift in real trials; frontend defaults still “Chen-shaped”; single `CLIENT_ID` per deployment (not multi-tenant product).
5. **Next sprint suggestion:** **“Thin default risk”** — either enrich `demo_broker` as neutral defaults in `clientConfig.ts`, or document a **minimum required keys** template + validator for `ui_copy.json` / `handoff_phrases.json`; optionally a one-page **CLIENT_ID runbook** for demo vs pilot envs.

---

## 11. 中文宏观总结

- **我们现在到底都有哪些层？** 网页 → API → 引擎（triage）→ 配置装载 → 三层 JSON（common / industry / client）→ 回归脚本。
- **每个大模块在干什么？** 网页展示与交互；API 接请求；引擎决定逻辑与流程；装载层读配置并合并；JSON 放话术与词库；脚本负责验证。
- **什么最重要？** `CLIENT_ID`、客户目录里的 JSON、guardrail、以及跨客户 A/B 隔离测试。
- **什么先不要碰？** 一上来就改 `triage.py`、`config_loader.py`、案件存储结构 —— 除非你已经准备好全盘回归。
- **以后切换客户先做什么？** 新建/复制 `configs/clients/<新id>/`，改 UI 与移交话术，设环境变量，跑 `guardrail_inbox_triage.sh`。
- **这套手册够不够用？** **对“同类新客户、配置级热插拔、演示/试点”够用**；若要做真正的多租户登录切换、或大规模改引擎，还需要后续 sprint。

---

## Appendix — Ten required answers (explicit)

1. **Major architectural layers today?** UI; API; triage engine; config loader; config files (common, industry, client); persistence; regression batteries.
2. **Major modules/files and roles?** See §4 and `MODULE_ARCHITECTURE_GUIDE.md`.
3. **What belongs to engine / industry / client / lexicon / regression battery?** See `FILE_FOLDER_RESPONSIBILITY_MAP.md` — engine = `inbox_triage/*.py` + routes; industry = `configs/industries/insurance/`; client = `configs/clients/<id>/`; lexicon = `markers.json` + related templates; battery = `configs/inbox_triage_scenarios.json` + `scripts/*`.
4. **Most important files for client migration?** New `configs/clients/<id>/*`, env `CLIENT_ID`, then isolation + guardrail scripts.
5. **Usually safe to change?** Client `ui_copy.json`, `handoff_phrases.json`, targeted `reply_overrides.json`.
6. **Dangerous / high impact?** `triage.py`, `config_loader.py`, `case_store.py`, global `markers.json`, API routes.
7. **Validation steps after changes?** `guardrail_inbox_triage.sh` minimum; A/B scripts for handoff/stitched/reply work; optional API/UI smoke.
8. **Smallest realistic second-client process?** New client folder + three JSON files filled + `CLIENT_ID` + guardrail green.
9. **Founder first vs later?** First: client pack + guardrail + isolation. Later: engine features, new intents in code, infra hardening.
10. **Biggest strengths / remaining risks?** Strengths: real config layering + strong regression + isolation tests. Risks: engine complexity, LLM vs rule drift, Chen-leaning UI defaults, non-multi-tenant `CLIENT_ID` model.

---

*Entry point: [READ_THIS_FIRST.md](./READ_THIS_FIRST.md)*
