# UI / Backend / Config / Test Split Spec

Concrete split of **who owns what** for Unified Intake.

---

## 1. Backend orchestration

| Component | Path | Responsibility |
|-----------|------|----------------|
| Flow brain | `services/fiqa_api/inbox_triage/triage.py` | Classification, multi-turn merge, add-car/remove-car/claim/missing-doc/cancel structured extraction, handoff vs next-ask, append boundary, broker_next_step tailoring, LLM vs rule routing |
| Config I/O | `services/fiqa_api/inbox_triage/config_loader.py` | Load industry + client JSON; `get_ui_copy` allowlist; add-car rules load/save; `CLIENT_ID` default `chen_kui` |
| HTTP | `services/fiqa_api/routes/inbox_triage.py` | REST contract, soft-route inference helpers, reroute/starter dicts, case endpoints |
| Persistence | `services/fiqa_api/inbox_triage/case_store.py` | JSON case file, attachments, message history |
| Session (if used) | `session_store.py` | In-progress session continuity (referenced from routes) |
| RAG hook | `notice_retrieval.py` | Optional augment for explanations (imported from triage) |

---

## 2. Config / rule files

| File | Purpose |
|------|---------|
| `configs/industries/insurance/markers.json` | Intent marker lexicon (+ document item markers) |
| `configs/industries/insurance/category_templates.json` | Per-category broker_next_step / client_prep (some categories stay “dynamic” in code) |
| `configs/industries/insurance/reply_templates.json` | Industry reply templates |
| `configs/clients/chen_kui/reply_overrides.json` | Shallow merge overrides |
| `configs/industries/insurance/add_car_rules.json` | Add-car **ask** copy (zh/en) for standard next-step prompts |
| `configs/clients/chen_kui/handoff_phrases.json` | Customer-facing handoff lines per scenario key (add_car, remove_car, other_*, customer_requested_human, …) |
| `configs/clients/chen_kui/ui_copy.json` | Portal labels, transaction ribbon, closure card, same-request panel — **keys allowlisted** in `get_ui_copy` |
| `configs/common/workflow_defaults.json` | Generic fallbacks when templates missing |
| `configs/inbox_triage_scenarios.json` | Pack for `run_inbox_triage_scenarios.py` |
| `configs/*_simulations.json` (various) | Multi-turn / adversarial / trial stress inputs |
| `docs/sprints/**/scenario_battery.json` | Sprint-local batteries (e.g. add-car stress) consumed by dedicated runners |

---

## 3. Frontend

| File | Role |
|------|------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Conversation UI, quick-start intents, handoff detection, add-car transaction chrome, case report one-liner helpers, append / new-issue UX |
| `ui/src/api/inboxTriage.ts` | Typed API client for triage + case operations |
| `ui/src/api/clientConfig.ts` | Fetches `GET .../client-config`; **DEFAULT_UI_COPY** mirrors backend allowlist for offline resilience |

**UI logic vs backend truth:** The UI may **infer** “this looks like add-car” (`triageResultLooksLikeAddCar`) for labels and toasts, but **slots and handoff_ready** always come from the API response.

---

## 4. Tests / regression batteries

| Kind | Examples |
|------|-----------|
| **Guardrail entry** | `scripts/guardrail_inbox_triage.sh` — orchestrates many checks |
| **Scenario packs** | `scripts/run_inbox_triage_scenarios.py` (uses `configs/inbox_triage_scenarios.json`) |
| **Multi-turn / adversarial** | `run_multi_turn_simulations.py`, `run_adversarial_simulation.py`, `run_complex_adversarial_simulation.py` |
| **Workflow backbone** | `scripts/test_state_workflow_backbone.py` |
| **Case boundary** | `scripts/run_case_boundary_battery.py` |
| **Trial / handoff timing** | `run_handoff_timing_simulations.py`, `run_broker_trial_stress_simulations.py` |
| **Add-car focused** | `run_add_car_*.py` (scenario, mutation, edge, stress, high-ROI regression, etc.) |
| **API smoke** | `scripts/test_inbox_triage_api.py` (when server up) |

**Role of tests:** They are the **behavioral contract** for a system whose main logic is a large Python module. Changing `triage.py` without updating packs is the primary regression risk.

---

## 5. “What lives where” summary table

| Concern | Primary location |
|---------|------------------|
| Ask order (add-car) | Code |
| Ask wording (add-car) | Config (+ code fallback) |
| Handoff customer wording | Config (+ code fallback) |
| Portal / closure / ribbon copy | Config + UI defaults |
| Intent detection | Config markers + code helpers + LLM |
| Case persistence schema | `case_store.py` |
| Same-case vs new-issue append | Code (`triage.py`) + UI surfacing |
| Commercial edge cases (timing, corrections) | Code (`triage_conversation` branches) |
