# Broker Workbench — Boundary Handling Spec

## API / persistence

- Append path continues to set `lifecycle_status` = `office_followup`.
- When triage returns `case_boundary`, `append_follow_up_message` persists it on the case (`new_issue` | `borderline` | `same_case`).

## Broker-facing fields

- **`broker_next_step`:** English operational prefix so the workbench scan shows **split risk** before the normal next step.
- **`conversation_summary`:** Machine-readable boundary tag at the front for search/list views and human glance.
- **`human_confirmation_required`:** Set on **borderline** only; field token `case_topic_boundary`.

## UI (Unified Intake)

When `case_boundary` is present:

- `new_issue` → tag **线索边界 · 可能新事项**
- `borderline` → tag **线索边界 · 建议人工确认**

Shown alongside existing `secondary_issue_note` / summary block when structured fields are empty.

## Operational guidance

- **new_issue:** Decide whether to **split case record** or keep one thread with two broker tasks; triage category already reflects the latest message.
- **borderline:** Confirm with customer or internal notes before binding work to the wrong policy action.
