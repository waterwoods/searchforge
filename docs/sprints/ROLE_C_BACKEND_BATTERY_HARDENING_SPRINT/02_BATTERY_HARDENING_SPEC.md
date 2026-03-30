# ROLE C BACKEND BATTERY HARDENING — Spec

## Desired battery qualities

1. **Trace:** Every step records turn index, customer/reply text (clamped), `lifecycle_status`, `still_needed_fields`, `handoff_ready`, `add_car_turn_intent` (when present), session `case_id`, observed `formal_submitted_at` / `updated_at` after inject, and `injected_formal_submit` for truth-chain rows.
2. **Warnings:** Bounded heuristics aligned with Truth → Intent → Reply; false positives acceptable if labeled as signals.
3. **Summary:** Per-run aggregation: warning counts by layer, turns with warnings, top warning codes.

## Chosen warning / oracle categories

| Code | Layer | Meaning |
|------|--------|
| `STATE_INFO` | state | Truth-chain inject row (informational) |
| `TRUTH_PRE_SUBMIT_OFFICE_RECEIPT` | truth | Forbidden office-receipt phrasing pre-submit (inject turn exempt) |
| `TRUTH_HANDOFF_READY_CONTACT_GAP` | truth | `handoff_ready` while `name`/`phone` still in `still_needed_fields` |
| `REPLY_POST_SUBMIT_FORMAL_NAG` | reply | Post-submit reply still nags portal formal submit |
| `REPLY_REPEATED_BLOCK` | reply | Same reply stem four turns in a row |
| `REPLY_CONTACT_GAP_TAIL_MISMATCH` | reply | Contact-gap tail with non-generic / non-receipt intent |
| `INTENT_LATE_GENERIC` | intent | Turn ≥7, long customer line, `generic_followup` |
| `INTENT_STICKY_GENERIC` | intent | Repeated `generic_followup` on non-trivial customer text |
| `STATE_POST_SUBMIT_LIFECYCLE_COLLECTING` | state | Runner has `case_id` but `lifecycle_status` is `collecting` |

## Run expectations

- **API contract:** `POST /api/inbox/simulation-role-c-customer` must allow `max_turns` large enough for 10-turn batteries with truth-chain buffer (repo uses `le=12`). Older servers capped at `8` will reject `12`; use a current `fiqa_api`, reduce turns / disable truth-chain, or set optional `ROLE_C_SIMULATION_MAX_TURNS=8` knowing 10-turn runs may fail partway.
- **Environment:** `ROLE_C_BATTERY_BASE_URL` (default `http://127.0.0.1:8001`), `OPENAI_API_KEY` on backend for Role C.

## Acceptance criteria

- [x] Battery emits enriched trace + `run_summary` + `warnings_flat`.
- [x] At least one bounded live run of three sprint_10_turn variants (C1, C3, C4) completed.
- [x] Sprint docs: blueprint, spec, final report.
