# Web-Informed Realistic Battery — Blueprint

## Purpose

Exercise the **current rule-based / fast-path Add-Car brain** against **10 web-informed, Chinese-forward California customer scenarios**. The objective is broker-relevant confidence: realistic wording, clear pass/fail signals, and an honest view of where rules suffice versus where humans or future LLM assist should sit.

## Non-goals

- Frontend redesign, OCR, carrier APIs, architecture rewrites, or non–Add-Car features.

## What “web-informed” means (and does not mean)

- **Means:** Scenarios are shaped by (a) common insurer/broker checklists for add-car / quote data (VIN, plate, YMM, mileage, owner/driver, garaging), (b) Chinese-language US auto-insurance guidance and community Q&A patterns, and (c) how people actually type: fragments, price-first questions, screenshot offers, late ZIP/driver.
- **Does not mean:** Ethnographic truth or statistically representative research. These are **plausible stress tests**, not definitive customer research.

## Sprint outputs

| Artifact | Role |
|----------|------|
| `scenario_battery.json` | 10 scenarios with IDs, turns, and design rationale |
| `battery_run_results.json` | Machine snapshot of last rule-path run (`LLM_GENERATION_ENABLED=false`) |
| `scripts/run_web_informed_add_car_realistic_battery.py` | Runner (same pattern as other Add-Car batteries) |
| Supporting specs + `FINAL_REPORT.md` | Criteria, gaps, escalation map, and founder-facing summary |

## Success criteria (sprint level)

1. Scenarios cover the 10 required behavioral categories (see design spec).
2. At least three scenarios embed strong **practical Chinese** office/customer phrasing (price, screenshots, ZIP cost worry, registration timing, corrections).
3. At least two are **messy** (multi-turn, topic jump, partial answers).
4. Each scenario is classified after a real run: Strong / Acceptable / Weak / Trust-breaking, with a clear **rule vs human vs LLM** label.

## Execution defaults

- **Path:** `triage_conversation` in `services/fiqa_api/inbox_triage/triage.py`, **LLM off** for deterministic evaluation.
- **Command:** `PYTHONPATH=. LLM_GENERATION_ENABLED=false python3 scripts/run_web_informed_add_car_realistic_battery.py`
