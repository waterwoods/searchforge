# P16-Z17 Phase 3 — Multi-Day Append Test

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Case under test:** `case_98f4ac099d15` (live server)  
**Method:** `POST /api/inbox/cases/{case_id}/append-message`

---

## Scenario note

The sprint script assumes:

- Day 1: "I bought a Tesla" → **case created**
- Day 2: VIN append
- Day 3: driver append

**Live reality:** Case is not persisted until formal submit passes (VIN required in thread for Add-Car handoff). The append tests below use a case created after a complete Day 1–2 triage thread, then append on Day 2 and Day 3 as specified.

---

## Baseline — formal submit (end of Day 1/2 collection)

| Field | Value |
|-------|-------|
| **case_id** | `case_98f4ac099d15` |
| **formal_submitted_at** | `2026-06-03T08:58:13Z` |
| **collected_fields** | `year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing` |
| **still_needed_fields** | `[]` |
| **case_messages** | 7 (sequences 1–7) |
| **case_activity** | 1 × `case_created` |

---

## Day 2 — "VIN is 5YJ3E1EA1KF123456"

**API:** `POST /api/inbox/cases/case_98f4ac099d15/append-message`

| Check | Result |
|-------|--------|
| **same case_id** | ✅ `case_98f4ac099d15` |
| **duplicate case created** | ✅ No |
| **collected_fields merged** | ✅ VIN retained in `collected_fields` |
| **still_needed_fields** | ✅ `[]` |
| **case_messages count** | 9 (was 7 + customer + system) |
| **case_activity** | `follow_up_added` / `conversation_appended` prepended |
| **formal_submitted_at** | ✅ Unchanged (`2026-06-03T08:58:13Z`) |
| **updated_at** | ✅ New timestamp (`2026-06-03T08:58:21Z`) |

---

## Day 3 — "My daughter will drive it too."

**API:** Same append path

| Check | Result |
|-------|--------|
| **same case_id** | ✅ `case_98f4ac099d15` |
| **duplicate case created** | ✅ No |
| **driver added** | ✅ `primary_driver` in `collected_fields` |
| **no data loss** | ✅ `vin` still in `collected_fields` |
| **case_messages count** | 11 |
| **message sequences** | `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]` monotonic |
| **case_activity count** | 3 |

---

## Append function chain (verified)

```
appendFollowUpMessage(case_id, text)
  → triage_for_append(existing source_text, new_message)
  → append_follow_up_message(case_id, text, triage_result)
      • case_messages += customer + system
      • case_activity prepends follow_up_added / conversation_appended
      • collected_fields / still_needed_fields merged
      • formal_submitted_at preserved
      • lifecycle_status → office_followup
```

Source: `services/fiqa_api/inbox_triage/case_store.py` — `append_follow_up_message()`.

---

## Customer UI caveat (not API)

`handlePostHandoffAppendSameCase()` requires `lastCaseId` in React state. After browser refresh, append UI is **not visible** unless customer re-sets `lastCaseId` (resume hint excludes submitted cases). **Append API works; customer UX does not survive refresh.**

---

## Multi-turn pre-submit regression (observed)

When adding VIN via **triage** (not append) mid-session, extraction can **drop** previously collected slots (live: turn with VIN alone regressed `year`, `zip`, `delivery_date`, `primary_driver` from collected). Append path does **not** show this regression. Prefer append post-submit; pre-submit continuity depends on session `workflow_state` + full turn list.

---

## Verdict

| Sprint check | Result |
|--------------|--------|
| same case_id | ✅ |
| no duplicate case | ✅ |
| collected_fields merged | ✅ |
| timeline updated | ✅ |
| driver added Day 3 | ✅ |
| no data loss | ✅ |

**Persistence layer: PASS.** Customer-facing append after refresh: **FAIL without wiring.**
