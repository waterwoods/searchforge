# Entity ↔ Triage Integration Plan (Phase 4)

## Product contract

- **Source of truth:** When a vehicle entity row exists for the intake `session_id` and the payload carries a usable vehicle identity, that payload is the broker-facing truth for **primary vehicle line** and **vehicle_key**.
- **Triage extraction** (regex / add-car heuristics / slot augmentation) remains the **candidate** signal each turn; it is merged into the entity store, then the store is read back for decisions.
- **Merged truth:** `existing_entity_payload + candidate_extraction → merged_payload` (persisted), then **read** merged payload for outputs. If no row or no usable identity in payload, **fallback** to current heuristics unchanged.

See also: `docs/VEHICLE_ENTITY_MEMORY_MVP.md`.

## 1. When to WRITE entity

- **After** add-car lane extraction for this turn is available: truth fields and merged text used for `_extract_vehicle_identity_for_key` / primary vehicle concrete.
- **Only** when `is_add_car` is true (add-car lane).
- **Non-blocking:** DB errors or missing `SERVICE_RECORD_DATABASE_URL` are ignored; triage JSON is unchanged on failure.

## 2. When to READ entity

Immediately **after** the write attempt for that turn (so the same request sees merged DB state when DB is available):

Before building or consuming:

- `primary_vehicle_summary` (office-facing line and bundle inputs that use it)
- `vehicle_key` (persistence / boundary signals)
- Downstream artifacts that already depend on those fields indirectly (e.g. early `build_v4_case_draft_bundle` `primary_vehicle_summary` argument, `client_reply_draft` paths driven by the same bundle)

**Scope of this phase:** Override **primary_vehicle_summary** and **vehicle_key** when entity identity is usable. Other fields (`client_reply_draft` composition from free text, still_needed lists) remain heuristic-driven unless they already consume `primary_vehicle_summary`.

## 3. Merge logic (candidate + existing → merged_entity)

Implemented at persistence boundary (`entity_repository` + triage candidate construction):

| Rule | Behavior |
|------|----------|
| Last correction wins | Candidate fields come from full merged conversation + last-bubble-scoped identity extraction (existing triage behavior); each turn’s candidate is merged on top of stored payload. |
| Non-empty overwrites empty | Incoming **non-empty** scalars replace empty or missing stored values. |
| Empty does not clobber | Incoming empty string **does not** erase a non-empty stored scalar (`year`, `make`, `model`, `vin`, `zip`, `driver`). |
| VIN strongest | Non-empty incoming `vin` always sets `vin` (normalized upper). |
| Nested | `confidence` dict shallow-merged; `source_turns` unchanged in MVP candidate (still list default). |

**Explicit correction** is already reflected in extraction (scoped last bubble); no separate flag in MVP schema.

## 4. Usable identity (READ gate)

Entity drives `primary_vehicle_summary` / `vehicle_key` only if payload has at least one of:

- VIN (length ≥ 11 after strip), or  
- `year` + `model` (non-empty strings)

Otherwise triage keeps heuristic `primary_vehicle_summary` / `vehicle_key`.

## 5. Scenario / runner requirement

Multi-turn library runs must pass a **stable `session_id`** in `reply_truth_context` per scenario so Postgres (when configured) accumulates entity state across turns. Deterministic runs without DB continue to pass via heuristic fallback.

## 6. Non-goals (this sprint)

- Rewriting triage architecture or handoff policy.
- Multi-vehicle ranking / disambiguation.
- Removing or weakening existing heuristics when entity is absent.
