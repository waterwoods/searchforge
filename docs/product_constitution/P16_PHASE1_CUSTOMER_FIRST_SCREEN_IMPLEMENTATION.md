# P16 Phase 1 — Customer First Screen Implementation

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-SCREEN  
**Date:** 2026-06-07  
**Constitution:** `P16_CUSTOMER_FIRST_CONSTITUTION.md`

---

## What Was Built

### Customer Entry Screen (UI)

New component: `ui/src/features/intake/components/CustomerFirstEntryScreen.tsx`

Cold URL flow:

1. Banner — Add-Car Request / 加车申请  
2. Trust lines — no account, no password, phone return key  
3. **Phone** (required, first field)  
4. **Name** (optional Phase 1)  
5. **Continue** → active case check

Integrated as gate in `CustomerEntryTab.tsx`: intake chat does not appear until Customer First completes (except session restore / My Requests continue).

### Active Case Check (API + UI)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/inbox/customer/active-case?phone=` | Phone return-key lookup (Rule 2, Rule 7) |
| `POST /api/inbox/customer/start-add-car` | Create collecting draft with claimed phone; 409 if active exists |

Backend modules:

- `services/fiqa_api/inbox_triage/phone_normalization.py` — US 10-digit normalize/validate  
- `services/fiqa_api/inbox_triage/active_case_lookup.py` — active add-car match + draft create  
- `services/fiqa_api/db/service_record_repository.py` — `list_binding_stub_rows_by_phone_digits` (indexed PG lookup)  
- `services/fiqa_api/inbox_triage/case_truth_repository.py` — `list_cases_for_phone_lookup`

### Continue Flow

| Scenario | UX | Next step |
|----------|-----|-----------|
| **A — No active case** | “Start New Add-Car Request” | `POST start-add-car` → add-car intake |
| **B — Active case** | Vehicle, missing fields, submit state | Continue existing / Contact broker |

**Saved draft ≠ submitted:** `submit_state: not_yet` when `lifecycle_status` is `collecting` or `handoff_pending`; UI copy explicit.

### Out of Scope (unchanged)

- SMS, OTP, OAuth, WeChat required path  
- Customer portal, multi-case picker, CRM  
- Formal submit phone gate (Phase 3)

---

## Constitution Alignment

| Rule | Phase 1 status |
|------|----------------|
| 1 Customer never logs in | ✅ Entry screen has no login |
| 2 Phone is return key | ✅ Lookup API + UI; localStorage cache for convenience |
| 3 Phone required formal submit | ⏳ Phase 3 |
| 4 Progress = missing fields | ✅ Scenario B shows `still_needed_fields` |
| 5 Broker closes/reopens | ✅ No customer close; Contact Broker path |
| 6 Broker confirms identity | ✅ Claimed phone/name only |
| 7 One active case | ✅ 409 on second start; Scenario B blocks new vehicle |

---

## Files Touched

| Area | Files |
|------|-------|
| UI | `CustomerFirstEntryScreen.tsx`, `CustomerEntryTab.tsx`, `customerFirstEntry.ts`, `inboxTriage.ts` |
| API | `routes/inbox_triage.py`, `active_case_lookup.py`, `phone_normalization.py`, `case_store.py` |
| DB read | `service_record_repository.py`, `case_truth_repository.py` |
| Tests | `tests/test_active_case_by_phone.py` |
| Simulation | `scripts/run_p16_customer_first_screen_simulations.py` |

---

## Known Limits

1. **Name optional** — collected but not required; see Review for delete recommendation.  
2. **Phone lookup** scans PG by phone column + JSON fallback; not yet deduped pilot data (Phase 4).  
3. **Session restore** still works same-browser; phone gate is primary for cross-device return.  
4. **Intake API key** still required on `/api/inbox/*` perimeter (same as existing customer UI bundle).

---

*End of implementation record*
