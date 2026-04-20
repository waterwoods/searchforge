# Unified Intake — DB-primary observability signals (Cloud Run / Neon)

**Purpose:** Grep-friendly log markers for the Postgres-primary live path without a metrics platform. All signals use the prefix **`UNIFIED_INTAKE_DB_OBS`** (or are tagged `signal=` inside that line).

## How to use (founder / operator)

- **Cloud Run logs:** filter by `UNIFIED_INTAKE_DB_OBS` or by `signal=` below.
- **Interpretation:** any **warning** with `JSON_READ_FALLBACK*` or `PG_LIST_*` / `PG_READ_EXCEPTION` means investigate DB connectivity, missing rows, or flag drift vs JSON.

## Signal reference

| Signal | Meaning |
|--------|---------|
| `JSON_READ_FALLBACK_MISSING_PG_ROW` | Get-by-id: no PG row; served from JSON (fallback allowed). |
| `JSON_READ_FALLBACK_AFTER_PG_ERROR` | Get-by-id: PG raised; then JSON fallback (check stack trace above). |
| `PG_READ_EXCEPTION` | Get-by-id: Postgres read raised (exception logged). |
| `PG_LIST_HYDRATION_GAP` | List path: `record_id` in PG list query but `load_full_case` returned None for some ids. |
| `PG_LIST_ALL_IDS_FAILED_HYDRATION` | List path: PG returned ids but none hydrated. |
| `PG_LIST_EXCEPTION` | List query or hydration raised (exception logged). |
| `JSON_READ_FALLBACK_LIST_AFTER_PG_ERROR` | List fell back to JSON after PG failure. |
| `JSON_READ_FALLBACK_LIST_STALE_JSON` | PG returned **zero** record ids but JSON still has cases — possible empty DB vs stale file. |
| `PG_MUTATION_LOAD_MISS` | Append/update path could not load case from PG (JSON writes off). |
| `PG_APPEND_NO_ROW` | Append `UPDATE` matched no row (case missing in `service_records`). |
| `PG_DUAL_WRITE_NEW_CASE_FAIL` / `PG_DUAL_WRITE_APPEND_FAIL` | Legacy dual-write path only (JSON authoritative). |
| `PG_FETCH_FOR_WORKBENCH_FAIL` | Workbench enrichment could not batch-fetch PG rows for mirror compare. |

## API / UI (no log noise)

Workbench list items may include **`pg_mirror_state`**: `mirrored` \| `mismatch` \| `pg_missing` \| `unknown` — use for per-row consistency at a glance.

## Related code

- Reads: `services/fiqa_api/inbox_triage/case_truth_repository.py`
- Mutation load: `services/fiqa_api/inbox_triage/case_store.py` (`_load_case_for_mutation`)
- Append write: `services/fiqa_api/db/service_record_repository.py` (`persist_case_append`)
- Workbench: `services/fiqa_api/inbox_triage/workbench_enrichment.py`
