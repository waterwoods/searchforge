# Knowledge Architecture and Config Layer

**Purpose:** Define the clean architecture layers for the Unified Entry / Broker Workbench platform.  
**Scope:** Chen Kui insurance mainline; future hot-swappable client/industry packages.  
**Created:** 2026-03-09 — Knowledge Architecture + Config Layer Sprint

---

## 1. The Five Architecture Layers

| Layer | What it is | Examples |
|-------|------------|----------|
| **1. Rules / workflow logic** | Deterministic operational rules that control flow, thresholds, and decisions | detect → ask → enough? → handoff; urgency rules; handoff thresholds; what fields to request next; broker-side summary rules |
| **2. Common domain knowledge** | Reusable industry knowledge, official explanations, generic FAQ | DMV/SR-22 explanations; notice interpretation; generic insurance FAQ; official gov/insurer content |
| **3. Client-specific knowledge** | Client office phrasing, habits, preferences, material requirements | Chen Kui office phrasing; Chinese customer habits; client-specific FAQ; business-specific preferences |
| **4. State / persistence** | Current case state, follow-up context, conversation memory | current case state; waiting_on; next_contact_by; notes; activity; conversation_summary; saved cases |
| **5. Tests / regression assets** | Scenario packs, calibration cases, validation runners | inbox triage scenarios; proxy calibration cases; multi-turn simulations; expression robustness cases |

---

## 2. Layer Definitions (What Belongs, What Does Not)

### Layer 1: Rules / Workflow Logic

**Belongs:**
- Intent detection rules (add-car, remove-car, payment risk, etc.)
- Handoff thresholds (e.g. add-car: year+model+zip enough)
- Urgency mapping (cancellation → critical, renewal_reminder → low)
- Per-category "ask next" logic
- Broker summary rules (conversation_summary format)
- Max turn counts before handoff

**Does NOT belong:**
- Raw text of notices or explanations (→ common domain knowledge)
- Client office phrasing (→ client-specific knowledge)
- Case data or conversation history (→ state)
- Test expectations (→ tests)

**Where it should live:** Code (Python) for core logic; config for thresholds/mappings when they should be tunable without code change.

---

### Layer 2: Common Domain Knowledge

**Belongs:**
- Official DMV/CDI/insurer explanations
- Notice interpretation knowledge (what "payment failed" means)
- Generic insurance FAQ
- Reusable industry knowledge (SR-22, garaging proof, declaration page)

**Does NOT belong:**
- Workflow rules (→ rules)
- Chen Kui office tone (→ client-specific)
- Case state (→ state)
- Test inputs (→ tests)

**Where it should live:** RAG / Qdrant (vector search) for retrieval; optionally config for small static glossaries.

---

### Layer 3: Client-Specific Knowledge

**Belongs:**
- Chen Kui office phrasing ("我先帮你算", "办公室会尽快处理")
- Chinese customer habits and common phrasings
- Client-specific FAQ
- Material requirements (what this broker typically asks for)
- Tone/style preferences (conclusion first, next step second)

**Does NOT belong:**
- Generic insurance facts (→ common domain)
- Workflow rules (→ rules)
- Case data (→ state)

**Where it should live:** Config (templates, phrasing overrides); RAG for client-specific knowledge packs when large; code for hardcoded Chen Kui defaults today.

---

### Layer 4: State / Persistence

**Belongs:**
- Current case state (case_id, case_status)
- waiting_on, next_contact_by
- case_notes, case_activity
- source_text, conversation_summary
- Progressive answers (year, model, zip, etc.)

**Does NOT belong:**
- Rules or thresholds (→ rules)
- Knowledge content (→ RAG)
- Test scenarios (→ tests)

**Where it should live:** Database / case store (today: JSON file `data/unified_intake_cases.json`).

---

### Layer 5: Tests / Regression Assets

**Belongs:**
- Scenario packs (input → expected_category, expected_urgency)
- Proxy calibration cases (expected_draft_contains_any)
- Multi-turn simulations (turns → expected_handoff_after_turn)
- Expression robustness cases (intent variants)
- Validation runners and expectations

**Does NOT belong:**
- Production rules (→ rules)
- Production knowledge (→ RAG)
- Production case data (→ state)

**Where it should live:** Config files (`configs/*.json`); scripts (`scripts/run_*.py`).

---

## 3. Storage / Implementation Mapping

### A. What Belongs in Code

