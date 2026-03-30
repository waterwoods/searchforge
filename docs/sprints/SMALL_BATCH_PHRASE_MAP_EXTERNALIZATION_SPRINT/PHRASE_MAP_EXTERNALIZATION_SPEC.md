# Phrase Map Externalization Spec

## Strategy

Reuse existing per-client stitched phrase map in `configs/clients/<client_id>/handoff_phrases.json`:

- key path: `stitched.<key>.{zh,en}`
- loader: existing `get_stitched_handoff_phrases()`
- runtime: existing `_stitched_customer_visible_line()`

No framework changes. No new config loader path.

## New phrase keys

1. `handoff_doc_clarification_suffix_add_car`
2. `handoff_doc_clarification_suffix_other`
3. `handoff_add_car_coverage_answer`
4. `handoff_add_car_coverage_suffix`
5. `handoff_payment_correction_urgency`

## Storage location

- Client A: `configs/clients/chen_kui/handoff_phrases.json`
- Client B: `configs/clients/socal_precision/handoff_phrases.json`

## Fallback behavior

- If a key is missing, engine keeps current hardcoded default.
- No cross-client fallback.
- `demo_broker` exercises omitted-key behavior explicitly in A/B battery.

## A/B separation design

- `chen_kui`: retains existing office-forward voice.
- `socal_precision`: uses desk/business-day voice and avoids Chen Kui wording.

## Risk level

Low:
- wording-only substitution
- unchanged routing logic and handoff conditions
- existing helper and config pattern reused
