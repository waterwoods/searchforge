# RESTART / REBASELINE ROLE C SMOKE — Blueprint

## Sprint goal

Re-baseline the **local Unified Intake API runtime** so the running process matches the current repo (especially Add-Car **Truth → Intent → Reply** behavior), then **prove** alignment with direct HTTP checks and a **short Role C smoke** battery.

## Why now

A prior report showed **live HTTP on `8001` returned `add_car_turn_intent: null`** while the repo already serializes structured intent. That gap makes every battery and UI test **untrustworthy** until the process is restarted on current code.

## Read-first (aligned)

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — flagship Add-Car, service record, no CRM sprawl.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical path, persistence, three-layer note.
- `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md` — Truth constrains Intent constrains Reply.

## Scope

**In scope:** local port **8001** process lifecycle, runtime proof, short Role C smoke (HTTP), lightweight sprint docs.

**Out of scope:** product redesign, new features, CRM/workflow engine, large batteries, Cloud Run / Vercel deploy (unless explicitly chosen as the proof target — this sprint defaulted to **local 8001** as the fastest trustworthy path).

## Target outcome

- One **fresh** `uvicorn` on **127.0.0.1:8001** loaded from this repo.
- **Direct verification** that `POST /api/inbox/triage` returns a non-null **`add_car_turn_intent`** object on Add-Car paths.
- **Short Role C smoke** (three variants × 4 turns) completes without errors and traces include intent payloads.
