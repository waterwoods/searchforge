# ROLE D CONFIGURABLE CUSTOMER + COMPLEX ADD-CAR SIMULATION — Blueprint

## Sprint goal

Ship a **bounded, configurable Role D** in the Simulation / Scenario Replay tab so builders and brokers can stress-test and demo **messy but believable Add-Car customer behavior** without turning the surface into a free-form AI playground.

## Why now

- Roles A/B remain valuable for deterministic regression and crisp demos but under-represent **fragmentation, typos, corrections, and mixed household/price/material pressure**.
- The master outline (`§4.6`) already calls for scenario assets beyond fixed scripts; Role D is the next incremental step **before** any full LLM-driven Role C productization.
- Add-Car business truth remains: **collect enough accurate information for broker quote-prep and office follow-up** — Role D should pressure that collection path, not maximize chat length.

## Read-first alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — §4.6 Simulation / Scenario Replay, §4.7 Flow explanation, Add-Car task skeleton.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical intake path, scope guardrails.

## Scope

- Role D product concept and **three-input** configuration: persona template, optional one-line customer note, difficulty (顺畅 / 真实 / 刁钻).
- Deterministic **multi-turn script generation** from that configuration (bounded tables, not unconstrained generation).
- Integration as a **real scenario card** with existing replay + right-hand state panel (`triageMessage`, same semantics as A/B).

## Non-scope

- Full sandbox or autonomous agent playground.
- Redesign of the whole simulation tab or a workflow engine.
- Non–Add-Car flows, giant settings matrices, or server-side LLM customer simulation.

## Target outcome

- Demo viewers can say “this could be my client” with **minimal setup**.
- QA can replay **varied** Add-Car pressure paths without hand-typing long threads.
- Regression remains possible because outputs are **repeatable** for a given template + difficulty + note.
