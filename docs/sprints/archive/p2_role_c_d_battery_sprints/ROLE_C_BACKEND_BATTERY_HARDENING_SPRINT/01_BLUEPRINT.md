# ROLE C BACKEND BATTERY HARDENING — Blueprint

## Sprint goal

Harden the backend Role C Add-Car battery so it behaves more like an **engineering validation instrument**: richer traces, bounded Truth / Intent / Reply / State warnings, and readable per-run summaries—without building frontend “Role C Plus” or broad product scope.

## Why now

Role C already stresses multi-turn behavior and surfaces state/reply drift; the next step is **repeatable, layer-oriented signal** (what failed, where, which layer) so regressions and quality work are visible before investing in UI.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md`
3. `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

**In scope:** `scripts/run_role_c_add_car_battery.py` trace/output, `scripts/role_c_battery_oracles.py` heuristics, bounded live runs, this sprint folder.

**Out of scope:** Frontend Role C Plus, CRM/workflow engines, large test platforms, non–Add-Car expansion.

## Target outcome

- One command run produces **structured trace rows** (intent, lifecycle, still-needed, case/timing fields where available) plus **warning codes** and **run_summary**.
- Engineers can answer: which turn, which layer, and what to inspect next—without claiming perfect oracle coverage.
