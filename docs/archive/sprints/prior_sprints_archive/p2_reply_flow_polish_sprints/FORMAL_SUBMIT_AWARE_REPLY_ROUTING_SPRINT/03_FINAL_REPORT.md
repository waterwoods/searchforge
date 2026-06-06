# FORMAL-SUBMIT–AWARE REPLY ROUTING — Final report

## Implemented

- **`reply_truth_context`** on `triage_conversation`: gates post-submit phrasing via `formal_submitted_at`, `lifecycle_status` (`handed_off` / `office_followup`), and `formal_submit_this_turn` (Add-Car formal-submit API flag).
- **`_truth_allows_post_submit_handoff_phrasing`**: never true from `handoff_ready` alone.
- **Handoff key resolution**: base family from existing classifier → `_effective_add_car_handoff_storage_key` prefers `add_car_*_submitted` when gated; pack gaps use **`_POST_SUBMIT_ADD_CAR_FALLBACK_ZH_EN`** (overrides pre-submit pack lines when post-submit truth holds but `*_submitted` keys are missing).
- **Stitched paths**: doc-clarification suffix, coverage suffix, clarification followup, materials-sent — post-submit variants via `_stitched_customer_visible_line_prefer` + pack keys or inline post defaults.
- **Lifecycle**: `lifecycle_status` → `handed_off` when `formal_submit_this_turn` on Add-Car handoff (matches imminent persist).
- **API**: `TriageRequest.case_id` loads case and merges truth context; **`triage_for_append`** passes context from the loaded case.
- **Client packs**: `chen_kui` and `socal_precision` — full `add_car_*_submitted` handoff blocks + stitched `*_submitted` keys.
- **UI**: `triageMessage(..., caseId)` and portal `submitMessage` passes `lastCaseId` so continued triage on the same record can route post-submit when the backend has the case.

## Partial / dependencies

- **Truth quality**: If `case_id` is wrong or stale, routing follows **loaded** case truth—callers must send the correct id.
- **Scripts / offline tests** that call `triage_for_append` without a real case object still omit context unless they pass `reply_truth_context`; behavior reverts to pre-submit phrasing (safe but weak).
- **Non–Add-Car** lanes unchanged.

## Recommended next sprint

- **Regression pack**: explicit scenarios asserting substring presence/absence for pre vs post-submit Add-Car (rule path, no LLM).
- **Optional**: pass `reply_truth_context` from batteries that simulate append without `save_case` for stricter CI coverage.

## Validation

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (2026-03-29).
- Ad-hoc: `triage_conversation` with `formal_submit_this_turn` and with `formal_submitted_at` + supplement message — post-submit drafts confirmed.
