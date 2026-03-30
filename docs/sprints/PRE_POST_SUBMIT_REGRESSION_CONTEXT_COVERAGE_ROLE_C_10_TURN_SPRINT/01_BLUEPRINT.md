# PRE/POST-SUBMIT REGRESSION + CONTEXT COVERAGE + ROLE C 10-TURN — Blueprint

## Intent

Lock Add-Car **pre-submit vs post-submit** reply behavior against the two-layer standard, close the highest-leverage **context** gap in live batteries (missing `case_id` / persisted truth), then **pressure-test** with longer Role C runs.

## Non-goals

No product redesign, no CRM/workflow engine scope, no new non–Add-Car surfaces, no large simulation platform.

## Loops (execution)

1. **Gap check** — Confirm routing uses `reply_truth_context` from case when `case_id` is present; identify battery paths that never persisted / never passed `case_id`.
2. **Regression + patches** — Add a small in-process oracle pack; extend Role C caps and battery **truth-chain** mode.
3. **Live 10-turn runs** — At least four personas × 10 Role C turns with optional formal-submit inject.
4. **Harvest + rank** — Group issues; rank top trust/demo risks.
5. **Founder summary** — Decision questions answered in `03_FINAL_REPORT.md` and chat output.

## Success criteria

- Guardrail includes deterministic pre/post-submit wording checks (LLM off).
- Role C HTTP path allows **10** simulated customer turns plus **buffer** for one injected formal-submit line.
- Live battery can run with **`case_id` after persist** so post-submit phrasing is actually exercised.
