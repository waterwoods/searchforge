# Execution Outline

## Loop 1 — Audit

- Scan `triage.py` customer-facing handoff overlays.
- Confirm already externalized families to avoid overlap.
- Select 3-family small batch with high visibility and low logic risk.

## Loop 2 — Externalization design

- Define stitched keys and fallback semantics.
- Confirm per-client key placement and no cross-client fallback.

## Loop 3 — Implementation

- Wire selected phrases in `triage.py` through `_stitched_customer_visible_line()`.
- Add key blocks for `chen_kui` and `socal_precision`.
- Keep defaults in code as backup.

## Loop 4 — A/B simulation

- Create small-batch scenario battery.
- Add script runner aligned with existing A/B runner style.
- Include negative, fallback, and flagship checks.

## Loop 5 — Regression + guardrail

- Run new small-batch battery
- Run directly affected existing A/B runners
- Run Add-Car stress battery
- Run full `guardrail_inbox_triage.sh`

## Loop 6 — Founder summary

- Document moved vs deferred vs keep-in-code.
- Report portability and risk judgment.
