# P19H — Workflow State Machine Temporal Audit Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Audit doc:** `docs/p19h_state_machine_temporal_audit_2026_07_10.md`

---

## Test execution

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h_state_machine_temporal_invariants.py -v --tb=no
```

```
tests/test_p19h_state_machine_temporal_invariants.py ............        [100%]
======================== 12 passed, 4 warnings in 0.37s ========================
```

```bash
PYTHONPATH=. python3 -m pytest tests -q -k "claim"
# PASS (full claim subset)

PYTHONPATH=. python3 -m pytest tests -q -k "h5"
# PASS (full h5 subset)
```

---

## Simulation matrix tally

| Status | Count |
|--------|-------|
| PASS | 21 |
| FAIL | 0 |
| UNKNOWN | 2 |
| NEEDS TEST | 1 |

---

## Key code paths verified (read-only)

| Concern | File / symbol |
|---------|---------------|
| Holding vs guided start | `claim_basics.should_route_claim_holding_ack`, `should_route_claim_guided_workflow` |
| Lane switch confirm | `claim_basics.ingest_claim_lane_switch_choice`, `ingest_claim_lane_switch_confirm` |
| Raw inbound filter | `workbench_enrichment.filter_broker_workbench_cases`, `is_raw_inbound_case` |
| `broker_done` gate | `case_store.mark_claim_broker_done`, `ClaimBrokerDoneError` |
| End Card send | `claim_end_card.try_send_claim_end_card` (only from `mark_claim_broker_done`) |
| Timeline idempotency | `case_store._claim_timeline_is_duplicate` (`claim_started`, `broker_done`) |
| Scenario simulator | `workflow_scenario_simulator.SCENARIO_NC*`, `SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT` |

---

## Deploy smoke cross-reference (prior agents)

| Smoke | Verdict | Relevant rows |
|-------|---------|---------------|
| `p19h3f1c_deploy_start_card_only_intake_visibility_smoke_2026_07_10` | GO | 1, 3, 5, 18–20 |
| `p19h3f2_deploy_true_end_card_broker_done_smoke_2026_07_10` | GO | 21–22, 18 |

---

## Main Agent conflict check

```
git status --short (audit start):
 M services/fiqa_api/inbox_triage/case_store.py
 M services/fiqa_api/wecom/claim_basics.py
 M services/fiqa_api/wecom/intent.py
 M services/fiqa_api/wecom/reply.py
 M services/fiqa_api/wecom/slice.py
 M services/fiqa_api/wecom/workflow_scenario_simulator.py
 ...
```

Audit agent added only:

- `docs/p19h_state_machine_temporal_audit_2026_07_10.md`
- `docs/evidence/p19h_state_machine_temporal_audit_2026_07_10.md`
- `tests/test_p19h_state_machine_temporal_invariants.py`

**No production code modified.**

---

## Verdict

**GO** — temporal invariants hold; 0 FAIL in audit battery.