| Item | Location | Why |
|------|----------|-----|
| Core workflow logic | `services/fiqa_api/inbox_triage/triage.py` | Deterministic, versioned with app |
| Intent detection functions | `triage.py` (`_is_add_vehicle_request`, etc.) | Fast, testable, no external dependency |
| Handoff thresholds | `triage.py` (`_add_car_enough_for_handoff`, etc.) | Operational rules |
| Category templates | `triage.py` (`_get_category_templates`, `_build_client_reply_draft`) | Today: hardcoded; future: load from config |
| Case store logic | `inbox_triage/case_store.py` | CRUD, validation |
| Search/RAG routing | `services/search_core.py` | Backend selection, filter building |

**Principle:** Rules that must be fast, deterministic, and versioned with the app live in code.

---

### B. What Belongs in Config Files

| Item | Current | Target | Why |
|------|---------|--------|-----|
| Scenario mappings | `configs/inbox_triage_scenarios.json` | `configs/` or `configs/tests/` | Regression; no code change needed |
| Proxy calibration cases | `configs/chen_kui_proxy_calibration_cases.json` | `configs/clients/chen_kui/` | Client-specific test pack |
| Multi-turn simulations | `configs/customer_entry_multi_turn_simulations.json` | `configs/tests/` | Regression |
| Expression robustness | `configs/expression_robustness_cases.json` | `configs/tests/` | Regression |
| Marker sets (future) | Today in code | `configs/industries/insurance/markers.json` | Tunable without deploy |
| Field prompts (future) | Today in code | `configs/industries/insurance/field_prompts.json` | Tunable |
| Case-focus labels | Today in code | Config | Client/industry overrides |

**Principle:** Data that changes per client, per industry, or per test pack should be config, not code.

---

### C. What Belongs in RAG / Qdrant

| Item | Current | Target | Why |
|------|---------|--------|-----|
| Auto insurance corpus | `auto_insurance_demo_core` collection | Same | Retrieval for broker Q&A |
| Official DMV/CDI content | In corpus | Same | Semantic search |
| Insurer pages | In corpus | Same | Diversity, citations |
| Common domain FAQ | In corpus | Same | Reusable across clients |
| Client-specific FAQ (future) | — | Separate collection or filter | Hot-swap per client |

**Why NOT everything goes into RAG:**
- Rules must be deterministic; RAG is probabilistic retrieval.
- State must be transactional; Qdrant is not a case store.
- Fast path (triage) should not depend on RAG latency.
- Inbox triage today does NOT use RAG; it uses rules + optional LLM.

**Why rules should not be stored as loose knowledge:**
- Rules drive control flow; they must be exact and versioned.
- Knowledge is for retrieval; rules are for execution.

---

### D. What Belongs in Database / Case Store

| Item | Current | Target | Why |
|------|---------|--------|-----|
| Saved cases | `data/unified_intake_cases.json` | Same for demo; DB for production | Case state |
| case_id, case_status | In JSON | Same | Workflow state |
| waiting_on, next_contact_by | In JSON | Same | Follow-up context |
| case_notes, case_activity | In JSON | Same | Broker memory |
| source_text, conversation_summary | In JSON | Same | Handoff context |

**Why state should not be stored in Qdrant:**
- Qdrant is for vector search over documents, not transactional case CRUD.
- Case updates (status, notes, follow-up) need atomic writes.
- Case store is keyed by case_id; Qdrant is keyed by embedding similarity.

---

### E. What Belongs in Tests

| Item | Location | Purpose |
|------|----------|---------|
| Inbox triage scenarios | `configs/inbox_triage_scenarios.json` | Category/urgency regression |
| Proxy calibration | `configs/chen_kui_proxy_calibration_cases.json` | Draft style regression |
| Multi-turn simulations | `configs/customer_entry_multi_turn_simulations.json` | Handoff flow regression |
| Expression robustness | `configs/expression_robustness_cases.json` | Phrasing robustness |
| Runners | `scripts/run_inbox_triage_scenarios.py`, etc. | Execute and report |

---

## 4. Separation of Common vs Client-Specific Knowledge

| Dimension | Common (industry) | Client-specific |
|-----------|------------------|-----------------|
| **Content** | DMV rules, SR-22, generic insurance | Chen Kui phrasing, office tone |
| **Storage** | RAG collection (shared) | Config + optional client RAG pack |
| **Reuse** | Same for all insurance brokers | Per client |
| **Example** | "SR-22 is a proof of insurance filing" | "我先帮你确认" |

