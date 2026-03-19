# Retrieval + Knowledge Layer Foundation Sprint Report

**Sprint:** Retrieval + Knowledge Layer Foundation  
**Date:** 2026-03-09  
**Scope:** Unified Entry / Broker Workbench mainline

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| **Stage 1** — Define retrieval boundaries | **Completed** | Created `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` |
| **Stage 2** — Define knowledge package model | **Completed** | Documented in same doc; common/industry/client layering |
| **Stage 3** — Choose first safe retrieval slice | **Completed** | Chose DMV/SR-22 explanation support |
| **Stage 4** — Implement first retrieval foundation | **Completed** | Created `knowledge/` folder, `dmv_sr22_explanations.md`, `knowledge_paths.py` |
| **Stage 5** — Validate product stability | **Completed** | All validation scripts passed |
| **Stage 6** — Audit + practical judgment | **Completed** | Verdict: Accept |

**Skipped:** None.

---

## 2. Retrieval boundary definition

### What should go into RAG / Qdrant

| Item | Why |
|------|-----|
| DMV / SR-22 explanation snippets | Customer asks "what is SR-22?" — semantic retrieval finds explanation |
| Notice interpretation reference | "What does payment failed mean?" — retrieval finds notice-type explanations |
| Declaration page / garaging proof explanations | Customer confused about document names — retrieval finds definitions |
| Common insurance FAQ | "Why did my premium go up?" — retrieval finds rate-factor content |
| Official DMV/CDI/insurer content | Already in `auto_insurance_demo_core`; semantic search over official sources |
| Chen Kui office FAQ (future) | Client-specific phrasing, office process notes — optional client RAG pack |

### What should NOT go into RAG / Qdrant

| Item | Why |
|------|-----|
| Workflow thresholds (add-car enough when year+model+zip) | Rules must be deterministic; RAG is probabilistic |
| Handoff rules, max turns | Control flow must be exact |
| Intent markers (add_vehicle, payment, dmv_help) | Used for fast rule-based detection; config, not retrieval |
| Reply templates (first-turn wording) | Config-driven; loaded at startup |
| Case state (case_id, waiting_on, notes) | Transactional; keyed by case_id |
| Test scenarios | Regression assets; not production knowledge |
| Urgency mapping | Rule; deterministic |

**Why this matters:** Rules decide *what to do*. Knowledge helps *explain, clarify, and answer*. Mixing them causes confusion and makes hot-swap harder.

---

## 3. Knowledge package model

| Pack | Path | Contents | Retrieval-ready today |
|------|------|----------|------------------------|
| **Common** | `knowledge/common/` | Generic service-entry best practices | Placeholder |
| **Industry (insurance)** | `knowledge/industries/insurance/` | DMV/SR-22, notice interpretation, document explanations, FAQ | **First slice:** DMV/SR-22 |
| **Client (Chen Kui)** | `knowledge/clients/chen_kui/` | Office FAQ, Chinese customer preferences | Placeholder |

**Load order:** common → industry → client. Same as config. Retrieval can filter by pack when querying.

---

## 4. Practical implementation / foundation step

| File / folder | Purpose |
|---------------|---------|
| `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` | Single source of truth for retrieval boundaries; decision tree; what goes where |
| `knowledge/README.md` | Knowledge layer overview; structure; ingestion-prep note |
| `knowledge/INGESTION_PREP.md` | Future ingestion path; current vs future state |
| `knowledge/common/README.md` | Common pack placeholder |
| `knowledge/industries/insurance/README.md` | Insurance pack overview; first slice documented |
| `knowledge/industries/insurance/dmv_sr22_explanations.md` | **First retrieval slice** — SR-22 definition, what to bring to DMV, suspension clearance, common questions |
| `knowledge/clients/chen_kui/README.md` | Client pack placeholder |
| `services/fiqa_api/inbox_triage/knowledge_paths.py` | Reference paths; `get_knowledge_paths_by_pack()`, `list_retrieval_ready_files()` for future ingestion |

**Doc updates:** `docs/PROJECT_DOC_SYSTEM_MAP.md`, `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md`, `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` — added references to retrieval foundation doc.

**Why this helps:** A founder or engineer can now answer "what goes into RAG?" without guessing. The knowledge folder is ingestion-ready; future Qdrant ingestion can use `knowledge_paths.py` to discover files.

---

## 5. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui/) | **PASS** | UI builds |
| `run_inbox_triage_scenarios.py` | **PASS** (40/40) | Category, urgency regression |
| `run_chen_kui_proxy_calibration.py` | **PASS** (14/14) | Draft style regression |
| `run_multi_turn_simulations.py` | **PASS** (14/14) | Handoff flow regression |
| `run_expression_robustness.py` | **PASS** (36/36) | Phrasing robustness |
| `test_inbox_triage_api.py` | **PASS** | API contract |
| `guardrail_inbox_triage.sh` | **PASS** | Pre-demo quality |
| `unified_intake_smoke_check.sh` | **PASS** | Smoke flow |

