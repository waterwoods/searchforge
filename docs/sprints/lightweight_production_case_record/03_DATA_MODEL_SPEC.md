# Lightweight Production Case Record — Data Model Spec

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15

---

## 1. Storage Strategy

**Decision**: Stay with JSON file storage. Improve structure within the same file. No migration to SQLite/Postgres in this sprint.

**Rationale**: Startup-practical; no new infra; existing `UNIFIED_INTAKE_CASES_PATH` works. Schema version field added for future migration.

---

## 2. Payload Structure

```json
{
  "schema_version": 1,
  "cases": [
    { ... case object ... }
  ]
}
```

---

## 3. Case Entity

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| case_id | string | ✓ | Unique ID (e.g., case_abc123) |
| case_status | string | ✓ | new, reviewing, waiting_customer, agent_followup, closed |
| created_at | string (ISO 8601) | ✓ | Creation timestamp |
| updated_at | string (ISO 8601) | ✓ | Last update |
| waiting_on | string | ✓ | none, client, broker, carrier, underwriting |
| next_contact_by | string | ✓ | Short note (e.g., "2026-03-09", "tomorrow") |
| case_notes | array | ✓ | Broker notes |
| case_activity | array | ✓ | Activity log (case_created, status_changed, etc.) |
| case_messages | array | ✓ | **NEW** Message-level history |
| source_text | string | ✓ | **Derived** from case_messages for backward compat; or kept in sync |
| issue_category | string | ✓ | From triage |
| urgency | string | ✓ | low, medium, high, critical |
| broker_next_step | string | ✓ | From triage |
| client_prep | string | ✓ | From triage |
| client_reply_draft | string | ✓ | From triage |
| manual_followup_needed | bool | ✓ | From triage |
| conversation_summary | string | | From triage |
| collected_fields | array | | From triage |
| still_needed_fields | array | | From triage |
| handoff_ready | bool | | From triage |
| case_creation_suggested | bool | | From triage |
| human_confirmation_required | bool | | From triage |
| human_confirmation_fields | array | | From triage |
| collection_stage | string | | collecting, enough_for_handoff |
| follow_up_type | string | | new_info, correction, already_sent, etc. |
| customer_name | string | | **NEW** Optional |
| customer_phone | string | | **NEW** Optional |
| customer_email | string | | **NEW** Optional |
| policy_number | string | | **NEW** Optional |
| contact_note | string | | **NEW** Optional |

---

## 4. Case Message Entity (NEW)

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| message_id | string | ✓ | Unique ID (e.g., msg_xyz789) |
| role | string | ✓ | customer | system |
| text | string | ✓ | Message content |
| created_at | string (ISO 8601) | ✓ | When added |
| sequence | int | ✓ | Order in conversation (1, 2, 3, ...) |

**Ordering**: Messages ordered by sequence. `source_text` derived as:
`"\n\n".join(f"[{客户|系统}] {m.text}" for m in sorted(case_messages, key=lambda x: x["sequence"]))`

---

## 5. Case Activity (Existing, Unchanged)

| Field | Type | Purpose |
|-------|------|---------|
| activity_id | string | Unique |
| activity_type | string | case_created, status_changed, follow_up_updated, note_added, follow_up_added, message_added |
| message | string | Human-readable description |
| created_at | string | Timestamp |

---

## 6. Case Note (Existing, Unchanged)

| Field | Type | Purpose |
|-------|------|---------|
| note_id | string | Unique |
| body | string | Note content |
| created_at | string | Timestamp |

---

## 7. Customers (Deferred)

**No separate customers table/entity in this sprint.** Customer fields live on the case. If we add a customers table later, `customer_id` can reference it.

---

## 8. Migration / Compatibility

| Scenario | Strategy |
|----------|----------|
| Existing case (no case_messages) | On read: parse `source_text` into case_messages; or leave empty and derive source_text from "" |
| New case | Create case_messages from initial turn(s) |
| Append | Add new message to case_messages; append to source_text for backward compat |
| Old clients | source_text remains present; clients that only use source_text keep working |

**Backward compatibility**: `source_text` is always present. When case_messages exists, it is the source of truth; source_text is kept in sync for triage and legacy display.

---

*See also: `04_EXECUTION_OUTLINE.md`, `services/fiqa_api/inbox_triage/case_store.py`*
