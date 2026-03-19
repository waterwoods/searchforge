# Execution Outline

**Sprint:** In-Progress Conversation Persistence + Single Source of Truth

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| Session store | Backend | JSON file, save/update/get, eviction |
| Triage integration | Backend | Call save on triage when session_id + no case_id |
| Restore API | Backend | GET /api/inbox/session/{session_id} |
| Frontend restore | Frontend | On mount, GET session; restore turns + workflow_state |
| Contract alignment | All | Ensure workflow_state is single source |

---

## 2. Implementation Order

1. **Session store module** (session_store.py) — save_session, get_session, evict
2. **Triage route** — after triage, when session_id and no case_id: save_session
3. **Restore endpoint** — GET /api/inbox/session/{session_id}
4. **Frontend API** — getInProgressSession(sessionId)
5. **Frontend CustomerEntryTab** — useEffect on mount: restore if session_id exists

---

## 3. Test Plan

- `run_inbox_triage_scenarios.py`
- `run_multi_turn_simulations.py`
- `audit_state_field_accuracy.py`
- `verify_speed_routing.py`
- `guardrail_inbox_triage.sh`
- `unified_intake_smoke_check.sh`
- Manual: start conversation, 1–2 turns, refresh, verify restore

---

## 4. Likely Loop Count

- **Loop 1:** In-progress message + state persistence (backend + frontend restore)
- **Loop 2:** Recovery hardening, workflow_state consistency
- **Loop 3:** Optional refinement (one guardrail or transition rule)

---

*See: 05_ACCEPTANCE_SLA_CRITERIA.md*
