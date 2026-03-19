# Eight-Question Integration Audit — Execution Outline

**Sprint:** Eight-Question Integration Audit + Fix Sprint

---

## Audit Workstreams

| # | Workstream | Role | Assets to Inspect |
|---|------------|------|-------------------|
| 1 | Docs / knowledge | Product asset auditor | faq_handling_matrix.md, auto_insurance_faq_intake_corpus.json, HIGH_VALUE_QUESTION_REALISM_* |
| 2 | Backend / routing | Backend auditor | triage.py, config_loader, VALID_CATEGORIES, _is_* helpers |
| 3 | Scenario configs | Scenario auditor | inbox_triage_scenarios.json, customer_entry_multi_turn_simulations.json |
| 4 | Simulation Assistant | Frontend auditor | simulation_assistant_scenarios.json, flow_type mapping |
| 5 | Frontend surfaces | QA auditor | UnifiedIntakePage, SimulationAssistant, category labels |
| 6 | Verification scripts | QA auditor | run_inbox_triage_scenarios, run_multi_turn_simulations, guardrail, smoke |

---

## Asset Surfaces (Minimum)

### Docs / knowledge
- `configs/docs/faq_handling_matrix.md`
- `configs/auto_insurance_faq_intake_corpus.json`
- `docs/sprints/HIGH_VALUE_QUESTION_REALISM_PRODUCT_POLISH_REPORT.md`

### Backend
- `services/fiqa_api/inbox_triage/triage.py` — VALID_CATEGORIES, _classify_with_guardrails, _is_* helpers

### Scenario assets
- `configs/inbox_triage_scenarios.json` — expected_category per scenario
- `configs/customer_entry_multi_turn_simulations.json` — category names
- `configs/simulation_assistant_scenarios.json` — flow_type per scenario

### Frontend
- `ui/src/pages/UnifiedIntakePage.tsx` — category labels, case focus
- `ui/src/components/simulation/SimulationAssistant.tsx` — scenario list, flow_type display
- `ui/src/config/simulation_assistant_scenarios.json` — UI copy of scenarios

---

## Likely Loop Count

- **Loop 1:** Full audit + verification scripts → integration matrix
- **Loop 2:** Small fixes (if high-value, low-risk)
- **Loop 3:** Optional, only if Loop 2 reveals one more clear improvement

---

## Mapping: 8 Types → Backend Categories

| 8-question type | Backend category / detection |
|-----------------|-----------------------------|
| new_car_quote | customer_question + _is_add_vehicle_request() |
| cancellation_warning | cancellation_warning |
| payment_failed | payment_lapse_expiration |
| missing_document | missing_document |
| already_sent_followup | missing_document (Turn 2+ already_sent) or FAST path |
| notice_confusion | customer_question + _is_english_notice_confusion() |
| premium_too_high | customer_question + _is_premium_review_request() |
| claim_intake | customer_question + _is_claim_intake_request() |

---

## Simulation Assistant flow_type Mapping

| 8-question type | SA flow_type | Example scenarios |
|-----------------|--------------|-------------------|
| new_car_quote | add_car | SIM3, SIM4, SIM11, SIM15, R3, R4 |
| cancellation_warning | notice_cancellation | SIM1, SIM7, SIM9, R1, R7 |
| payment_failed | notice_cancellation | SIM1, SIM7, SIM9, SIM14, R1, R7 |
| missing_document | missing_document | SIM2, SIM8, SIM10, R2, R8, FAQ-W1 |
| already_sent_followup | (embedded in missing_document) | SIM8, SIM10, R2, R8, FAQ-AS1 |
| notice_confusion | **GAP: no explicit flow_type** | — |
| premium_too_high | renewal_premium | SIM6, SIM13, R6 |
| claim_intake | claim | SIM5, SIM12, R5 |

---

*Next: Acceptance / Audit Criteria*
