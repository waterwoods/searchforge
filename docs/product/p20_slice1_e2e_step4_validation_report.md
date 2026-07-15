# P20 Slice 1 E2E Step 4 Validation Report

**Status:** CONDITIONAL — automated vertical integration PASS; live Postgres + iPhone Preview remain manual  
**Date:** 2026-07-15  
**Scope:** End-to-end Slice 1 capability validation across Workbench, backend, projections/timeline, Mini Program, preflight. No Slice 2, amend/withdraw, content-hash dedup, production deploy, or commit.

## Release recommendation

**CONDITIONAL ready for non-production iPhone Preview / manual QA.**  
Do not treat as production release until the manual script is executed against QA with a Slice 1–enabled claim and DevTools Gate 3 compile is recorded.

## E2E contract trace

```text
BrokerWorkbenchTab (createCaseRequestMore)
  → POST /api/inbox/cases/{case_id}/request-more
      body: command_id, idempotency_key, expected_case_version,
            requested_items[], reason, request_id?, correlation_id?
      actor: office:{office_id}
  → P20Slice1CommandService.accept_request_more
  → companion tables + command outcome (atomic in PG adapter / in-memory store)
  → events: broker_request_more_created
  → customer_projection + broker_projection (same aggregate version)
  → Workbench merges projection into currentCase

Customer GET /api/h5/tasks/{token}/intake
  → additive slice1_projection / task_contract_v1
  → Mini Program Task Home → one Primary Next Action
  → pages/request-item/request-item

Customer POST /api/h5/tasks/{token}/request-items/{item_id}/submit
      body: command_id, idempotency_key, expected_case_version,
            client_draft_id?, fact? | evidence?
      actor: h5:{user_ref|nonce}
  → submit_request_item
  → events: customer_continue_started? + field_saved|evidence_received
           + customer_request_item_satisfied [+ supplement_submitted]
  → next active item OR wait_for_broker_review / review_customer_response
```

Verified field alignment (Workbench client ↔ routes ↔ service ↔ Mini Program):

| Hop | Identifiers / version / actions |
|---|---|
| Create | `command_id`, `idempotency_key`, `expected_case_version`, ordered `item_type` |
| Create success | `outcome` accepted/replayed, `aggregate_version`, dual projections, `request_summary` |
| Conflict | HTTP 409 + full command result `detail` |
| Customer fetch | `customer_next_action.action_type`, `required_input`, queued `actionable:false` |
| Customer submit | fact XOR evidence; replay 200; conflict 409 |
| Insurance card | `provide_evidence` + `policy_or_insurance_card` (Step 3 fix confirmed in E2E) |

**Contract mismatches found in Step 4:** none new.  
**Prior mismatch confirmed fixed:** `policy_or_insurance_card` → `provide_evidence`.

## Database / migration validation

File: `services/fiqa_api/db/schema/migrations/002_p20_slice1_request_more.sql`

| Check | Result |
|---|---|
| Documented non-prod DROP rollback | PASS (header comments) |
| One-open-request partial unique | PASS (`uq_claim_request_groups_one_open`) |
| Deterministic item order unique | PASS (`uq_claim_request_items_position`) |
| Event sequence unique | PASS (`uq_claim_slice1_events_sequence`) |
| Idempotency + command unique outcomes | PASS |
| Partial failure rollback (in-memory) | PASS (`test_failure_during_acceptance_rolls_back_business_effects`) |
| Live Postgres apply | **UNVERIFIED** — `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL` unset in this environment |

Static SQL + repository/unit/E2E in-memory coverage used as substitute.

## Scenarios run (automated)

| # | Scenario | Result |
|---|---|---|
| 1 | Single VIN → broker review | PASS |
| 2 | VIN → insurance → photos ordered activation | PASS |
| 3 | Duplicate broker create replay | PASS |
| 4 | Duplicate customer submit; queue not skipped | PASS |
| 5 | Stale version conflict; no mutation | PASS |
| 6 | Next-day resume via authoritative fetch | PASS |
| 7 | Lost response → same identity replay | PASS |
| 8 | Legacy case unaffected | PASS |

Additional: VIN expected event sequence + field completeness; migration SQL static asserts; H5 submit route accept/replay/conflict.

## Event sequence (VIN-only)

```text
1 broker_request_more_created     broker   → broker_more_requested
2 customer_continue_started       customer → customer_continuing
3 field_saved                     customer → customer_continuing
4 customer_request_item_satisfied system   → broker_review_ready
5 supplement_submitted            customer → broker_review_ready
```

Append-only, monotonic `sequence_number` / `aggregate_version`, stable `command_id` / `correlation_id` / `idempotency_key`, request/item evidence IDs present. Replay does not append duplicates.

## Customer / Broker projection parity

Invariant enforced in E2E helpers: same `case_id`, `workflow_state`, `aggregate_version`, `request_progress`, open `request_id`, and compatible next actions from one projection object returned as both `customer_projection` and `broker_projection`.

| State | Customer Primary | Broker Primary |
|---|---|---|
| Open request / continuing | provide_fact / provide_evidence (one item) | wait_for_customer_item |
| All satisfied | wait_for_broker_review | review_customer_response |

