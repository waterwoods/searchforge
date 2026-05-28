# RIGHT RAIL CORRECTION / UPDATE VISIBILITY — Blueprint

## Alignment

- **Master outline** (`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`): Add-Car flagship, service record as primary object, thread as evidence; right rail explains business state.
- **Truth switch** (`docs/PROJECT_TRUTH_SWITCH.md`): portal → triage API → `triage.py`; bounded UI copy safe-first.
- **Prior rails**: `RIGHT_RAIL_RECORD_SUMMARY_FLOW_EXPLAINER_SPRINT` established grouped received/missing + conditional “latest update” from `follow_up_type` and new `collected_fields` vs prior system turn.
- **Simulation / Role C / Role D**: multi-turn live triage (`ROLE_D_MULTI_TURN_LIVE_API_VALIDATION_SPRINT`, `ROLE_C_CONTROLLED_LLM_CUSTOMER_SPRINT`); right column must stay trustworthy turn-by-turn.

## Problem

Corrections and updates were easy to miss: **new collected fields were hidden whenever `follow_up_type === 'correction'`**, and there was no factual **still-needed delta** or short **“what this means for the step/gaps”** copy.

## Goal (bounded)

Improve trust without a diff engine or backend change:

1. Emphasize **latest understood record** before the green/orange groups.
2. Show **更正** and **本回合新记入** together when both apply.
3. Show **缺项集合变化** (set diff on `still_needed_fields` only).
4. Add **对当前步骤与缺项的含义** when we can say something honest from prior vs current triage.

## Non-goals

- Redesign simulation, CRM, workflow engine, or triage engine.
- Field-level old→new values without API support.

## Done when

- Portal pre-handoff rail, simulation rail, and post-handoff grouped snapshot share the same turn model (`buildAddCarRailTurnModel`).
- `npm run build` passes for `ui`.
