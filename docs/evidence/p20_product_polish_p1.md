# Evidence — Product Polish P1 (Entry / Error / Resume + UX Audit)

Date: 2026-07-14  
Scope: Unify Entry + Error onto Task Runtime; audit full journey UX (no new business features).

## Delivered

- `miniapp/pages/entry/` → `taskPage` + `TaskShell`; resume-aware loading; retryable/non-retryable recovery.
- `miniapp/pages/error/` → `taskPage` + `TaskShell` + `TaskError` + `TaskCTA`; `reLaunch` Entry recovery.
- `contactBrokerModalCopy()` + `token_missing` / `navigation_failed` messages in `taskMapping`.
- Focused tests: `entryPage.test.ts`, `errorPage.test.ts`.
- Design audit: `docs/design/p20_product_polish_p1.md` (20 observations).

## Automated Tests

### Mini Program

`cd miniapp && npm test`

- PASS: 92
- FAIL: 0

### Python

`pytest tests/test_p19m1_mini_program_logic.py -q`  

- PASS (`.....................`)

`pytest tests/test_p20_track_b_backend_foundation.py -q`

- PASS (`.....`)

## Backend / Contract

- Backend changed: **NO**
- DB/schema changed: **NO**
- Contract changed: **NO**

## Complete walkthrough checklist

Manual items are **TODO** unless actually verified in WeChat DevTools this session.  
Automated-only confidence is marked **WARNING** (code/tests suggest OK; still needs DevTools).

### Entry

| Step | Check | Mark |
|------|-------|------|
| Cold open with valid token | Loading explains open; lands Task Home | WARNING |
| Resume storage open | Copy mentions 恢复; lands correct hub/receipt | WARNING |
| Missing token | Non-retryable; contact guidance; no fake success | WARNING |
| Network fail on bootstrap | Retryable error; retry cooldown polite | WARNING |
| Expired link | Clears resume; contact path | TODO |
| Navigation fail | Shows navigation_failed safe copy | TODO |

### Task Home

| Step | Check | Mark |
|------|-------|------|
| Know where you are | Title + progress + status readable | TODO |
| Primary CTA clear | Verb-led next action | TODO |
| Missing rows actionable | Tap navigates to section | TODO |
| Retry on load fail | Bounded retry / contact | TODO |
| Contact broker | Currently opens disclaimer — known issue | TODO |
| No endless spinner after load | Busy clears | TODO |

### Story

| Step | Check | Mark |
|------|-------|------|
| Loading message meaningful | `正在加载事故经过…` | TODO |
| Prefill / resume draft | Dirty guard preserves typing | TODO |
| Save success | Toast + return hub | TODO |
| Save fail | Text preserved; retryable | TODO |
| CTA wording | 保存并返回 / 稍后再填 | TODO |

### Basics

| Step | Check | Mark |
|------|-------|------|
| Loading + choices clear | Injury/police easy | TODO |
| Validation feedback | Toast when incomplete | TODO |
| Save + police read-back | No optimistic success | TODO |
| CTA wording | 保存并返回 / 稍后再填 | TODO |

### Photos

| Step | Check | Mark |
|------|-------|------|
| Slot labels + required hints | Clear | TODO |
| Upload progress | Percent visible | TODO |
| Success after read-back only | No optimistic slot success | TODO |
| Duplicate upload blocked | Busy guard | TODO |
| Return wording mismatch | “任务首页” vs hub “我的资料” | TODO |

### Review

| Step | Check | Mark |
|------|-------|------|
| Summary readable | Story / photos / received / missing | TODO |
| Disabled reason when not ready | Visible under CTA | WARNING |
| Duplicate submit blocked | Busy submitting | WARNING |
| Success only after submitted read-back | Then Receipt | WARNING |
| Edit links usable | Story/Basics/Photos | TODO |

### Receipt

| Step | Check | Mark |
|------|-------|------|
| Success state obvious | Title + status pill | WARNING |
| Timestamp when available | From contract timestamps | WARNING |
| Next step message | Clear | WARNING |
| Supplement guidance | Shown when allowed/needed | WARNING |
| Return to Task Home | 返回我的资料 | WARNING |
| Reload safe | No stale receipt | WARNING |

### Cross-journey

| Step | Check | Mark |
|------|-------|------|
| No dead ends | Every error has retry or contact | WARNING |
| Wording consistency | Hub return + contact still uneven | TODO |
| Resume kill/reopen | Entry → correct destination | TODO |
| Customer-safe network copy | `backend_unreachable` still engineer-facing | TODO |

## Notes

- Never marked manual checklist rows **PASS** without a real DevTools walkthrough in this sprint.
- High-priority remaining: Task Home contactBroker, customer-safe unreachable copy, return-CTA wording.

## Files changed

- `miniapp/pages/entry/{ts,wxml,json}`
- `miniapp/pages/error/{ts,wxml,json}`
- `miniapp/utils/taskMapping.ts`
- `miniapp/tests/entryPage.test.ts` (new)
- `miniapp/tests/errorPage.test.ts` (new)
- `docs/design/p20_product_polish_p1.md` (new)
- `docs/evidence/p20_product_polish_p1.md` (new)
