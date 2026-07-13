# P20 Track A1 Shared Foundations — Evidence

- Date: 2026-07-13
- Branch: `sprint/p16-trust-layer`
- Scope: Track A1 foundation only (no page migration)

## Files changed

- `miniapp/types/task.ts`
- `miniapp/utils/resolveTaskViewModel.ts`
- `miniapp/behaviors/taskPage.ts`
- `miniapp/components/task-loading/index.{ts,json,wxml,wxss}`
- `miniapp/components/task-error/index.{ts,json,wxml,wxss}`
- `miniapp/components/task-cta/index.{ts,json,wxml,wxss}`
- `miniapp/components/task-shell/index.{ts,json,wxml,wxss}`
- `miniapp/tests/miniprogramMocks.ts`
- `miniapp/tests/resolveTaskViewModel.test.ts`
- `miniapp/tests/components.test.ts`
- `miniapp/tests/taskPage.test.ts`
- `miniapp/package.json`
- `docs/design/p20_task_ui_kit_v0_2026_07_12.md`
- `docs/design/p20_track_a_implementation_plan_2026_07_12.md`

## Architecture implemented

- Added A1 Task Contract and ViewModel typing layer in `miniapp/types/task.ts`.
- Implemented `resolveTaskViewModel()` as the single contract-first normalization seam.
- Implemented `taskPage` shared behavior for token guard, loading, cached fallback, centralized busy map, bounded retry/cooldown, stale-request protection, safe error mapping, `saveAndReturn(saveFn)`, and no-op `track()`.
- Implemented four reusable WeChat custom components:
  - `TaskLoading`
  - `TaskError`
  - `TaskCTA`
  - `TaskShell`

## Test setup

- Added minimal Node-based TypeScript unit test setup in `miniapp/package.json`.
- Runner: built-in `node:test` + `tsx` (no browser DOM and no WeChat simulator dependency for pure logic tests).
- Local command:
  - `cd miniapp && npm test`

## Tests and counts

- New A1 tests:
  - `miniapp/tests/resolveTaskViewModel.test.ts` (8 tests)
  - `miniapp/tests/components.test.ts` (4 tests)
  - `miniapp/tests/taskPage.test.ts` (8 tests)
  - Total: 20 tests, pass.
- Existing regression suites run:
  - `PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q` (21 pass)
  - `PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q` (5 pass)

## Contract-first and fallback behavior

- `task_contract` emission confirmed in backend (`intake_info_for_token()` additive `task_contract` field exists).
- Contract present path: resolver prioritizes `task_contract`.
- Legacy fallback path: resolver uses existing `taskMapping` inference only when contract absent.
- Retirement criterion documented in code/docs: fallback inference is temporary and non-authoritative after parity validation.

## Component validation

- Unit tests validate:
  - `TaskCTA` suppresses tap when disabled/loading.
  - `TaskError` emits `retry` and `contactBroker` correctly.
  - `TaskShell` mode selection (loading / blocking_error / content).
  - `TaskLoading` safe default message behavior.
- No production navigation modifications and no page migration.

## Deferrals (A2/A3)

- Deferred components: `TaskField`, `TaskChoice`, `TaskPhoto`, `TaskReview`, `TaskReceipt`, `TaskStatusCard`, `TaskProgress`.
- Deferred work: Task Home and other page migrations; full page composition changes; advanced save/upload orchestration beyond A1 behavior seams.

## Confirmed non-scope

- No backend code changes.
- No API contract changes.
- No DB/schema changes.
- No deploy/push/commit.
- No migration of existing 8-page journey.

## Known risks

- `resolveTaskViewModel` fallback still depends on legacy inference quality until full parity migration is complete.
- `taskPage` behavior is implemented but not yet wired into production pages (intentional A1 boundary), so runtime benefits depend on A2/A3 adoption.
