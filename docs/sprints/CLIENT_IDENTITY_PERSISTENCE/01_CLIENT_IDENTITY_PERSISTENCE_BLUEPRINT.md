# Client Identity Persistence Blueprint

**Sprint:** Client Identity Persistence + End-to-End Client-Aware Flow  
**Created:** 2026-03-18

---

## 1. Why End-to-End Client Identity Persistence Matters Now

The product already has:
- Client-aware UI copy (ClientConfigProvider, URL ?client=)
- Client-aware initial triage (TriageRequest.client_id, pass to triage_conversation)
- Handoff phrases loaded by client_id
- configs/clients/{client_id}/ structure

**But:** client awareness is stronger at entry than across the full lifecycle.

- **Initial triage:** client-aware ✓
- **Case persistence:** client_id not stored ✗
- **Append/follow-up:** triage_for_append uses get_active_client_id() (env default), not case client ✗
- **Reopen/workbench:** case has no client_id; append uses URL context or env default ✗

If the founder wants true reuse across Client A / Client B / future SMBs, client identity must survive the full operational path.

---

## 2. Why This Is the Right Move After Initial Client-Aware Handoff Wiring

The previous sprint (CLIENT_AWARE_HANDOFF_WIRING) fixed:
- client_id in triage path
- get_handoff_phrases(client_id)
- Frontend passes clientId to triageMessage

**Deferred:** client_id on persisted cases, triage_for_append client-aware.

This sprint picks up that deferred work: **persist client_id on cases** and **use it for append/reopen**.

---

## 3. What This Sprint Will Strengthen

| Area | Before | After |
|------|--------|-------|
| Case persistence | No client_id | client_id stored on case |
| save_case | Ignores client | Accepts client_id, persists |
| triage_for_append | Uses env default | Uses case.client_id when present |
| append_case_message route | No client context | Passes case.client_id to triage |
| append_follow_up_message | N/A | Preserves case client_id |
| Workbench reopen | Append uses URL/env | Append uses case.client_id |

---

## 4. What This Sprint Intentionally Will NOT Do

- **No full multi-tenant auth** — single broker pilot; no per-user isolation
- **No DB partitioning** — JSON case store unchanged
- **No giant config editor** — config structure unchanged
- **No add-car-rules client param** — deferred; add when Rules Center needs multi-client

---

## 5. Core Principle

Do NOT build full multi-tenant auth.  
Do NOT over-engineer platform infra.  
Do NOT start giant admin tooling.  

This sprint is about making client-aware behavior survive the whole case lifecycle.
