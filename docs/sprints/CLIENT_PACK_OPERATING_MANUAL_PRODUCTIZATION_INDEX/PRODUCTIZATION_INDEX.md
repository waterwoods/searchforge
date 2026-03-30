# Productization Index — Unified Intake

**Product:** SearchForge **Unified Intake** (broker-facing inbox triage + customer entry / office workbench UI).

**Goal of this index:** Tell a founder **where things live**, **what to read first**, and **how to validate**.

---

## 1. Major architectural layers (today)

```
┌─────────────────────────────────────────────────────────────┐
│  UI (React) — UnifiedIntakePage, client config fetch        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP: /api/inbox/*
┌───────────────────────────▼─────────────────────────────────┐
│  API layer (FastAPI) — routes/inbox_triage.py               │
│  Session + case persistence — session_store, case_store     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Triage engine — inbox_triage/triage.py                     │
│  (rules + optional LLM; workflow state; append / handoff)    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Config loader — inbox_triage/config_loader.py              │
│  Load order: common → industry → client (client wins)       │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  configs/common/   configs/industries/   configs/clients/
                      insurance/            <client_id>/
```

| Layer | Location (concept) | Role |
|-------|-------------------|------|
| **Presentation** | `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/clientConfig.ts` | Customer + broker UX; fetches `ui_copy` per client |
| **API / orchestration** | `services/fiqa_api/routes/inbox_triage.py` | Validates requests, calls triage, persistence, client-config endpoint |
| **Engine** | `services/fiqa_api/inbox_triage/triage.py` | Classification, drafts, workflow keys, add-car flow, append semantics |
| **Config I/O** | `services/fiqa_api/inbox_triage/config_loader.py` | JSON loads, merge rules, `CLIENT_ID` |
| **Persistence** | `services/fiqa_api/inbox_triage/case_store.py`, `session_store.py` | Demo-safe JSON case history + sessions |
| **Industry pack** | `configs/industries/insurance/*.json` | Shared CA auto-insurance markers & templates |
| **Client pack** | `configs/clients/<client_id>/*` | Broker-specific copy & overrides |
| **Common copy** | `configs/common/*.json` | Cross-client defaults (soft-route text, workflow fallbacks) |
| **Regression batteries** | `configs/inbox_triage_scenarios.json` + `scripts/*.py` | Rule-based and A/B isolation checks |

---

## 2. Reading order (founder → engineer)

1. **This index** — orientation.
2. **`docs/STANDARD_SCENARIO_PACKAGE.md`** (repo root) — what “good” looks like in demos.
3. **`AGENTS.md`** — default commands (`guardrail_inbox_triage.sh`, demo scripts).
4. **`MODULE_ARCHITECTURE_GUIDE.md`** (this sprint) — module-by-module plain English.
5. **`FILE_FOLDER_RESPONSIBILITY_MAP.md`** — safe vs risky areas.
6. Industry README: `configs/industries/insurance/README.md`
7. Client README: `configs/clients/chen_kui/README.md` (and second pack e.g. `socal_precision/`)

---

## 3. File group table (high level)

| Group | Path pattern | For what |
|-------|--------------|----------|
| Triage engine | `services/fiqa_api/inbox_triage/triage.py` | Core behavior |
| Config loader | `services/fiqa_api/inbox_triage/config_loader.py` | All config merge rules |
| HTTP routes | `services/fiqa_api/routes/inbox_triage.py` | REST contract |
| Case store | `services/fiqa_api/inbox_triage/case_store.py` | Saved cases JSON |
| App wiring | `services/fiqa_api/app_main.py` | Router mount |
| Industry pack | `configs/industries/insurance/*.json` | Markers, templates, add-car prompts |
| Client pack | `configs/clients/<id>/*.json` | Handoff, stitched phrases, reply overrides, UI copy |
| Common | `configs/common/*.json` | Soft-route strings, workflow defaults |
| UI | `ui/src/pages/UnifiedIntakePage.tsx`, `ui/src/api/clientConfig.ts` | UX + types for `ui_copy` |
| Main scenario pack | `configs/inbox_triage_scenarios.json` | Rule-based regression inputs |
| Guardrail | `scripts/guardrail_inbox_triage.sh` | Umbrella validation |

---

## 4. Repo navigation (operator cheat sheet)

| I want to… | Go to… |
|------------|--------|
| Change broker branding / buttons | `configs/clients/<id>/ui_copy.json` + optional UI defaults in `clientConfig.ts` |
| Change handoff customer wording | `configs/clients/<id>/handoff_phrases.json` (`handoff`, `stitched`) |
| Change first-turn reply style | `configs/clients/<id>/reply_overrides.json` (over industry) |
| Tune intent keywords (industry-wide) | `configs/industries/insurance/markers.json` |
| Change add-car “ask next” prompts (industry) | `configs/industries/insurance/add_car_rules.json` |
| Change soft-route reroute lines | `configs/common/soft_route_inbox.json` |
| Run “did we break triage?” | `bash scripts/guardrail_inbox_triage.sh` |
| Prove client A ≠ client B copy | Scripts: `run_cross_client_ab_scenarios.py`, `run_append_boundary_ab_scenarios.py`, `run_residual_copy_ab_scenarios.py` (also inside guardrail) |

---

## 5. Validation pointers (canonical)

| Check | Command / artifact |
|-------|-------------------|
| **Primary umbrella** | `bash scripts/guardrail_inbox_triage.sh` |
| Core rule scenarios | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| API smoke (server up) | `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001` |
| Add-car focused batteries | `scripts/run_add_car_scenario_battery.py`, `run_add_car_driver_zip_materials_stress_battery.py`, etc. (see validation doc) |

---

## 6. Explicit answers (index-level)

| # | Question | Short answer |
|---|----------|--------------|
| 1 | Major layers? | UI → API → triage engine → config loader → JSON packs (common / industry / client) → regression batteries |
| 2 | What files matter most for migration? | New folder under `configs/clients/<new_id>/` + set `CLIENT_ID` + run guardrail + cross-client A/B scripts |
| 3 | What to read first? | This index → module guide → migration checklist → `guardrail_inbox_triage.sh` |

---

*See also: [GLOSSARY.md](./GLOSSARY.md), [CLIENT_PACK_OPERATING_MANUAL_BLUEPRINT.md](./CLIENT_PACK_OPERATING_MANUAL_BLUEPRINT.md).*
