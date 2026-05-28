# HANDOFF REPLY VARIETY + TRUTH ALIGNMENT — Final report

## What was implemented

- **Add-car post-handoff reply families** (bounded rule layer in `triage.py`): `timeline_process`, `quote_detail`, `supplement` (turn 2+), `correction`, plus existing paths for **materials sent**, **doc clarification**, **coverage side question**, and **default** `add_car`.
- **Turn-aware supplement:** first customer bubble in a thread uses **flagship** `handoff.add_car` line; “补充” wording applies from **turn 2+** when intent is incremental `new_info`.
- **Variety:** optional `zh_alt` / `en_alt` on `add_car` for even customer-turn indices (config-driven).
- **Truth:** append `stitched.handoff_add_car_contact_gap_tail` when quote-ready / almost-ready but **name or phone** still missing from the record.
- **Client packs:** `configs/clients/chen_kui/handoff_phrases.json` and `configs/clients/socal_precision/handoff_phrases.json` — new keys `add_car_supplement`, `add_car_timeline`, `add_car_quote_detail`, `add_car_correction`, `zh_alt`/`en_alt`, `handoff_add_car_contact_gap_tail`.
- **Config loader** docstring updated for new keys.

## What remains partial

- **Non–add-car** generic handoff lines still use existing `other` / `other_clarification` buckets; timeline/quote-detail families are **add-car first** in this sprint.
- **NLU depth:** classification is marker-based; edge cases may still map to `default`.
- **English** parity for families depends on client `en` strings.

## What still depends on backend/state quality

- `still_needed_fields` / contact gap only as strong as `_add_car_structured_fields` and extraction.
- **LLM** triage path inherits the same handoff overlay after rule result; behavior is unchanged in structure but **draft** content still comes from the handoff phrase layer when `handoff` is true.

## Recommended next sprint

- **Workbench echo:** surface `follow_up_type` / handoff family in operator UI for debugging live sessions.
- **Non–add-car** post-handoff families (renewal/payment) if pilot traffic shows the same repetition.

## Validation

- `bash scripts/guardrail_inbox_triage.sh` — **PASS** (rule + simulations + residual A/B + cross-client).
