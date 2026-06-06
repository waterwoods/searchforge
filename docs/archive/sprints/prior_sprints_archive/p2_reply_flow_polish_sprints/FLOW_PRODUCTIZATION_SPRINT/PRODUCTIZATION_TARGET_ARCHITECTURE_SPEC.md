# Productization Target Architecture Spec (Lightweight)

**Constraint:** Small team, single primary customer today, trial-grade reliability over framework elegance.

---

## 1. Target stack (no new framework)

Keep **FastAPI + React + JSON configs + Python engine**. The productization target is **clarity and load rules**, not LangGraph or a rules DSL.

---

## 2. Layer specifications

### 2.1 Common engine

**Belongs**

- `triage_conversation`, `triage_for_append`, `triage_message` (or a future thin facade over them).
- Workflow state keys and lifecycle semantics (`WORKFLOW_STATE_KEYS`, handoff_ready, collection_stage, etc.).
- Case persistence (`case_store.py`), append pipeline, validation.
- LLM/rule selection, output normalization, guardrail merge.

**Does not belong**

- Broker office name, Chinese marketing copy, per-client SLA promises.
- Insurance-specific marker strings (those belong in industry lexicon).

**Why the boundary matters:** The engine is what you **unit-test and scenario-test**. If copy leaks in, tests become brittle and customers hear inconsistent tone.

---

### 2.2 Industry pack (auto insurance)

**Belongs**

- Intent markers (`markers.json`).
- Document item lexicon + labels.
- Category templates (`category_templates.json`).
- Base reply templates (`reply_templates.json`).
- Add-car (and similar) **prompt text** for next asks (`add_car_rules.json`).

**Does not belong**

- Specific broker branding (“陈奎办公室”).
- Web layout or React component structure.

**Why:** Same engine + swap `configs/industries/<id>/` → new vertical **later**; today you only ship `insurance`.

---

### 2.3 Client pack (broker office)

**Belongs**

- `handoff_phrases.json` (ZH/EN per flow key).
- `ui_copy.json` (all customer-visible chrome + quick starts).
- `reply_overrides.json` (shallow merge over industry templates).

**Does not belong**

- Append boundary **logic** (which domain crosses are `new_issue`).
- Field extraction regex for VIN/ZIP/etc.

**Why:** A new broker in **same industry** should be mostly **folder + env** (`CLIENT_ID`), not a fork of `triage.py`.

---

### 2.4 Lexicon / rule maps

**Belongs**

- Keyword/marker lists, tunable without redeploy (where filesystem allows).
- Short prompt fragments (“ask for zip next”) keyed by flow state.

**Does not belong**

- Branching graphs with ten nested conditions — that becomes unmaintainable JSON.

**Why:** Founders and CS can tune **language**; engineers retain **control flow**.

---

### 2.5 Regression battery

**Belongs**

- Scenario JSON packs + dedicated runners (`run_*_scenarios.py`, simulations).
- `guardrail_inbox_triage.sh` as the **single entry** for “is the product still the product.”
- API smoke tests when server available.

**Does not belong**

- Long-form architecture prose (link to sprint docs).

**Why:** This layer is how you **sell** change management to brokers (“we rerun the battery”).

---

## 3. Load order (canonical)

1. **Common** defaults (`workflow_defaults.json`).
2. **Industry** templates, markers, industry reply templates.
3. **Client** overrides (handoff, UI copy, reply_overrides).

**Fix required for full parity:** `reply_overrides` must key off `get_active_client_id()`, not a hardcoded client folder.

---

## 4. What “hot-plug” means here

Hot-plug = **new directories under `configs/` + `CLIENT_ID` (and future `INDUSTRY_ID`)**, not hot-plug of arbitrary Python without review.

---

## 5. What not to build yet

- Generic workflow DSL in YAML.
- Visual rule builder for boundary logic.
- Multi-tenant auth and per-tenant DB — out of stated scope.

---

## 6. Mapping to main questions (target view)

| Question | Answer |
|----------|--------|
| Common engine vs packs | Engine = orchestration + persistence + LLM/rule; packs = words + markers + templates. |
| Hot-pluggable architecture | Directory-based packs + stable loader + env IDs. |
| Customer migration easier when | Strings and overrides are single-sourced; no hardcoded client paths. |
| Customer review easier when | UI copy + handoff phrases + scenario reports align with what the engine does. |
