# P16-Z16 Phase 1 — Customer Entry Audit

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Constraint:** Audit only — no redesign, no new features  
**Sources:** `CustomerEntryTab.tsx`, `inboxTriage.ts`, `routes/inbox_triage.py`, `case_store.py`, `session_store.py`

---

## Executive answer

**Yes — a customer can create a real, persisted case today** on the Add-Car path via formal submit. Pre-submit multi-turn intake works but lives in session storage, not the case store. The Customer Entry tab is a working case builder for Add-Car; it is not a greenfield concept.

---

## 1. Can a customer create a real case today?

| Path | Creates persisted `case_id`? | Notes |
|------|---------------------------|-------|
| **Add-Car formal submit** | ✅ Yes | Primary mature path |
| **Add-Car multi-turn (pre-submit)** | ❌ No | Session-only until formal submit |
| **Generic intake (non–Add-Car)** | ✅ When `handoff_ready` | No `formal_submit` gate |
| **Post-handoff append** | ❌ No new case | Mutates existing case |

Customer Entry always calls `triageMessage(..., persistCase=true, ...)`. Persistence is server-gated — the UI cannot force a case without meeting backend rules.

---

## 2. What exact action creates `case_id`?

`case_id` is created inside `save_case()` when the triage route decides `should_persist`:

```python
# routes/inbox_triage.py — persist gate
if add_car_lane:
    should_persist = formal and (struct_ok or handoff_ready)
else:
    should_persist = handoff_ready
```

**Add-Car (customer portal):**

1. Customer sends messages until `isAddCarReadyForFormalSubmit(lt)` is true (UI) — backend equivalent: struct complete or `handoff_ready`.
2. Customer clicks **「正式提交办公室」** → `submitMessage` sets `formalSubmit=true`.
3. `POST /api/inbox/triage` with `formal_submit: true`, `persist_case: true`.
4. `save_case()` assigns `case_id = f"case_{uuid4().hex[:12]}"`.

**Generic lanes:** Any turn where triage returns `handoff_ready=true` with `persist_case=true` triggers `save_case()` without `formal_submit`.

After case creation, the UI calls `clearSessionId()` and stores `lastCaseId` in React state.

---

## 3. What data is persisted?

### On formal submit (`save_case`)

| Field group | Examples |
|-------------|----------|
| Identity | `case_id`, `created_at`, `updated_at`, `formal_submitted_at`, `client_id`, `origin_session_id` |
| Thread | `source_text`, `case_messages[]` (sequenced customer/system) |
| Triage | `issue_category`, `urgency`, `collected_fields`, `still_needed_fields`, `quote_ready_status`, `broker_next_step`, `client_prep`, `client_reply_draft` |
| Workflow | `case_status`, `lifecycle_status` (= `handed_off`), `handoff_ready`, `waiting_on`, `next_best_question` |
| Add-Car | `service_lane`, `vehicle_key`, `primary_vehicle_summary`, `service_type` |
| Audit | `case_activity[]` seeded with `case_created` |
| Contact | `customer_name`, `customer_phone` (from extraction) |
| Storage | JSON file (`data/unified_intake_cases.json`) and/or Postgres via `service_record_repository` |

### Pre-submit (in-progress session)

When `session_id` is sent and no `case_id` is returned, `save_in_progress_session()` persists:

- Full turn list (including embedded `triageResult` on system turns)
- `workflow_state` subset: `collected_fields`, `still_needed_fields`, `handoff_ready`, `lifecycle_status`, etc.
- Optional `light_identity_binding`

Backend: Postgres when `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL` is set; otherwise **no persistence** unless `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1`.

---

## 4. What breaks after refresh?

| State | After browser refresh |
|-------|----------------------|
| **Pre-submit conversation** | ✅ Restored if `localStorage` still has `unified_intake_session_id` AND Postgres session row exists (`GET /api/inbox/session/{id}`) |
| **Post-submit conversation UI** | ❌ Lost — `turns[]` and `lastCaseId` are React state only; `clearSessionId()` removes session key |
| **Post-submit append panel** | ❌ Lost — requires `lastCaseId` in memory; refresh shows empty Customer Entry |
| **Persisted case record** | ✅ Survives — broker workbench and My Requests can load it |
| **WeChat identity strip dismiss** | ✅ Survives in `sessionStorage` per `clientId` |

**Critical gap:** After formal submit, a returning customer must rediscover the case via **My Requests** or the empty-state resume hint — but neither restores the post-handoff thread or append UI automatically.

---

## 5. What depends on localStorage?

| Key | Purpose | File |
|-----|---------|------|
| `unified_intake_session_id` | Pre-submit session continuity | `inboxTriage.ts` |

Functions: `getSessionId()`, `getOrCreateSessionId()`, `clearSessionId()`.

- Created on first triage call.
- Used for in-progress restore on mount (`getInProgressSession`).
- **Cleared on case creation** (`clearSessionId()` when `data.case_id` returned).
- **Cleared on「提交新问题」** (`handleNewConversation`).

No localStorage for `case_id`, `turns`, or post-submit state.

---

## 6. What depends on database storage?

| Concern | Backend | Requires DB? |
|---------|---------|--------------|
| **Case records** | `case_store.py` + optional Postgres | No — JSON default; PG when configured |
| **In-progress sessions** | `session_repository.py` | **Yes** for production-like behavior |
| **Session ↔ case binding** | `patch_session_case_binding`, `save_session_binding_after_case_created` | Yes (same session store) |
| **WeChat light identity** | Session row `light_identity_binding` | Yes |

Without Postgres: pre-submit refresh recovery fails silently (404 on session GET). Cases still persist to JSON.

---

## CustomerEntryTab flow map

```
Empty state → triageMessage (session_id from localStorage)
     ↓
Multi-turn → save_in_progress_session each turn (if no case_id)
     ↓
Formal submit → save_case → case_id → clearSessionId()
     ↓
Post-handoff → appendFollowUpMessage(case_id) [collapsed panel]
```

**Resume hints (empty state):**

- `listRecentCasesPage` → filter ongoing Add-Car cases where lifecycle ≠ submitted.
- **Reality:** All `save_case()` records have `formal_submitted_at`, so lifecycle is always `submitted`. This hint targets edge/legacy rows only; normal Add-Car pre-submit resume is **session-only**.

**「用这条记录继续」** sets `lastCaseId` + `selectedButtonIntent='add_car'` but does **not** load case thread into `turns[]`.

---

## Verdict

Customer Entry is a **real case builder** for Add-Car with working formal persist and post-handoff append — but **return-later UX is fragmented** between session restore (pre-submit only) and My Requests (post-submit, read-only progress).
