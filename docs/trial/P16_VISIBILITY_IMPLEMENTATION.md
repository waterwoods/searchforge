# P16 Visibility Implementation

**Date:** 2026-06-06  
**Classification:** UI-only (allowed scope)

---

## Files changed

| File | Change |
|------|--------|
| `ui/src/features/intake/utils/intakePure.ts` | Visibility boost, demo penalty, `explainCaseWorkbenchScore()` |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Product-only queue card fields |
| `scripts/run_p16_office_visibility_simulation.py` | Post-fix simulation battery (28 scenarios) |

---

## Ranking changes (`intakePure.ts`)

1. **`getRecentFormalSubmissionVisibilityBoost()`** — +165 when formal submit <24h and handed off.
2. **`getFounderDemoSeedWorkbenchPenalty()`** — −300 when source matches `FOUNDER_DEMO_QUEUE`.
3. **`getCaseWorkbenchScore()`** — delegates to `explainCaseWorkbenchScore()` for transparent breakdown.
4. **`isFounderDemoSeedSourceText()`** — normalized text match helper.

No changes to `orderCasesForWorkbench()` comparator shape.

---

## Card changes (`BrokerWorkbenchTab.tsx`)

Product-only branch now renders:

- Readiness + submitted tags
- `AddCarCaseStatusStrip`
- Vehicle headline
- Short case ID (copyable)
- 待补问 missing fields
- Office next step preview

---

## Not touched (per sprint guardrails)

- DB schema / Postgres repository
- `case_store.py` / API routes
- Triage, append, binding, business rules

---

## Rollback

Revert the two UI files; no migration or data rollback required.

---

## Implementation status

**Safe minimal fix applied.** Ready for simulation certification.
