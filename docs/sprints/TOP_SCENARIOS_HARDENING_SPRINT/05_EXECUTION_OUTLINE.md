# Execution Outline

**Sprint:** Top Scenarios Hardening Master Sprint

---

## Workstreams

1. **Classification order** — Premium before payment when premium_review markers present
2. **Add-driver markers** — Add to config; intent detection; reply template
3. **Bundling markers** — Add to config; route to customer_question
4. **Scenario tests** — Add new scenarios to inbox_triage_scenarios.json

## Implementation Order

1. Fix premium-vs-payment disambiguation (triage.py)
2. Add add_driver markers + _is_add_driver_request + reply
3. Add bundling markers + _is_bundling_request + reply
4. Add new scenario tests
5. Run full guardrail

## Test Plan

- `run_inbox_triage_scenarios.py` — must stay 53+ pass (add new scenarios)
- `run_multi_turn_simulations.py` — must stay 38 Strong
- `guardrail_inbox_triage.sh` — must PASS
- Manual edge-case verification

## Loop Count

- Loop 1: Core fixes (premium, add-driver, bundling)
- Loop 2: Verification + any regression fixes
- Loop 3: Optional — LC-AC3 handoff timing if low-risk

---

*See: 06_ACCEPTANCE_SLA_CRITERIA.md*
