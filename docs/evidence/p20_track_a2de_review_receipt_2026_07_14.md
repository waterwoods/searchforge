# Sprint A2d/e Evidence — Review + Receipt Migration

Date: 2026-07-14
Scope: Migrate `pages/review` and `pages/receipt` onto shared Mini Program Task Runtime (`taskPage`, `TaskShell`, `TaskCTA`, `TaskError`, `resolveTaskViewModel`).

## Delivered

- Migrated `miniapp/pages/review/` to shared `taskPage` + `TaskShell` + `TaskCTA` + `TaskError`.
- Migrated `miniapp/pages/receipt/` to shared `taskPage` + `TaskShell` + `TaskCTA` + `TaskError`.
- Extended `resolveTaskViewModel()` with route-aware Review/Receipt CTA + `resolveSubmitDisabledReason()`.
- Submit path: shared `busy.submitting`, server read-back confirmation, no optimistic success, duplicate submit blocked.
- Receipt path: authoritative reload on show, timestamp when available, next-step + supplement guidance, safe return to Task Home.

## Verification Matrix

| Requirement | Result |
|-------------|--------|
| Review uses taskPage / TaskShell / TaskCTA | PASS |
| Contract-first view model / shared resolver | PASS |
| Submit disabled with reason when not ready | PASS |
| Submit uses shared busy lifecycle | PASS |
| Server read-back after submit (no optimistic success) | PASS |
| Duplicate submit blocked | PASS |
| Receipt success / next-step / timestamp | PASS |
| Supplement guidance when required | PASS |
| Safe return to Task Home | PASS |
| Reload-safe (no stale receipt) | PASS |

## Automated Tests

### Mini Program tests

Command:

`cd miniapp && npm test`

Result:

- PASS: 82 tests
- FAIL: 0

New/updated focused coverage includes:

- `miniapp/tests/reviewPage.test.ts`
  - submit ready
  - disabled reason
  - duplicate submit blocked
  - read-back success
  - failed submit
- `miniapp/tests/receiptPage.test.ts`
  - success render
  - reload
  - return home
  - next-step display
  - supplement state
- `miniapp/tests/resolveTaskViewModel.test.ts`
  - review route CTA + disabled reason
  - receipt route CTA

### Python tests

Command:

`pytest tests/test_p19m1_mini_program_logic.py -q`

Result:

- PASS

Command:

`pytest tests/test_p20_track_b_backend_foundation.py -q`

Result:

- PASS

## Backend/Contract Change Check

- Backend service/API routes changed: NO
- DB/schema changed: NO
- Request contract changed: NO

## Manual DevTools Checklist (to run in WeChat DevTools)

1. From Task Home, open Review when data is incomplete — confirm submit CTA disabled with visible reason.
2. Complete story/basics/photos until Review enables submit.
3. Tap submit once — confirm loading state; tapping again does not double-submit.
4. Confirm navigation to Receipt only after server confirms `submitted`.
5. Force submit failure (network off) — stay on Review with clear error; no success flash.
6. Open Receipt — confirm success title, next-step text, and submit timestamp when contract timestamps exist.
7. Pull/re-enter Receipt — confirm content refreshes from server (no stale prior case title).
8. If supplement is allowed / missing photo guidance present, confirm secondary "继续补充照片" works.
9. Tap "返回我的资料" and land on Task Home.
10. Kill/reopen from entry resume path and confirm Receipt still loads authoritative server state.
