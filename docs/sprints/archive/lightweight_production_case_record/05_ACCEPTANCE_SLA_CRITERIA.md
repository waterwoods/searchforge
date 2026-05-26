# Lightweight Production Case Record — Acceptance / SLA Criteria

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15

---

## 1. Message-Level History

| Criterion | Pass | Fail |
|-----------|------|------|
| Each user turn persisted | case_messages contains one record per customer message | Merged blob only |
| Each system turn persisted | case_messages contains one record per system reply | Not stored |
| Ordering | Messages have sequence or created_at for correct order | Unordered |
| Append adds message | append_follow_up_message adds new message to case_messages | Overwrites only source_text |
| Backward compat | source_text present and usable for triage | source_text missing or broken |

---

## 2. Lightweight Customer Linkage

| Criterion | Pass | Fail |
|-----------|------|------|
| Optional fields exist | customer_name, customer_phone, customer_email, policy_number, contact_note on case | Not present |
| Persisted | Values stored when provided | Not stored |
| API accepts | PATCH or create accepts customer fields | Rejected or ignored |
| Display | Workbench can show customer info when present | Not visible |

---

## 3. Explicit Workflow State

| Criterion | Pass | Fail |
|-----------|------|------|
| Persisted | collected_fields, still_needed_fields, issue_category, handoff_ready, etc. on case | Missing or derived-only |
| On create | save_case persists all triage workflow fields | Partial |
| On append | append_follow_up_message updates workflow fields from triage | Not updated |
| Human confirmation | human_confirmation_required, human_confirmation_fields persisted | Missing |

---

## 4. Minimal Lifecycle Status

| Criterion | Pass | Fail |
|-----------|------|------|
| Formal values | case_status in (new, reviewing, waiting_customer, agent_followup, closed) | Ad-hoc values |
| waiting_on | none, client, broker, carrier, underwriting | Missing or invalid |
| Office visible | Case list/detail shows status | Not visible |
| Transitions | update_case_status accepts valid values | Rejects valid |

---

## 5. Acceptable to Defer

| Item | Reason |
|------|--------|
| Separate customers table | Minimal linkage on case suffices for pilot |
| SQLite/Postgres | JSON file sufficient for single-broker pilot |
| Full event sourcing | case_activity + case_messages enough |
| Assignment/routing | Out of scope |
| Auth | Out of scope |

---

## 6. Regression Criteria

| Check | Must Pass |
|-------|-----------|
| verify_inbox_case_persistence.py | All assertions |
| guardrail_inbox_triage.sh | PASS |
| run_inbox_triage_scenarios.py | All scenarios |
| run_multi_turn_simulations.py | No new failures |
| audit_state_field_accuracy.py | All pass |
| verify_speed_routing.py | OK |

---

*See also: `06_FOUNDER_DEMO_INSPECTION_NOTES.md`*
