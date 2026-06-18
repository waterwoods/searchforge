# P16 Case Memory Persistence — Fix Report

**Sprint:** P16-P2-CASE-MEMORY-PERSISTENCE-SPRINT  
**Date:** 2026-06-07

---

## 1. Root cause

Collecting-phase triage with bound `case_id` did not call `append_follow_up_message`. Messages stayed in React state; Postgres retained only the Customer First draft starter.

---

## 2. Exact files changed

| File | Change |
|------|--------|
| `services/fiqa_api/routes/inbox_triage.py` | Added `_collecting_case_memory_target`, `_persist_collecting_case_memory`; wired append after triage when case bound and append allowed |
| `tests/test_collecting_case_memory_persistence.py` | Regression tests |
| `scripts/run_p16_case_memory_simulation.py` | E2E simulation battery A–D |

---

## 3. DB tables used

| Table / column | Usage |
|----------------|-------|
| `service_records` | Case row (existing) |
| `case_messages` (JSONB) | Customer + system turns with monotonic `sequence` |
| `source_text` | Rebuilt from messages on each append |
| `collected_fields`, `still_needed_fields` | Merged via `_merge_append_field_lists` on append |
| `updated_at` | Bumped on each append |

No new tables. Uses existing `append_follow_up_message()` → `persist_case_append()` path.

---

## 4. Before behavior

```
Phone → Find Active Case → Continue → Empty chat (1 draft starter)
```

- Each `/api/inbox/triage` turn with `case_id`: response had fields; **Postgres unchanged**
- `in_progress_sessions`: not written (blocked by `case_id`)
- Hydration: `customerEntryTurnsFromSavedCase` could not rebuild BMW / 2027 / ZIP thread

---

## 5. After behavior

```
Phone → Find Active Case → Continue → Full timeline + Still Needed + Status
```

When triage runs with:

- `existing_case` loaded (explicit or resolved `case_id`)
- customer text non-empty
- `append_allowed !== false`
- `case_boundary !== new_issue`

→ `append_follow_up_message(case_id, text, triage_result)` persists customer message, system reply, and merged field lists.

Boundary-blocked turns (e.g. second vehicle) **do not** mutate case memory — same as append-message route.

---

## 6. Fix logic (minimal)

```python
memory_target = _collecting_case_memory_target(
    existing_case=existing_case, result=result, text=text, effective_case_id=effective_case_id,
)
if memory_target:
    updated = _persist_collecting_case_memory(...)
    if updated:
        result.update(updated)  # HTTP contract + hydration source aligned
```

Inserted after `persist_case` handoff block, before `_finalize_triage_http_contract`.

---

## 7. Verification (local + Cloud Run QA)

| Check | Result |
|-------|--------|
| `pytest tests/test_collecting_case_memory_persistence.py` | PASS (2/2) |
| Simulation A–D vs `localhost:8001` | PASS |
| Simulation A–D vs `https://fiqa-api-g7zatxrycq-uw.a.run.app` (post-deploy) | PASS |
| Postgres `case_messages` after multi-turn | Customer turns present, order preserved |

---

## 8. Remaining risks

| Risk | Mitigation |
|------|------------|
| Append blocked on vehicle-scope conflict (e.g. conflicting VIN) | By design — no silent mutation |
| Formal-submit `save_case` path still creates new record | Unchanged; collecting uses append path |
| Duplicate append if client retries same turn | Idempotency not in scope — same as append-message |
| `client_id` filter on active-case lookup | Test/preview data must use matching client (e.g. `chen_kui`) |

---

## 9. GO / CONDITIONAL GO / NO GO

**GO** — fix verified locally, on Cloud Run QA API (deployed via `deploy_paid_pilot.sh`), and Preview UI browser path.
