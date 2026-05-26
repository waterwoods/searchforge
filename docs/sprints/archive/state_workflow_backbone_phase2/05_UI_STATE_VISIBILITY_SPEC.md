# State / Workflow Backbone Phase 2 — UI State Visibility Spec

**Purpose**: Define what the UI should show for state/lifecycle visibility.

---

## 1. Minimum Visibility Requirements

| Element | When | Display |
|---------|------|---------|
| **Collecting vs handoff** | Always | Clear tag: "Collecting info" or "Ready for handoff" |
| **Current topic** | When known | Issue category or inferred focus (Add car quote, Missing document, etc.) |
| **Collected** | When collected_fields present | List of humanized fields |
| **Still needed** | When still_needed_fields present | List of humanized fields |
| **Handoff pending** | handoff_ready=true, no case | "Ready to save" or similar |
| **Case exists** | case_id present | Case ID, case_status |
| **Lifecycle / office status** | When case | case_status: New, Reviewing, Waiting client, Done |

---

## 2. Practical Display Rules

- **No clutter**: Show only when relevant
- **Customer Entry**: Always show collection_stage; show collected/still_needed when non-empty
- **Broker Workbench**: Show case_status, waiting_on; show collected/still_needed in case detail
- **Lifecycle tag**: Use existing case_status; add "Collecting" when no case and not handoff_ready

---

## 3. In-Progress vs Handoff vs Office-Follow-Up

| State | Indicator |
|-------|-----------|
| **Collecting** | collection_stage=collecting; "Collecting info" tag |
| **Ready for handoff** | collection_stage=enough_for_handoff; "Ready for handoff" tag; case_creation_suggested |
| **Handed off** | case_id exists; case_status=new |
| **Office follow-up** | case_status in (reviewing, waiting_client, done) |

---

## 4. Implementation Notes

- Reuse existing Tags for collection_stage (green=handoff, default=collecting)
- Ensure collected_fields / still_needed_fields always visible in case detail when present
- Add lifecycle_status to case display when available (derived from case_status)

---

*See: 06_EXECUTION_OUTLINE.md*
