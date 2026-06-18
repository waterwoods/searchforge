# P16 Status Truth — Audit

**Sprint:** P16-P3-STATUS-TRUTH-SPRINT  
**Date:** 2026-06-07

---

## 1. Lifecycle states today

| State | Storage field | Customer meaning | Formal submit? |
|-------|---------------|------------------|----------------|
| **Draft / collecting** | `lifecycle_status: collecting` | Saved, still gathering vehicle/contact fields | No — `formal_submitted_at` empty |
| **Ready for handoff** | `lifecycle_status: handoff_pending` + `handoff_ready: true` | All structural slots filled; customer may tap formal submit | No until `formal_submit: true` |
| **Submitted to office** | `lifecycle_status: handed_off` + `formal_submitted_at` set | Office-visible service record | Yes |
| **Office follow-up** | `lifecycle_status: office_followup` | Same record, customer append / broker action | Already submitted |
| **Closed** | `case_status: closed` | Matter complete | N/A |

Derived API axis (non-authoritative): `case_lifecycle` ∈ `collecting | almost_ready | ready_for_handoff | submitted` from `case_lifecycle.py`.

Customer-facing surface (P16):

| Dimension | Values | Source |
|-----------|--------|--------|
| `status_label` | `saved_not_yet_submitted` \| `submitted_to_office` | `active_case_lookup.customer_status_label` |
| `contact_state` | `waiting_for_customer` \| `broker_reviewing` \| `office_reviewing` | `resolve_customer_contact_state` |
| `submit_state` | `not_yet` \| `submitted` | mirrors `is_formal_submitted` |

---

## 2. How `status_label` is computed

**Backend (authoritative for phone return card):**

```python
# active_case_lookup.py
def customer_status_label(case):
    return "submitted_to_office" if is_customer_formal_submitted(case) else "saved_not_yet_submitted"

def is_customer_formal_submitted(case):
    if still_needed_fields: return False          # fix: gap gate
    if lifecycle in (collecting, handoff_pending): return False
    if formal_submitted_at: return True
    return lifecycle in (handed_off, office_followup)
```

**Frontend (chat closure + fallback):**

```typescript
// AddCarRecordSummaryRail.tsx
isFormalSubmissionToOfficeComplete(triage):
  if still_needed_fields.length > 0 → false       // fix
  if lifecycle collecting/handoff_pending → false
  if formal_submitted_at → true
  if lifecycle handed_off/office_followup → true
```

Phone return card uses API `status_label` via `resolveCustomerStatusLabel` in `customerFirstEntry.ts`.

---

## 3. When does a case transition to `submitted_to_office`?

| Transition | Trigger | Gate |
|------------|---------|------|
| Draft created | `POST /api/inbox/customer/start-add-car` | Phone valid, no active case |
| Collecting turns | `POST /api/inbox/triage` + bound `case_id` | Case Memory append; **no** formal submit |
| Formal submit | `POST /api/inbox/triage` with `formal_submit: true` | Add-Car lane + structural completeness (`_add_car_structurally_complete_for_persist`) |
| Persist | `save_case` | Sets `formal_submitted_at`, `lifecycle_status: handed_off` |

**Pre-fix bug path:** collecting append → `office_followup` + backfilled `formal_submitted_at` → UI treated as submitted without gate.

---

## 4. Can a case be “submitted” while `still_needed_fields` is non-empty?

| Phase | Pre-fix | Post-fix |
|-------|---------|----------|
| Intended | **No** | **No** |
| Observed (BMW X5) | **Yes** — lifecycle corruption | **No** |

`contact_state` was partially correct pre-fix (`waiting_for_customer` when gaps exist), but `status_label` and chat closure card disagreed.

---

## 5. Status surface audit (Preview UI)

### Customer can see

| Question | Surface | Pre-fix | Post-fix |
|----------|---------|---------|----------|
| Did I submit? | Status card `status_label`; green closure card | **Conflict** on collecting turns | Aligned: Saved / not closure |
| What is missing? | Still Needed list; chat `client_reply_draft` | **Yes** | **Yes** |
| What is happening now? | Contact State | Partial (contact ok, submit wrong) | **Yes** |

### Surfaces reviewed

| Component | Path | Shows |
|-----------|------|-------|
| Active case card | `CustomerFirstEntryScreen.tsx` | Status, Still Needed, Contact State |
| Chat closure | `CustomerEntryTab.tsx` ~1348 | Green card when `formalSubmissionComplete` |
| Pre-submit gap alert | `CustomerEntryTab.tsx` `showAddCarPreSubmitGapAlert` | Missing fields banner (hidden when formal complete — was hidden incorrectly) |
| Add-car rail | `AddCarRecordSummaryRail.tsx` | Step 2 vs 3, formal submit CTA |

### Minimal visibility improvements (implemented via truth fix)

No new product surfaces added. Fixing submit detectors removes the contradictory green closure card during collection.

**Optional follow-up (not in scope):** rename Status card label from binary “Submitted To Office” to include “Waiting For Customer” when gaps exist — currently `contact_state` already carries that dimension.

---

## 6. North Star validation

| Constitution rule | Pre-fix | Post-fix |
|-------------------|---------|----------|
| Progress = Missing Fields | Violated (submit UI ignored gaps) | **Pass** |
| Customer Must Always Know The Status | Violated (dual message) | **Pass** |
| Phone Required For Formal Submit | Violated (phantom submit) | **Pass** |

---

## 7. Expected business model alignment

Implemented model maps to user’s four states:

| User model | Implementation |
|------------|----------------|
| Draft | `collecting` + `saved_not_yet_submitted` |
| Waiting For Customer | gaps present → `contact_state: waiting_for_customer` |
| Submitted To Office | `handed_off` + empty gaps + `formal_submitted_at` |
| Closed | `case_status: closed` (excluded from active lookup) |

No new states added; truth gates tightened on existing fields.
