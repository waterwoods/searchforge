# HANDOFF STATE STABILITY + SUBMITTED SIGNAL — Blueprint

## Sprint goal

Stabilize the Add-Car handoff state line (`collecting` → `handoff_pending` → office-received) and make **formal submission to the office** more observable, without CRM/workflow-engine scope or database redesign.

## Why now

Product copy and rails already distinguish “资料已齐 · 可提交” from post-handoff, but **`handoff_ready` from the API is true in both “ready to formally submit” and “broker-ready” situations**, so the customer portal could treat `handoff_pending` like a completed handoff. That undermines trust in the same story on customer vs office surfaces.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Zendesk-style state, Intercom-style handoff, Add-Car flagship wedge.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical path, persistence truth, guardrail gate.

## Scope

- Add-Car lifecycle gating in the customer portal (formal submit vs API `handoff_ready`).
- Add-Car flow step / right-rail alignment with that distinction.
- Workbench queue label for persisted `handed_off` / `office_followup` Add-Car cases.
- Submitted-at display when `created_at` exists on the persisted response (bounded; no fake events).

## Non-scope

- CRM, workflow engine, Postgres schema changes, simulation redesign, broad polish.

## Target outcome

Customer and office can agree on: still collecting, ready-but-not-submitted, or office has received the persisted record—using existing fields only (`case_id`, `lifecycle_status`, `created_at`).
