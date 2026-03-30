## Sprint goal

Deploy and/or validate the **Role C Plus visibility + low-eye-strain UI polish** on the Unified Intake Simulation tab so that, on the real demo-facing frontend, **Role C** and **Role C Plus** are clearly visible as separate scenario cards and the Simulation layout is calmer and easier to scan—without redesigning the product or changing backend behavior.

## Why now

- Role C Plus and related Simulation tab polish have been implemented in code and partially deployed in an earlier **Role C Plus frontend deploy + runtime check** sprint.
- The feature is strategically important: Add-Car is the flagship wedge; Role C / Role C Plus are the primary simulation instruments for explaining how messy turns become a service record.
- The founder now needs to judge the UI with real eyes on the **live demo URL**, not just through code or local builds.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`
- `docs/sprints/ROLE_C_PLUS_LIGHTWEIGHT_FRONTEND_SPRINT/01_BLUEPRINT.md`
- `docs/sprints/ROLE_C_PLUS_FRONTEND_DEPLOY_RUNTIME_CHECK_SPRINT/01_BLUEPRINT.md`

## Scope

- Use the **existing Vercel production alias** for Unified Intake (`ui-smoky-beta.vercel.app`).
- Check whether the live **Unified Intake → 场景仿真 (Simulation)** tab:
  - loads successfully on the demo URL;
  - exposes **Role C** and **Role C Plus** as distinct scenario entries/cards;
  - shows the newer, calmer Simulation layout (Role C / Role C Plus zone, per-turn snapshots, end-of-run summary block).
- Deploy the frontend to Vercel **only if** evidence shows the Role C Plus / polish bundle is not already live.
- Keep the existing demo alias stable; no new domains or routing changes.
- Produce a concise, founder-readable report answering the decision questions in both English-structured sections and short Chinese summary.

## Out of scope

- No new features beyond already-implemented Role C Plus and Simulation polish.
- No backend or Cloud Run changes unless a hard blocker appears (e.g. live API shape incompatible with UI).
- No redesign of Unified Intake or Simulation; only visibility / readability validation for the existing design.
- No changes to non-Simulation tabs or other workbench tools.

## Target outcome

- Andy can open **`https://ui-smoky-beta.vercel.app/workbench/unified-intake`**, switch to **场景仿真**, and:
  - clearly see **Role C** as the manual controlled-LLM scenario;
  - clearly see **Role C Plus** as a separate “one-click multi-turn” scenario block/card;
  - experience the Simulation tab as visually calmer and easier to scan (hierarchy, card layout, right-rail record-first panel).
- A lightweight written record exists of:
  - what was checked on the live frontend;
  - whether a new deploy was performed in this sprint;
  - what remains subjective and explicitly awaits founder judgment.

