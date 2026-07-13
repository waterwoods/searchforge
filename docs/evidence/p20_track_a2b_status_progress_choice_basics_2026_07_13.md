# P20 Track A2b — Status/Progress/Choice/Basics Migration Evidence (2026-07-13)

| Field | Value |
|-------|-------|
| Branch | `sprint/p16-trust-layer` |
| Scope | `TaskStatusCard` + `TaskProgress` + `TaskChoice` + Task Home adoption + Basics migration |
| Out of scope | Photos / Review / Receipt / Entry / Error migration, backend changes |
| Backend/API/DB | **No changes** |

## Components created

- `miniapp/components/task-status-card/**`
  - Customer-safe status + instruction + received list + still-needed list + next-action text
  - No raw phase logic, no API call, no workflow inference
- `miniapp/components/task-progress/**`
  - Text progress (`n / total`) + bar
  - Safe clamp for invalid values, zero-total safe
- `miniapp/components/task-choice/**`
  - Large-tap single-select options
  - Emits `select` with selected value
  - Disabled guard, no duplicate emit for same selected value

## Basics before / after

### Before

- Page-local lifecycle (no shared `taskPage` behavior)
- 3 sequential PATCH calls with one `saving` flag
- No explicit step-level failure context
- Injury used ad hoc chip UI; police choice missing
- Fixed timeout navigate-back after save

### After

- Adopted shared lifecycle:
  - `taskPage` behavior
  - `TaskShell`, `TaskCTA`, `TaskLoading`, `TaskError`, `TaskChoice`
- Still uses existing backend endpoints (`/api/h5/tasks/{token}/fields`)
- Injury and police both use `TaskChoice`
- Duplicate save blocked by shared busy guard
- Save path:
  1) patch `injury`
  2) patch `time_location`
  3) patch `vehicle_other_party`
  4) authoritative `getTask` read-back
  5) navigate only after successful read-back
- Failure UX:
  - Preserves local values on failure
  - Surfaces which PATCH failed (step-level message)
  - No fixed timeout
- Partial-risk transparency:
  - Police value is read-back verified; mismatch is surfaced as explicit warning and page does not silently pretend full success

## Task Home adoption

- `pages/task-home` now uses:
  - `TaskStatusCard`
  - `TaskProgress`
- Preserved:
  - One primary CTA
  - Missing-item navigation
  - Contract-first view model seam
  - Safe load/error/retry behavior

## UX improvements (customer-visible)

- Status is presented as a clear card section rather than spread across ad hoc markup
- Progress now always includes visible text (`n / total`) in addition to bar
- Basics risk facts (injury / police) are one-tap choices, reducing typing and ambiguity
- Save feedback is clearer, including explicit step failure messaging

## Tests

### Mini Program tests

- Command: `cd miniapp && npm test`
- Result: **PASS 61/61**

Added/expanded test coverage:

- `components.test.ts`
  - `TaskStatusCard` normalization/empty-safe behavior
  - `TaskProgress` clamp + zero-total behavior
  - `TaskChoice` emit + disabled behavior
- `basicsPage.test.ts` (new)
  - shared behavior usage
  - initial prefill
  - injury/police choice state and save calls
  - duplicate save blocked
  - failed save preserves values
  - read-back required before navigation
  - no fixed timeout
  - no internal field render

### Python regression tests

- `PYTHONPATH=. python3 -m pytest tests/test_p19m1_mini_program_logic.py -q` → **PASS 21**
- `PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q` → **PASS 5**

## Manual DevTools checklist (Founder required)

Not auto-marked PASS in this evidence. Founder verification still required:

1. Task Home status card renders
2. Progress shows text + bar
3. Basics opens
4. Injury choice works
5. Police-report choice works
6. Save succeeds
7. Return to Task Home
8. Orange missing items update
9. CTA no longer spins
10. Console has no new application red errors

## Deferred (explicit)

- Native datetime picker refinement
- Single section-save backend endpoint (replace 3-PATCH path)
- `TaskPhoto`
- Review/Receipt migration
