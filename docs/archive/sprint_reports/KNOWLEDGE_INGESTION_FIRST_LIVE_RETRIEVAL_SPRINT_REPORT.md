# Knowledge Ingestion + First Live Retrieval Sprint Report

**Sprint:** Knowledge Ingestion + First Live Retrieval  
**Date:** 2026-03-09  
**Status:** Accept

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| **Stage 1** — Lock first live retrieval slice | ✅ Completed | `dmv_sr22_explanations.md` chosen; already retrieval-ready |
| **Stage 2** — Build ingestion path | ✅ Completed | `scripts/ingest_insurance_knowledge.py` created and run |
| **Stage 3** — Build retrieval validation path | ✅ Completed | `scripts/test_knowledge_retrieval.py` created; 4/4 queries pass |
| **Stage 4** — Define retrieval/product flow boundaries | ✅ Completed | Section 6a added to `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` |
| **Stage 5** — Validate product stability | ✅ Completed | npm build, guardrail, smoke check, proxy calibration all pass |
| **Stage 6** — Audit + practical judgment | ✅ Completed | Verdict: Accept |

**Skipped:** None.

---

## 2. First live retrieval slice

**Chosen:** `knowledge/industries/insurance/dmv_sr22_explanations.md`

**Why chosen:**
- Documented as first retrieval slice in RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION
- High-value for Chen Kui: DMV/SR-22 is a common customer question
- Already well-structured with clear `##` sections
- Single narrow slice per sprint constraints

**Why high-value:**
- Customers frequently ask "What is SR-22?", "What do I bring to DMV?", "How do I clear suspension?"
- Bilingual content (English + 中文) supports Chinese-speaking customers
- Broker workflow guidance embedded in content

---

## 3. Ingestion / retrieval implementation

| File | Purpose |
|------|---------|
| `scripts/ingest_insurance_knowledge.py` | Reads `knowledge/industries/insurance/*.md`, chunks by `##`, embeds (fastembed/sbert 384-dim), upserts to `auto_insurance_demo_core` with `knowledge_pack`, `topic`, `content_type` |
| `scripts/test_knowledge_retrieval.py` | Validates retrieval with 4 targeted queries; uses `client.search()` for Qdrant server 1.8 compatibility |
| `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` | Updated: section 6 (first slice now LIVE), new section 6a (how retrieval connects to product flows) |
| `knowledge/INGESTION_PREP.md` | Updated: status from "not yet wired" to "first slice live" |
| `knowledge/README.md` | Updated: ingestion now live |

**Metadata fields used:**
- `knowledge_pack: "insurance"`
- `client_pack: null`
- `topic: "dmv_sr22"` (inferred from filename)
- `source_path`, `chunk_title`, `content_type: "knowledge"`

---

## 4. Retrieval boundary integrity

| Area | Status |
|------|--------|
| **Remains rule/config driven** | Intent detection, handoff thresholds, next-question logic, urgency mapping, reply templates, case state |
| **Now retrieval-backed** | DMV/SR-22 explanation; broker Q&A / demo query (includes knowledge chunks in results) |
| **Boundary clearer** | Section 6a in RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION: when to use retrieval vs rules |

**Principle:** Retrieval assists *explanation*. Rules/config drive *workflow*.

---

## 5. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | ✅ Pass | UI build |
| `scripts/run_inbox_triage_scenarios.py` (LLM_GENERATION_ENABLED=0) | ✅ 40/40 | Category, urgency, draft shape |
| `scripts/run_chen_kui_proxy_calibration.py` | ✅ 14/14 | Chen Kui draft style |
| `scripts/run_expression_robustness.py` | ✅ 36/36 | Phrasing robustness |
| `scripts/run_multi_turn_simulations.py` (LLM_GENERATION_ENABLED=0) | ✅ 14/14 | Handoff flow |
| `scripts/test_inbox_triage_api.py` | ✅ Pass | API contract |
| `scripts/guardrail_inbox_triage.sh` | ✅ Pass | Pre-demo quality |
| `scripts/unified_intake_smoke_check.sh` | ✅ Pass | Smoke + guardrail |
| `scripts/ingest_insurance_knowledge.py` | ✅ Pass | Ingestion path |
| `scripts/test_knowledge_retrieval.py` | ✅ 4/4 | Retrieval validation |

---

## 6. Business / platform value

