# P16-Z16 Phase 4 — Real Flow Walkthrough

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Scenario:** 3-day Tesla Add-Car case  
**Method:** Code trace + live backend simulation (`PYTHONPATH=. python3`)

---

## Scenario

| Day | Customer message |
|-----|------------------|
| Day 1 | "I bought a Tesla" |
| Day 2 | "VIN is 5YJ3E1EA1KF123456" |
| Day 3 | "My daughter will drive it too" |

Assumptions: Add-Car lane, `client_id=chen_kui`, same browser for Day 1 pre-submit; Day 2–3 via append API (simulating return after formal submit).

---

## Day 1 — Start case

### Turn 1: Customer sends message

| Transition | Value |
|------------|-------|
| **UI action** | Empty state → Send / Add-Car starter |
| **session_id** | `getOrCreateSessionId()` → e.g. `sess_a1b2c3...` stored in `localStorage` key `unified_intake_session_id` |
| **API** | `POST /api/inbox/triage` `{ text, persist_case: true, session_id, soft_route: "add_car", formal_submit: false }` |
| **case_id** | `null` — not persisted yet |
| **collected_fields** | `['make_model', 'insurance_status_new_customer']` |
| **still_needed_fields** | `['year', 'make_model', 'vin', 'zip', 'delivery_date', 'primary_driver']` |
| **handoff_ready** | `false` |
| **case_lifecycle** | `collecting` |
| **case_messages** | — (not in case store) |
| **Session store** | `save_in_progress_session(session_id, turns+reply, workflow_state)` |

### Customer leaves (pre-submit)

| Asset | State |
|-------|-------|
| `localStorage.unified_intake_session_id` | Present |
| Postgres `intake_sessions` row | Turns + workflow_state (if DB configured) |
| Case store | Empty for this customer |

### Customer returns same day (pre-submit refresh)

| Transition | Value |
|------------|-------|
| Mount effect | `getSessionId()` → same UUID |
| **API** | `GET /api/inbox/session/{session_id}` |
| **UI** | `setTurns(restored)` + toast「已恢复未完成的报送」 |
| **case_id** | Still null |

### Day 1 end — Formal submit

| Transition | Value |
|------------|-------|
| **UI** | Customer clicks「正式提交办公室」→ `formalSubmit=true` |
| **API** | `POST /api/inbox/triage` with `formal_submit: true` |
| **Gate** | `should_persist = formal && (struct_ok \|\| handoff_ready)` |
| **case_id** | **`case_4ed01ea2acb4`** (example from simulation) |
| **formal_submitted_at** | `2026-06-03T08:36:30Z` |
| **lifecycle_status** | `handed_off` |
| **case_messages** | 3 entries (Day 1 thread parsed from source_text) |
| **case_activity** | `[{ activity_type: "case_created", ... }]` |
| **localStorage** | `clearSessionId()` — session key removed |
| **React state** | `lastCaseId = case_id`, post-handoff closure card shown |

---

## Day 2 — Return + VIN append

### Customer context (real UX)

- Refresh → Customer Entry **empty** (no session, no `lastCaseId`)
- My Requests → case visible with `updated_at`, missing fields
- **「去客户报送继续」** → switches tab, **does not load case**

### Simulated append (API truth)

| Transition | Value |
|------------|-------|
| **API** | `POST /api/inbox/cases/case_4ed01ea2acb4/append-message` `{ new_message: "VIN is ..." }` |
| **triage_for_append** | Re-triages with full thread context |
| **collected_fields** | `['make_model', 'vin', 'insurance_status_new_customer']` |
| **case_messages** | 5 entries (was 3 + customer + system) |
| **case_activity** | `['follow_up_added', 'case_created']` |
| **formal_submitted_at** | Unchanged ✅ |
| **updated_at** | New timestamp |
| **broker_next_step** | Updated (e.g. confirm remaining gaps, then quote) |

---

## Day 3 — Driver append

| Transition | Value |
|------------|-------|
| **API** | Same append path |
| **collected_fields** | Adds `primary_driver` |
| **case_messages** | 7 entries, sequences `[1,2,3,4,5,6,7]` |
| **case_activity** | 3 entries total |
| **broker_next_step** | "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day." |

---

## Timeline diagram

```
Day 1                    Day 2 (append)           Day 3 (append)
─────                    ──────────────           ──────────────
session_id active   →    session_id cleared  →    (none)
case_id null        →    case_id stable      →    case_id stable
case_messages —     →    seq 1-5             →    seq 1-7
formal_submitted_at — →  unchanged           →    unchanged
UI turns in memory  →    UI empty (refresh)  →    broker sees all
```

---

## State transition summary

| Variable | Day 1 start | Day 1 submit | Day 2 append | Day 3 append |
|----------|-------------|--------------|--------------|--------------|
| `session_id` (localStorage) | created | **cleared** | absent | absent |
| `case_id` | null | `case_*` | same | same |
| `collected_fields` | partial | partial | +vin | +primary_driver |
| `case_messages` count | 0 | 3 | 5 | 7 |
| `case_activity` | — | 1 | 2 | 3 |
| Customer UI thread | in React | in React | **lost if refresh** | broker-only unless re-wired |

---

## Verdict

The **3-day story works at the persistence layer** without building anything new. The **customer-facing return path breaks on refresh** after Day 1 submit because session is cleared and `case_id` is not rehydrated into Customer Entry. Broker sees the full timeline throughout.
