# Long-Tail Generic Customer Reply Externalization Sprint Blueprint

## Goal
- Externalize the next small batch of lower-frequency but customer-visible generic reply wording.
- Preserve existing triage control flow and handoff logic.
- Strengthen A/B isolation between `chen_kui` and `socal_precision`.

## In Scope
- Audit remaining hardcoded long-tail customer-visible lines in `services/fiqa_api/inbox_triage/triage.py`.
- Externalize 2-4 safe wording families via existing reply-template/override pattern.
- Add A/B scenario battery and runner.
- Validate no regressions on guardrail and prior key batteries.

## Out Of Scope
- Rewriting `triage.py` architecture.
- Moving control logic into JSON.
- Framework changes, OCR/carrier API work, UI redesign.

## Chosen Small Batch
- `missing_signature`
- `underwriting_followup`
- `renewal_reminder`
- `informational`

## Why This Batch
- All four are customer-visible, generic, lower-frequency lines.
- They are currently hardcoded and can leak shared office voice.
- They are wording-only and isolated from decision logic, so low-risk.
