# Configs — Where Things Live

**Package model:** common base → industry pack → client pack. See `docs/CLIENT_PACK_FOUNDATION.md`.

## Package Layers

| Layer | Path | What |
|-------|------|------|
| **Common** | `common/` | Workflow defaults (broker_next_step, client_prep, client_reply_draft fallbacks) |
| **Industry** | `industries/insurance/` | Markers, reply templates, category_templates, add_car_rules |
| **Client** | `clients/chen_kui/` | Handoff phrases, reply overrides, ui_copy |
| **Client (demo)** | `clients/demo_broker/` | Demo broker ui_copy for A→B variation proof (?client=demo_broker) |

## Quick Reference

| Purpose | Location |
|---------|----------|
| **Triage regression** | `inbox_triage_scenarios.json` |
| **Chen Kui draft style** | `chen_kui_proxy_calibration_cases.json` |
| **Multi-turn handoff** | `customer_entry_multi_turn_simulations.json` |
| **Expression robustness** | `expression_robustness_cases.json` |
| **RAG corpus URLs** | `broker_demo_urls.json`, `broker_demo_urls.txt` |
| **Simulation Assistant** | `simulation_assistant_scenarios.json` (canonical); UI copy: `ui/src/config/simulation_assistant_scenarios.json` |
| **Demo env** | `demo.env.example` |

## Runners

| Config | Runner |
|--------|--------|
| inbox_triage_scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| chen_kui_proxy_calibration | `PYTHONPATH=. python3 scripts/run_chen_kui_proxy_calibration.py` |
| multi_turn_simulations | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` |
| expression_robustness | `PYTHONPATH=. python3 scripts/run_expression_robustness.py` |
