# Plug-in architecture map — Unified Intake

**Principle:** **Postgres vehicle entity payload** (when enabled) is the authority for mirrored API `vehicle_key` / `primary_vehicle_summary`. Plug-ins **read and write through facades**, not ad hoc imports from low-level stores in random routes.

---

## 1. Client Pack

| Topic | Detail |
|-------|--------|
| **Where config lives** | `services/fiqa_api/inbox_triage/config_loader.py`; JSON under `configs/clients/` (and related); UI: `ClientConfigContext`, `ui/src/api/clientConfig.ts`. |
| **What can change per broker** | `client_id`, UI copy (`ui_copy`), soft-route starters, handoff phrases, reply templates, add-car rules visibility, WeChat binding mode flags. |
| **Interface that should exist** | `ClientConfigProvider.resolve(client_id) -> ClientPack` (typed bundle: copy, templates, flags). |
| **Do not leak** | Raw file paths, internal template keys, or server-only secrets to the browser. |
| **Test before swapping** | Smoke: triage returns expected `issue_category` / soft-route copy; UI quick-start buttons match config snapshot test. |

---

## 2. Industry Pack

| Topic | Detail |
|-------|--------|
| **Insurance now** | `configs/industries/`, `configs/common/add_car_field_strategy.json`, intake lanes (`intake_service_lanes.py`), pilot contracts under `docs/PILOT_CONTRACT_ADD_CAR_V1.md`. |
| **Future verticals** | New industry id → separate field strategy JSON + lane map + optional OCR/routing pack; **do not** fork `triage.py` per vertical without extracting `TriagePolicy`. |
| **Interface** | `IndustryPack.field_strategy_id`, `service_lane_map`, `default_engine` hooks (conceptually `IndustryRegistry.get_pack(industry_id)`). |
| **Do not leak** | Hard-coded carrier logic inside entity repository or vehicle resolver — keep carrier-specific copy in templates/strategy. |
| **Test before swapping** | `tests/test_field_strategy*.py`, guardrail script, lane-specific chaos scenarios. |

---

## 3. LLM Provider

| Topic | Detail |
|-------|--------|
| **OpenAI now** | Model + client configured via env; calls embedded in triage flow and `assist_layer.py`. |
| **Future provider swap** | Introduce `LLMAdapter` with `complete_triage_json`, `complete_slot_fill`, `assist_completion` — single module boundary. |
| **Do not leak** | Provider-specific message shapes into `entity_repository` or case persistence; keep JSON schema validation at adapter boundary. |
| **Test before swapping** | Golden JSON fixtures for triage outputs; chaos runs with LLM on/off; contract tests for schema. |

---

## 4. Entity Store

| Topic | Detail |
|-------|--------|
| **Postgres now** | `entity_repository.py`: `get_active_vehicle`, `update_vehicle_entity`, `get_all_vehicles`, `active_vehicle_request_cache_scope`. Schema: `services/fiqa_api/db/schema/intake_entities.sql`. Contract: `docs/VEHICLE_ENTITY_MEMORY_MVP.md`. |
| **Possible future store** | Another SQL DB or document store — same **session-scoped active vehicle** semantics (one `is_active` winner per session for vehicle). |
| **Interface** | `EntityStore.get_active(session_id)`, `upsert_vehicle(session_id, payload, ...)`, `list_vehicles(session_id)`. |
| **Do not leak** | SQL or merge semantics into triage **beyond** a thin DTO; triage should call facade methods only. |
| **Test before swapping** | `tests/test_active_vehicle_resolver.py` + PG truth chaos (`pg_truth_match`); migration test for row shape. |

---

## 5. Case Store

| Topic | Detail |
|-------|--------|
| **Postgres / stub / full read** | `case_truth_repository.py`: `get_case_for_read` (full), `get_case_triage_stub_for_read` (hot path), `list_recent_cases_for_binding`. Flags: `db_primary_reads_enabled`, JSON fallback for dev. |
| **Writes** | `case_store.py` + dual-write / DB-primary settings (`service_record_settings.py`). |
| **Interface** | `CaseReadFacade` (stub + full + binding list) and `CaseWriteFacade` (persist, notes, attachments). |
| **Do not leak** | JSON file layout into triage; **always** use facade so cutover is flag-driven. |
| **Test before swapping** | Integration tests for stub vs full parity on fields triage needs; binding list shape for inbox route. |

---

## 6. Template Store

| Topic | Detail |
|-------|--------|
| **Current** | `get_reply_templates`, `get_handoff_phrases`, `get_soft_route_inbox_copy`, stitched blocks in composer (`triage_handoff_reply_composer.py`). |
| **Interface** | `TemplateStore.render(key, locale, context)` — keys versioned per client pack. |
| **Do not leak** | Template rendering into entity merge or `vehicle_key` computation. |
| **Test before swapping** | Snapshot tests for rendered handoff lines; missing-key fallback behavior. |

---

## 7. Knowledge / RAG

| Topic | Detail |
|-------|--------|
| **Role** | **Optional**, non-core for add-car pilot; future retrieval for generic Q&A lanes. |
| **Interface** | `KnowledgeRetriever.query(scope, text) -> chunks` behind feature flag; triage may **consult** but not **overwrite** entity truth. |
| **Do not leak** | Vector search results into `primary_vehicle_summary` or PG payload without explicit product rules. |
| **Test before swapping** | Offline eval harness; guardrail that RAG-off matches RAG-on for add-car vehicle fields. |

---

## VehicleResolver plug-in (cross-cutting)

| Topic | Detail |
|-------|--------|
| **Current** | `triage.py` heuristics + `routing_guard.py`; PG finalize on HTTP route. Parallel resolver module **deleted** 2026-05-28. |
| **Test** | Scenario pack + `pg_truth_match` chaos for multi-vehicle sessions. |
