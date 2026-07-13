# P20 Track A2a — Task Home / Story Migration Evidence (2026-07-13)

| Field | Value |
|-------|-------|
| **Branch** | `sprint/p16-trust-layer` |
| **Scope** | Task Home + Story migration onto A1 shared foundations; A1.5/A1.6 runtime hardening |
| **Out of scope** | Backend/API/db/schema; other page migration; new framework |

## Before-state map

### Task Home (before)

- Token guard: inline `app.taskToken` check in page (`redirectTo /pages/entry/entry`).
- Lifecycle: `onShow -> refreshTask()` with page-local fetch and page-local busy state.
- Load/refresh: page directly called `CustomerTaskApi.getTask(token)`.
- Cached fallback: used `app.task` when `getTask` failed; showed toast; otherwise redirected.
- Loading/error: page-local `loading` state; no unified TaskShell/TaskError state model.
- Retry: no bounded shared retry; only reload on `onShow`.
- CTA: page computed CTA via `resolveNextAction(task)` and local `primaryRoute`.
- Missing/supplement rows: page built rows via `buildSupplementRows(task)` and local tap handler.
- Status/progress: page-local rendering from dashboard + `progressPercent`.
- Inference: page directly invoked legacy inference seam (`resolveNextAction`).
- Navigation guard: local `navigating` flag in page.

### Story (before)

- Token guard: inline check in save path only.
- Prefill: `onShow` loaded local value from `app.task.key_facts.accident_description`.
- Save navigation: fixed `setTimeout(() => navigateBack(), 400)`.
- Error handling: page-local `catch` + toast mapping only.

## Migration summary

### Task Home

- Adopted `behaviors: [taskPage]`; removed page-owned token/load/retry/busy duplication.
- Wrapped rendering in `TaskShell`; primary action via `TaskCTA` driven by `taskViewModel.cta`.
- Removed independent page call to `resolveNextAction()`; inference centralized in `resolveTaskViewModel()`.
- Supplement rows remain tappable; route mapping retained in page.

### Story

- Adopted `behaviors: [taskPage]`; wrapped in `TaskShell` + `TaskCTA` + `TaskError`.
- Save path uses `saveAndReturn()`: save → authoritative `getTask` read-back → update `app.task` / view model → toast → `navigateBack` (no fixed timeout).
- Failed save preserves Story text; duplicate save blocked by shared busy guard.

## A1.5 / A1.6 runtime hardening

### A1.5 — UI-string normalization

- `resolveTaskViewModel()` guarantees non-null UI strings (`safetyCopy`, `disabledReason`, `target`, `hint`, etc.).
- `TaskShell` / `TaskCTA` / `TaskError` / `TaskLoading` coerce null props via internal safe fields + `optionalTypes`.
- `taskPage` uses non-null sentinels (`EMPTY_TASK_VIEW_MODEL`, `EMPTY_TASK_ERROR`).

### A1.6 — Null-prop + missing-module hotfixes

- **Null-prop fix:** flat page bindings `shellSafetyCopy` and `ctaDisabledReason` synced via `taskViewModelDataPatch()` on every VM update (avoids WXML nested-path null on first paint).
- **Missing-module fix:** merged `taskViewModelDefaults` into `resolveTaskViewModel.ts` so WeChat DevTools compiler includes helpers in the existing module graph (`utils/taskViewModelDefaults.js is not defined` resolved).

## Files in commit scope

- `miniapp/pages/task-home/**`
- `miniapp/pages/story/**`
- `miniapp/behaviors/taskPage.ts`
- `miniapp/components/task-shell/**`, `task-cta/**`, `task-error/**`, `task-loading/**`
- `miniapp/utils/resolveTaskViewModel.ts`
- `miniapp/types/task.ts`
- `miniapp/tests/taskHomePage.test.ts`, `storyPage.test.ts`, `taskShellBindings.test.ts`, plus updates to `components.test.ts`, `taskPage.test.ts`, `resolveTaskViewModel.test.ts`, `miniprogramMocks.ts`
- `docs/evidence/p20_track_a2a_task_home_story_migration_2026_07_13.md`

**Excluded from commit:** `miniapp/project.config.json`, `miniapp/project.private.config.json`, `config.local.ts`, unrelated docs/evidence.

## Tests and counts

| Suite | Result |
|-------|--------|
| `cd miniapp && npm test` | **PASS 39/39** |
| `pytest tests/test_p19m1_mini_program_logic.py -q` | **PASS 21** |
| `pytest tests/test_p20_track_b_backend_foundation.py -q` | **PASS 5** |

New/expanded Mini Program tests: `taskHomePage` (6), `storyPage` (6), `taskShellBindings` (3), plus binding/regression cases in `taskPage` and `components`.

## Founder DevTools verification (2026-07-13)

| Check | Status |
|-------|--------|
| Task Home loads successfully | **PASS** |
| No blank screen | **PASS** (after A1.6 module merge) |
| No `taskViewModelDefaults.js` missing-module error | **PASS** (after A1.6) |
| No `TaskShell.safetyCopy` null warning | **PASS** (after A1.6 flat bindings; clean compile) |
| No `TaskCTA.disabledReason` null warning | **PASS** (after A1.6 flat bindings; clean compile) |
| Only WeChat base-library yellow notices | **YES** — framework noise only |

## Remaining manual verification

- **Story GUI save flow:** NOT marked PASS in this evidence — requires Founder manual exercise (type story → save → read-back → navigate back).
- **Real-device / LAN preview:** not in scope for this commit.

## Architecture confirmations

- Task Home uses `taskPage`, `TaskShell`, `TaskCTA`; no page-level `resolveNextAction`.
- Story uses shared token/error/busy lifecycle and authoritative read-back before return.
- `resolveTaskViewModel()` remains single normalization seam; `taskPage` lifecycle-only.
- No backend/API/schema changes; no other page migration; no TDesign/global store.

## Deferred (intentional)

- `TaskStatusCard`, `TaskProgress`, `TaskChoice`, `TaskPhoto`
- Migration of `basics/photos/review/receipt/entry/error`
- Autosave/draft infrastructure expansion

## Hard guardrail confirmations

- Backend changed: **NO**
- Other pages migrated: **NO**
- Secrets/tokens in commit: **NO** (test-only `h5t1.valid` mocks; no `config.local.ts`)
