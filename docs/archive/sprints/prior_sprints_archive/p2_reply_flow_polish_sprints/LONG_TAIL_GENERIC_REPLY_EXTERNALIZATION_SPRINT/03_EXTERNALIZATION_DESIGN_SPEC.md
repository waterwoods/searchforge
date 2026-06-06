# Externalization Design Spec

## Strategy
- Reuse existing `reply_templates` + per-client `reply_overrides` merge path.
- Keep engine fallback literals as safety net.
- No cross-client fallback for overrides (existing behavior preserved).
- Externalize wording only; logic remains in `triage.py`.

## New Wording Keys
- `missing_signature`
- `underwriting_followup`
- `renewal_reminder`
- `informational`

Each key stores:
- `zh`: Chinese customer-facing draft
- `en`: English customer-facing draft

## Config Locations
- Industry base:
  - `configs/industries/insurance/reply_templates.json`
- Client B overrides:
  - `configs/clients/socal_precision/reply_overrides.json`
- Client A override file kept empty for these keys:
  - `configs/clients/chen_kui/reply_overrides.json`

## Fallback Behavior
- If industry key missing: use existing hardcoded fallback literal in `triage.py`.
- If client override key missing: use industry key.
- No override spillover across clients.

## Risk Level
- Low risk:
  - no change to category classification,
  - no change to handoff thresholds,
  - no change to control flow.
- Only customer-visible wording source moved to config.
