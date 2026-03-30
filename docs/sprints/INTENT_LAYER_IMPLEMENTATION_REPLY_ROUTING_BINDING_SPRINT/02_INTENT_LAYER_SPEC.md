# Add-Car Intent Layer — Spec (implemented)

## Intent families

| Family | Meaning |
|--------|---------|
| `supplement_info` | Customer adds new facts (late turn, non-questioning bubble). |
| `correction` | Customer corrects prior information (`follow_up_type` / markers). |
| `timeline_question` | Timing, process, what happens next. |
| `quote_detail_question` | Deductible, coverage options, limits (not the narrow coverage-adjust side path). |
| `materials_claim` | Customer claims materials were sent (`already_sent` path) without a primary “did you receive?” ask. |
| `office_receipt_question` | Whether the office received / saw the record / queue visibility. |
| `generic_followup` | Default / flagship handoff line when no finer family applies. |

## Truth constraints

- **Office receipt:** If `formal_submitted_at` / post-submit lifecycle is absent, intent may still be `office_receipt_question`, but copy must **not** claim the office already holds the durable record. Routing uses `add_car_office_receipt` (pre-submit phrasing) vs `add_car_office_receipt_submitted` when truth allows post-submit phrasing (`_truth_allows_post_submit_handoff_phrasing` + `_effective_add_car_handoff_storage_key`).
- **Quote detail:** When `still_needed_fields` is merged from the thread, a truth note is attached for reviewers (completeness not implied).
- **Materials:** When only customer-claimed send, truth notes record that office verification is still pending.

## Routing model

1. Merge `still_needed_fields` from `_add_car_structured_fields(merged_text)` into a truth dict for intent.
2. `resolve_add_car_turn_intent(...)` → `handoff_base_key` (`add_car`, `add_car_supplement`, `add_car_timeline`, `add_car_quote_detail`, `add_car_correction`, `add_car_office_receipt`).
3. Triage picks `handoff_phrases.json` blocks and applies post-submit `_submitted` variants when truth allows.
4. API: `add_car_turn_intent` = `{ intent_family, handoff_base_key, truth_notes }`.

## Tests / acceptance

- `tests/test_add_car_intent.py`: distinct routing for timeline vs quote-detail; office-receipt vs materials; pre-submit truth notes; supplement on late materials turns.
- `bash scripts/guardrail_inbox_triage.sh` must pass.
