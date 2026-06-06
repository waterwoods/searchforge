# Add-Car High-ROI Extraction + Intent Guard Fix — Blueprint

## Mission

Harden Unified Intake / Add-Car **without** “smarter AI” vagueness: **extract → normalize → validate**, lexicon coverage, and **statement vs question** guards before `already_sent`.

## Three weaknesses (scenario battery)

| Area | Symptom | Risk |
|------|---------|------|
| ZIP | `邮编95131` missed | Quote pipeline stalls on “missing zip” |
| Driver | `我自己开`, `儿子开`, etc. missed | Premature handoff or wrong broker step |
| `already_sent` | `要不要发你` matched `发你` | Wrong warm “verify sent materials” path |

## Non-goals

OCR, carrier API, frontend redesign, non–Add-Car features, large architecture rewrites.

## Implementation anchors (code)

- `services/fiqa_api/inbox_triage/triage.py`: ZIP signal regex, driver lexicon, `_is_prospective_send_offer_message`, `_derive_follow_up_type` ordering.
- Regression: `regression_scenarios.json` + `scripts/run_add_car_high_roi_regression.py`.

## Success definition

- Listed phrases extract or classify as specified.
- Existing audit / battery / guardrails stay green.
- Broker-facing copy stays office-realistic; changes are explainable in one sentence each.
