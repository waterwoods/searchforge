# PERSIST / FORMAL-SUBMIT — Alignment spec

## Current mismatch (before)

- `persist_case` + `handoff_ready` immediately called `save_case`, returning `case_id` and workbench-visible rows.
- Triage still exposed `lifecycle_status: handoff_pending` in the same turn, while persistence behaved like “already handed off.”
- UI partially compensated (`isFormalSubmissionToOfficeComplete` ignored `case_id` when `handoff_pending`), but the office queue could still show the record early.

## Target aligned model

| Phase | Customer / session | Office-visible case |
|--------|-------------------|---------------------|
| Collecting | `handoff_ready: false` | No |
| Ready (`handoff_pending`) | `handoff_ready: true`, no `case_id` from triage persist | No |
| Formal submit | Customer action sends `formal_submit: true` | Yes — `save_case`, `handed_off` in store |

**Broker channel:** Direct paste / demo loader sends `formal_submit: true` so one-shot intake still creates a case when rules say handoff.

**Formal-submit-only last turn:** Triage may return `handoff_ready: false` on boilerplate; persistence is allowed when `formal_submit` and rule-based Add-Car completeness (`_add_car_enough_for_handoff` on labeled thread) match the same bar as handoff.

## Acceptance criteria

1. Full Add-Car thread with `persist_case: true` and `formal_submit: false` yields **no** `case_id` while `lifecycle_status` is `handoff_pending`.
2. Same thread with `formal_submit: true` yields `case_id` and stored `lifecycle_status: handed_off`.
3. Non–Add-Car flows (e.g. missing_document) still persist on `handoff_ready` without `formal_submit`.
4. Guardrail + `scripts/test_inbox_triage_api.py` pass; production two-step smoke passes.
