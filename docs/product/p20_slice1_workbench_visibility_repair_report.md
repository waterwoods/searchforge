# P20 Slice 1 Workbench Visibility Repair Report

**Status:** implementation prepared, not deployed  
**Date:** 2026-07-15  
**Scope:** wire structured Broker Request More into the real `/workbench/document-intake` drawer without Slice 2, amend, withdraw, deploy, or commit.

## Root Cause

The confirmed defect was a Workbench surface mismatch. Slice 1 Request More existed inside `BrokerWorkbenchTab`, but `/workbench/document-intake` opens cases through `DocumentIntakeInboxPage` and renders the drawer body with `BrokerCaseDetail`. That production route had no Request More mount point, so eligible Claim cases could not expose the Step 2 capability there.

## Shared Component Approach

The Request More UI/state/controller was extracted into one shared component:

- `ui/src/features/intake/components/StructuredRequestMorePanel.tsx`

It owns the common eligibility helpers, projection normalization, ordered request display, command identity, one-submit-in-flight guard, timeout retry identity preservation, conflict merge/refresh behavior, and successful response projection merge. `BrokerWorkbenchTab` now mounts this component instead of carrying its own separate Request More implementation.

## BrokerCaseDetail Wiring

`BrokerCaseDetail` now mounts the shared panel in the broker action area directly below the top action banner and above the existing claim/evidence cards. The drawer passes:

- current `case_id` through `caseRecord`
- current projection/capability fields from the loaded case
- detail-loading and detail-load-error state
- `onCaseChange` to replace the drawer projection after command success
- `refreshCase` to reload authoritative case state after conflict or projection-load failure

Existing claim brief, accident basics, evidence checklist, attachments, broker-done, copy, and delete actions remain in place.

## Visibility Rules

The shared panel only renders when:

- `service_lane === "claim"`
- Slice 1 is enabled by `slice1_capability_version >= 1`, `p20_slice1_capability_version >= 1`, or an existing Slice 1 projection
- the case is not terminal/archived/broker-done
- the broker can load the office case projection or receives a recoverable projection-load error for an enabled case

Create is allowed only when the broker projection says `broker_next_action.action_type === "create_request"`, or when an enabled broker-review Claim has no projection/open request yet. Existing open requests show progress and block duplicate create. Unsupported lanes and non-enabled legacy cases preserve the existing drawer without showing the capability.

## QA Claim Enablement

Approved enablement remains either `P20_SLICE1_REQUEST_MORE=1` or case-level capability. For manual QA, prefer one reversible case-level enablement, not a global flag:

```sql
-- QA / non-production only. Replace the case id with the single test Claim.
BEGIN;
UPDATE service_records
SET extra = jsonb_set(COALESCE(extra, '{}'::jsonb), '{slice1_capability_version}', '1'::jsonb, true),
    updated_at = NOW()
WHERE record_id = 'QA_CLAIM_CASE_ID';
COMMIT;

-- Rollback for the same QA claim:
BEGIN;
UPDATE service_records
SET extra = COALESCE(extra, '{}'::jsonb) - 'slice1_capability_version',
    updated_at = NOW()
WHERE record_id = 'QA_CLAIM_CASE_ID';
COMMIT;
```

Before QA, confirm the claim is identifiable, non-production, `service_lane = claim`, and in broker review (`claim_phase = broker_review` or equivalent Workbench projection). Do not bulk-enable existing cases.

## Tests Run

- `cd ui && npx tsx src/api/inboxTriage.requestMore.test.ts` -> PASS
- `cd ui && npx tsx src/features/intake/components/StructuredRequestMorePanel.test.ts` -> PASS
- `cd ui && npm run typecheck -- --pretty false` -> scaffold no-op (`skip typecheck`)
- `cd ui && npx tsc --noEmit --pretty false` -> FAIL on pre-existing broad repository diagnostics; no new diagnostics were reported for `StructuredRequestMorePanel.tsx` or its test by IDE lints.

Backend Slice 1 API tests are unchanged by this repair and should be rerun before deployment if backend files are included in the deploy package.

## Remaining Deployment Steps

1. Apply the Slice 1 companion-table migration in QA/non-production.
2. Deploy backend command/projection code with durable DB env configured.
3. Enable exactly one QA Claim via case-level `slice1_capability_version: 1`.
4. Deploy the UI repair to QA.
5. Run manual QA Test A from `/workbench/document-intake` → Open case → Request More.

Mini Program Three Gates are **not applicable** for this repair because no Mini Program files were changed.

## Rollback Notes

Rollback is UI-safe: remove or revert the shared panel mount, or disable the single QA case capability. Do not delete accepted Slice 1 command/event/request data. Global rollback remains disabling `P20_SLICE1_REQUEST_MORE` and avoiding further case-level enablement.
