# P20 Slice 1 Workbench Step 2 Implementation Report

**Status:** conditional implementation complete for Broker Workbench structured Request More  
**Date:** 2026-07-15  
**Scope:** Broker Workbench API client, structured Request More panel, route tests, and focused API client test. Mini Program UI, deploy, commit, amend/withdraw, and evidence content-hash deduplication remain out of scope.

## Workbench flow implemented

Broker Workbench claim case detail now shows a compact Structured Request More panel for Slice 1 enabled claim cases. Eligible broker-review cases can open a modal, create one ordered request group, add one or more requested items, provide customer-facing group/item instructions, and submit through the Slice 1 command route.

Accepted or replayed server responses are merged into the open Workbench case as the authoritative Slice 1 projection. The panel displays request status, progress count, active item, queued items, satisfied items, last server update, customer next action, and broker next action. Completed requests show the broker review action.

## Exact files changed in Step 2

- `ui/src/api/config.ts`
- `ui/src/api/inboxTriage.ts`
- `ui/src/api/inboxTriage.requestMore.test.ts`
- `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`
- `tests/test_p20_slice1_api.py`
- `docs/product/p20_slice1_workbench_step2_implementation_report.md`

The worktree also contains pre-existing Step 1 backend files and P20 documents from the backend foundation work; those were not reverted or redesigned in this step.

## API contracts used

- `POST /api/inbox/cases/{case_id}/request-more`
- Request body: `command_id`, `idempotency_key`, `expected_case_version`, `requested_items[]`, `reason`, optional `request_id`, optional `correlation_id`.
- Request item body: `item_type`, `label`, `instructions`, `required`, `position`, optional `request_item_id`.
- Success: `201 accepted` or `200 replayed`, returning `outcome`, command identity, `aggregate_version`, `customer_projection`, `broker_projection`, `request_summary`, `server_timestamp`, and event IDs.
- Conflict: `409` with full command result in `detail`.
- Rejected/validation/feature-disabled: `422` with command result or validation detail.
- Authorization failure: `403`.
- Server/storage failure: `503`.

## Route tests added

Added `tests/test_p20_slice1_api.py` covering:

- successful create Request More
- multiple ordered items
- duplicate command replay
- stale `expected_case_version`
- feature-disabled case
- unauthorized office access
- missing broker actor identity
- authoritative projection shape returned by the route

## UI states

- Not enabled: legacy Workbench behavior remains, with a compatibility note only.
- Enabled/no open request: shows Slice 1 enabled and Request More entry when broker action is create request.
- Open request: shows request status, active customer item, queued items, satisfied items, progress count, customer next action, broker next action, and server update time.
- Completed request: shows broker review-ready action instead of leaving Request More as the active status.
- Modal draft: complete initial state, deterministic positions, preset and blank rows, duplicate row validation, required labels/instructions, and one submit in flight.

## Conflict and retry behavior

Duplicate clicks are blocked while submitting. Timeout/uncertain network failure preserves the same `command_id`, `idempotency_key`, `request_id`, and original expected version for safe retry. Accepted idempotent replay is treated as success.

Version conflicts show: “The case changed while you were editing. We refreshed the latest status. Review and submit again.” The Workbench merges the conflict projection, refreshes the full case when possible, preserves the draft, clears the old command identity, and requires explicit resubmission.

## Compatibility behavior

Non-Slice-1 cases keep existing Workbench notes, attachments, follow-up, status, and claim brief behavior. Legacy timeline/notes are displayed separately and are not converted into structured request items. Slice 1 request state is additive.

## Tests run

- `python3 -m pytest tests/test_p20_slice1_api.py tests/test_p20_slice1_command_service.py` -> 19 passed
- `npx tsx src/api/inboxTriage.requestMore.test.ts` -> passed

## Known limitations

- Mini Program customer UI is deferred.
- Amend/withdraw remain deferred because they were not required for the minimum safe create flow.
- Focused React component DOM tests were not added; the repo currently has Node utility tests but no Workbench component test harness.
- Full repo typecheck was not run; `BrokerWorkbenchTab.tsx` still has pre-existing broad TypeScript diagnostics unrelated to the Slice 1 panel.
- Workbench authoritative fetch uses the existing case refresh plus command response projection; no separate broker projection GET endpoint was added.

## Rollback notes

Disable case-level Slice 1 enablement or `P20_SLICE1_REQUEST_MORE` to stop new structured Request More commands. Keep accepted Slice 1 projections/events readable. Reverting the Workbench panel/client removes the broker entry point without deleting Slice 1 backend data.
