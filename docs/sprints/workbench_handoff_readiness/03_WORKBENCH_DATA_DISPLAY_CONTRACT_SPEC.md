# Workbench Data Display Contract Spec

**Sprint:** Workbench Handoff Readiness  
**Purpose:** Define exactly what the Workbench should display from the shared backbone.

---

## 1. Data Sources

| Field | Source | Notes |
|-------|--------|-------|
| case_messages | Case record | Source of truth; each {role, text, sequence, created_at} |
| source_text | Derived from case_messages | Fallback when case_messages empty |
| workflow_state | Case record | collected_fields, still_needed_fields, lifecycle_status, etc. |
| broker_next_step | Case record | From triage |
| conversation_summary | Case record | Intent + Collected + Still needed + context hint |
| follow_up_type | Case record | correction, already_sent, etc. |

---

## 2. Display Contract

| Display element | Data | Format |
|-----------------|------|--------|
| **Recent customer messages** | case_messages where role=customer, last N (2–3) | Bullet or block; label "Customer said:" |
| **Collected** | collected_fields | Green chips; humanize labels |
| **Still needed** | still_needed_fields | Orange chips; humanize labels |
| **Lifecycle status** | lifecycle_status | Tag: Handed off / Office follow-up |
| **Next move** | broker_next_step | Bold text |
| **Correction/context hint** | follow_up_type or conversation_summary | Badge when correction, already_sent |
| **Case summary** | conversation_summary | Fallback when no structured fields |
| **Full conversation** | source_text or case_messages | Collapsible; below fold |

---

## 3. Recent Messages Logic

```text
recent_customer_messages = case_messages
  .filter(m => m.role === 'customer')
  .sort(by sequence desc)
  .take(3)
```

---

## 4. Correction / Context Hint Logic

When `follow_up_type` in ("correction", "already_sent"):
- Show badge with human-readable label
- Place near "Your next move" or Collected/Still needed

---

*End of contract spec*
