# P0 — Broker Close → History (read-only)

**Status:** Implemented (Commit 2)  
**Date:** 2026-07-22  
**Objective:** Canonical Broker Close clears Active Case binding and makes the case immutable History.  
**Out of scope:** Reopen, full History browsing UI, Workbench redesign, Vehicle/Timeline/T6, Production deploy.

---

## Soft Archive ≠ Broker Close

| | Soft Archive (`workbench_archived`) | Broker Close |
|--|-------------------------------------|--------------|
| Purpose | Queue visibility filter | Terminal lifecycle |
| Releases Active Case | **No** | **Yes** |
| Customer writes | Still allowed | Rejected (`case_closed_read_only`) |
| History marker | No | `case_history_state=history` |

---

## Canonical Close fields

Stamped by `close_case(case_id, actor, reason?)`:

| Field | Value |
|-------|--------|
| `case_status` | `closed` |
| `admin_lifecycle` | `closed` |
| `case_history_state` | `history` |
| `closed_at` | ISO-8601 UTC |
| `closed_by` | broker/office actor |
| `close_reason` | optional |

Binding cleanup: `mp_customer_active_case`, in-process index, `intake_sessions.payload.active_case_id`.

---

## Customer write gate

`case_is_customer_writable(case)` / `assert_customer_case_writable(case)` → error `case_closed_read_only`.

Gated: H5 patch, upload, skip, evidence-actions, submit, request-item submit; Slice1 Request More / Send Request reject closed.

---

## API

- `POST /api/inbox/cases/{case_id}/close` (broker + office access)
- `PATCH /api/inbox/cases/{case_id}/status` with `status=closed` routes through `close_case`

No customer close endpoint.

---

## Workbench

- Button **Close Case** + confirmation warning
- Badge **Closed / History**; Close hidden after close; Request More disabled
- Soft archive label: **队列隐藏（≠ Close）**
- QA-only seed button: **Create Test Case** (hidden when QA tools off)
