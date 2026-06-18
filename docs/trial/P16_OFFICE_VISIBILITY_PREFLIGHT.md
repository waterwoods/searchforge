# P16 Office Visibility — Phase 0 Preflight

**Sprint:** P16-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Scope:** Presentation only (no DB/API changes)

---

## Certified upstream facts (unchanged)

| Check | Result |
|-------|--------|
| DB write | OK |
| API visibility | OK |
| Server list rank for `case_ea74d66fa3ba` | **#1** (newest `updated_at`) |
| Customer formal submit | SUCCESS |
| Vehicle | 2024 Tesla Model Y |

**Conclusion:** Data path healthy. Defect is Office Workbench **UI sort + card scope**.

---

## Snapshot before fix

### Queue ranking (product-only Office Workbench)

| Layer | Order key | `case_ea74d66fa3ba` rank |
|-------|-----------|--------------------------|
| API `GET /api/inbox/cases` | Postgres / JSON `updated_at` DESC | **#1** |
| UI `orderCasesForWorkbench()` | `getCaseWorkbenchScore()` DESC, then `updated_at` | **#12** |

Root cause tags: **UI_SORT_ISSUE**, **UI_QUEUE_SCOPE_ISSUE**.

### Score snapshot (before)

`case_ea74d66fa3ba` (handed_off, medium urgency, no follow-up due, no `waiting_on: broker`):

| Component | Points |
|-----------|--------|
| Attention section (`tracking` / `parked`) | 0 |
| Urgency (`medium`) | +8 |
| **Total** | **8** |

Founder demo seed example (cancellation, `waiting_on: broker`, due today, high urgency):

| Component | Points |
|-----------|--------|
| Action + due today | 100 + 60 |
| Urgency high | +15 |
| **Total** | **175** |

Eleven demo/action cases with scores **150–175** sat above the real submit at **8**.

### Card layout (product-only UI — before)

`BrokerWorkbenchTab.renderRecentCaseCard()` product-only branch showed:

- Urgency tag
- **`source_text` preview (90 chars)** only

Missing without opening case:

- Vehicle summary
- Case ID
- Submitted status
- Missing fields
- Office next step (Chinese)

Full (non–product-only) cards already had richer fields; pilot surface uses **product-only** mode.

### Workbench queue scope (before)

- Page load: 50 cases from API (server order #1 correct).
- Client re-sort demoted fresh submits below demo seeds.
- Product-only flat list (no action/tracking sections) — all demotion visible as scroll.

---

## Evidence files

- Ranking logic: `ui/src/features/intake/utils/intakePure.ts` — `getCaseWorkbenchScore`, `orderCasesForWorkbench`
- Product-only cards: `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` — `renderRecentCaseCard`
- Demo noise source: `ui/src/features/intake/constants/index.ts` — `FOUNDER_DEMO_QUEUE`

---

## Preflight verdict

**Proceed to minimal UI fix.** No database, API, triage, or persistence changes required.
