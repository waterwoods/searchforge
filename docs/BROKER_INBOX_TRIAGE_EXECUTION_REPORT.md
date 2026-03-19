# Broker Inbox Triage Assistant – Long Execution Cycle Report

**Date:** 2026-03-07  
**Cycle:** First MVP definition and prototype

---

## 1. Product definition

| Doc | Location | Defines |
|-----|----------|---------|
| Master goal | `docs/goals/BROKER_INBOX_TRIAGE_MASTER_GOAL.md` | Mission, user, input/output, success criteria, constraints |
| Quality standard | `docs/standards/BROKER_INBOX_TRIAGE_STANDARD.md` | Output shape, categories, urgency, client draft rules, escalation |
| Runbook | `docs/runbooks/BROKER_INBOX_TRIAGE_RUNBOOK.md` | Workflow, dev loop, scenario runner, guardrail |
| Guardrails | `docs/guardrails/BROKER_INBOX_TRIAGE_GUARDRAILS.md` | Scenario pack, output shape, weak output detection |
| Scenarios (human) | `docs/BROKER_INBOX_TRIAGE_SCENARIOS.md` | 12 scenarios with expected outputs |
| Scenarios (machine) | `configs/inbox_triage_scenarios.json` | JSON scenario pack for runner |

---

## 2. MVP workflow

```
Input (pasted message) → Classify → Urgency → Manual follow-up? → Broker next step → Client prep → Client reply draft → Output
```

All six outputs produced in one pass. LLM when enabled; rule-based fallback when `LLM_GENERATION_ENABLED` is off.

---

## 3. Scenario pack

- **Count:** 12 scenarios
- **Categories:** missing_signature, missing_document, cancellation_warning, policy_delay_pending, underwriting_followup, renewal_reminder, customer_question, payment_lapse_expiration, informational, unclear
- **Location:** `configs/inbox_triage_scenarios.json`, `docs/BROKER_INBOX_TRIAGE_SCENARIOS.md`

---

## 4. MVP prototype

| Component | Location | Status |
|-----------|----------|--------|
| Triage logic | `services/fiqa_api/inbox_triage/triage.py` | Working: LLM + rule-based fallback |
| Scenario runner | `scripts/run_inbox_triage_scenarios.py` | Working: 12/12 pass with rule-based |
| CLI | `scripts/inbox_triage_cli.py` | Working: single-message triage |
| Guardrail | `scripts/guardrail_inbox_triage.sh` | Working: scenario pack + output shape |

**Weak / placeholder:** Rule-based fallback is keyword-driven; LLM produces richer drafts when enabled. No API route yet; no UI.

---

## 5. Validation loops completed

| Loop | Target | Change | Result |
|------|--------|--------|--------|
| 1 | S2 category mismatch (underwriting vs missing_document) | Reordered rules: document-request patterns before underwriting | 12/12 pass |
| 2 | Output shape | Added `_validate_output_shape()` to scenario runner | All results have 6 required fields |

---

## 6. Guardrails added

| Check | Script | Protects |
|-------|--------|----------|
| Scenario pack exists | `guardrail_inbox_triage.sh` | Config file present |
| Scenario pack passes | `run_inbox_triage_scenarios.py` | Category, urgency, manual_followup match expected |
| Output shape | `run_inbox_triage_scenarios.py` | All 6 fields present, non-empty, correct types |

---

## 7. Manual-work reduction

| Before | After |
|--------|-------|
| Andy explains inbox triage scope | `BROKER_INBOX_TRIAGE_MASTER_GOAL.md` defines it |
| Andy defines output shape | `BROKER_INBOX_TRIAGE_STANDARD.md` defines it |
| Andy runs scenarios manually | `run_inbox_triage_scenarios.py` + `guardrail_inbox_triage.sh` |
| Cursor guesses workflow | Runbook documents dev loop |
| OpenClaw validates ad hoc | Scenario pack + guardrail for regression |

---

## 8. Current readiness

- **Internal review:** Yes. MVP is defined, implemented, and guarded.
- **Biggest gap:** No API route or UI; broker must use CLI or integrate manually. LLM path requires `LLM_GENERATION_ENABLED=1` and `OPENAI_API_KEY`.

---

## 9. Recommended next cycle

**One clear next step:** Add a minimal API route `POST /api/inbox/triage` that accepts `{"text": "..."}` and returns the triage result, so the demo UI or a simple test page can call it.

---

*End of report*
