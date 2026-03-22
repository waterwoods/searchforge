# Add-Car Scenario Battery — Blueprint

## Purpose

Evaluate whether **current `triage.py` / `triage_conversation`** behavior for **Add-Car (加车 / new vehicle quote)** stays on the right playbook across **messy, realistic** Chinese–English California customer messages—not only happy paths.

## Audience

- **Founder**: readability, decision support (broker demo readiness).
- **Broker (Chen Kui context)**: trust, office usefulness, “would I be embarrassed?”

## Non-goals (this sprint)

- OCR, carrier APIs, non–Add-Car scenarios, broad redesign, speculative architecture.

## What “battery” means here

A **fixed set of 17 multi-turn scenarios** (`scenario_battery.json`) run through the **same code path** brokers will rely on locally when LLM is off (`LLM_GENERATION_ENABLED=false`), with results captured in `run_results_rule_path.json`.

## Success criteria (sprint-level)

- Scenarios cover **clean, messy, partial, correction, side-question, price anxiety, materials-sent, vague, dense, hesitation, mixed language, late ZIP/driver/contact, topic jumps, two-car confusion**.
- Each scenario is **judged** against explicit criteria (see `02_EVALUATION_CRITERIA_SPEC.md`).
- Outputs identify **highest-value weak spots** without overreacting (see `03_FIX_PRIORITY_SPEC.md`).

## Artifacts

| Artifact | Role |
|----------|------|
| `scenario_battery.json` | Canonical scenario list + design rationale fields |
| `scripts/run_add_car_scenario_battery.py` | Runner (uses `triage_conversation`) |
| `run_results_rule_path.json` | Frozen outputs from this sprint run |
| `06_FINAL_REPORT.md` | Broker-oriented summary + 中文总结 + founder block |

## Execution summary

```bash
cd /path/to/searchforge
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_scenario_battery.py
PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_add_car_scenario_battery.py --json > docs/sprints/ADD_CAR_SCENARIO_BATTERY_EVALUATION/run_results_rule_path.json
```

**Note:** If `LLM_GENERATION_ENABLED=true` and an API key is set, results may differ (fast/LLM path). This sprint baseline is **rule path** for reproducibility.
