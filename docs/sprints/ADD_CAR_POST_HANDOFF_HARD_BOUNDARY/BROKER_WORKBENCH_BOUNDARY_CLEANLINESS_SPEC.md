# Broker Workbench Boundary Cleanliness Spec

## Goals

Brokers should see at a glance:

- Whether a follow-up is **still the same service record** vs **likely a new issue**.
- Whether **human confirmation** on topic boundary is recommended.

## Recent-case list cards

When `case_activity[0].activity_type === follow_up_added`:

| Condition | Tag |
|-----------|-----|
| `case_boundary === new_issue` | **追加 · 疑似新事项** (volcano) |
| `case_boundary === borderline` | **追加 · 边界待确认** (gold) |
| Otherwise | **追加 · 同一条服务记录** (cyan) |

## Case detail sheet

Existing **线索边界** tags remain when `case_boundary` is set:

- `new_issue` → “可能新事项”  
- `borderline` → “建议人工确认”  

`broker_next_step` and `conversation_summary` carry machine-readable boundary prefixes for scanning.

## Append input (workbench)

Unchanged: brokers paste customer follow-up; backend runs `triage_for_append` and persists boundary fields.
