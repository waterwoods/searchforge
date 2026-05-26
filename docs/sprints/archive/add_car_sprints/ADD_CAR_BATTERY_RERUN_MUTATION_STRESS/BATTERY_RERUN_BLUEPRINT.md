# Battery Re-Run Blueprint — Add-Car (Chen Kui / Unified Entry)

## Purpose

Re-validate Add-Car after high-ROI fixes (ZIP formats, driver micro-phrases, already-sent question-vs-statement) using the **existing** scenario batteries and guardrails—before introducing mutation stress.

## Scope (in)

- Rule path / `triage_conversation` with `LLM_GENERATION_ENABLED=false` (deterministic evaluation).
- Original Add-Car scenario battery (`ACB-*`).
- ACE* edge simulations embedded in `customer_entry_multi_turn_simulations.json`.
- Full multi-turn simulation pack (includes ACE*).
- `scripts/guardrail_inbox_triage.sh` (broker-facing regression umbrella).

## Scope (out)

- New product features, OCR, carrier APIs, UI redesign.
- Non–Add-Car scenario design (covered only as guardrail side effect).

## Commands (canonical)

| Step | Command |
|------|---------|
| Add-Car battery | `PYTHONPATH=. python3 scripts/run_add_car_scenario_battery.py` |
| ACE edge slice | `PYTHONPATH=. python3 scripts/run_add_car_edge_case_simulations.py` |
| Full multi-turn | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 -u scripts/run_multi_turn_simulations.py` |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |

## Success bar

- **Battery:** All `ACB-*` scenarios complete without script error; note any turn that is broker-embarrassing even if `handoff_ready=True`.
- **ACE:** Exit 0 (all strong).
- **Multi-turn:** Exit 0, weak count 0.
- **Guardrail:** `Guardrail: PASS`.

## Weak-case focus (from prior sprint)

| Theme | Representative IDs |
|-------|---------------------|
| ZIP variants | ACB-C03, ACB-M02, ACE07, ACE14 |
| Driver phrasing | ACB-M03, ACE11 |
| Already sent / materials | ACB-E03, ACB-M04 turn 2, ACE03, ACE12, BS11, HT13 |

## Known non-mission noise

- **ACB-E07** turn 1 (office hours) routes to `unclear` with a generic “不完整” style reply—that is **outside** the three Add-Car fix themes but worth tracking for broker polish separately.

## Output

Record pass/fail, counts, and any subjective “broker blush” notes in `FINAL_REPORT.md` and `FOUNDER_INSPECTION_NOTES.md`.
