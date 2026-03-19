# Retrieval + Knowledge Layer Foundation

**Purpose:** Define clearly what belongs in rules/config vs retrievable knowledge vs state. A founder or engineer should no longer be confused about "what goes into RAG."

**Scope:** Unified Entry / Broker Workbench mainline. Chen Kui insurance first client.

---

## 1. The Five Boundaries

| Boundary | What it is | Where it lives | Goes into Qdrant/RAG? |
|----------|------------|----------------|------------------------|
| **Workflow rules** | Deterministic logic: detect → ask → enough? → hand off; thresholds; next-question logic | Code (`triage.py`), config (markers, thresholds) | **NO** |
| **Config-driven behavior** | Markers, reply templates, handoff phrases, document labels | `configs/industries/insurance/`, `configs/clients/chen_kui/` | **NO** |
| **Retrievable knowledge** | Explanatory content: DMV/SR-22, notice interpretation, FAQ, declaration page / garaging proof | Qdrant collections, `knowledge/` (ingestion-prep) | **YES** |
| **Case state / persistence** | Current case, waiting_on, notes, conversation_summary | `data/unified_intake_cases.json`, case_store | **NO** |
| **Tests** | Scenario packs, calibration cases, validation runners | `configs/*.json`, `scripts/run_*.py` | **NO** |

---

## 2. What Should NEVER Go into Qdrant / RAG

| Item | Why |
|------|-----|
| Workflow thresholds (e.g. add-car enough when year+model+zip) | Rules must be deterministic; RAG is probabilistic. Control flow must be exact. |
| Handoff rules (when to hand off, max turns) | Same. Rules drive execution. |
| Intent markers (add_vehicle, payment, dmv_help, etc.) | Used for fast rule-based detection. Config, not retrieval. |
| Reply templates (first-turn wording) | Config-driven; loaded at startup. Not semantic search. |
| Case state (case_id, waiting_on, notes) | Transactional; keyed by case_id. Qdrant is for similarity search. |
| Test scenarios (expected_category, expected_urgency) | Regression assets. Not production knowledge. |
| Urgency mapping (cancellation → critical) | Rule. Deterministic. |

**Principle:** Rules decide *what to do*. Knowledge helps *explain, clarify, and answer*.

---

## 3. What SHOULD Go into Qdrant / RAG

| Item | Why |
|------|-----|
| DMV / SR-22 explanation snippets | Customer asks "what is SR-22?" — semantic retrieval finds explanation. |
| Notice interpretation reference | "What does payment failed mean?" — retrieval finds notice-type explanations. |
| Declaration page / garaging proof explanations | Customer confused about document names — retrieval finds definitions. |
| Common insurance FAQ | "Why did my premium go up?" — retrieval finds rate-factor content. |
| Official DMV/CDI/insurer content | Already in `auto_insurance_demo_core`; semantic search over official sources. |
| Chen Kui office FAQ (future) | Client-specific phrasing, office process notes — optional client RAG pack. |

**Principle:** Knowledge is for retrieval. When a human would "look it up," that content belongs in RAG.

---

## 4. What Stays in Code/Config Even Long Term

| Item | Location | Reason |
|------|----------|--------|
| Intent detection logic | `triage.py` | Fast, deterministic, versioned with app |
| Handoff thresholds | `triage.py` (future: config) | Operational rules |
| Markers (keywords for intent) | `configs/industries/insurance/markers.json` | Tunable without deploy; not retrieval |
| Reply templates | `configs/industries/insurance/reply_templates.json` | First-turn wording; config merge |
| Handoff phrases | `configs/clients/chen_kui/handoff_phrases.json` | Client phrasing; config |
| Document item labels (dec page, garaging proof) | `markers.json` document_items | Short labels for UI; config |

---

## 5. Common vs Industry vs Client Knowledge

| Layer | Content | Storage | Example |
|-------|---------|--------|---------|
| **Common knowledge** | Reusable service-entry best practices; generic communication guidance | `knowledge/common/` (future); small today | (Future) generic fallback wording |
| **Industry knowledge** | Insurance concepts; DMV/SR-22; notice types; declaration page; garaging proof; common FAQ | Qdrant `auto_insurance_demo_core`; `knowledge/industries/insurance/` | "SR-22 is a proof of insurance filing" |
| **Client knowledge** | Chen Kui office FAQ; Chinese-speaking customer preferences; office-specific process notes | `knowledge/clients/chen_kui/` (future); config today | "我先帮你算" style; office-specific phrasing |

**Hot-swap implication:** Industry pack = common + insurance knowledge. Client pack = overrides for phrasing + optional client RAG collection.

### Knowledge Package Model (Practical)

