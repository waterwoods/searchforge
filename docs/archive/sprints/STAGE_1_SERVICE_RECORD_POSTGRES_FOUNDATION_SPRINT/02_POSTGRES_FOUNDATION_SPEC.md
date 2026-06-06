# Stage 1 Postgres foundation — technical spec

## Chosen minimum schema direction

Relational core tables with **JSONB** for evolving structured extraction and per-message raw payloads:

| Table | Role |
|-------|------|
| `service_records` | Primary object: stable columns for state, ownership hints, contact (pilot parity), `extra` JSONB. |
| `record_messages` | Retained raw conversation lines + optional `raw_payload` JSONB; unique `(record_id, external_message_id)` for idempotent append. |
| `structured_record_data` | One row per record; `structured_payload` JSONB for triage/workflow fields. |
| `state_history` | Append-only transitions; initial row on create; append rows on follow-up. |
| `office_actions` | Empty in this sprint; reserved for broker notes / handoff actions (inserts can follow in a later sprint). |

**Deferred**

- `customers` as a separate entity (contact fields live on `service_records` for now; avoids duplicate identity writes during pilot).
- Dual-write for status updates, notes, attachments, follow-up fields-only API paths.
- Automated migration framework (Alembic, etc.); single SQL file + `IF NOT EXISTS` for Stage 1 bootstrap.

## Persistence / dual-write strategy

1. **Source of truth (pilot):** JSON `case_store` unchanged; all existing API behavior preserved.
2. **Postgres:** Populated only when:
   - `SERVICE_RECORD_DATABASE_URL` or `DATABASE_URL` is set, and
   - `UNIFIED_INTAKE_PG_DUAL_WRITE` is truthy (`1`, `true`, `yes`, `on`).
3. **Hooks:** After successful JSON write in `save_case` and `append_follow_up_message`, call `maybe_dual_write_*` (errors logged; never raised to the client).
4. **Schema apply:** Manual (or CI): `bash scripts/apply_stage1_service_record_schema.sh` with URL in env.

## Dependencies

- `psycopg` (binary extra) declared in `pyproject.toml` for Poetry installs; pip: `pip install 'psycopg[binary]>=3.2,<4'`.

## Acceptance criteria

- [ ] SQL file creates all five tables and key indexes on a fresh Postgres 13+ database.
- [ ] With dual-write **disabled**, demo and guardrails behave exactly as before (no URL / flag).
- [ ] With dual-write **enabled** and schema applied, a new persisted case produces rows in `service_records`, `record_messages`, `structured_record_data`, and `state_history`.
- [ ] Append with dual-write updates the record, upserts structured data, inserts only new messages, and appends a `state_history` row.
- [ ] No new CRM tables or broad normalized insurance domain model.
