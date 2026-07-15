# P20 Slice 1 Backend Step 1 Implementation Report

**Status:** backend foundation implemented behind Slice 1 flag/case capability  
**Date:** 2026-07-15  
**Scope:** Broker Request More -> Customer Continue backend command boundary and persistence only

## Implementation summary

Implemented the narrow Slice 1 backend command boundary for structured Broker Request More and Customer Continue. The workflow service owns legal transitions, one active request item, ordered queued items, command replay, expected-version conflict handling, canonical event construction, and customer/broker projections.

No Mini Program UI, Broker Workbench UI, deploy, commit, or unrelated refactor was included.

## Files changed

- `services/fiqa_api/db/schema/migrations/002_p20_slice1_request_more.sql`
- `services/fiqa_api/db/service_record_repository.py`
- `services/fiqa_api/inbox_triage/p20_slice1_command_service.py`
- `services/fiqa_api/inbox_triage/case_store.py`
- `services/fiqa_api/inbox_triage/h5_task_intake.py`
- `services/fiqa_api/inbox_triage/claim_workbench_display.py`
- `services/fiqa_api/routes/inbox_triage.py`
- `services/fiqa_api/routes/h5_task_intake.py`
- `tests/test_p20_slice1_command_service.py`
- `docs/product/p20_slice1_backend_step1_implementation_report.md`

## Schema / storage changes

Added reversible companion-table migration for:

- `claim_slice1_aggregates`
- `claim_request_groups`
- `claim_request_items`
- `claim_slice1_events`
- `claim_slice1_command_outcomes`

The Postgres adapter locks the `service_records` case row and applies aggregate, request, item, event, legacy projection, and command-outcome writes in one transaction. The legacy `claim_timeline` capped list remains display-only and is not used as Slice 1 source of truth.

## Commands implemented

- Broker create Request More:
  - `POST /api/inbox/cases/{case_id}/request-more`
  - Requires `command_id`, `idempotency_key`, `expected_case_version`, broker actor identity, and ordered structured items.

- Customer submit requested item:
  - `POST /api/h5/tasks/{task_token}/request-items/{item_id}/submit`
  - Requires token-bound customer identity, `command_id`, `idempotency_key`, `expected_case_version`, active item id, and exactly one fact or evidence reference.

- Authoritative fetch:
  - Existing `GET /api/h5/tasks/{token}/intake` now additively returns `slice1_projection` and `task_contract_v1` when enabled.

Amend and withdraw remain deferred.

## Events implemented

- `broker_request_more_created`
- `customer_continue_started`
- `field_saved`
- `evidence_received`
- `customer_request_item_satisfied`
- `supplement_submitted`

Accepted events include command/correlation identity, aggregate version, sequence number, expected version, actor, actor identity, before/after state, visibility, evidence payload, idempotency key, and server timestamp.

## Compatibility behavior

Slice 1 is gated by `P20_SLICE1_REQUEST_MORE` or `slice1_capability_version >= 1`. Non-enabled cases continue on the legacy H5/Workbench paths.

Accepted Slice 1 commands write a small compatibility projection onto the legacy case payload (`p20_slice1_projection`, request summary, `claim_phase`, guided state), but canonical Slice 1 truth remains in companion tables.

## Tests run

- `python3 -m pytest tests/test_p20_slice1_command_service.py` -> 12 passed
- `python3 -m pytest tests/test_h5_claim_intake_form.py` -> 20 passed

## Known limitations

- Postgres physical transaction safety requires `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL`; route usage returns 503 if no durable service-record DB is configured.
- Amend and withdraw endpoints are still deferred.
- Evidence bytes and content-hash canonical deduplication remain deferred; customer submission can bind an existing `attachment_id`.
- UI integration and client conflict/retry handling are not implemented in this step.
- Focused API route tests are not yet added; service/domain tests cover command behavior and the existing H5 suite covers v0 compatibility.

## Deferred Step 2 / 3 work

- Broker Workbench request editor and progress display.
- Mini Program request-item UI and retry/conflict handling.
- Request amend / withdraw commands.
- Broader API authorization/contract tests.
- Full generalized event/command spine for non-Slice-1 workflow transitions.

## Rollback notes

Disable `P20_SLICE1_REQUEST_MORE` and stop enabling `slice1_capability_version` for new cases to prevent new commands. Keep companion tables and compatibility projections for read-back; do not delete accepted command, event, request, item, or outcome rows. The migration file includes non-production teardown commands for rehearsal rollback only.
