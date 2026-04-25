# Vehicle Entity Memory MVP — Sprint Report

## 1. Time spent

Approximately **45 minutes** (implementation, schema, repository, optional triage hook, validation loop, test alignment with current branch behavior).

## 2. What was built

### Schema

- `services/fiqa_api/db/schema/intake_entities.sql` — `intake_entities` table with `payload JSONB`, `is_active`, `updated_at`, indexed for `(session_id, entity_type)` filtered by `is_active`.
- Apply with: `psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f services/fiqa_api/db/schema/intake_entities.sql` (or `DATABASE_URL`).

### Repository

- `services/fiqa_api/inbox_triage/entity_repository.py`
  - `save_vehicle_entity(session_id, payload, case_id=None)`
  - `get_active_vehicle(session_id)`
  - `update_vehicle_entity(session_id, payload, case_id=None)` — JSONB merge (shallow merge; nested `confidence` dict merged).

### Hooks (optional / best-effort)

- `triage.py`: `_try_persist_vehicle_entity_mvp` runs after add-car augmented truth fields are computed; calls `update_vehicle_entity` only when `reply_truth_context` includes `session_id` (from API). Exceptions are swallowed; **no change to response JSON or handoff logic**.
- `routes/inbox_triage.py`: `_reply_truth_context_for_triage` now accepts optional `session_id` and `case_id` and passes them through for that hook (additive; does not alter triage routing).

### Documentation

- `docs/VEHICLE_ENTITY_MEMORY_MVP.md` — purpose, scope, entity shape, invariants.

### Tests / scripts

- `scripts/test_vehicle_entity_repo.py` — create → update year → update VIN → read back (skips cleanly if no DB URL).
- Test suite updates: `test_append_truth_alignment` import/signature fix for `resolve_add_car_handoff_phrase_key`; `test_conversion_layer`, `test_materials_ack_vin_correction_stability`, `test_vehicle_key_normalization`, `test_vehicle_layer_markers` aligned with current copy and vehicle-key behavior on this branch.

## 3. What was NOT done

- Multi-vehicle entity resolution and multiple actives.
- Person entity or contact graph.
- Using entity state in client replies or still-needed field lists.
- Removal / deactivation APIs for rows.

## 4. Stability

| Check | Result |
|--------|--------|
| `pytest -q` (LLM off) | **PASS** |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |

## 5. Next step recommendation

1. Apply `intake_entities.sql` in pilot/staging Postgres and re-run `scripts/test_vehicle_entity_repo.py` with a real URL.
2. Backfill `case_id` on entity rows when sessions bind to cases (already passed when present in `reply_truth_context`).
3. When product is ready, replace ad-hoc vehicle heuristics with explicit reads from `get_active_vehicle(session_id)` in a single orchestration layer (still keep triage output contract stable behind a feature flag).

## 6. Manual mini-scenario (operator)

With DB applied and API session id `sid`:

1. Send add-car thread: Camry 2020 → confirm entity payload shows year/model.
2. Correction to 2021 → merge should show `year=2021`.
3. Add VIN → `vin` populated; other fields preserved.

Verify triage JSON unchanged vs pre-entity runs (hook is no-op without `session_id` in context; with `session_id`, DB side effects only).