**Retrieval-ready paths:** No interference with existing rules/config/state. Inbox triage still uses rules + config only; no RAG dependency added.

---

## 6. Business / platform value

| Benefit | How |
|---------|-----|
| **Reduces confusion** | Single doc (`RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md`) answers "what goes into RAG?" |
| **Supports future scaling** | Knowledge package model (common/industry/client) is real; future ingestion path is documented |
| **Helps packaging and selling** | New client = new `knowledge/clients/<client>/` folder; new industry = new `knowledge/industries/<industry>/` folder |

---

## 7. Remaining blocker(s)

1. **Live ingestion not wired** — `knowledge/` files are ingestion-prep only. `auto_insurance_demo_core` is still built from URLs. To use `dmv_sr22_explanations.md` in retrieval, an ingestion script must be added.
2. **Inbox triage does not call RAG** — Triage remains rule-based. Optional RAG augmentation for explanatory content (e.g. DMV/SR-22) would require a separate integration step.
3. **No runtime client/industry switch** — Paths are fixed to `chen_kui` and `insurance`. Env vars `CLIENT_PACK` / `INDUSTRY_PACK` would enable hot-swap.

---

## 8. Recommended next step

**One clear next step:** Add a small ingestion script that reads `knowledge/industries/insurance/*.md`, chunks by section, embeds with the same model as the demo corpus, and upserts to `auto_insurance_demo_core` (or a separate `knowledge_insurance` collection) with `knowledge_pack: "insurance"` payload. Wire it to run after `build_demo_core_collection.py` or as a standalone step.

---

## 9. 中文或中英混合宏观总结

**这次把哪些东西明确为「该进 RAG / Qdrant」：**
- DMV/SR-22 解释、notice 解读参考、declaration page / garaging proof 说明、保险 FAQ
- 通用保险知识、官方 DMV/CDI 内容
- 未来：陈奎办公室 FAQ、客户特定知识

**哪些东西明确「不能进 RAG」：**
- 工作流规则（handoff 阈值、max turns）
- Intent markers、reply templates
- Case state（case_id、waiting_on、notes）
- 测试场景

**这次做出来的 retrieval foundation 到底有没有真实价值：**
- 有。边界清晰了，founder/engineer 不再困惑。`knowledge/` 文件夹和 `dmv_sr22_explanations.md` 是 ingestion-ready 的，未来 ingestion 脚本可以直接用 `knowledge_paths.py` 发现文件。

**有没有困难或限制：**
- 目前 `knowledge/` 文件尚未 ingest 到 Qdrant，所以 retrieval 还不能直接用到。需要加 ingestion 脚本。

**这对以后热插拔和卖给别的客户有什么帮助：**
- 知识包模型（common → industry → client）已经定义好。新客户 = 新 `knowledge/clients/<client>/`；新行业 = 新 `knowledge/industries/<industry>/`。结构清晰，便于打包和销售。

---

## 10. Practical retrieval cheat sheet

| Type | Where | RAG? |
|------|-------|------|
| **Rules/config** | `triage.py`, `configs/industries/insurance/`, `configs/clients/chen_kui/` | **NO** |
| **Common knowledge** | `knowledge/common/` (placeholder) | **YES** (future) |
| **Insurance knowledge** | `knowledge/industries/insurance/`, Qdrant `auto_insurance_demo_core` | **YES** |
| **Chen Kui knowledge** | `knowledge/clients/chen_kui/` (placeholder) | **YES** (future) |
| **State** | `data/unified_intake_cases.json`, `case_store.py` | **NO** |
| **Tests** | `configs/inbox_triage_scenarios.json`, `scripts/run_*.py` | **NO** |

---

## 11. Future knowledge package summary

| Area | Retrieval-ready now | Not retrieval-ready | Next retrieval step |
|------|---------------------|---------------------|---------------------|
| **DMV/SR-22** | Source file exists (`dmv_sr22_explanations.md`) | Not yet in Qdrant | Add ingestion script; upsert to collection |
| **Notice interpretation** | — | No source file | Add `notice_interpretation.md` to `knowledge/industries/insurance/` |
| **Declaration/garaging** | — | Labels in config only | Add short `document_explanations.md` |
| **Chen Kui office FAQ** | — | Placeholder only | Add when client-specific content is defined |
| **Common** | — | Placeholder only | Add only if generic content is useful |

---

*End of sprint report*
