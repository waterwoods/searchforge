# Unified Intake — Master Blueprint

**Purpose:** One place to understand what Unified Intake is, how data flows, and which modules own which truths.  
**Audience:** Engineers onboarding in ~30 minutes; founders scanning in ~5 minutes (see also `docs/SYSTEM_ONE_PAGE_MAP.md`).  
**Last aligned:** 2026-04-28 (architecture audit sprint; docs only).

---

## 1. What this product is

Unified Intake is a **broker-channel intake layer for California auto insurance** that turns minimal customer text (and optional images) into a **structured, broker-usable case draft** with a **single confirmation-style turn** where possible, then **hands off to the office** for completion, binding, and compliance. The system optimizes for **low customer effort** and **traceable machine decisions** (field strategy, defaults, tier gating), not for replacing the broker or the carrier.

---

## 2. What this product is NOT

| Not this | Why it matters |
|----------|----------------|
| **Full CRM** | No long-lived customer 360°, sales pipeline, or marketing automation as core scope. |
| **Autonomous insurance carrier** | No rating, binding, or policy issuance; office completes precision work. |
| **Broad general chatbot** | Lanes (add-car pilot, soft routes) and **truth contracts** bound behavior; LLM is assist/suggest, not authority. |
| **Fleet / policy admin system of record** | Case + session stores support intake; Postgres entities hold **intake vehicle truth** for the thread, not the full policy platform. |

---

## 3. Core user flow

```
Customer input (text / image hints)
    → POST /api/inbox/triage (API route)
    → Session load / case bind (SessionStore + CaseStore facade)
    → triage_conversation (Triage engine)
    → Add-car path: vehicle decision + slot merge → EntityStore (PG vehicle row) when applicable
    → Draft / handoff / funnel signals
    → Route post-steps: `_finalize_response_with_pg_truth` (PG identity mirror + reply finalize), lifecycle, optional assist (background)
    → JSON response (TriageResult-shaped)
    → Broker handoff / workbench (office completes deferred fields)
```

**Broker-facing mirror:** When Postgres is configured and `session_id` is present, API `primary_vehicle_summary` and `vehicle_key` must match the active vehicle entity row after the turn (see `docs/PG_TRUTH_PIPELINE_CONTRACT.md`).

---

## 4. Core backend modules

| Module | Responsibility | Source of truth? | Hot-swappable? |
|--------|----------------|------------------|----------------|
| **API Route** (`services/fiqa_api/routes/inbox_triage.py`) | HTTP orchestration: session/case resolution, `triage_conversation`, perf metrics, analytics scheduling, **`_finalize_response_with_pg_truth`** (PG mirror + customer reply finalize), optional assist thread. | **No** (orchestration) | Replace transport (e.g. worker) behind same facade — today this file *is* the service boundary. |
| **Triage Engine** (`inbox_triage/triage.py` + policies) | Intent, add-car structure, field strategy alignment, handoff gating, entity writes, LLM calls for triage JSON / slots. | **No** (derives + writes) | Policy modules (`triage_add_car_policy.py`, etc.) are partial plug points; core file is large. |
| **VehicleResolver** (`inbox_triage/active_vehicle_resolver.py`) | Deterministic add-car **segment + message →** explicit vehicle choice / `AMBIGUOUS` (clarify, no guess). | **No** (decision logic) | **Yes** — swap implementation if contract preserved; **today:** unit-tested; **call site:** must stay **single** (see deprecated doc). |
| **EntityStore** (`inbox_triage/entity_repository.py`) | Postgres `intake_entities` active vehicle row, merge semantics, per-request read cache. | **Yes** for **API vehicle identity** when PG + session (contract). | **Yes** — formalize as protocol; today PG-backed. |
| **CaseStore (read facade)** (`inbox_triage/case_truth_repository.py`) | `get_case_for_read`, `get_case_triage_stub_for_read`, binding lists; JSON vs PG behind flags. | **Case payload** per env (PG-primary vs JSON legacy). | **Yes** — adapter per deployment. |
| **CaseStore (writes)** (`inbox_triage/case_store.py` + DB repository) | Persist service records, attachments, notes. | **Authoritative case** per deployment mode. | **Yes** with migration. |
| **SessionStore** (`inbox_triage/session_store.py` + repository) | In-progress turns + workflow state; binding patches. | **Session continuity** when DB enabled. | **Yes** — storage backend. |
| **LLM Adapter** (OpenAI client usage inside triage + `assist_layer.py`) | Triage JSON, bounded slot fill, optional post-truth assist copy. | **Never** for vehicle identity or PG writes; **suggestion-only** per contracts. | **Yes** — isolate vendor/model env. |
| **Template / Copy Store** (`config_loader.py`, `configs/**`, handoff phrases) | Reply templates, soft-route copy, stitched blocks. | **No** (presentation) | **Yes** per `client_id` / locale. |
| **Client Config** (`config_loader`, UI `ClientConfigContext`) | Active client, UI copy, feature flags surfaced to UI. | **No** | **Yes** — primary broker differentiation lever. |
| **Industry Pack** (`configs/industries/**`, `add_car_field_strategy.json`) | Insurance markers, field strategy, lane defaults; future verticals = new pack + strategy. | **Behavior** when wired to `field_strategy.py` | **Yes** — new industry = pack + tests. |

