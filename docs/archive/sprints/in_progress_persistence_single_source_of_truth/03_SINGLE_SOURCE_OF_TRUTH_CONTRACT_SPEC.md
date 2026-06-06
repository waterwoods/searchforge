# Single Source of Truth Contract Spec

**Purpose:** Define workflow_state as the primary contract; avoid frontend/backend/workbench divergence.

---

## 1. What workflow_state Must Contain

From `triage.py` WORKFLOW_STATE_KEYS:

| Key | Type | Description |
|-----|------|-------------|
| collection_stage | string | "collecting" \| "enough_for_handoff" |
| follow_up_type | string | Intent-specific follow-up type |
| handoff_ready | bool | Broker should receive case |
| case_creation_suggested | bool | UI: suggest persist |
| collected_fields | string[] | Structured fields collected |
| still_needed_fields | string[] | Fields still needed |
| human_confirmation_required | bool | Broker confirm before acting |
| human_confirmation_fields | string[] | Which fields drive confirmation |
| next_best_question | string | What to ask when handoff_ready=false |
| lifecycle_status | string | "collecting" \| "handoff_pending" \| "handed_off" \| "office_followup" |

---

## 2. Which UI Surfaces Read From It

| Surface | Fields Used |
|---------|-------------|
| Customer Entry | lifecycle_status, collection_stage, handoff_ready, next_best_question |
| Case Report / One-liner | collection_stage, handoff_ready |
| Broker Workbench (case cards) | lifecycle_status, collection_stage |
| Simulation Assistant | handoff_ready, collection_stage |

---

## 3. Which Backend Decisions Depend On It

| Decision | Field |
|----------|-------|
| Persist case? | handoff_ready |
| Save in-progress session? | No case_id in response |
| Triage output | All WORKFLOW_STATE_KEYS from triage_conversation |

---

## 4. How Broker/Workbench Consumes It

- Case cards: lifecycle_status, collection_stage
- Case detail: full workflow_state from case record
- Append flow: triage_for_append returns workflow_state; append_follow_up_message persists it

---

## 5. Avoiding Divergence

- **Backend produces** workflow_state; frontend and workbench **display** it.
- **Do not** duplicate "shadow logic" (e.g. frontend inferring handoff_ready from turns).
- **In-progress session** stores workflow_state from last triage; frontend restores and displays it.
- **Case** stores workflow_state at save/append; workbench displays from case.

---

*See: 02_IN_PROGRESS_PERSISTENCE_DESIGN_SPEC.md*
