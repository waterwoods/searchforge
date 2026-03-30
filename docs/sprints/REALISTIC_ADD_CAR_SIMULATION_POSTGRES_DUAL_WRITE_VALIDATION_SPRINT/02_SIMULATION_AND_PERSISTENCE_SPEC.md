# Simulation, persistence, and observation spec

## Simulation battery categories

| ID | Category | Example thrust | What it tests |
|----|----------|----------------|---------------|
| B1 | Happy-path direct Add-Car | Full vehicle + zip + pickup + driver + quote ask | Intent, slot fill, `quote_ready_status`, handoff, PG row shape |
| B2 | Already sent / 微信 | Materials claimed sent; mixed doc/VIN wording | `customer_says_materials_sent`, completeness, `almost_ready` vs driver/date gaps |
| B3 | VIN not ready | “VIN还没拿到…可以先报吗” | `materials_still_pending`, quote path without VIN |
| B4 | Spouse / second driver | Spouse may drive; second driver ask | Primary driver + household nuance in summary/steps |
| B5 | Correction / 改口 | Wrong pickup day corrected in same message | Last-utterance merge; `delivery_date` |
| B6 | Price-sensitive / re-shop | Too expensive; change carrier or coverage | Risk of non–Add-Car routing; field starvation |
| B7 | “还缺什么” | Follow-up style: what is still missing | Continuation vs `missing_document` false positive |
| B8 | Short low-information | “想加车” | `need_more`, guarded handoff |
| B9 | Multi-turn (in-memory history) | Vague first line + detailed second | Merge + `materials_send_question` / pending signals |
| B10 | Multi-turn append | Open case + follow-up with VIN + 微信 | `append_follow_up_message` + extra `record_messages` + `state_history` |

## Structured data success criteria

- `issue_category` and Add-Car slot fields (`collected_fields` / `still_needed_fields`) are directionally correct for office use.
- `conversation_summary` / `title_summary` in Postgres reflects vehicle and context, not generic noise.
- `quote_ready_status` aligns with obvious gaps (e.g. missing name/phone still flagged where expected).

## Postgres validation criteria

With `SERVICE_RECORD_DATABASE_URL` (or `DATABASE_URL`) set and `UNIFIED_INTAKE_PG_DUAL_WRITE` truthy:

- One `service_records` row per `save_case` (and append updates same `record_id`).
- `record_messages` row count matches customer (+ system when present) messages; append uses upsert semantics on `(record_id, external_message_id)`.
- `structured_record_data.structured_payload` contains triage keys mirrored from `_build_structured_payload`.
- `state_history` receives at least `case_created` on new case and `conversation_appended` on append.
- `missing_fields_summary` column reflects `still_needed_fields` when populated (post-sprint fix).

## State / flow observation criteria

- `handoff_ready` vs API `persist_case` behavior: production only persists when `handoff_ready` unless explicitly forcing save for diagnostics.
- `broker_next_step` readable as next office action.
- Append path sets `lifecycle_status` to office follow-up semantics in JSON (`office_followup`).

## Acceptance criteria

- [x] Battery executed with documented scenarios.
- [x] Postgres path exercised on a **real** disposable Postgres instance (not mocked).
- [x] Gaps named concretely (especially misclassification and API vs forced-save).
- [x] At most one small, justified persistence improvement; guardrail passes.
