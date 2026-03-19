# Baseline Audit and 10–20 Point Breakdown

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. Baseline Audit — Current Backbone State

### 1.1 Message Persistence

| Aspect | State | Notes |
|--------|-------|-------|
| Session turns | **Strong** | Normalized, stored in unified_intake_sessions.json |
| Case messages | **Strong** | case_messages in case; source_text derived |
| Message format | **Acceptable** | message_id, role, text, created_at, sequence |

### 1.2 In-Progress Session Persistence

| Aspect | State | Notes |
|--------|-------|-------|
| Save/get | **Strong** | save_in_progress_session, get_in_progress_session |
| workflow_state extraction | **Strong** | WORKFLOW_STATE_KEYS in session_store |
| Eviction | **Acceptable** | 50 sessions, oldest evicted |
| Delete on handoff | **Strong** | delete_in_progress_session when case created |

### 1.3 Case Persistence

| Aspect | State | Notes |
|--------|-------|-------|
| Save on handoff | **Strong** | save_case when handoff_ready |
| workflow_state on case | **Strong** | Copied from triage |
| lifecycle_status | **Weak** | _normalize_case OVERRIDES with derived value on every read |
| append_follow_up_message | **Strong** | Updates case_messages, workflow_state |
| lifecycle_status on append | **Weak** | Not explicitly set; relies on _normalize_case |

### 1.4 workflow_state Contract

| Aspect | State | Notes |
|--------|-------|-------|
| Triage output | **Strong** | WORKFLOW_STATE_KEYS in triage.py |
| Session store | **Strong** | _extract_workflow_state uses same keys |
| Case store | **Strong** | save_case, append_follow_up_message copy from triage |

### 1.5 Lifecycle/Status Handling

| Aspect | State | Notes |
|--------|-------|-------|
| Triage lifecycle_status | **Strong** | collecting \| handoff_pending |
| Case lifecycle_status | **Weak** | _normalize_case overwrites; ignores stored value |
| Terminal status (closed) | **Strong** | TERMINAL_STATUS guardrail |

### 1.6 Frontend/Backend/Workbench Consistency

| Aspect | State | Notes |
|--------|-------|-------|
| TriageResult contract | **Acceptable** | TypeScript interface exists |
| Session restore | **Strong** | GET /session/{id} |
| Case display | **Acceptable** | lifecycle_status shown; may show wrong value if overwritten |

### 1.7 Storage Strategy

| Aspect | State | Notes |
|--------|-------|-------|
| JSON files | **Acceptable** | Atomic write via NamedTemporaryFile |
| Path override | **Strong** | Env vars |
| Schema validation | **Weak** | No formal validation |

### 1.8 Demo/Prod Ambiguity

| Aspect | State | Notes |
|--------|-------|-------|
| Separation | **Weak** | Same storage; path override only |
| Documented | **Acceptable** | DEPLOYMENT_READINESS |

---

## 2. Classification Summary

| Category | Count |
|----------|-------|
| Strong | 12 |
| Acceptable | 6 |
| Weak | 5 |

---

## 3. Biggest Current Weakness

**lifecycle_status overwritten in _normalize_case:** Every read (get_case_by_id, list_recent_cases) overwrites lifecycle_status with a derived value (handed_off if status=new, else office_followup). This ignores any stored value from triage and creates ambiguity when append_follow_up_message doesn't set lifecycle_status.

---

## 4. Biggest Current Fragility

**No session_id → case_id linkage:** When a case is created from a session, the session is deleted. There is no traceability from case back to the session that created it. For debugging or audit, we cannot reconstruct the pre-handoff flow.

---

## 5. Biggest Current Architectural Ambiguity

**Source of truth for lifecycle_status:** Is it triage (for new case), stored value, or derived from case_status? The code mixes all three: save_case sets "handed_off", _normalize_case overwrites on read, append doesn't set it.

---

## 6. 10–20 Point Breakdown

| # | Point | Current | Target |
|---|-------|---------|--------|
| 1 | **Message record model** | message_id, role, text, created_at, sequence | Keep; document |
| 2 | **In-progress session model** | session_id, turns, workflow_state, updated_at | Keep; document |
| 3 | **workflow_state model** | WORKFLOW_STATE_KEYS in triage, session, case | Single shared constant; document |
| 4 | **Case record model** | Full case with workflow_state | Add origin_session_id (optional) |
| 5 | **Lifecycle/status model** | lifecycle_status derived in _normalize_case | Preserve stored; derive only when missing |
| 6 | **session_id / conversation_id / case_id boundaries** | session_id pre-handoff; case_id post-handoff | Document; optional origin_session_id |
| 7 | **When each entity is created** | Session: first turn with session_id; Case: handoff_ready | Document |
| 8 | **When each entity is updated** | Session: each turn; Case: status, notes, append | Document |
| 9 | **How message + state + case remain linked** | Session has turns; case has case_messages | Document; case_messages source of truth |
| 10 | **Frontend contract for state display** | TriageResult, InProgressSession | Document |
| 11 | **Workbench contract for case/lifecycle display** | SavedCase, lifecycle_status | Document |
| 12 | **Source-of-truth vs derived** | lifecycle_status mixed | Clarify: stored wins; derive only when missing |
| 13 | **Storage strategy** | JSON files | Stay; document |
| 14 | **Demo/prod separation** | Env path override | Document; defer full mode flag |
| 15 | **Config vs code boundary** | Config in configs/; rules in code | Document |
| 16 | **Guardrails against divergence** | Scripts exist | Ensure lifecycle_status in audit |
| 17 | **Regression test coverage** | run_inbox_triage_scenarios, etc. | Add lifecycle_status assertions if needed |
| 18 | **Intentionally deferred** | SQLite, demo mode flag, multi-tenant | Document |

---

*See also: `02_MINIMAL_PRODUCTION_BACKBONE_ARCHITECTURE_SPEC.md`, `04_DATA_CONTRACT_SCHEMA_SPEC.md`*
