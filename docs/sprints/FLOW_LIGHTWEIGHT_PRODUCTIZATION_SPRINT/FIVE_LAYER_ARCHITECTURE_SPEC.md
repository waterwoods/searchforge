# Five-Layer Architecture Spec

This spec is the **conceptual product architecture** for Unified Intake. Implementation still lives in a pragmatic Python monolith; layers are **ownership boundaries**, not separate deployables (yet).

---

## 1. Common Engine

**Purpose:** Orchestration, case lifecycle, append/boundary behavior, workflow invariants, persistence primitives.

**Belongs here today**

- `triage.py` — `triage_conversation`, `triage_for_append`, handoff gating, multi-turn merge, LLM vs rule routing.
- `case_store.py` — JSON case store, attachments, status enums, validation.
- `session_store.py` — in-progress session continuity.
- `routes/inbox_triage.py` — HTTP contract, normalization, persistence triggers (orchestration **calls** into engine).

**Move next (low risk)**

- None required for this sprint; prefer **docs + thin config** first.

**Do not move yet**

- Core state transitions, append boundary resolution, conflict/reroute logic inside `triage_conversation`.

---

## 2. Industry Pack

**Purpose:** Insurance-specific flows (add-car, payment/cancel, missing doc, claim, renewal), industry prompts and defaults.

**Belongs here today**

- `configs/industries/insurance/markers.json` — intent markers, document_items.
- `configs/industries/insurance/reply_templates.json` — base reply templates.
- `configs/industries/insurance/category_templates.json` — broker_next_step / client_prep per category.
- `configs/industries/insurance/add_car_rules.json` — next-step prompts (including `ask_driver_only`).

**Move next**

- Optional: richer industry “pack manifest” (version, description) for onboarding docs only.

**Do not move yet**

- Heavy policy encoded only in JSON without scenario coverage.

---

## 3. Client Pack

**Purpose:** Broker/office wording, UI copy, handoff phrases, client-specific overrides.

**Belongs here today**

- `configs/clients/<client_id>/handoff_phrases.json`
- `configs/clients/<client_id>/ui_copy.json`
- `configs/clients/<client_id>/reply_overrides.json` (optional shallow merge over industry templates)

**Move next**

- Per-client `reply_overrides` content (today Chen Kui file may be empty; structure is ready).
- Optional: client-specific soft-route copy **if** product needs different reroute lines per office (today: common file).

**Do not move yet**

- Entire `triage.py` branches per client — use config + `client_id` parameters instead.

---

## 4. Lexicon / Rule Map Layer

**Purpose:** Markers, aliases, triggers, extraction vocabulary, phrase guards, small editable rules.

**Belongs here today**

- Insurance markers JSON (above).
- Add-car rule prompts (industry JSON).
- In-code fallbacks in `triage.py` (`_FALLBACK_MARKERS`, etc.) when JSON missing.

**Move next**

- Incremental migration of **stable** marker sets from code fallback to JSON **when** scenarios exist.

**Do not move yet**

- Complex conditional logic (e.g. mixed-intent resolution) into giant JSON blobs.

---

## 5. Regression Battery Layer

**Purpose:** Executable contracts — scenarios, stress runners, guardrail orchestration.

**Belongs here today**

- `scripts/guardrail_inbox_triage.sh` — master guardrail.
- `scripts/run_inbox_triage_scenarios.py` + `configs/inbox_triage_scenarios.json`
- Multi-turn, adversarial, case-boundary, handoff-timing, broker-trial stress, client-aware tests (see `REGRESSION_BATTERIES_INDEX.md`).

**Move next**

- Index doc only (done in this sprint folder) + optional CI wiring (out of sprint scope).

**Do not move yet**

- Replacing Python runners with opaque external tools without local reproducibility.

---

## Tables (quick reference)

### What lives where (summary)

| Concern | Primary layer | Primary location |
|---------|----------------|------------------|
| Handoff when | Common Engine | `triage.py` |
| “What to ask next” for add-car | Industry + Engine | `add_car_rules.json` + `_get_next_ask_for_add_car` |
| Office wording at handoff | Client Pack | `handoff_phrases.json` |
| Reply draft templates | Industry + Client | `reply_templates.json` + `reply_overrides.json` |
| Quick-start / reroute lines | Common + Config | Route + `configs/common/soft_route_inbox.json` |
| Case JSON schema | Common Engine | `case_store.py` |

### Move now / later / keep in code

| Item | Disposition |
|------|-------------|
| Client-scoped `reply_overrides` path | **Move now** (done) |
| Soft-route reroute + starter copy | **Move now** (done) |
| `ask_driver_only` in loader/save | **Move now** (done) |
| More markers out of `triage.py` | **Later** (scenario-backed) |
| Split `triage.py` into packages | **Later** (high test cost) |
| Orchestration order & append boundary | **Keep in code** |

### Risks if over-refactored

| Risk | Symptom |
|------|---------|
| Big-bang file split | Guardrail red without commensurate test migration |
| Policy in JSON only | Silent behavior drift, harder code review |
| Removing fallbacks | Broken demo when config not mounted |
| Cross-client override merge | Wrong broker voice applied to another client |
