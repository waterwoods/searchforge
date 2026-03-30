# HANDOFF REPLY VARIETY + TRUTH ALIGNMENT — Blueprint

## Sprint goal

Improve **post-handoff / handoff-stage customer reply policy** so that replies stay truthful about office handoff but **vary by customer intent** (supplement, timeline, quote-detail questions, corrections, materials sent) instead of repeating one canned closure every turn—while keeping the **same lifecycle state story** (handoff_pending, same record).

## Why now

Live testing showed correct state with **robotic, repetitive** post-handoff wording (e.g. variants of “资料已到办公室，核对后会联系您”), which undermines trust and feels like the system stopped listening. This sprint tightens **reply families + truth constraints** without redesigning the product.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — record-first, state-driven flow, Intercom-style handoff
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical triage path and config boundaries

## Scope

**In scope:** Bounded rule/template policy for post-handoff add-car replies; client-pack phrase keys; optional contact-gap truth tail; validation.

**Out of scope:** CRM, workflow engine, simulation redesign, broad LLM rewrite, non–Add-Car expansion.

## Target outcome

- **Intent-aware** add-car handoff replies (supplement / timeline / quote detail / correction vs default).
- **Truth:** no implied completeness when name/phone are still missing on the record (contact-gap sentence).
- **Variety:** alternate default `zh`/`en` on even follow-up turns when configured.
- **Hot-swappable** copy via `configs/clients/<client_id>/handoff_phrases.json`.
