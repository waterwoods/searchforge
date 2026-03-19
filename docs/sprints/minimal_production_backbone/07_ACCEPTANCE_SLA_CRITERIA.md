# Acceptance / SLA Criteria — Minimal Production Backbone

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. Backbone Coherence

- [ ] workflow_state keys consistent across triage, session, case
- [ ] lifecycle_status on new case comes from triage, not derived from case_status
- [ ] Single WORKFLOW_STATE_KEYS definition used everywhere

---

## 2. Persistence Quality

- [ ] Session save/get works for refresh recovery
- [ ] Case persist on handoff clears session
- [ ] append_follow_up_message updates case_messages and workflow_state
- [ ] No regression in existing persistence behavior

---

## 3. State Correctness

- [ ] audit_state_field_accuracy.py passes (or no new failures)
- [ ] lifecycle_status values correct for collecting vs handed_off

---

## 4. Case/Message Integrity

- [ ] case_messages is source of truth; source_text derived
- [ ] New case has workflow_state from triage
- [ ] Append preserves case_id, status, notes

---

## 5. Frontend/Backend/Workbench Consistency

- [ ] TriageResult includes workflow_state keys when expected
- [ ] GET /session returns turns + workflow_state
- [ ] Case card displays lifecycle_status correctly

---

## 6. Demo/Prod Boundary Clarity

- [ ] Documented: what is demo-only vs pilot-safe
- [ ] Env vars for paths documented

---

## 7. What Remains Acceptable to Defer

- SQLite migration
- Full demo/prod mode flag
- Per-broker isolation
- Backup/restore automation
- Formal schema validation (JSON Schema)

---

*See also: `08_FOUNDER_DEMO_INSPECTION_NOTES.md`*
