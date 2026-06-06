# INTENT LAYER IMPLEMENTATION + REPLY ROUTING BINDING — Blueprint

## Sprint goal

Implement a **bounded, first-class Intent Layer for Add-Car** and bind **reply routing (handoff phrase family)** to **Truth × Intent**, so late-turn replies stop collapsing into a single generic template family without reducing truth safety.

## Why now

The three-layer standard (`TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`) is documented; the main gap was **implementation**. Intent was only partially expressed via `follow_up_type` and scattered heuristics, not an explicit, testable artifact.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md` (§6A structured truth vs reply)
3. `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

**In scope:** Add-Car only; explicit intent resolution module; handoff `add_car_*` key selection driven by intent + truth; API field for observability; focused pytest regression.

**Out of scope:** Non–Add-Car lanes, full NLU, workflow engine, UI redesign, LLM-first routing.

## Target outcome

- Reviewable intent families on each Add-Car turn.
- Distinct routing keys for timeline vs quote-detail vs office-receipt vs materials vs supplement vs correction.
- Pre/post-submit truth still gates office-receipt wording (no “office already has it” without formal submit truth).
