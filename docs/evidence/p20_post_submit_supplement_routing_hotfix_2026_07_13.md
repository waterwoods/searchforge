# Evidence — Post-Submit Supplement Routing Hotfix (2026-07-13)

| Field | Value |
|-------|-------|
| Sprint | P20 Hotfix — Fix Post-Submit Supplement Routing Dead End |
| Severity | **High** |
| Problem | 「继续补充资料」routes to non-editable Review |
| Expected | Route to actionable missing-data page (Basics / Story / Photos) |
| Status | **Fixed in code / Manual DevTools verification required** |
| Backend / DB / Task Contract / Workflow | **No changes** |

---

## Root cause

1. Backend Task Contract (unchanged) for submitted cases still emits  
   `next_action = { type: go_to_section, target: "review", label: "继续补充资料" }`  
   whenever `review_ready` is true.
2. Mini Program Task Home trusted that contract CTA and mapped `review` → `/pages/review/review`.
3. Client `buildSupplementRows` previously skipped non-photo checklist items when `submitted`, weakening post-submit actionable missing rows.
4. Review (when reached) disables formal submit after submit — correct — but was treated as the default supplement destination, producing an inert / near-dead-end surface.

## Broken routing path

```
Task Home
  → tap「继续补充资料」(contract target=review)
  → Review
  → missing items shown
  → no / weak edit navigation
  → only「返回我的资料」
```

## Fix applied

1. Centralized `resolveSupplementAction(missingItems)` in `taskMapping.ts`  
   (deterministic priority: Story → Basics → Photos; `resolveReviewSupplementAction` kept as alias).
2. `resolveNextAction`: submitted + actionable missing → supplement to first missing page;  
   submitted + none → Receipt.
3. `buildSupplementRows`: submitted status no longer strips non-photo supplement rows  
   (supplement editing allowed; formal re-submit still blocked).
4. `resolveTaskViewModel`: on Task Home (non-Review / non-Receipt), override post-submit CTA:  
   - missing →「继续补充资料」+ first actionable route  
   - none →「查看提交结果」→ Receipt  
   Never follow inert Review for supplement.
5. Review keeps tappable missing rows + supplement CTA; submit stays disabled when already submitted.

## Supplement routing behavior

| Condition | Task Home「继续补充资料」 |
|-----------|---------------------------|
| Missing story / accident narrative | → `/pages/story/story` |
| Missing anyone_injured / police_* / basics fields | → `/pages/basics/basics` |
| Missing required photo/evidence | → `/pages/photos/photos` |
| Multiple missing | First by priority (Story → Basics → Photos) |
| No missing items | → Receipt (`查看提交结果`) |
| Already submitted | Formal「提交给陈总审核」disabled; supplement still allowed |

## Files changed

- `miniapp/utils/taskMapping.ts`
- `miniapp/utils/resolveTaskViewModel.ts`
- `miniapp/pages/review/review.ts`
- `miniapp/tests/supplementRouting.test.ts` (new)
- `miniapp/tests/taskHomePage.test.ts`
- `miniapp/tests/reviewPage.test.ts`
- `tests/test_p19m1_mini_program_logic.py` (client-logic mirror only)
- `docs/qa/p20_devtools_walkthrough_checklist.md`
- `docs/qa/p20_pilot_blockers.md`
- `docs/evidence/p20_post_submit_supplement_routing_hotfix_2026_07_13.md`

## Tests

### Mini Program

`cd miniapp && npm test` → **PASS 112 / 112**

Focused coverage:

- submitted + missing Basics → Basics
- submitted + missing Story → Story
- submitted + missing Photos → Photos
- multiple → deterministic first route
- no missing → Receipt fallback (not Review)
- supplement refresh clears resolved items
- no duplicate formal submit
- no dead-end Task Home → Review path
- Review post-submit still shows supplement CTA; submit blocked

### Python

- `pytest tests/test_p19m1_mini_program_logic.py -q` → **PASS 23**
- `pytest tests/test_p20_track_b_backend_foundation.py -q` → **PASS 5**

## Backend changed

**NO**

## Manual DevTools verification (Founder)

Required — do not mark PASS from automation alone:

1. Submit a task (or open an already-submitted token) that still has missing Basics / Story / Photos.
2. On Task Home, tap「继续补充资料」→ must open the first actionable page, **not** Review.
3. Save supplement → return to hub → missing items refresh / resolved rows disappear.
4. Confirm「提交给陈总审核」cannot duplicate formal submit after submitted.
5. If Review is opened manually while submitted + missing: rows +「去补充…」still work; only「返回我的资料」is not the sole escape.

## Commit / Deploy

- Commit created: **NO**
- Push / Deploy: **NO**
