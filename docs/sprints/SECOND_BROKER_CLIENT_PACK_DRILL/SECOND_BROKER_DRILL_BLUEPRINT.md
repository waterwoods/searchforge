# Second Broker Drill Blueprint

## Mission

Prove or falsify: *For a second broker in the same insurance category, we can mostly swap client-specific behavior through **client pack configuration**, with only minimal core-engine changes.*

This is a **drill**, not production onboarding and not multi-tenant platform work.

## Non-goals

Cross-industry portability, LangGraph replacement, OCR, carrier APIs, auth/tenancy, large UI redesign.

## Drill broker (fictional)

- **client_id:** `socal_precision`
- **Positioning:** Southern California, Chinese-speaking, California auto — same category as Chen Kui.
- **Differentiation:** Concise copy, explicit **营业日 / business-day** language, **本所 / 本事务所** identity instead of generic 办公室; quick-start labels like **加车核价** vs **获取报价**.

## What we validate

1. `GET /api/inbox/client-config?client=socal_precision` serves distinct UI copy.
2. `POST /api/inbox/triage` with `client_id: socal_precision` uses that client’s handoff phrases and merged reply templates.
3. Where the engine still injects **办公室** or Chen-specific markers, we record it as a **portability gap**, not hidden success.

## Minimal code touched in this sprint

- **Industry marker:** add `转接人工` to `talk_to_agent` markers (and triage fallback) so second-broker UI wording (“转接人工”) still triggers human-intent detection. This is broker-agnostic and low risk.
- **No** new tenant tables, **no** auth, **no** refactor of `triage_conversation` state machine.

## Artifacts

- Config pack: `configs/clients/socal_precision/`
- Scenarios: `drill_scenarios.json`
- Runner: `scripts/run_second_broker_drill.py`