| Pack | Path | Contents | Retrieval-ready today |
|------|------|----------|------------------------|
| **Common** | `knowledge/common/` | Generic service-entry best practices; fallback wording | Placeholder |
| **Industry (insurance)** | `knowledge/industries/insurance/` | DMV/SR-22; notice interpretation; declaration page/garaging proof; common FAQ | **Slices:** dmv_sr22, notice_interpretation, declaration_page_garaging |
| **Client (Chen Kui)** | `knowledge/clients/chen_kui/` | Office FAQ; Chinese customer preferences; process notes | Placeholder |

**Load order:** common → industry → client. Same as config. Retrieval can filter by pack when querying.

---

## 6. Current vs Future State

| Area | Current | Future |
|------|---------|--------|
| Inbox triage | Rules + config. **Light RAG** for notice + document confusion. | Rule-based fast path; retrieval augments notice and document-explanation replies when available. |
| Broker Q&A / demo | RAG over `auto_insurance_demo_core` | Same; add industry knowledge pack structure |
| Knowledge folder | `knowledge/` with common/industries/clients | **Live:** DMV/SR-22, notice_interpretation, declaration_page_garaging |
| First retrieval path | **LIVE** — `english_notice_confusion` (notice_interpretation, dmv_sr22) | `notice_retrieval.retrieve_notice_explanation` |
| Second retrieval path | **LIVE** — document confusion (declaration page, garaging proof) | `notice_retrieval.retrieve_document_explanation` |

---

## 6a. How Retrieval Connects to Product Flows

**When to use retrieval (RAG):**

| Situation | Use retrieval? | Why |
|-----------|----------------|-----|
| DMV / SR-22 explanation | **YES** | Customer asks "what is SR-22?" — retrieval finds explanation. |
| Notice meaning explanation | **YES** | "What does payment failed mean?" — retrieval finds notice-type content. |
| Declaration page / garaging proof | **YES** | Customer confused about document names — retrieval finds definitions. |
| Broker Q&A / demo query | **YES** | Any question where a human would "look it up." |

**When to stay rule/config driven (NO retrieval):**

| Situation | Use retrieval? | Why |
|-----------|----------------|-----|
| Handoff threshold decision | **NO** | Rules decide when enough info is collected. Deterministic. |
| Next-question logic | **NO** | Rules decide what to ask next. Config-driven. |
| Current case status | **NO** | State store. Not similarity search. |
| Intent detection (add-car, payment, etc.) | **NO** | Fast rule-based markers. Not semantic. |
| Reply template selection | **NO** | Config merge. Not retrieval. |
| Urgency mapping | **NO** | Rule. Deterministic. |

**Principle:** Retrieval assists *explanation*. Rules/config drive *workflow*.

---

## 7. Quick Decision Tree

**"Where does this go?"**

1. **Does it control flow or thresholds?** → Rules/config. Not RAG.
2. **Is it current case state?** → Case store. Not RAG.
3. **Is it a test expectation?** → Config/tests. Not RAG.
4. **Would a human look it up to explain something?** → RAG. Yes.
5. **Is it short phrasing for first-turn reply?** → Config (reply_templates). Not RAG.

---

## 8. Runtime Stability — Retrieval-Active vs Fallback

**When retrieval is active:** Embedder warmup complete (`EMBED_READY=True`) and Qdrant reachable. `english_notice_confusion` replies are augmented with knowledge-backed snippets (e.g. "根据常见情况，'payment failed' 一般意思是...").

**When fallback is used:** Embedder still warming up, Qdrant unreachable, or retrieval disabled. Reply uses template-only (e.g. "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我...").

| Condition | Retrieval | Fallback |
|-----------|-----------|----------|
| App just started, warmup in progress | No | Yes |
| Qdrant Cloud 404 / paused | No | Yes |
| `NOTICE_RETRIEVAL_ENABLED=0` | No | Yes |
| Warmup complete, Qdrant OK | Yes | No |

**Diagnostics:**
- `retrieval_ready()` in `notice_retrieval.py` — returns True only when both embedder and Qdrant ready
- `PYTHONPATH=. python3 scripts/verify_retrieval_health.py` — standalone retrieval path check
- `PYTHONPATH=. python3 scripts/verify_retrieval_health.py --live` — check against running API
- Logs: `[NOTICE_RETRIEVAL]` at INFO when fallback used (warmup, init fail, search fail)

**Recovery:** If retrieval never activates, run `bash scripts/restore_8001_readiness.sh` (forces local Qdrant, restarts backend, waits for ready).

---

*See also: `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md`, `docs/CONFIG_EXTRACTION_GUIDE.md`, `docs/CLIENT_PACK_FOUNDATION.md`*
