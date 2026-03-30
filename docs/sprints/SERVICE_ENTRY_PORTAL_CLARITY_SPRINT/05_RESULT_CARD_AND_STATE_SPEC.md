# Result card and state spec

## Pre-handoff (“still in intake”)

**Progress card** (existing):

- Shows **主题**, **报价状态** (if any), **已收集**, **还需**, **下一步建议**, lifecycle tag.
- **Title row**: add-car uses `add_car_progress_card_title`; otherwise `portal_generic_progress_title`.
- **Annotation**: `portal_progress_annotation` — frames updates as **state tied to报送**, not live chat hype.

**Thread card**:

- Role labels emphasize **报送** vs **办公室整理回复**.

## Post-handoff (“case submitted”)

**Closure card** (existing green card):

1. Optional add-car status badge (`handoff_status_badge_add_car`).
2. **Closure headline** (`handoff_closure_headline_*`).
3. Case focus tags + one-liner (logic unchanged).
4. **Recorded snapshot** (add-car): `handoff_received_summary_title_add_car`, intro, 已记录项 / 办公室后续可能还需.
5. **Timing** alert: `handoff_office_followup_timing_add_car`.
6. **Summary block**: label from `portal_closure_reply_summary_label` (**办公室办理摘要**) + draft text.
7. **Processing** line + **case follow** lines (`handoff_case_created_line` / `handoff_case_pending_line`).
8. Collapsible **same-request append** (`handoff_same_request_*`).
9. **Boundary hint** + CTAs: **查看工作台**, **提交新问题**.

## What “stronger case result” means here

- User sees **headline + 记录摘要 + 办公室办理摘要 + 跟进时间 + 服务记录** language—not a single green bubble that feels like “the bot replied.”

## Logic boundary

- No change to when `handoff_ready` is set or what the API returns; **display labels and section copy only**.
