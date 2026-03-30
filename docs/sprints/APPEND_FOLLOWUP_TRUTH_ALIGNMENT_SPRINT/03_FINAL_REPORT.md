# APPEND / FOLLOW-UP TRUTH ALIGNMENT — Final report

## What was implemented

- **Route truth bundle** (`_reply_truth_context_from_case`): case `still_needed_fields` + `service_record_append` for append-only API.
- **`triage_for_append`:** `lifecycle_status` → **`office_followup`** when formal submit truth or append flag (not blanket `handoff_pending`).
- **Intent merge:** `_resolve_add_car_handoff_phrase_key` unions extracted gaps with persisted case gaps (deduped).
- **Intent nudge:** `nudge_append_generic_to_supplement_intent` in `add_car_intent.py` — append + post-submit + generic flagship → **`add_car_supplement`**.
- **Tests:** `tests/test_append_truth_alignment.py`; extended `tests/test_add_car_intent.py`; stricter **`scripts/test_inbox_triage_api.py`** append checks.

## What improved

- Append path is **truth-aligned with “record already exists”** in triage output (lifecycle), not only after `case_store` overwrite.
- **Short follow-up bubbles** can still carry **case-level gap** into intent ceiling for quote-detail / similar routes.
- **Generic continuation** on append is less likely to sit on **pre-submit flagship** wording.

## What remains weak

- **LLM / extraction drift** on edge threads can still produce collection-style customer copy; no full truth–reply reconciliation pass here.
- **Resolved intent** is not yet a first-class API field for every turn (three-layer §H).
- **Non–Add-Car** append semantics unchanged.

## Recommended next sprint

- **Intent anti-collapse (bounded):** explicit `resolved_intent` on API + stronger late-turn regression for long threads (per master outline and three-layer spec), still Add-Car–first.

## Validation

- `PYTHONPATH=. python3 -m pytest tests/test_append_truth_alignment.py tests/test_add_car_intent.py`
- `bash scripts/guardrail_inbox_triage.sh` — **PASS**
- HTTP `scripts/test_inbox_triage_api.py` append section — run with server on **8001** (not executed in this session if server down).
