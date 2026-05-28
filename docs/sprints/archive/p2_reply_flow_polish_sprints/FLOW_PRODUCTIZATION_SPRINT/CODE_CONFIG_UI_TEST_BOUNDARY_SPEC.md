# Code vs Config vs UI vs Test — Boundary Spec

**Purpose:** Decide what belongs where **now**, without pretending the engine is already a plugin system.

---

## 1. Definitions

| Surface | Owns | Must not own (at this stage) |
|---------|------|------------------------------|
| **Code (engine)** | Ordering of decisions, conflict resolution, append/boundary **policy**, schema of workflow state, persistence invariants | Long static copy for every broker; exhaustive intent lists without fallback |
| **Config (industry)** | Markers, industry reply templates, category templates, add-car prompt text, shared insurance semantics | Client brand, office name, broker-specific SLA wording |
| **Config (client)** | Handoff phrases, UI copy, quick-start labels, `reply_overrides` merge | Core “what is a case boundary” graph |
| **UI** | Layout, accessibility, loading states, **merging** API copy with safe defaults | Business classification rules |
| **Tests** | Executable spec of behavior + regression locks | Documentation prose (link out to docs instead) |

---

## 2. Decision matrix (when adding a change)

| If you are changing… | Put it in… | Because… |
|---------------------|------------|------------|
| A **phrase** customers or brokers read | Client or industry JSON (by scope) | Faster trial tweaks, no redeploy if config is writable |
| A **keyword** customers use | `markers.json` (or industry lexicon file) | Tunable intent detection |
| **Which step comes next** in a flow | Code | Keeps behavior testable and explicit |
| **When** the system hands off | Code | Central policy; scenarios lock this |
| **Whether** a message starts a new case | Code (`_classify_append_case_boundary`) | Safety-critical; needs scenario coverage |
| **How** the UI labels “submit” / “new issue” | `ui_copy.json` | Client pack |
| **Validation** of stored cases | `case_store.py` | Data integrity |
| **New regression** for a broker promise | Scenario JSON + runner + guardrail entry | Prevents silent drift |

---

## 3. Current violations (intentional inventory)

These are **not** bugs — they are **boundary leaks** to fix when ROI is clear:

1. **`inbox_triage.py` route module** contains `REROUTE_MESSAGES` and `SOFT_ROUTE_STARTER_REPLIES` (Chinese business copy). **Better home:** client pack or industry “routing copy” JSON, loaded via `config_loader`.
2. **`config_loader.get_reply_templates()`** always loads `configs/clients/chen_kui/reply_overrides.json`. **Better:** `configs/clients/{active_client_id}/reply_overrides.json`.
3. **`ui/src/api/clientConfig.ts`** duplicates Chen Kui defaults (`DEFAULT_UI_COPY`). **Acceptable** as offline/fail-safe fallback; **risk** is drift vs `ui_copy.json`. Mitigation: treat JSON as source of truth and regenerate TS defaults occasionally, or minimize defaults to generic English only.
4. **`add_car_rules.json`** includes keys not read by `get_add_car_rules()` (e.g. `ask_driver_only`). **Fix:** extend loader + engine or remove from JSON — **schema alignment** is part of productization.
5. **`triage.py` `_FALLBACK_MARKERS`** duplicates `markers.json` when file missing. **Acceptable** for resilience; **productization** note: deploy should always ship JSON so fallbacks are emergency-only.

---

## 4. What must stay in code (explicit, for stability)

- **Append / case boundary classification** graph and pivot detection (`_classify_append_case_boundary`, related helpers).
- **Structured field extraction** for add-car, claim, removal, cancellation (regex/heuristics) until you have a second industry to justify a plugin interface.
- **LLM vs rule** routing and normalization (`_llm_triage`, `_normalize_output`).
- **Handoff gating** interaction with `next_best_question` and scenario-backed timing.
- **Case store** limits and allowed enums.

Reason: externalizing these early creates **hidden programming languages** in JSON that are harder to test than Python.

---

## 5. What is already well externalized

- Insurance **markers** (`configs/industries/insurance/markers.json`) with loader + fallback.
- **Handoff phrases** per client (`handoff_phrases.json`).
- **UI copy** per client (`ui_copy.json`) served via API and consumed in React.
- **Workflow fallbacks** (`workflow_defaults.json`).
- **Category templates** and **industry reply templates** (industry JSON).

---

## 6. Test boundary rules

- **Rule-based scenarios** (`LLM_GENERATION_ENABLED=0`) are the **contract** for demo and trial.
- **Guardrail script** is the **orchestrator** — productization means keeping the **list of packs** understandable (see Execution Outline).
- **API tests** validate transport + shape; **scenario tests** validate semantics.

---

## 7. Answers tied to main questions (boundary lens)

- **Already product-like:** split config directories (industry vs client vs common), API-served UI copy, marker JSON.
- **Too code-bound:** boundary reply paragraphs, route-level reroute strings, parts of add-car extraction.
- **Should remain code for now:** orchestration order, boundary policy, handoff rules, case persistence invariants.