## Idempotency / retry / version conflict

| Behavior | Evidence |
|---|---|
| Broker duplicate → replayed, one group/event | scenario 3 + API route test |
| Customer duplicate → replayed, no skip | scenario 4 |
| Lost response same identity | scenario 7 |
| Stale version → conflict, no events | scenario 5 + H5/API route tests |
| Mini Program uncertain retry keeps identity | Step 3 code + lifecycle unit tests |

## Legacy compatibility

Non-enabled case: `fetch_projection` None; create rejected `slice1_not_enabled`; no tables populated. Mini Program falls back to legacy Task Home when projection absent.

## Reliability gates

### Mini Program

| Rule | Result | Evidence |
|---|---|---|
| First-render defaults | PASS | `slice1RequestItem.test.ts` |
| Single-flight init | PASS | `slice1Lifecycle` + `taskPage` |
| onLoad/onShow race | PASS | lifecycle helpers + task-home wiring |
| Stale response protection | PASS | `taskPage` stale test |
| Loading termination | PASS | timeout + success/fail paths |
| Page/upload loading separation | PASS | request-item upload vs busy.loading |
| Duplicate tap protection | PASS | submit gate tests |
| Retry identity preservation | PASS | request-item + lifecycle |
| Background/resume | CONDITIONAL | page onShow rehydrate; no separate App.onShow proof on device |
| Session-expiry path | CONDITIONAL | code redirects on 403; not live-token tested |
| Destroyed-page safety | PASS | pageAlive / isDestroyed guards |
| JSON-serializable data | PASS | defaults + draft policy |
| No white screen | PASS | error/loading branches |

### Workbench

| Rule | Result | Evidence |
|---|---|---|
| One submit in flight | PASS | Step 2 panel (prior) + client |
| Safe retry identity | PASS | Step 2 report + client |
| Version conflict refresh | PASS | API 409 + Workbench handler |
| Draft preservation | PASS | Step 2 |
| Unmount safety | CONDITIONAL | no new DOM harness in Step 4 |
| Recoverable errors | PASS | typed `Slice1RequestMoreError` |

## Three Gates

| Gate | Result | Notes |
|---|---|---|
| 1 Completeness | PASS | `request-item.ts/json/wxml/wxss` present; shared components complete |
| 2 usingComponents paths | PASS | `validate_miniapp_component_gates.mjs` passed |
| 3 DevTools clear-cache full compile | CONDITIONAL | Must be performed by operator before Preview claim; not executable in this agent environment |

## Preview preflight

`npm run preview:preflight` → **PASSED**  
qa profile, non-loopback API, empty `devTaskToken`, AppID present, Slice 1 pages registered, route expectations listed.

Does **not** create Slice 1 test cases automatically; enabling a QA claim remains an operator step.

## Observability added

Non-sensitive logs:

- Backend: `p20_slice1_command_outcome` (outcome, versions, action type, progress counts; no tokens/facts/bytes)
- Backend: `p20_slice1_projection_fetch_failed` on H5 projection fetch exception
- Mini Program: `[slice1_submit]` / `[slice1_submit_retry]` redacted console info

## Integration defects fixed in Step 4

None required beyond validation coverage and observability. Step 3 insurance-card action_type fix re-confirmed by scenario 2.

## Tests run

```text
python3 -m pytest tests/test_p20_slice1_e2e.py \
  tests/test_p20_slice1_command_service.py \
  tests/test_p20_slice1_api.py
→ 31 passed

miniapp: slice1* + taskPage → 30 passed
node scripts/validate_miniapp_component_gates.mjs → passed
npm run preview:preflight → passed
```

## Remaining manual verification

1. Apply migration on QA/non-prod Postgres if not already applied  
2. Enable Slice 1 on a test claim  
3. WeChat DevTools Gate 3 compile  
4. Execute `docs/product/p20_slice1_manual_qa_script.md` (A–G)  
5. Optional iPhone experience build (publish only with explicit approval)

## Known limitations

- Live DB transaction path not exercised in this environment  
- No automated WeChat DevTools / iPhone runner  
- Amend/withdraw and content-hash evidence dedup deferred  
- Workbench component DOM tests still absent  
- App-level foreground hook beyond page `onShow` not added  

## Rollback notes

Disable `P20_SLICE1_REQUEST_MORE` / stop setting `slice1_capability_version` on new cases. Keep companion tables and accepted outcomes. Mini Program without projection continues legacy Task Home. Non-prod rehearsal may DROP companion tables per migration header.

## Files changed

- `tests/test_p20_slice1_e2e.py` (new)
- `tests/test_p20_slice1_api.py` (H5 submit route coverage)
- `services/fiqa_api/inbox_triage/p20_slice1_command_service.py` (observability)
- `services/fiqa_api/inbox_triage/h5_task_intake.py` (projection fetch warning)
- `miniapp/pages/request-item/request-item.ts` (redacted submit/retry logs)
- `docs/product/p20_slice1_e2e_step4_validation_report.md`
- `docs/product/p20_slice1_manual_qa_script.md`

## Production code changed

YES (minimal observability only)

## Commit

NO

## Deploy

NO
