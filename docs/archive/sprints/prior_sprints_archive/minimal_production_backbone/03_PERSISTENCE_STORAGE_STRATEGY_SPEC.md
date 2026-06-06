# Persistence / Storage Strategy Spec

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. What Should Be Persisted

| Entity | What | When |
|--------|------|------|
| **Session** | turns, workflow_state, updated_at | Each triage when session_id present and no case |
| **Case** | Full case record (see Data Contract) | When handoff_ready and persist_case |
| **Case message** | message_id, role, text, created_at, sequence | On case save; on append |

---

## 2. When Persistence Occurs

| Event | Action |
|-------|--------|
| Triage returns, no case, session_id present | save_in_progress_session |
| Triage returns handoff_ready, persist_case | save_case; delete_in_progress_session |
| Broker updates status/notes/follow-up | Update case in place |
| Broker pastes follow-up | append_follow_up_message |

---

## 3. What Remains Ephemeral

- In-memory triage result (until persisted)
- KV-cache session (query.py) — separate from Unified Intake
- Frontend conversation state (until restored from session or case)

---

## 4. Current Storage Approach

| Store | Path | Format | Limits |
|-------|------|--------|--------|
| Sessions | data/unified_intake_sessions.json | JSON | 50 sessions, evict oldest |
| Cases | data/unified_intake_cases.json | JSON | 200 cases |

**Env overrides:** UNIFIED_INTAKE_SESSIONS_PATH, UNIFIED_INTAKE_CASES_PATH

**Write strategy:** NamedTemporaryFile + replace (atomic on same filesystem)

---

## 5. Stay on Current Storage or Introduce Formal Store?

**Decision: Stay on JSON for this sprint.**

**Rationale:**

- JSON + atomic write is sufficient for single-broker pilot
- Migration to SQLite would add complexity without clear payoff for v1
- Formalizing schemas and contracts gives most of the benefit
- If pilot scales, SQLite migration can be a follow-up sprint

**Improvements this sprint:**

- Document schema explicitly
- Ensure workflow_state consistency
- Add optional origin_session_id to case for traceability

---

## 6. What Is Realistic Right Now

- Keep JSON files
- Add schema validation in code (required keys, types)
- No new storage backend
- Demo/prod: same storage, different paths via env

---

*See also: `04_DATA_CONTRACT_SCHEMA_SPEC.md`*