**Hot-swap implication:** Industry package = common knowledge + shared rules. Client package = overrides for phrasing, templates, and optional client-specific knowledge collection.

---

## 5. Hot-Swappable Package Model (Design Only)

### A. Common Platform Base

- Intake skeleton (detect → ask → enough? → hand off)
- Broker workbench UI
- Shared persistence (case store interface)
- Shared test framework (scenario runner, calibration runner)
- Core triage engine (rule-based + optional LLM)

**Reusable:** Yes. **Replaceable:** No (core).

---

### B. Industry Package (e.g. Insurance)

- Category set (cancellation_warning, missing_document, etc.)
- Marker sets (ADD_VEHICLE_MARKERS, PAYMENT_MARKERS, etc.)
- Handoff thresholds (add-car enough when year+model+zip)
- Common domain RAG collection (auto insurance corpus)
- Field prompts (what to ask for add-car, remove-car)

**Reusable:** Across insurance brokers. **Replaceable:** Yes (swap for food/sausage, local service).

---

### C. Client-Specific Package (e.g. Chen Kui)

- Reply templates (Chinese, conclusion-first)
- Proxy calibration cases
- Client-specific phrasing overrides
- Optional client FAQ / knowledge pack in RAG

**Reusable:** No (per client). **Replaceable:** Yes (swap for another broker).

---

## 6. What Is Implemented vs Conceptual

| Area | Status |
|------|--------|
| Five-layer definition | **Defined** (this doc) |
| Rules in code | **Implemented** (triage.py) |
| State in JSON case store | **Implemented** |
| RAG for query (auto insurance) | **Implemented** |
| Inbox triage (no RAG) | **Implemented** |
| Config for test packs | **Implemented** |
| Config for rules/thresholds | **Partial** (mostly in code) |
| Hot-swap engine | **Conceptual** |
| Industry/client package dirs | **Proposed** (Stage 5) |

---

## 7. Proposed Config Layer Structure (Stage 5)

**Goal:** Predictable locations for rules/config, knowledge boundaries, state, and test assets.

### Proposed Layout (Future; Not Implemented Yet)

```
configs/
├── common/                    # Shared across clients
│   └── (future: shared markers, field prompts)
├── industries/
│   └── insurance/             # Insurance industry pack
│       ├── markers.json       # (future) ADD_VEHICLE_MARKERS, etc.
│       └── handoff_thresholds.json  # (future) add-car enough when...
├── clients/
│   └── chen_kui/              # Chen Kui client pack
│       ├── proxy_calibration_cases.json
│       └── templates.json      # (future) reply templates
├── tests/                     # Regression packs
│   ├── inbox_triage_scenarios.json
│   ├── multi_turn_simulations.json
│   └── expression_robustness_cases.json
├── broker_demo_urls.json      # RAG corpus URLs (stays)
└── demo.env.example           # Env template (stays)
```

### Current vs Proposed

| Current | Proposed | Action |
|--------|----------|--------|
| `configs/inbox_triage_scenarios.json` | `configs/tests/inbox_triage_scenarios.json` | **Proposed** — no move now |
| `configs/chen_kui_proxy_calibration_cases.json` | `configs/clients/chen_kui/proxy_calibration_cases.json` | **Proposed** — no move now |
| `configs/customer_entry_multi_turn_simulations.json` | `configs/tests/multi_turn_simulations.json` | **Proposed** — no move now |
| `configs/expression_robustness_cases.json` | `configs/tests/expression_robustness_cases.json` | **Proposed** — no move now |

**Principle:** Do not move files now. Document the target structure. Move only when adding a second client or when scripts need the new paths.

**Retrieval boundaries:** See `docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md` for what should NEVER go into RAG vs what SHOULD. Knowledge source files: `knowledge/` (common, industries, clients).

### AI Agent / Founder Readability

A future AI agent or founder should find:

- **Rules/config:** `configs/industries/insurance/` (future), `docs/MATURE_INTAKE_SKELETON.md`
- **Knowledge boundaries:** RAG collections (`auto_insurance_demo_core`), `configs/broker_demo_urls.json`
- **State boundaries:** `data/unified_intake_cases.json`, `case_store.py`
- **Test assets:** `configs/inbox_triage_scenarios.json`, `configs/expression_robustness_cases.json`, `scripts/run_*.py`

---

*End of architecture doc*
