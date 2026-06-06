# TRUTH LAYER + REPLY LAYER INDUSTRIAL STANDARD SPRINT — Blueprint

## Sprint goal

Define and publish an **industrial-grade, reusable two-layer contract** for Unified Intake (Add-Car first):

1. **Structured truth layer** — fields, gaps, state, gates, office-visible record, time truth.
2. **Reply generation layer** — human-readable wording subordinate to (1).

Make this contract **explicit in core docs** and **actionable** for future sprints, tests, demos, and reviews—without redesigning the product or starting a large implementation pass.

## Why now

Recent sprints surfaced a recurring pattern: defects and credibility risk often come from **insufficient separation** between structured state and customer-facing copy. Replies can sound complete while structured truth is still partial; “office has it” language can appear before **formal submit** or true office-visible persistence; templates can repeat or over-assume verification. A written standard turns this into **measurable** behavior.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

- Architecture **doctrine** for the two-layer model.
- Product-truth rules, reply-layer rules, non-overreach rules.
- Bounded updates to the master outline and truth switch.
- This sprint folder: blueprint, full spec, final report.

## Non-scope

- Broad code refactors, new frameworks, non–Add-Car expansion, generic UI redesign, large feature work.

## Target outcome

- Core docs reference the two-layer model and point to the normative spec.
- `02_TWO_LAYER_STANDARD_SPEC.md` is the **internal rulebook** for safe replies vs true state.
- Clear list of **what remains to implement** later (enforcement in engine/UI/tests).
