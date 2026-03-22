# Case Persistence Review + Workbench Polish — Final Report

**Date:** 2026-03-20  
**Mode:** Document-driven review + small high-value polish (demo queue **out of scope**).

## Summary

- **Persistence:** Documented as-is: cases + sessions + attachment metadata/files on local JSON + disk under `data/`, with env overrides. Classified as **lightweight / single-node**, not commercial DB.
- **Workbench:** Improved **office-facing language** and **stable internal keys** for due-date and attention scoring (Chinese labels for follow-up, waiting-on, case status options, activity/notes cards, empty queue copy)—**without** modifying demo queue loading logic.

## Artifacts

| Doc | Path |
|-----|------|
| Blueprint | `01_CASE_PERSISTENCE_REVIEW_BLUEPRINT.md` |
| Current architecture | `02_CURRENT_PERSISTENCE_ARCHITECTURE_SPEC.md` |
| Future commercial target | `03_FUTURE_COMMERCIAL_STORAGE_RECOMMENDATION_SPEC.md` |
| Execution outline | `04_EXECUTION_OUTLINE.md` |
| Acceptance criteria | `05_ACCEPTANCE_CRITERIA.md` |
| Founder notes | `06_FOUNDER_NOTES.md` |

## Validation

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (scenarios, API on 8001, persistence, workflow backbone, simulations).
- `cd ui && npm run build` — **PASS** (after Workbench copy / logic updates in `UnifiedIntakePage.tsx`).

## Biggest remaining weakness

**JSON file + local disk** does not scale to multi-instance hosting or formal compliance; attachment URLs assume same filesystem. Next investment: **Postgres + object storage** per `03_...`.
