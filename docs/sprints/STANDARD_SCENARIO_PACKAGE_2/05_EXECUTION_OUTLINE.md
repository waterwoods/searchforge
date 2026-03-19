# Execution Outline — Package 2.0 Sprint

**Sprint:** Standard Scenario Package 2.0

---

## 1. Workstreams

| Workstream | Scope |
|------------|-------|
| **Conversation summary** | Improve _build_conversation_summary for add-car, missing_document, payment, renewal |
| **Broker next step** | Improve broker_next_step when "already sent" / "already paid" |
| **Collected / still needed** | Improve _missing_document_structured_fields, _cancellation_structured_fields for "client says sent" |
| **Handoff phrases** | Ensure other_received, other_corrected used correctly; add "verify receipt" when client says sent |
| **Guardrails** | Add scenarios to inbox_triage_scenarios.json for Package 2.0 edge cases |

---

## 2. Implementation Order

1. **Loop 1:** Conversation summary + broker_next_step for missing_document and payment (already_sent / already_paid)
2. **Loop 2:** Add-car summary clarity + renewal premium handoff when bill sent
3. **Loop 3:** Talk to Agent mid-flow; collected/still_needed accuracy; final coherence

---

## 3. Test Plan

After each loop:
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` (if applicable)
- `bash scripts/guardrail_inbox_triage.sh`
- `cd ui && npm run build`

---

## 4. Loop Plan

- **Loop 1:** Deepen missing_document + payment (already_sent, already_paid) — summary, broker_next_step, collected/still_needed
- **Loop 2:** Deepen add-car summary + renewal premium handoff
- **Loop 3:** Talk to Agent mid-flow; tighten package coherence; one better guardrail

---

*End of Execution Outline*
