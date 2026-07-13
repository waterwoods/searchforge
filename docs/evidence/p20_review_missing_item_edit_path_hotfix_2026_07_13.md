# Evidence — Review Missing-Item Edit Path Hotfix (2026-07-13)

| Field | Value |
|-------|-------|
| Sprint | P20 Hotfix — Restore Missing-Item Edit Path from Review |
| Severity | **High** |
| Problem | Missing information displayed on Review without an edit path |
| Expected | Clear navigation to the relevant page (Basics for injury/police) |
| Status | **Fixed in code / Manual DevTools verification required** |
| Backend / DB / Contract | **No changes** |

---

## Root cause

Review rendered `missing` as plain (non-interactive) label strings and only offered「返回我的资料」as a secondary escape. Shared route metadata already existed in `resolveMissingItemNav` / ViewModel `missingItems`, but Review did not surface taps or a recovery CTA.

## Exact dead-end path

1. Customer reaches Review with incomplete Basics (e.g. missing「是否有人受伤」「是否报警」).
2. Review lists the missing items in orange.
3. Primary CTA「提交给陈总审核」is disabled.
4. Customer cannot tap the missing rows.
5. Only escape is「返回我的资料」— no direct path to Basics from Review.

## Fix applied

1. Review uses ViewModel `missingItems` (with actionable routes) as `missingRows`.
2. Missing rows are tappable → `navigateOnce(row.route)` (injury / police → `/pages/basics/basics`).
3. One shared secondary recovery CTA via `resolveReviewSupplementAction` (e.g.「去补充基本资料」) so multiple Basics items do not spawn competing buttons.
4.「返回我的资料」remains as an escape, not the only recovery option.
5. `onShow` already reloads task + `applyReviewState` — returning from Basics refreshes missing list / submit gate.
6. Added `police_reported` → `police_involved` / Basics alias in shared mapping (no workflow rule change).

Primary CTA remains「提交给陈总审核」.

## Missing-item routing behavior

| Key / label | Route | Recovery CTA (when actionable) |
|-------------|-------|--------------------------------|
| `anyone_injured` / 是否有人受伤 | `/pages/basics/basics` | 去补充基本资料 |
| `police_involved` / 是否报警 | `/pages/basics/basics` | 去补充基本资料 |
| `police_reported` (alias) | `/pages/basics/basics` | 去补充基本资料 |
| Story / Photos missing | story / photos routes | 去填写事故经过 / 去补充事故照片 |

Routing stays centralized in `taskMapping.ts` (`resolveMissingItemNav`, `resolveReviewSupplementAction`).

## Files changed

- `miniapp/utils/taskMapping.ts`
- `miniapp/pages/review/review.ts`
- `miniapp/pages/review/review.wxml`
- `miniapp/pages/review/review.wxss`
- `miniapp/tests/reviewPage.test.ts`
- `docs/qa/p20_devtools_walkthrough_checklist.md`
- `docs/qa/p20_pilot_blockers.md`
- `docs/evidence/p20_review_missing_item_edit_path_hotfix_2026_07_13.md`

## Tests

### Mini Program

`cd miniapp && npm test` → **PASS 101 / 101**

Focused Review coverage:

- Missing injury/police → one Basics recovery action
- Supplement CTA / row tap → Basics
- Duplicate navigate guard while navigating
- Return/`onShow` refresh clears resolved items and enables submit
- No dead-end wiring in WXML

### Python

- `pytest tests/test_p19m1_mini_program_logic.py -q` → PASS 21
- `pytest tests/test_p20_track_b_backend_foundation.py -q` → PASS 5

## Manual DevTools verification (Founder)

Still required — do not mark PASS from automation alone:

1. Open Review with unfinished injury/police.
2. Confirm missing rows show and are tappable → Basics.
3. Confirm one「去补充基本资料」CTA (not duplicate buttons).
4. Save Basics → return → Review refreshes; resolved items gone.
5. Submit stays disabled until ready; then submit still works.
6.「返回我的资料」still works as escape.

## Commit / Deploy

- Commit created: **NO**
- Push / Deploy: **NO**
