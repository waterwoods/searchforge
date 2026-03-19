# Knowledge Architecture + Config Layer Sprint Report

**Sprint:** Knowledge Architecture + Config Layer Sprint  
**Date:** 2026-03-09  
**Scope:** Unified Entry / Broker Workbench Platform Base

---

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| **Stage 1** — Define 5 architecture layers | ✅ Completed | `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md` |
| **Stage 2** — Define storage/implementation mapping | ✅ Completed | Same doc |
| **Stage 3** — Map current repo into architecture | ✅ Completed | `docs/CURRENT_SYSTEM_FILE_CLASSIFICATION.md` |
| **Stage 4** — Design hot-swappable package model | ✅ Completed | In architecture doc |
| **Stage 5** — Propose cleaner config layer | ✅ Completed | Proposed structure in doc; no file moves |
| **Stage 6** — Audit + validate | ✅ Completed | All validation scripts passed |

**Skipped:** None. All stages completed.

---

## 2. Architecture Definition

### The Five Layers

| Layer | What it is | Examples |
|-------|------------|----------|
| **1. Rules / workflow logic** | Deterministic operational rules | detect → ask → enough? → handoff; urgency rules; handoff thresholds; what fields to request next |
| **2. Common domain knowledge** | Reusable industry knowledge | DMV/SR-22 explanations; notice interpretation; generic insurance FAQ |
| **3. Client-specific knowledge** | Client office phrasing, habits | Chen Kui office phrasing; Chinese customer habits; client-specific FAQ |
| **4. State / persistence** | Case state, follow-up context | Case state; waiting_on; next_contact_by; notes; activity; conversation_summary |
| **5. Tests / regression assets** | Scenario packs, calibration cases | inbox_triage_scenarios; proxy_calibration; multi_turn_simulations; expression_robustness |

---

## 3. Storage / Implementation Mapping

| Where | What belongs |
|-------|--------------|
| **Code** | Core workflow logic, intent detection, handoff thresholds, category templates, case store CRUD |
| **Config** | Scenario mappings, proxy calibration cases, multi-turn simulations, expression robustness, RAG corpus URLs |
| **RAG / Qdrant** | Common domain knowledge (auto insurance corpus); official DMV/CDI/insurer content |
| **Database / case store** | Case state, waiting_on, next_contact_by, notes, activity, source_text, conversation_summary |
| **Tests** | Scenario packs, calibration packs, regression runners |

**Why NOT everything goes into RAG:** Rules must be deterministic; RAG is probabilistic. State must be transactional; Qdrant is not a case store. Inbox triage does not use RAG today.

---

## 4. Current Repo Classification

| Category | Count | Status |
|----------|-------|--------|
| Core logic | triage.py, case_store.py, routes/inbox_triage.py | Good place |
| Config (Unified Intake) | inbox_triage_scenarios, chen_kui_proxy, multi_turn, expression_robustness | Good place |
| State | data/unified_intake_cases.json | Good place |
| RAG | auto_insurance_demo_core, Qdrant collections | Good place |
| Tests | run_*.py scripts, guardrail, smoke | Good place |

**Mixed:** Markers and templates in triage.py are hardcoded. Future: extract to config when hot-swap needed.

---

## 5. Hot-Swappable Package Model

| Package | Role | Reusable | Replaceable |
|---------|------|----------|-------------|
| **Common platform base** | Intake skeleton, broker workbench, case store, test framework | Yes | No |
| **Industry package** (e.g. insurance) | Category set, markers, handoff thresholds, RAG collection | Across insurance brokers | Yes (swap for food/sausage, etc.) |
| **Client-specific package** (e.g. Chen Kui) | Reply templates, proxy calibration, phrasing overrides | No | Yes |

**Status:** Design only. Hot-swap engine not implemented.

---

## 6. Config Layer Improvements

| What | Status |
|------|--------|
| Proposed layout | `configs/common/`, `configs/industries/insurance/`, `configs/clients/chen_kui/`, `configs/tests/` |
| File moves | **Not done** — document only; move when adding second client |
| `configs/README.md` | Created — quick reference for configs and runners |
| PROJECT_DOC_SYSTEM_MAP | Updated — references new architecture docs |
| runbook | Updated — "where things live" link |

