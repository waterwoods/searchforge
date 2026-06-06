# Validation / Regression Checklist

**After you change triage, config, or UI** — run checks in this spirit. The **canonical umbrella** is `guardrail_inbox_triage.sh`.

---

## 1. Must-run (blocks “release” for Unified Intake)

| Check | Command | What “green” means |
|-------|---------|---------------------|
| **Unified guardrail** | `bash scripts/guardrail_inbox_triage.sh` | All steps PASS (no FAIL) |
| If guardrail unavailable | At minimum: `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Scenario pack matches expectations |

**Blocks release if:** any **FAIL** inside guardrail (not SKIP/WARN for optional API).

---

## 2. Strongly recommended (included in guardrail today)

| Check | Purpose |
|-------|---------|
| `scripts/test_first_turn_continuity.py` | First turn must not prematurely hand off |
| `scripts/verify_inbox_case_persistence.py` | Case save/load sanity |
| `scripts/test_state_workflow_backbone.py` | Workflow keys & terminal semantics |
| `LLM_GENERATION_ENABLED=0 … run_multi_turn_simulations.py` | Multi-turn flows |
| `… run_adversarial_simulation.py` | Adversarial inputs |
| `… run_complex_adversarial_simulation.py` | Long / mixed intent |
| `… run_case_boundary_battery.py` | Same case vs new issue |
| `… run_simulation_assistant_scenarios.py` | Simulation assistant pack |
| `… run_broker_trial_stress_simulations.py` | Trial stress |
| `… run_handoff_timing_simulations.py` | Handoff timing |
| `scripts/test_client_aware_handoff.py --direct` | Client-aware handoff |
| `scripts/test_client_identity_append.py --direct` | Append uses case `client_id` |
| `… run_cross_client_ab_scenarios.py` | **chen_kui vs socal_precision** isolation |
| `… run_append_boundary_ab_scenarios.py` | Append/boundary string isolation |
| `… run_residual_copy_ab_scenarios.py` | Residual copy isolation |

---

## 3. Optional (context-dependent)

| Check | When |
|-------|------|
| `python3 scripts/test_inbox_triage_api.py --url http://localhost:8001` | Local server running; verifies HTTP contract |
| `scripts/run_add_car_scenario_battery.py` | After add-car logic/copy changes |
| `scripts/run_add_car_driver_zip_materials_stress_battery.py` | After add-car materials stress work |
| `scripts/run_add_car_mutation_battery.py` | After add-car rule mutations |
| Browser manual pass | UI-only or `ui_copy` changes |

---

## 4. UI-specific validation

- [ ] Hard refresh UI after backend `ui_copy` change  
- [ ] Confirm `clientConfig` merge: empty strings don’t wipe defaults unintentionally  
- [ ] Quick-start buttons fire expected `soft_route` + starter text

---

## 5. A/B client isolation (after any handoff/stitched/reply/UI change)

Run at least:

```bash
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_append_boundary_ab_scenarios.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_residual_copy_ab_scenarios.py
```

**Green means:** outputs for client A do not contain client B’s configured phrases (per test definitions).

---

## 6. What “green” vs “yellow” means

| Outcome | Meaning |
|---------|---------|
| **PASS** | Safe to merge from regression POV |
| **SKIP** (e.g. no server on 8001) | Acceptable in guardrail; run API test when server up |
| **WARN** | Investigate; may be environment |
| **FAIL** | **Do not ship** triage changes until fixed |

---

## 7. Environment tips

- **`LLM_GENERATION_ENABLED=0`** — deterministic rule-based runs for scripts that support it.  
- **`CLIENT_ID`** — must match the broker you intend to test.  
- **`PYTHONPATH=.`** — required from repo root for imports.

---

*Shorter priority view: [IMPORTANT_VS_NOT_IMPORTANT.md](./IMPORTANT_VS_NOT_IMPORTANT.md)*
