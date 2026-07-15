# P20 Slice 1 Mini Program Step 3 Implementation Report

**Status:** CONDITIONAL — customer Next Action + submit/retry path implemented  
**Date:** 2026-07-15  
**Scope:** WeChat Mini Program customer side for Broker Request More → Customer Continue. No deploy, no commit, no amend/withdraw, no content-hash evidence dedup.

## Customer flow implemented

1. Task Home loads authoritative `GET /api/h5/tasks/{token}/intake`.
2. When additive `slice1_projection` / `task_contract_v1` is present, Task Home shows exactly one primary Next Action, queued upcoming items (non-actionable), satisfied items, progress, and broker waiting status.
3. Primary CTA navigates to `pages/request-item/request-item`.
4. Request-item page renders the server-selected active item only (VIN / free text / insurance card / photo evidence).
5. Customer submits with `command_id` + `idempotency_key` + `expected_case_version`.
6. Accepted/replayed responses replace local state with server projection; next queued item becomes active, or UI shows “资料已提交，等待经纪人审核”.
7. Uncertain network outcomes keep the same command identity and offer retry; version conflicts refresh authoritative state without auto-resubmit.
8. Local drafts restore only when `case_id` + `request_id` + `request_item_id` still match.

Legacy (non-Slice-1) Task Home behavior remains unchanged.

## Files changed

### Mini Program (production)

- `miniapp/app.json` — register `request-item`
- `miniapp/types/task.ts` — Slice 1 additive types
- `miniapp/services/taskApi.ts` — `submitRequestItem`, `extractAttachmentId`
- `miniapp/utils/request.ts` — structured 409/422 detail preservation
- `miniapp/utils/slice1Customer.ts` — projection mapping / validators
- `miniapp/utils/slice1Lifecycle.ts` — single-flight / submit-gate helpers
- `miniapp/utils/requestItemDraft.ts` — safe draft persistence
- `miniapp/utils/resolveTaskViewModel.ts` — Slice 1 server action wins
- `miniapp/utils/taskMapping.ts` — Slice 1 error copy
- `miniapp/behaviors/taskPage.ts` — single-flight, timeout, page-alive, rehydrate
- `miniapp/pages/task-home/task-home.ts` / `.wxml` — Slice 1 overlay + routing
- `miniapp/pages/request-item/*` — new request-item page
- `miniapp/scripts/preview_preflight.ts` — AppID/pages/route readiness

### Backend (minimal contract fix)

- `services/fiqa_api/inbox_triage/p20_slice1_command_service.py` — `policy_or_insurance_card` → `provide_evidence`
- `tests/test_p20_slice1_command_service.py` — assert insurance-card action type

### Tests / docs

- `miniapp/tests/slice1RequestItem.test.ts`
- `miniapp/tests/slice1Lifecycle.test.ts`
- `miniapp/tests/slice1TaskApi.test.ts`
- `docs/product/p20_slice1_miniprogram_step3_implementation_report.md`

## Request item types implemented

| Type | UI | Submit payload |
|---|---|---|
| `vin` | validated 17-char text | `fact: { field: "vin", value }` |
| `free_text` | bounded textarea | `fact: { field: "free_text", value }` |
| `policy_or_insurance_card` | photo choose/upload | `evidence: { attachment_id }` after upload |
| `photo_evidence` | photo choose/upload | `evidence: { attachment_id }` after upload |

## Next Action behavior

- Server projection selects the sole active item.
- Client never chooses among queued items.
- Queued rows are display-only.
- `wait_for_broker_review` removes submit CTA and shows waiting copy.
- Legacy cases without Slice 1 projection keep existing intake routing.

## Submission / idempotency behavior

- One logical submit mints one `command_id` + `idempotency_key`.
- Duplicate taps blocked by `submitInFlight`.
- Timeout/uncertain retry reuses the same identity and original `expected_case_version` until conflict/acceptance clears it.
- Idempotent `replayed` treated as success.
- Version conflict clears command identity, applies returned/refetched projection, does not auto-resubmit.

## Upload behavior

- Uses existing claim evidence-pack upload path with slot `other_evidence`.
- Local selection ≠ server completion.
- Page `loading` and per-item `uploading` are separate.
- Success requires durable `attachment_id` before command submit.
- Upload failure is recoverable; accepted upload with lost command response reconciles via authoritative refetch / idempotent replay.

