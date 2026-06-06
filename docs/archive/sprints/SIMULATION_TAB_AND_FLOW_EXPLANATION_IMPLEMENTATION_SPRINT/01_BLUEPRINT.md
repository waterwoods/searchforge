# SIMULATION TAB + FLOW EXPLANATION — Sprint blueprint

## Sprint goal

Ship a **first-class Simulation / Scenario Replay tab** (Add-Car A/B/C) and a **Flow Explanation layer** on Add-Car progression and office handoff, aligned with `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §4.6–4.7 and `docs/PROJECT_TRUTH_SWITCH.md`.

## Why now

- Brokers and founders need **repeatable, named demos** without improvising in unconstrained chat.
- Users report cases feeling like they **“end suddenly”** after handoff; the product must explain **where the case sits** in the three-step Add-Car skeleton.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` (§4.6 Simulation, §4.7 Flow explanation)
2. `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

**In scope**

- Third tab: **场景仿真** with left scenario cards, center replay, right structured state panel.
- Fixed-script **A** (smooth Add-Car), **B** (higher-risk / multi-concern), **C** (placeholder + minimal turn for structure).
- Multi-turn replay against live `triageMessage` with `soft_route: add_car`.
- Flow explanation **pre-handoff** (step 2) and **post-handoff** (step 3) for Add-Car.
- Client-pack / default copy hooks in `ui_copy` + `clientConfig.ts`.

**Non-scope**

- CRM, full workflow engine, LLM playground, non–Add-Car platformization, backend redesign.

## Target outcome

- Demo and regression can point at **named Add-Car scenarios** on a dedicated tab.
- Handoff and mid-intake show **process-oriented** copy (completed step, current step, gaps, owner, next user options in prose).
