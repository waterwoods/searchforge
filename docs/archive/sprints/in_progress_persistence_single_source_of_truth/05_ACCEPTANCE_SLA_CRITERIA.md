# Acceptance / SLA Criteria

**Sprint:** In-Progress Conversation Persistence + Single Source of Truth

---

## 1. In-Progress Message Persistence

- [ ] Each triage response (when session_id provided, no case_id) saves turns + workflow_state
- [ ] Turns include customer + system messages in order
- [ ] workflow_state includes handoff_ready, lifecycle_status, collected_fields, still_needed_fields, next_best_question

---

## 2. In-Progress State Persistence

- [ ] workflow_state stored alongside turns
- [ ] Stored workflow_state matches triage result (no divergence)

---

## 3. Refresh Recovery

- [ ] After 1–2 turns, refresh page: conversation restores from session_id
- [ ] Restored turns display correctly
- [ ] Restored workflow_state drives UI (lifecycle_status, next_best_question, etc.)
- [ ] User can continue conversation after restore

---

## 4. workflow_state Consistency

- [ ] Frontend displays from workflow_state (no shadow logic)
- [ ] Backend produces workflow_state; case store persists it
- [ ] Workbench reads workflow_state from case

---

## 5. Office Usability

- [ ] Case creation/handoff still works when handoff_ready
- [ ] No regression in existing flows
- [ ] Session cleared when case persisted

---

## 6. Acceptable to Defer

- TTL / automatic session expiry
- Session cleanup on case creation (orphaned sessions OK)
- Multi-tab session locking
- Auth / per-user sessions

---

*See: 06_FOUNDER_DEMO_INSPECTION_NOTES.md*
