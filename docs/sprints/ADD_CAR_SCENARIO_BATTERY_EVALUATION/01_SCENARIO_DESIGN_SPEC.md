# Scenario Design Spec — Add-Car Battery

## Principles

1. **Messy by default** — copy real WeChat/SMS habits: late fields, fillers, mixed zh/en, corrections.
2. **One flagship flow** — every scenario is anchored in **Add-Car / new vehicle quote**, even when the customer also asks something else.
3. **Observable expectations** — each scenario in `scenario_battery.json` includes `why_matters`, `expected_good_behavior`, and `failure_looks_like` so reviewers don’t argue from memory.

## Coverage matrix (required mix)

| Bucket | Count in battery | Intent |
|--------|------------------|--------|
| Clean | 3 | Baseline trust: sensible asks + handoff |
| Moderately messy | 7 | Partial info, echo risk, dense text, late ZIP/driver/contact, hesitation |
| Edge / risky | 7 | Correction, materials sent, price anxiety + add-car, doc side-question, two-car, topic jump |

**Total: 17 scenarios** (within 10–20 requirement).

## Turn structure

- Each scenario is a **sequence of customer turns** only (system turns are implied by the engine).
- The runner calls `triage_conversation(latest_text, prior_turns)` after each customer message—matching Unified Intake multi-turn behavior.

## Language and realism

- **Chinese-first** with **English vehicle names** where common (Tesla Model Y, zip, dealer).
- **California ZIPs** in valid ranges.
- **Office-realistic side questions** (garaging proof, 材料要不要发你, 能便宜吗).

## File of record

All scenario IDs and text live in:

`docs/sprints/ADD_CAR_SCENARIO_BATTERY_EVALUATION/scenario_battery.json`

Do not fork scenario text into markdown copies; edit the JSON when the battery changes.

## IDs

- `ACB-Cxx` — clean  
- `ACB-Mxx` — messy  
- `ACB-Exx` — edge  