---

## 7. Validation Summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui) | ✅ PASS | UI build |
| `run_inbox_triage_scenarios.py` | ✅ 40/40 | Category/urgency regression |
| `run_chen_kui_proxy_calibration.py` | ✅ 14/14 | Draft style |
| `run_multi_turn_simulations.py` | ✅ 14/14 | Handoff flow |
| `run_expression_robustness.py` | ✅ 36/36 | Phrasing robustness |
| `test_inbox_triage_api.py` | ✅ PASS | API contract |
| `guardrail_inbox_triage.sh` | ✅ PASS | Pre-demo quality |
| `unified_intake_smoke_check.sh` | ✅ PASS | Smoke + guardrail |

**No regressions.** Architecture cleanup did not break the product.

---

## 8. Business / Product Value

| Benefit | How |
|---------|-----|
| **Faster expansion** | Clear boundaries: rules vs knowledge vs state vs tests; future client = swap config |
| **Less confusion** | File classification doc; founder/engineer knows where things live |
| **Selling to future clients** | Package model: common base + industry pack + client pack; hot-swap design ready |

---

## 9. Remaining Blockers

1. **Markers and templates in code** — Hardcoded in triage.py; extraction to config deferred until second client needed.
2. **No physical config reorganization** — Proposed structure only; scripts still use current paths.
3. **Hot-swap engine** — Conceptual; not built.

---

## 10. Recommended Next Step

**One clear next step:** When adding a second client or second industry, create `configs/clients/<client>/` and `configs/industries/<industry>/` and move the relevant config files. Update scripts to load from new paths. Do not do this now.

---

## 11. 中文或中英混合宏观总结

**这次把系统分成了哪几个盒子：**  
规则（workflow）、通用领域知识（domain）、客户特定知识（client）、状态（state）、测试（tests）五个层。

**哪些东西该放代码，哪些该放 Qdrant / RAG，哪些该放数据库：**  
- 代码：规则、意图检测、handoff 阈值、模板逻辑  
- Qdrant/RAG：通用保险知识、DMV/CDI 官方内容、FAQ  
- 数据库：case 状态、waiting_on、notes、activity  

**现在 repo 哪些地方更清楚了：**  
- 有 `KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md` 明确五层和存放位置  
- 有 `CURRENT_SYSTEM_FILE_CLASSIFICATION.md` 分类现有文件  
- configs/README 说明各 config 用途和 runner  

**有没有困难或限制：**  
- markers 和 templates 还在代码里，暂不抽离  
- 热插拔引擎未实现，只是设计  

**这对以后热插拔卖给别的客户有什么帮助：**  
- 设计清楚：common base + industry pack + client pack  
- 未来换客户 = 换 client pack，换行业 = 换 industry pack  

---

## 12. Practical Architecture Cheat Sheet

| Layer | Where |
|-------|-------|
| **Rules** | `triage.py` (code); `docs/MATURE_INTAKE_SKELETON.md` (design) |
| **Common knowledge** | Qdrant `auto_insurance_demo_core`; RAG corpus |
| **Client-specific knowledge** | `triage.py` (templates); `configs/chen_kui_proxy_calibration_cases.json` | 
| **State** | `data/unified_intake_cases.json`; `case_store.py` |
| **Tests** | `configs/inbox_triage_scenarios.json`, `expression_robustness_cases.json`, etc.; `scripts/run_*.py` |

---

## 13. Future Packaging Summary

| Package | Contents | Swappable? |
|---------|-----------|------------|
| **Common platform base** | Intake skeleton, broker workbench, case store, test framework | No |
| **Industry package** | Category set, markers, handoff thresholds, RAG collection | Yes (insurance → food → local service) |
| **Client-specific package** | Reply templates, proxy calibration, phrasing overrides | Yes (Chen Kui → another broker) |

---

*End of sprint report*
