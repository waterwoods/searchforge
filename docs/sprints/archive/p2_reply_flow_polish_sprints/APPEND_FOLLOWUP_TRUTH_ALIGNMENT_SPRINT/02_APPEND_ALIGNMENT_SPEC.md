# Append / follow-up alignment spec

## Current weakness (pre-sprint)

1. **`triage_for_append`** forced `lifecycle_status = handoff_pending` even for persisted, formally submitted cases — semantically pre-submit despite `case_store.append_follow_up_message` later writing `office_followup`.
2. **`_reply_truth_context_from_case`** only passed `formal_submitted_at` / `lifecycle_status`, not **`still_needed_fields`** — short append bubbles could omit gaps in merged extraction while the **case** still carried them, weakening intent ceiling (e.g. quote-detail + missing contact).
3. **Generic `add_car` intent** on an append with post-submit truth could still select the **flagship** phrase key before `_effective_add_car_handoff_storage_key` maps to `*_submitted` — risk of **submit-nag** tone vs **supplement_submitted** pools.

## Target append truth model

- **Existing truth:** Office-visible record exists (`formal_submitted_at` set); append is an **update** to that record.
- **Current message:** Supplement, correction, question, or materials claim on **that** record — not a new intake.
- **Lifecycle in append triage:** **`office_followup`** whenever formal submit truth or explicit append flag is present — not **`handoff_pending`**.
- **Intent truth bundle:** Union of **structured gaps from merged thread** and **persisted case `still_needed_fields`** for ceiling checks.
- **Reply:** Continue to use **post-submit** packs / fallbacks; avoid **“请先正式提交办公室”** when the record is already formally submitted.

## Bounded fixes implemented

1. **`_reply_truth_context_from_case`:** Adds `still_needed_fields` from case and **`service_record_append: True`**.
2. **`triage_for_append`:** Sets **`office_followup`** when `formal_submitted_at` or `service_record_append` is present.
3. **`_resolve_add_car_handoff_phrase_key`:** Merges extracted `still_needed` with case list (deduped).
4. **`nudge_append_generic_to_supplement_intent`:** When append + post-submit + generic flagship key, route to **`add_car_supplement`**.
5. **Tests:** `tests/test_append_truth_alignment.py`, `tests/test_add_car_intent.py` nudge tests; **`scripts/test_inbox_triage_api.py`** append assertions (lifecycle, no submit nag, `updated_at`).

## Acceptance criteria

- [x] Append triage result uses **`office_followup`** for formally submitted / append-flagged cases.
- [x] Persisted case after append still has **unchanged `formal_submitted_at`** and **non-empty `updated_at`** (API script).
- [x] Append customer draft **does not** contain the canonical pre-submit nag phrase **「请在入口完成「正式提交办公室」」** when a case already exists from formal submit flow.
- [x] Case **`still_needed_fields`** participates in **quote-detail intent** notes when the last bubble alone would not restate gaps.
- [x] **Generic append + post-submit** can be nudged to **supplement** phrase family.

## Remaining gaps (honest)

- **LLM path** may still produce collection-style lines if extraction disagrees with case; not fully unified in this sprint.
- **Non–Add-Car** append behavior unchanged.
- **Explicit intent artifact** in API for every turn remains a future sprint (three-layer spec §H).