## Lifecycle / recovery behavior

- `onLoad` owns cold start; first `onShow` joins and does not duplicate.
- Later `onShow` / pull-to-refresh rehydrate with generation supersede.
- Destroyed pages ignore late `setData`.
- Session expiry (`403` / invalid token) preserves draft metadata and redirects to error/entry recovery.
- Matching drafts restore; item-id mismatch does not restore.

## Local draft policy

Persist only:

- `case_id`, `request_id`, `request_item_id`, `item_type`
- draft text, `client_draft_id`
- optional pending `command_id` / `idempotency_key` / `expected_case_version`
- optional `attachment_id` and local path metadata

Do not persist workflow authority, tokens, or non-serializable handles.

Cleanup:

- delete after server-confirmed satisfaction
- preserve after validation/network failure
- invalidate when active item changes

**Local file retention:** keep selected local path metadata for resume only; never treat as confirmed evidence (safest existing project policy).

## Mini Program Reliability Gate

| # | Rule | Result |
|---|---|---|
| 1 | No undefined first-render bindings | PASS |
| 2 | Single-flight initialization | PASS |
| 3 | onLoad/onShow/pull-to-refresh do not race | PASS |
| 4 | Every loading state terminates | PASS |
| 5 | Page loading and upload status are separate | PASS |
| 6 | Stale responses cannot overwrite newer results | PASS |
| 7 | Every async branch has success/failure/timeout | PASS |
| 8 | Foreground/background recovery works | CONDITIONAL (rehydrate on show; no separate App-level foreground hook beyond page show) |
| 9 | Server is confirmed-state SSOT | PASS |
| 10 | Retry is idempotent | PASS |
| 11 | Duplicate taps are blocked | PASS |
| 12 | Minimum evidence does not close workflow locally | PASS |
| 13 | Immediate feedback precedes server confirmation | PASS |
| 14 | Errors are recoverable | PASS |
| 15 | Destroyed pages do not continue setData | PASS |
| 16 | Page.data is JSON-serializable | PASS |
| 17 | Preview configuration can be preflighted | PASS |
| 18 | New components follow Three Gates | NOT APPLICABLE (reused existing task-* components; no new custom component) |

## Tests run

- `node --import tsx --test tests/slice1RequestItem.test.ts tests/slice1Lifecycle.test.ts tests/slice1TaskApi.test.ts` → **19 passed**
- `node --import tsx --test tests/taskPage.test.ts` → **11 passed**
- `python3 -m pytest tests/test_p20_slice1_command_service.py` → **12 passed**
- Related `taskHomePage` / `resolveTaskViewModel` suites exercised during regression check

## Preview preflight result

`npm run preview:preflight` → **PASSED** (qa profile, non-loopback API, empty dev token, AppID present, Slice 1 pages registered).  
Does not publish Preview; backend Slice 1 capability still required on the target case.

## Known limitations

- No live WeChat Preview / phone end-to-end run in this step.
- Amend/withdraw not implemented (deferred by design).
- Content-hash evidence dedup deferred.
- App-level `onShow` foreground hook beyond page lifecycle not added.
- Claim evidence upload slot uses gallery category `other_evidence` (no dedicated insurance-card slot in claim pack).
- Focused DOM/page interaction tests cover helpers + first-render defaults; full page submit orchestration is unit-covered via lifecycle helpers rather than full wx runtime.

## Deferred end-to-end work

- Broker create → customer VIN → insurance card → broker review on QA with real tokens
- Next-day resume on physical phone
- Session expiry recovery rehearsal with real expired token
- Preview publish / Trial path

## Backend fixes

1. `policy_or_insurance_card` customer action_type corrected from `provide_fact` to `provide_evidence` so Mini Program upload path matches Workbench intent.

## Rollback notes

- Disable Mini Program request-item entry by removing Slice 1 routing / page registration; legacy Task Home remains.
- Backend: disable `P20_SLICE1_REQUEST_MORE` / case capability to stop new commands; keep accepted rows.
- No schema migration introduced in Step 3.

## Production code changed

YES

## Commit

NO

## Deploy

NO
