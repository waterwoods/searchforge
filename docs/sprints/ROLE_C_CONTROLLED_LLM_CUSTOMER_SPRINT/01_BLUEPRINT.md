# ROLE C CONTROLLED LLM CUSTOMER SPRINT — Blueprint

## Sprint goal

Ship **Role C** as a **true bounded LLM customer** inside the Unified Intake **Simulation** tab so Add-Car replay can show **variable, human-like multi-turn behavior** without becoming a free-form AI sandbox.

## Why now

- **A/B** are stable scripted assets; **D** is a bounded scripted/branch customer.
- The master outline (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §4.6) explicitly calls for a **C controlled-LLM variation role**.
- Add-Car value is **accurate, useful information → service record for quote-prep**; Role C pressure-tests that under messy but **on-topic** input.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — simulation layer, record-first.
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical paths, deploy truth.
3. Prior sprints: `docs/sprints/SIMULATION_TAB_AND_FLOW_EXPLANATION_IMPLEMENTATION_SPRINT/` (simulation tab), Role D–style work in `ui/src/components/simulation/roleDReplay.ts`.

## Scope

**In:** Role C product definition; bounded LLM customer lines; persona / note / difficulty / max-turn controls; Add-Car-only system prompt; replay + real `POST /api/inbox/triage`; right-rail continuity; lightweight sprint docs; frontend deploy; backend deploy if new API surface.

**Out:** Free-form playground; simulation tab redesign; non–Add-Car flows; CRM; giant prompt UI.

## Target outcome

Brokers and builders can select **角色 C**, tune bounded controls, run **多轮** replay where **each customer line is LLM-generated** (when `OPENAI_API_KEY` is set server-side), and still read **state / gaps / next step** from the **right column** as the product hero.
