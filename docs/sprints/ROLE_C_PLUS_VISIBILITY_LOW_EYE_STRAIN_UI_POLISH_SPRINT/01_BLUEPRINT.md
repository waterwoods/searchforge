# ROLE C PLUS VISIBILITY + LOW-EYE-STRAIN UI POLISH — Blueprint

## Sprint goal

1. Surface **Role C Plus** as its **own scenario card** in the Simulation tab (not only nested under Role C).
2. Apply **bounded, reversible** typography/contrast/spacing/hierarchy polish so the Simulation tab is **easier to scan and less fatiguing** to read.

## Why now

Role C Plus already works end-to-end, but discoverability was weak (one-click path lived only inside the Role C control panel). The next increment is **clarity for demos and founder review**, without a page redesign or backend churn.

## Read-first alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — simulation as first-class surface; Add-Car flagship; restrained page hierarchy.
- `docs/PROJECT_TRUTH_SWITCH.md` — Unified Intake path; safe-first UI edits.
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` — truth → intent → reply; Role C Plus snapshots remain observational, not a second truth layer.

## Scope

- **In:** Simulation tab only (`ScenarioReplayTab` and Role C scenario helpers); lightweight sprint docs; `npm run build` validation.
- **Out:** Full redesign, other pages, triage engine changes, new design system, deploy (unless separately run).

## Target outcome

Founder opens **Simulation** and immediately sees:

- **Role C** = manual, step-by-step controlled LLM + triage.
- **Role C Plus** = same stack, **one-click** multi-turn to completion.
- Clearer visual hierarchy and body text contrast on this tab only.

## Rollback principle

Changes are limited to a **small set of UI files**; reverting the diff restores prior layout and scenario list behavior.
