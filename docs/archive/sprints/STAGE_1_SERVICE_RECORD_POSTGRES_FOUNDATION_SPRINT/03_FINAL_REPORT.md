# STAGE 1 SERVICE RECORD POSTGRES FOUNDATION — Final report

## What was created

- `services/fiqa_api/db/schema/stage1_service_record.sql` — Stage 1 DDL.
- `services/fiqa_api/db/service_record_settings.py` — URL + dual-write flag.
- `services/fiqa_api/db/service_record_repository.py` — `persist_new_case`, `persist_case_append`.
- `services/fiqa_api/db/dual_write.py` — opt-in hooks.
- `scripts/apply_stage1_service_record_schema.sh` — `psql` apply helper.
- `services/fiqa_api/inbox_triage/case_store.py` — calls dual-write after JSON success (create + append).
- `pyproject.toml` — `psycopg[binary]` dependency.
- `docs/PROJECT_TRUTH_SWITCH.md` — persistence truth updated.

## What was not created

- Read path from Postgres; workbench/API still JSON-only.
- Dual-write for `update_case_status`, notes, attachments, customer patch, follow-up-only routes.
- `customers` table; Alembic migration chain; Docker Compose Postgres service for demo (optional future).
- Backfill job from existing JSON file.

## What remains for the next sprint

- Extend dual-write to status / office-relevant mutations and map `case_activity` into `office_actions` where appropriate.
- Add integration test against a disposable Postgres (or document manual verification checklist).
- Consider `INSERT ... ON CONFLICT` upsert for `persist_new_case` if idempotent retries matter.
- Decide when to promote `lifecycle_status` vs `case_status` in `state_history` for clearer audits.

## Migration guidance

1. Provision Postgres (managed recommended for production).
2. Run `bash scripts/apply_stage1_service_record_schema.sh` with `SERVICE_RECORD_DATABASE_URL` set.
3. Deploy app with `psycopg` available; set `UNIFIED_INTAKE_PG_DUAL_WRITE=1` in a canary environment.
4. Validate row counts and sample queries; keep JSON as authority until read cutover is explicitly planned.
5. Later: backfill historical JSON cases if needed (one-off script, not in this sprint).
