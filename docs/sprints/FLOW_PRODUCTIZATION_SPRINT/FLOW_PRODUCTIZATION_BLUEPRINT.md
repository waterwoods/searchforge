# Flow Productization Blueprint

**Sprint:** Flow Productization Sprint  
**Product:** SearchForge → Chen Kui Insurance Unified Entry (Unified Intake)  
**Purpose:** Move from “works in code” to “legible layers, clear boundaries, realistic portability path.”

---

## 1. North star

The product should be describable as five cooperating layers:

| Layer | Role |
|-------|------|
| **Common engine** | Case lifecycle, append/boundary, handoff timing, orchestration (rule + optional LLM), persistence contracts |
| **Industry pack** | Auto-insurance flows (add-car, claim, billing-adjacent, missing doc, etc.) and shared industry copy templates |
| **Client pack** | Broker office name, tone, handoff phrases, UI strings, quick-start buttons |
| **Lexicon / rule maps** | Markers, aliases, extraction-oriented signals, tunable prompts (e.g. add-car next asks) |
| **Regression battery** | Scenario JSON packs, guardrail scripts, API smoke tests |

This sprint does **not** require rewriting the engine. It requires **naming** what is already there and **prioritizing** what moves next.

---

## 2. What was reviewed (evidence base)

- **Orchestration / rules:** `services/fiqa_api/inbox_triage/triage.py` (~3.6k LOC) — multi-turn triage, append boundary, add-car field extraction, handoff logic, workflow state keys.
- **Config loading:** `services/fiqa_api/inbox_triage/config_loader.py` — industry markers, templates, client handoff + UI copy, add-car rules, workflow fallbacks.
- **API surface:** `services/fiqa_api/routes/inbox_triage.py` — triage endpoints, soft-route reroute copy, starter replies (partially duplicated with config elsewhere).
- **Persistence:** `services/fiqa_api/inbox_triage/case_store.py` — JSON case store, validation constants, append pipeline.
- **Configs:** `configs/industries/insurance/*.json`, `configs/clients/chen_kui/*.json`, `configs/common/workflow_defaults.json`.
- **UI:** `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/clientConfig.ts` — client config fetch + merged defaults.
- **Guardrails:** `scripts/guardrail_inbox_triage.sh` and chained Python runners.

---

## 3. Current state in one paragraph

You already have a **real** separation between **industry JSON** (markers, category templates, reply templates, add-car prompts) and **client JSON** (handoff phrases, UI copy). The **engine** still encodes the **order of decisions**, **boundary matrix** (which domain crosses trigger `new_issue`), **field extraction** (regex/heuristics), and **several narrative strings** (reroute, soft-route starters, boundary replies). The **UI** is **config-driven for copy** but **type- and layout-bound** in React. **Tests** are strong but **distributed** across many scripts and packs without a single “product map” doc.

---

## 4. Design principles (non-negotiables)

1. **Do not** externalize control flow into JSON until you have a second customer — that is high fragility for low ROI.
2. **Do** externalize **language**, **markers**, and **client-visible labels** aggressively — that is high ROI for trials and demos.
3. **Treat `triage.py` as the engine** until a deliberate extraction (e.g. `engine/` package) is justified by a second client or a hiring event.
4. **Single source of truth per string class** — today some strings exist in API routes, triage fallbacks, and UI defaults; convergence is productization work.

---

## 5. Optional artifacts (this folder)

- **Current Architecture Layer Map** — table of layers vs. files.
- **Code vs Config vs UI vs Test Boundary Spec** — decision guide.
- **Target Architecture Spec** — lightweight future shape.
- **Externalization Priority Spec** — move next / later / keep in code.
- **Portable Pack Spec** — what swaps for “same industry, new broker” vs. “new industry.”
- **Execution Outline** — how to run the next 1–3 weeks without overbuilding.
- **Founder Inspection Notes** — how to read the system in 30 minutes.
- **Final Report** — judgment + 中文总结.

---

## 6. Architecture table (at-a-glance)

| Concern | Mostly today | Ideal owner |
|---------|----------------|-------------|
| “When do we hand off?” | Code (`triage.py`, `_should_handoff`, add-car exceptions) | Engine |
| “What question do we ask next?” | Code + `add_car_rules.json` | Engine + lexicon |
| “What did the customer mean?” | Code + `markers.json` | Lexicon (+ engine disambiguation) |
| “What does the broker see?” | Code + industry templates | Industry pack |
| “What does the customer read?” | Client handoff + UI copy + many fallbacks | Client pack |
| “Same thread or new issue?” | Code (`_classify_append_case_boundary`) | Engine (policy), optional future config for **thresholds** only |
| “Persist case” | `case_store.py` | Engine |
| “Did we regress?” | Scripts + JSON scenarios | Regression battery |

---

## 7. “What should move next” checklist (summary)

See `EXTERNALIZATION_PRIORITY_SPEC.md` for the full list. Short form:

- [ ] Route-level **reroute** and **soft-route starter** strings → client or industry JSON (remove duplication with triage fallbacks).
- [ ] Align **`get_reply_templates()`** to use `get_active_client_id()` instead of hardcoded `chen_kui` path.
- [ ] Align **`add_car_rules.json`** schema with loader (e.g. `ask_driver_only` exists in JSON but loader only reads three keys).
- [ ] Document **one** “string ownership” matrix (this sprint delivers that in the boundary spec).
- [ ] Optional: boundary **narrative** blocks → client pack (keep **logic** in code).

---

## 8. Future hot-plug structure (target mental model)

```
configs/
  industries/<industry_id>/
    markers.json
    category_templates.json
    reply_templates.json
    add_car_rules.json   # or flows/add_car.json later
  clients/<client_id>/
    handoff_phrases.json
    ui_copy.json
    reply_overrides.json   # shallow merge over industry
  common/
    workflow_defaults.json
```

**Engine** (`triage.py`, `case_store.py`, routes) loads by `(INDUSTRY_ID, CLIENT_ID)` with your existing env pattern (`CLIENT_ID`; industry could follow).

Hot-plug = **swap folders**, not **swap frameworks**.
