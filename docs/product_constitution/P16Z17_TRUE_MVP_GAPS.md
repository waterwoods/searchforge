# P16-Z17 Phase 7 — True MVP Gap Analysis

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Scope:** Blockers only for:

```
Customer → Create Case → Return → Continue → Broker Review
```

Excluded: CRM, OCR, Stripe, P17, platform dreams, greenfield rebuild.

---

## Blockers (real only)

### Blocker 1 — Post-submit Customer Entry does not rehydrate case

**Symptom:** After formal submit + refresh, Customer Entry is empty. `lastCaseId` and post-handoff append UI live in React state only. UI calls `clearSessionId()` on case creation.

**Files:** `CustomerEntryTab.tsx` (~531–533, ~601–607), `inboxTriage.ts` (`clearSessionId`)

**Fix:** On mount, if no session restore, read active case from My Requests selection or `sessionStorage`/`localStorage` key `unified_intake_active_case_id`; set `lastCaseId` and show append panel.

**Estimate:** 1.0 engineer-day

---

### Blocker 2 — My Requests "continue" does not pass case_id

**Symptom:** `UserCaseListProgressPanel` button **去客户报送继续** calls `onContinueInCustomerPortal()` which only switches tab. Customer lands on empty Customer Entry.

**Files:** `UserCaseListProgressPanel.tsx` (~326–329), `UnifiedIntakePage.tsx` (~188), `MyRequestsTab.tsx`

**Fix:** Pass `case_id` through callback: `onContinueInCustomerPortal(caseId)` → Customer Entry receives prop or URL param → `setLastCaseId(caseId)`.

**Estimate:** 0.5 engineer-day

---

### Blocker 3 — Resume hint excludes submitted cases

**Symptom:** Empty-state **用这条记录继续** only lists cases where `resolveCaseLifecycle(c) !== 'submitted'`. After formal submit, lifecycle is `submitted` — hint hidden.

**Files:** `CustomerEntryTab.tsx` (~224–226), `caseLifecycleDisplay.ts` (`formal_submitted_at` → `submitted`)

**Fix:** Include `submitted` Add-Car cases with `formal_submitted_at` in resume hint (or merge with Blocker 1 active-case hydrate).

**Estimate:** 0.5 engineer-day (may merge with Blocker 1)

---

### Blocker 4 — Session store dependency for pre-submit return

**Symptom:** Pre-submit restore requires Postgres session row. Without `DATABASE_URL` / `SERVICE_RECORD_DATABASE_URL`, session API may not persist across server restart.

**Files:** `session_store.py`, deploy config

**Fix:** Ops: ensure demo/trial env has DB session backend. Document fallback behavior.

**Estimate:** 0.5 engineer-day (ops + checklist)

---

## Non-blockers (do not delay MVP)

| Item | Why not a blocker |
|------|-------------------|
| Partial formal submit without VIN | Correct product gate — office record needs structural truth |
| Broker activity panel hidden in trial | Message thread + glance sufficient for pilot |
| Customer message timeline UI | Broker has timeline; customer sees progress fields in My Requests |
| Cross-device return | Out of supervised pilot scope |
| Rename tabs to "Case Builder" | Copy change, not functional blocker |
| Triage extraction regression on isolated VIN turn | Workaround: use append post-submit; session holds full turns pre-submit |

---

## Engineer-day summary

| Task | Days |
|------|------|
| Active case hydrate on Customer Entry mount | 1.0 |
| My Requests → pass case_id to Customer Entry | 0.5 |
| Resume hint for submitted cases (or merge above) | 0.5 |
| Demo env session persistence verification | 0.5 |
| End-to-end UI walkthrough (3-day Tesla in browser) | 0.5 |

**Total: 3.0–3.5 engineer-days** to close MVP loop.

---

## Verdict

**No new Customer Builder required.** Three wiring gaps (case rehydrate, My Requests handoff, resume hint policy) block the return → continue path. Broker review already works.
