# State / Workflow Backbone Phase 2 — Design Spec

**Sprint**: State Workflow Backbone Phase 2  
**Purpose**: Target Phase 2 improvements; practical scope.

---

## 1. Main Remaining Architecture Gaps

| Gap | Current | Target |
|-----|---------|--------|
| Conversation identity pre-case | None; ephemeral | Optional session_id (localStorage + API) |
| Workflow_state completeness | Missing next_best_question, lifecycle_status | Full contract with all fields |
| UI state visibility | Partial; lifecycle underused | Clear collecting / handoff / office display |

---

## 2. Target Phase 2 Improvements

### A. Session Continuity
- Frontend generates `session_id` (UUID) on first Customer Entry message
- Stored in localStorage; passed to POST /api/inbox/triage
- Backend returns `conversation_id` = session_id when no case yet; `case_id` when persisted
- Refresh: if session_id in localStorage and no case persisted, optionally restore turns (deferred: restore from localStorage if we persist turns there)

### B. Workflow State Contract
- Add `next_best_question` to triage result when handoff_ready=false (what to ask next)
- Add `lifecycle_status` to case: `collecting` | `handoff_pending` | `handed_off` | `office_followup`
- Document full workflow_state shape in spec

### C. UI Visibility
- Prominent "Collecting" vs "Ready for handoff" indicator
- Collected / Still needed always visible when present
- Lifecycle tag: collecting / handed off / office follow-up

---

## 3. Practical Scope

- **In scope**: session_id in API + frontend; next_best_question in triage; lifecycle_status derived; UI visibility improvements
- **Out of scope**: Persisting in-progress turns server-side; full append "still collecting"; SQL migration

---

*See: 03_CONVERSATION_SESSION_CONTINUITY_SPEC.md, 04_WORKFLOW_STATE_CONTRACT_SPEC.md, 05_UI_STATE_VISIBILITY_SPEC.md*
