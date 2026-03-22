# Regression Batteries Index (Unified Intake)

**Master orchestrator:** `scripts/guardrail_inbox_triage.sh`

| Step | Script / artifact | Role |
|------|---------------------|------|
| Core scenarios | `scripts/run_inbox_triage_scenarios.py` | `configs/inbox_triage_scenarios.json` shape + rule path |
| First-turn continuity | `scripts/test_first_turn_continuity.py` | No premature `handoff_ready` |
| Case persistence | `scripts/verify_inbox_case_persistence.py` | Save/list/update |
| Workflow backbone | `scripts/test_state_workflow_backbone.py` | Workflow keys + terminal guards |
| Multi-turn | `scripts/run_multi_turn_simulations.py` | Long conversational regression |
| Adversarial | `scripts/run_adversarial_simulation.py` | Per-intent stress |
| Complex adversarial | `scripts/run_complex_adversarial_simulation.py` | Mixed intent + long context |
| Case boundary | `scripts/run_case_boundary_battery.py` | Append vs new issue |
| Simulation assistant | `scripts/run_simulation_assistant_scenarios.py` | Trial + real-customer pack |
| Broker trial stress | `scripts/run_broker_trial_stress_simulations.py` | Vague / talk-to-agent / correction |
| Handoff timing | `scripts/run_handoff_timing_simulations.py` | HT* scenarios |
| Standard package doc | `docs/STANDARD_SCENARIO_PACKAGE.md` | Commercial definition guard |
| Client-aware handoff | `scripts/test_client_aware_handoff.py` | chen_kui vs demo_broker |
| Client append identity | `scripts/test_client_identity_append.py` | `case.client_id` on append |

**Optional (when API running on 8001):** `scripts/test_inbox_triage_api.py`
