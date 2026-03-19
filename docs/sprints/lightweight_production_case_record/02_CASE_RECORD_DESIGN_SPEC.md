# Lightweight Production Case Record — Design Spec

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15

---

## 1. What a "Case" Is

A **case** is a formal record of a customer interaction that the broker office can track and act on.

| Attribute | Meaning |
|-----------|---------|
| **Identity** | case_id (unique, stable) |
| **Scope** | One logical customer request or thread (e.g., one add-car quote, one missing-document follow-up) |
| **Lifecycle** | New → Waiting for customer → Agent follow-up → Closed |
| **Linkage** | Optional link to a minimal customer identity |
| **Content** | Message history + workflow state + triage output |

---

## 2. What a "Message" Is

A **message** is one turn in the conversation: either from the customer or from the system (assistant).

| Attribute | Meaning |
|-----------|---------|
| **Role** | customer | system |
| **Text** | The message content |
| **Order** | Sequence number or created_at for ordering |
| **Context** | Which case it belongs to |

**Design decision**: Each user/assistant turn becomes its own record. Old `source_text` is derived by concatenating messages when needed for triage, or deprecated in favor of message-based triage input.

---

## 3. What "Customer Linkage" Is

**Customer linkage** is the lightest useful identity model for associating a case with a person.

| Field | Required? | Purpose |
|-------|-----------|---------|
| customer_id | Optional | Stable reference if we ever have a customer table |
| name | Optional | Display name (e.g., from WeChat, email) |
| phone | Optional | Contact number |
| email | Optional | Contact email |
| policy_number | Optional | If mentioned in conversation |
| contact_note | Optional | Free text (e.g., "WeChat: xxx") |

**Minimum viable**: Start with name, phone, email, policy_number as optional top-level case fields. No separate customers table in this sprint.

---

## 4. What Workflow State Needs to Be Persisted

From `LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md` and triage output:

| Field | Purpose |
|-------|---------|
| issue_category | Topic/flow (missing_document, add_car, cancellation_warning, etc.) |
| collected_fields | What we've extracted (year, model, zip, customer_says_sent_dec_page) |
| still_needed_fields | What would improve the case (primary_driver, delivery_date) |
| handoff_ready | Whether handoff threshold is met |
| case_creation_suggested | Whether UI should suggest creating a case |
| human_confirmation_required | Whether broker must verify before acting |
| human_confirmation_fields | Which fields need verification |
| collection_stage | collecting | enough_for_handoff |
| follow_up_type | new_info, correction, already_sent, clarification_question, etc. |

**Design decision**: All of these are persisted on the case record when triage produces them. They are not derived-only.

---

## 5. What a Minimal Formal Lifecycle Looks Like

| Status | Meaning |
|--------|---------|
| **new** | Just created; not yet reviewed |
| **waiting_customer** | Waiting for customer response (e.g., documents, info) |
| **agent_followup** | Broker/agent is following up (call, email, etc.) |
| **closed** | Resolved or no longer active |

**Alias**: Map existing `waiting_client` → `waiting_customer` for clarity. Keep `reviewing` as optional intermediate.

**Design decision**: Use `case_status` with values: new, reviewing, waiting_customer, agent_followup, closed. `waiting_on` (client/broker/carrier/underwriting) remains for follow-up target.

---

## 6. Relationship: Case ↔ Messages ↔ Customer

```
Case
 ├── case_id
 ├── case_status (lifecycle)
 ├── waiting_on, next_contact_by
 ├── customer_name, customer_phone, customer_email, policy_number (optional)
 ├── issue_category, collected_fields, still_needed_fields, ...
 └── case_messages[] (ordered)
      ├── message_id, role, text, created_at, sequence
      └── ...
```

**No separate customers table** in this sprint. Customer fields live on the case.

---

*See also: `03_DATA_MODEL_SPEC.md`, `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`*