- **Reduces confusion:** Clear answer to "what is truly live retrieval now?" — DMV/SR-22 knowledge is ingested and retrievable.
- **Supports future scaling:** One ingestion path exists; adding `notice_interpretation.md` or `declaration_page_garaging.md` is a file drop + re-run.
- **Helps packaging/selling:** Metadata (`knowledge_pack`, `topic`) enables future common/industry/client pack filtering; hot-swap design is preserved.

---

## 7. Remaining blocker(s)

1. **Qdrant client/server version mismatch:** Client 1.15 vs server 1.8 — `query_points` returns 404; test script uses deprecated `client.search()` which works. Consider aligning versions or documenting workaround.
2. **Retrieval not yet wired into triage:** Inbox triage does not call retrieval today. Optional RAG augmentation for DMV/SR-22 explanation is a future step.
3. **Single collection:** Knowledge chunks live in `auto_insurance_demo_core` alongside URL corpus. Filtering by `knowledge_pack` is possible but not yet used in product flows.

---

## 8. Recommended next step

**Add one more knowledge slice:** `notice_interpretation.md` or `declaration_page_garaging.md` in `knowledge/industries/insurance/`, then re-run `scripts/ingest_insurance_knowledge.py`. No code changes needed.

---

## 9. 中文或中英混合宏观总结

**这次具体把哪块知识真正打进了 Qdrant / retrieval flow：**
- `knowledge/industries/insurance/dmv_sr22_explanations.md` 已 ingest 到 `auto_insurance_demo_core`，5 个 chunk，metadata 含 `knowledge_pack: insurance`、`topic: dmv_sr22`。

**retrieval 现在是真活了，还是只是半活：**
- 真活：知识已进 Qdrant，`scripts/test_knowledge_retrieval.py` 验证 4 个查询都能正确召回相关 chunk。Broker Q&A / demo 查询也会返回这些 chunk（与 URL corpus 混合）。
- 半活：inbox triage 仍不用 RAG，规则驱动。未来可选在 DMV/SR-22 场景用 retrieval 辅助解释。

**哪些东西还是规则驱动，不该进 RAG：**
- 意图检测、handoff 阈值、next-question 逻辑、urgency 映射、reply 模板、case 状态 — 全部规则/config，不进 RAG。

**有没有困难或限制：**
- Qdrant client 1.15 与 server 1.8 不兼容，`query_points` 404；test 用 `client.search()` 可工作。
- 目前 retrieval 未接入 triage 流程，仅 demo Q&A 会用到。

**这次对以后热插拔和卖给别的客户有什么帮助：**
- 证明 knowledge 可从文件 → ingest → Qdrant → retrieval，路径打通。
- metadata 支持 `knowledge_pack`、`topic`，为 future common/industry/client pack 过滤打基础。
- 加新知识 = 加 md 文件 + 重跑 ingest，无需改代码。

---

## 10. Practical retrieval cheat sheet

| Item | Where |
|------|-------|
| **Ingestion script** | `scripts/ingest_insurance_knowledge.py` |
| **First knowledge slice** | `knowledge/industries/insurance/dmv_sr22_explanations.md` |
| **Metadata fields** | `knowledge_pack`, `client_pack`, `topic`, `source_path`, `chunk_title`, `content_type` |
| **Retrieval validation** | `scripts/test_knowledge_retrieval.py` |
| **Collection** | `auto_insurance_demo_core` (shared with URL corpus) |

**Commands:**
```bash
# Ingest (requires Qdrant)
USE_LOCAL_QDRANT=1 PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py

# Dry-run
PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py --dry-run

# Validate retrieval
USE_LOCAL_QDRANT=1 PYTHONPATH=. python3 scripts/test_knowledge_retrieval.py
```

**What still remains outside retrieval:**
- Intent detection, handoff thresholds, next-question logic, urgency, reply templates, case state — all rules/config.

---

## 11. Future retrieval expansion summary

| Status | What |
|--------|------|
| **Retrieval-ready** | `knowledge/industries/insurance/` structure; `knowledge/common/`, `knowledge/clients/chen_kui/` placeholders |
| **Retrieval-active** | DMV/SR-22 (`dmv_sr22_explanations.md`) — ingested, retrievable |
| **Next ingestion slice** | `notice_interpretation.md` or `declaration_page_garaging.md` in `knowledge/industries/insurance/` |

---

*End of sprint report*
