# ROLE C CONTROL KNOBS + BATTERY DESIGN — Blueprint

## Sprint goal

Turn Role C into a **reusable controlled LLM simulation service** for **Add-Car only**, with **2–3 core knobs**, usable from:

- the **simulation tab** (demo), and  
- **scripts / backend-style** multi-turn runs against the **live triage API**.

## Why now

Role C is already LLM-backed and bounded; the next leverage is **reuse and clarity**—one core, two surfaces—without expanding into a free-form lab or non–Add-Car scope.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — simulation layer, Add-Car wedge, record-first.  
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical triage path and validation expectations.

## Scope

- Explicit **knob model** (persona, difficulty, max customer turns; optional short note).  
- **Shared Python service** for “next customer line” used by the HTTP route and importable by tooling.  
- **HTTP battery script** that chains Role C → `POST /api/inbox/triage` for multi-turn stress on the real path.  
- Light UI copy alignment (clarify knobs, not redesign the tab).  
- This sprint folder (three short docs only).

## Non-scope

- Full simulation platform redesign.  
- Large config surfaces or many knobs.  
- Domains outside Add-Car.  
- Workflow engine or generic experiment console.

## Target outcome

Founder can say: Role C is **one bounded service**, **simply configured**, shown in the **UI**, and runnable as a **multi-turn battery** against the same product path as production intake.