---

## 5. Core frontend modules

### Production flow

- **`ui/src/pages/UnifiedIntakePage.tsx`** — Tabs A–C: Customer Entry, My requests, Broker Workbench; production-shaped demo/pilot shell.
- **`ui/src/api/inboxTriage.ts`** — Client contract (`TriageResult`) and HTTP helpers for triage, cases, session, attachments.
- **`ui/src/components/intake/**`** — Customer progress, add-car rail, lifecycle display (shared patterns).
- **`ui/src/components/workbench/**`** — Office boundary copy and workbench behaviors.

### Broker workbench

- Same page **Tab C** + case list APIs; office completion and flags.

### Simulation / QA

- **`ui/src/components/simulation/**`** — `ScenarioReplayTab` and replay helpers (Tab D on Unified Intake page).
- **Rule:** Do not treat simulation tabs as production SLO or funnel without labeling (see `docs/DEPRECATED_PATHS.md`).

---

## 6. Production invariants

1. **Vehicle *lines* in triage:** `triage.py` builds `primary_vehicle_summary` / `vehicle_key` via heuristics (`_derive_vehicle_key_from_add_car_text`), entity payload, and append **`routing_guard`** signals. **`active_vehicle_resolver.resolve_add_car_active_vehicle`** is **unit-tested** but **not imported** by `triage.py` on current mainline — converge by wiring it or retiring the unused surface (see `docs/DEPRECATED_PATHS.md`). **No** legacy full-thread primary extract named `_extract_primary_add_car_vehicle_concrete`.
2. **PG entity is API vehicle truth (when PG + session):** `primary_vehicle_summary` / `vehicle_key` on the HTTP response match the active Postgres row’s payload after `_finalize_response_with_pg_truth` (see `docs/PG_TRUTH_PIPELINE_CONTRACT.md`). **Truth chain for the API:** **Postgres active vehicle entity → route mirror** (triage may write/update that row earlier in the turn when configured).
3. **LLM is suggestion-only:** Does not write entities; ambiguity **clarifies** per `docs/AMBIGUITY_CLARIFY_CONTRACT.md`.
4. **Ambiguity clarifies, not guesses:** No switch/create on forced-clarify patterns without explicit resolution.
5. **API vehicle fields mirror active PG row** after processing when mirroring applies (same formatters as entity payload).
6. **p95 target &lt; 5s** for HTTP triage (product bar); lock-in reports show runs slightly over or under — monitor `route_perf` / `triage_turn_metrics` (session + case + postprocess often dominate).

---

## 7. Current readiness

| Dimension | Assessment (concise) |
|-----------|---------------------|
| **Correctness** | Strong on add-car chaos packs + PG truth checks when run with LLM on; scenario breadth remains the confidence limiter. |
| **Latency** | Often near **~5s HTTP p95**; tail can exceed; triage core is only part of wall time. |
| **Architecture cleanliness** | Clear **repository seams** (entity, case truth, session); route **single** `_finalize_response_with_pg_truth` for API vehicle + reply cleanup; **debt:** large `triage.py`, monolithic UI page. |
| **Pilot readiness** | **Credible with monitoring** per evaluation reports; binding/facade symbols must stay on mainline (CI import checks). |
| **Risks** | Misleading analytics (`early_dropoff`); branch/stash drift on case binding stubs; display-only summary edge cases under adversarial negation. |

---

## Related documents

- `docs/PRODUCT_TRUTH_DOCUMENT.md` — product principles, field strategy, broker completion.
- `docs/PG_TRUTH_PIPELINE_CONTRACT.md` — PG ↔ API vehicle identity contract.
- `docs/AMBIGUITY_CLARIFY_CONTRACT.md` — clarify vs guess rules.
- `docs/DEPRECATED_PATHS.md` — legacy paths and removal guidance.
- `docs/PLUGIN_ARCHITECTURE_MAP.md` — swap boundaries and tests.
- `docs/SYSTEM_ONE_PAGE_MAP.md` — 3-minute map for humans.
