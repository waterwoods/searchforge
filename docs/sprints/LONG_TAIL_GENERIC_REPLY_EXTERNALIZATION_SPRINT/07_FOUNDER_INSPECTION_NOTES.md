# Founder Inspection Notes

## What Changed
- Moved four long-tail customer-visible reply families from hardcoded-only output to config-backed wording:
  - `missing_signature`
  - `underwriting_followup`
  - `renewal_reminder`
  - `informational`

## Why It Is Commercially Useful
- Reduces subtle shared-voice leakage across same-industry clients.
- Improves polish on less-common but visible replies.
- Increases confidence that client pack swaps can preserve business logic while changing tone.

## Why Risk Stayed Low
- No changes to triage category classifier or handoff logic.
- Existing fallback literals preserved in code.
- Reused proven merge path (`industry templates` -> `client overrides`).

## What To Inspect Quickly
- `triage.py` now checks template keys first for those four categories in zh/en.
- `reply_templates.json` contains baseline defaults.
- `socal_precision/reply_overrides.json` contains differentiated tone for those keys.
- New long-tail A/B battery includes anti-leak checks plus add-car no-regression check.
