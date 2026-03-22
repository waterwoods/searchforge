# Execution Outline

## Loop 1 — Audit

- Reviewed `triage_conversation`, `triage_for_append`, `append_follow_up_message`, `_detect_secondary_intent_hint`, `WORKFLOW_STATE_KEYS`.
- **Finding:** Append always forced handoff but did not distinguish **same thread / new issue** for customer or broker.

## Loop 2 — Design

- Defined prior domain + last-message domains + cross matrix.
- Added pivot lexicon and exceptions (coverage side question, vehicle correction vs topic pivot).

## Loop 3 — Implement

- Implemented `_classify_append_case_boundary` + `_apply_append_case_boundary` in `triage.py`.
- Wired into `triage_for_append`.
- Persisted `case_boundary` on append; workbench tags in UI.

## Loop 4 — Simulate

- Added JSON pack + `run_case_boundary_battery.py`.
- Fixed ordering bugs (clarification/correction vs cross-domain).

## Loop 5 — Evaluate + regress

- `bash scripts/guardrail_inbox_triage.sh` — PASS (includes new `[7c]` step).

## Time box

~60–90 min target: focused on append path and broker-visible semantics; no ticketing product.
