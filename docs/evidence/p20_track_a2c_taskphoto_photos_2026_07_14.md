# Sprint A2c Evidence — TaskPhoto + Photos Migration

Date: 2026-07-14
Scope: `TaskPhoto` component and `pages/photos` migration onto shared task foundation.

## Delivered

- Added new reusable component: `miniapp/components/task-photo/`.
- Migrated `miniapp/pages/photos/` to shared `taskPage` behavior + `TaskShell` + `TaskCTA` + `TaskError`.
- Reused existing backend APIs only (`getUploadTaskInfo`, `uploadPhoto`, `getTask` read-back).
- Added upload progress callback support through existing request/upload wrappers (no API contract change).

## Verification Matrix

- Upload success: PASS
- Upload failure state: PASS
- Retry failed upload: PASS
- Duplicate upload blocked while busy: PASS
- Upload read-back confirmation: PASS
- Busy/loading cleared after upload path: PASS
- Return to Task Home fallback: PASS

## Automated Tests

### Mini Program tests

Command:

`cd miniapp && npm test`

Result:

- PASS: 68 tests
- FAIL: 0

New/updated focused coverage includes:

- `miniapp/tests/photosPage.test.ts`
  - upload success
  - upload failure
  - retry with existing local file
  - duplicate upload blocked
  - onShow hydration from shared load flow
  - safe return to Task Home fallback
- `miniapp/tests/components.test.ts`
  - `TaskPhoto` normalize + action emit behavior

### Python tests

Command:

`pytest tests/test_p19m1_mini_program_logic.py -q`

Result:

- PASS (`.....................`)

Command:

`pytest tests/test_p20_track_b_backend_foundation.py -q`

Result:

- PASS (`.....`)

## Backend/Contract Change Check

- Backend service/API routes changed: NO
- DB/schema changed: NO
- Request contract changed: NO

## Manual DevTools Checklist (to run in WeChat DevTools)

1. Open `pages/photos/photos` from Task Home.
2. Confirm each required slot shows clear label + required hint.
3. Upload first photo and verify progress percentage appears.
4. Confirm success only after server read-back refresh.
5. Force a failed upload (network off), verify slot-level error appears.
6. Tap retry on failed slot and verify upload succeeds after network recovers.
7. During active upload, verify additional upload taps are blocked.
8. Verify uploaded slots stay confirmed after leaving and returning to page.
9. Tap "返回任务首页" and verify navigateBack; if stack missing, fallback redirects to Task Home.
10. Confirm no endless spinner remains after success/failure paths.
