# ROLE C PLUS LIGHTWEIGHT FRONTEND SPRINT — Blueprint

## Sprint goal

Add a **lightweight frontend “Role C Plus”** on the Simulation tab: one-click bounded multi-turn auto-run on the **same live Role C + triage path** as manual stepping, plus readable per-turn snapshots and a compact end-of-run summary with bounded heuristic warnings—**without** removing or replacing existing Role C.

## Why now

Backend and demo-facing runtime expose Add-Car structured state and `add_car_turn_intent` on triage responses; Role C is a credible simulation instrument. The next increment is **frontend usability**: make multi-turn runs less manual and make truth/intent signals easier to scan during demos and spot checks.

## Read-first alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Add-Car wedge, simulation as first-class surface, not a chatbot product.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical intake path; structured truth vs reply; intent layer pointer.
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` — Truth → Intent → Reply; UI must not invent hidden state.

## Scope

- Simulation tab only; Add-Car / Role C path only.
- Preserve full manual Role C (persona, difficulty, max turns, 开始/下一步/清空).
- New: Role C Plus entry (一键跑完), per-turn snapshot strip, end report, heuristic warnings (frontend-only).

## Non-scope

- Replacing Role C or Role D.
- Workbench-wide redesign, generic analytics, or new backend contracts for this sprint.

## Target outcome

Founder can open Simulation → Role C, run **either** manual steps **or** one bounded auto-run, and read turn-by-turn lifecycle / handoff / still-needed / intent plus a short closing summary.
