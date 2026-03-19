# Data Contract / Schema Spec

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. Message Record

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| message_id | string | yes | e.g. msg_abc123 |
| role | "customer" \| "system" | yes | |
| text | string | yes | |
| created_at | string (ISO 8601) | yes | |
| sequence | int | yes | 1-based order |

---

## 2. workflow_state (Shared Contract)

**Source:** triage result. Extracted by session_store; persisted on case.

| Key | Type | Notes |
|-----|------|-------|
| collection_stage | string | collecting, enough_for_handoff |
| follow_up_type | string | new_info, correction, already_sent, clarification_question, etc. |
| handoff_ready | bool | |
| case_creation_suggested | bool | |
| collected_fields | string[] | |
| still_needed_fields | string[] | |
| human_confirmation_required | bool | |
| human_confirmation_fields | string[] | |
| next_best_question | string | |
| lifecycle_status | string | collecting, handoff_pending, handed_off, office_followup |

---

## 3. In-Progress Session Record

| Field | Type | Notes |
|-------|------|-------|
| session_id | string | Client-generated UUID |
| turns | message[] | role, text; system turns may include triageResult |
| workflow_state | object | Subset of workflow_state keys |
| updated_at | string (ISO 8601) | |

---

## 4. Case Record

| Field | Type | Notes |
|-------|------|-------|
| case_id | string | e.g. case_abc123 |
| case_status | enum | new, reviewing, waiting_client, waiting_customer, agent_followup, done, closed |
| created_at | string | |
| updated_at | string | |
| source_text | string | Derived from case_messages |
| case_messages | message[] | Source of truth for conversation |
| waiting_on | enum | none, client, broker, carrier, underwriting |
| next_contact_by | string | |
| case_notes | note[] | |
| case_activity | activity[] | |
| issue_category | string | |
| urgency | string | |
| broker_next_step | string | |
| client_prep | string | |
| client_reply_draft | string | |
| manual_followup_needed | bool | |
| conversation_summary | string | |
| collected_fields | string[] | |
| still_needed_fields | string[] | |
| handoff_ready | bool | |
| case_creation_suggested | bool | |
| human_confirmation_required | bool | |
| human_confirmation_fields | string[] | |
| collection_stage | string | |
| follow_up_type | string | |
| lifecycle_status | string | **From triage, not derived** |
| next_best_question | string | |
| origin_session_id | string? | Optional: session_id that created this case |
| customer_name, customer_phone, customer_email, policy_number, contact_note | string | |

---

## 5. Lifecycle / Status Fields

| Field | Values | Source of Truth |
|-------|--------|-----------------|
| lifecycle_status | collecting, handoff_pending, handed_off, office_followup | Triage (for new case); case update (for office_followup) |
| case_status | new, reviewing, ... | Broker update |

**Rule:** For a newly created case, lifecycle_status = triage.lifecycle_status (typically "handed_off"). Do NOT derive from case_status.

---

## 6. Frontend/Backend Response Contract

**POST /api/inbox/triage response:**

- When no case: `conversation_id` = session_id
- When case: full case object (SavedCase)
- workflow_state keys in triage result for in-progress display

**GET /api/inbox/session/{session_id}:**

- `{ turns, workflow_state, updated_at }`

**GET /api/inbox/cases:**

- `{ cases: SavedCase[] }`

---

## 7. Workbench Consumption Contract

- Case card: case_status, lifecycle_status, broker_next_step, collected_fields, still_needed_fields, case_messages
- Queue: sort by updated_at; filter by status
- Reopen: full case by case_id

---

## 8. Source of Truth vs Derived

| Field | Source of Truth | Derived From |
|-------|-----------------|--------------|
| case_messages | Stored | — |
| source_text | Derived | case_messages |
| workflow_state | Stored (from triage) | — |
| lifecycle_status (new case) | Triage | — |
| lifecycle_status (updated case) | Stored | office_followup when status != new |

---

*See also: `02_MINIMAL_PRODUCTION_BACKBONE_ARCHITECTURE_SPEC.md`*
