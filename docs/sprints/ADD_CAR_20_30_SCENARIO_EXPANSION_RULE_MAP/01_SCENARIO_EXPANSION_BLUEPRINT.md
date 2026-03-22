# Scenario Expansion Blueprint

## Purpose

Expand Add-Car validation beyond prior ZIP/driver/materials stress batteries with a **single 30-scenario** pack that mirrors **Chinese-speaking California auto insurance customers on WeChat**: clean flows, progressive disclosure, corrections, materials intent, price anxiety, office-style side questions, dense bubbles, and jumpy threads.

## Principles

1. **Higher confidence, not random expansion** — each scenario ties to a known product risk (extraction, `follow_up_type`, handoff, reply tone).
2. **Rule path first** — runner sets `LLM_GENERATION_ENABLED=false` so results reflect the **fast-path / rule brain** used for deterministic demos.
3. **Founder-readable** — IDs, names, and “why it matters” are written for broker context, not only for engineers.

## Scope

- **In scope:** Add-Car triage (`triage_conversation`), slot extraction, materials vs prospective-send, correction handling, broker-facing `broker_next_step` / summaries.
- **Out of scope:** OCR, carrier APIs, UI redesign, non–Add-Car products.

## Deliverables

| Artifact | Role |
|----------|------|
| `scenario_battery.json` | Executable scenarios (30) |
| `scripts/run_add_car_expansion_rule_map_battery.py` | Runner (default battery + optional ACB + ADZM) |
| Evaluation / rule-map docs | See sibling files in this folder |

## Success criteria

- ≥20 scenarios executed against current `triage.py` with captured JSON.
- Weak spots classified against explicit **Strong / Acceptable / Weak / Trust-breaking** rubric.
- A **concrete file/function map** for Add-Car rules (see `06_RULE_MAP_SUMMARY_SPEC.md` and `09_FINAL_REPORT.md`).
