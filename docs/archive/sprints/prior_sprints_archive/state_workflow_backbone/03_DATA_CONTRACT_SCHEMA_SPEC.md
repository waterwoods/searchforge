# State/Workflow Backbone — Data Contract Schema Spec

**Sprint**: State Workflow Backbone  
**Purpose**: Conversation/session identity, case identity, customer linkage, message record shape, workflow_state shape, lifecycle status, collected/still_needed/summary contract, frontend/backend response contract.  
**Base**: `case_store.py`, `triage.py`, `docs/sprints/lightweight_production_case_record/03_DATA_MODEL_SPEC.md`.

---

## 1. Conversation / Session Identity

| Concept | Current | Target |
|---------|---------|--------|
| **Before case** | Ephemeral; no ID | Optional `session_id` (e.g. UUID) for Customer Entry in-memory continuity. Not persisted. |
| **After case** | case_id | case_id is the canonical identity. case_messages = conversation. |
| **Append** | case_id required | case_id identifies the conversation thread. |

**Note**: No separate conversation_id in storage. Case = conversation once persisted. Pre-persist, session is UI-only.

---

## 2. Case Identity

| Field | Type | Purpose |
|-------|------|---------|
| case_id | string | Unique ID (e.g. case_abc123). Immutable. |
| created_at | string (ISO 8601) | Creation timestamp |
| updated_at | string (ISO 8601) | Last update |

---

## 3. Customer Linkage

| Field | Type | Purpose |
|-------|------|---------|
| customer_name | string | Display name |
| customer_phone | string | Phone |
| customer_email | string | Email |
| policy_number | string | Policy if known |
| contact_note | string | Free text (e.g. WeChat) |

All optional. Stored on case. No separate customers table.

---

## 4. Message Record Shape

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| message_id | string | ✓ | Unique (e.g. msg_xyz789) |
| role | string | ✓ | customer \| system |
| text | string | ✓ | Message content |
| created_at | string (ISO 8601) | ✓ | When added |
| sequence | int | ✓ | Order (1, 2, 3, ...) |

**Ordering**: By sequence. source_text derived as:
`"\n\n".join(f"[{客户|系统}] {m.text}" for m in sorted(case_messages, key=sequence))`

---

## 5. Workflow State Shape

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| issue_category | string | Triage | missing_document, cancellation_warning, customer_question, etc. |
| urgency | string | Triage | low, medium, high, critical |
| collection_stage | string | Triage | collecting, enough_for_handoff |
| follow_up_type | string | Triage | new_info, already_sent, clarification_question, etc. |
| handoff_ready | bool | Triage | Ready for broker |
| case_creation_suggested | bool | Triage | Signal for UI |
| collected_fields | list[string] | Per-flow extractors | year, model, zip, customer_says_sent_dec_page |
| still_needed_fields | list[string] | Per-flow logic | primary_driver, verify_carrier_received |
| human_confirmation_required | bool | Triage | Broker must verify |
| human_confirmation_fields | list[string] | Triage | VIN, customer_says_sent_*, etc. |
| broker_next_step | string | Triage | Actionable for broker |
| client_prep | string | Triage | What client should prepare |
| client_reply_draft | string | Triage | Draft reply |
| conversation_summary | string | Triage | Broker-facing summary |

---

## 6. Lifecycle Status

### 6.1 case_status

| Value | Meaning |
|-------|---------|
| new | Just handed off |
| reviewing | Broker working |
| waiting_client | Alias for waiting_customer |
| waiting_customer | Waiting on customer |
| agent_followup | Broker follow-up needed |
| done | Resolved |
| closed | Resolved |

### 6.2 waiting_on

| Value | Meaning |
|-------|---------|
| none | No explicit wait |
| client | Waiting on customer |
| broker | Broker action |
| carrier | Waiting on carrier |
| underwriting | Waiting on UW |

---

## 7. Collected / Still Needed / Summary Contract

### 7.1 collected_fields

- **Format**: List of snake_case identifiers.
- **Per-flow examples**:
  - Add-car: year, make_model, zip, delivery_date, primary_driver, vin
  - Missing doc: requested_declaration_page, customer_says_sent_declaration_page
  - Cancellation: notice_present, screenshot_sent, already_paid_claimed

### 7.2 still_needed_fields

- **Format**: List of snake_case identifiers.
- **Meaning**: What would materially improve the case or what broker must verify.
- **Examples**: primary_driver, verify_carrier_received, renewal_notice_or_bill

### 7.3 conversation_summary

- **Format**: Free text.
- **Content**: Intent hint + "Collected:" + "Still needed:" + message count + latest snippet.
- **Purpose**: Broker-facing; more actionable than raw source_text.

---

## 8. Frontend / Backend Response Contract

### 8.1 POST /api/inbox/triage

**Request**:
```json
{
  "text": "...",
  "persist_case": false,
  "conversation_turns": [{"role": "customer"|"system", "text": "..."}],
  "soft_route": "add_car"|"remove_car"|...
}
```

**Response** (triage result, always):
```json
{
  "issue_category": "customer_question",
  "urgency": "medium",
  "broker_next_step": "...",
  "client_prep": "...",
  "client_reply_draft": "...",
  "manual_followup_needed": true,
  "handoff_ready": true,
  "conversation_summary": "...",
  "collected_fields": ["year", "model"],
  "still_needed_fields": ["zip"],
  "collection_stage": "collecting",
  "follow_up_type": "new_info",
  "human_confirmation_required": false,
  "human_confirmation_fields": [],
  "case_creation_suggested": true
}
```

**When persist_case=true and handoff_ready**: Response includes full case object (case_id, case_messages, etc.).

### 8.2 POST /api/inbox/cases/{case_id}/append-message

**Request**:
```json
{ "new_message": "..." }
```

**Response**: Updated case object (same shape as GET case).

### 8.3 PATCH /api/inbox/cases/{case_id}/status

**Request**:
```json
{ "status": "reviewing" }
```

**Response**: Updated case object.

---

## 9. Case Object (Full)

```json
{
  "case_id": "case_abc123",
  "case_status": "new",
  "created_at": "2026-03-16T12:00:00Z",
  "updated_at": "2026-03-16T12:05:00Z",
  "waiting_on": "none",
  "next_contact_by": "",
  "source_text": "[客户] ...\n\n[系统] ...",
  "case_messages": [
    {"message_id": "msg_1", "role": "customer", "text": "...", "created_at": "...", "sequence": 1},
    {"message_id": "msg_2", "role": "system", "text": "...", "created_at": "...", "sequence": 2}
  ],
  "issue_category": "customer_question",
  "urgency": "medium",
  "broker_next_step": "...",
  "client_prep": "...",
  "client_reply_draft": "...",
  "manual_followup_needed": true,
  "conversation_summary": "...",
  "collected_fields": ["year", "model"],
  "still_needed_fields": ["zip"],
  "handoff_ready": true,
  "case_creation_suggested": true,
  "human_confirmation_required": false,
  "human_confirmation_fields": [],
  "collection_stage": "enough_for_handoff",
  "follow_up_type": "new_info",
  "customer_name": "",
  "customer_phone": "",
  "customer_email": "",
  "policy_number": "",
  "contact_note": "",
  "case_notes": [],
  "case_activity": []
}
```

---

*See also: `04_TRANSITION_GUARDRAIL_SPEC.md`, `services/fiqa_api/inbox_triage/case_store.py`*
