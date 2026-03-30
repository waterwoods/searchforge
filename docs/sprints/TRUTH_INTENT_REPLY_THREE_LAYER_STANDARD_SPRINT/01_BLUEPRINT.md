# TRUTH → INTENT → REPLY THREE-LAYER STANDARD — Sprint Blueprint

## Sprint goal

Define a **clear, industrial-grade three-layer product standard** for Unified Intake / Add-Car:

**Truth Layer → Intent Layer → Reply Layer**

so that future design, implementation, testing, and demo review can reference one normative doctrine—not vague philosophy.

## Why now

- The **two-layer** rule (structured truth outranks reply) is necessary and documented; it stops **truth drift** in wording.
- Live and Role-C findings show it is **still insufficient**: replies can remain truth-safe yet **wrong**, **generic**, or **detached from the latest turn**—especially after turns 6–10.
- The missing middle is an explicit **Intent layer**: *what this turn is actually doing*, resolved **under** truth, **before** reply phrasing.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
2. `docs/PROJECT_TRUTH_SWITCH.md`
3. `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md`
4. This sprint: `02_THREE_LAYER_STANDARD_SPEC.md`

## Scope

- Architecture doctrine for Truth / Intent / Reply.
- Explicit cross-layer constraints and forbidden failure modes.
- Industrial review checklist and acceptance criteria.
- Bounded patches to core docs (`master outline`, `PROJECT_TRUTH_SWITCH`).
- Mapping notes to current Add-Car engine (e.g. `triage.py` concentrates truth + reply; intent is partially implicit in markers/mixed-intent hints—not yet a first-class contract).

## Non-scope

- Broad implementation or large refactors of `triage.py`.
- Non–Add-Car expansion.
- Generic UI redesign.
- Rewriting unrelated documentation.

## Target outcome

- Core docs name the **three-layer** model and constraint chain.
- This folder holds the **single normative spec** (`02_THREE_LAYER_STANDARD_SPEC.md`) plus this blueprint and final report.
- Backlog and future sprints can cite **intent resolution** as a measurable bar alongside truth alignment.
