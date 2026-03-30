# FORMAL SUBMIT ACTION + ROLE C SYSTEMATIC BATTERY — Blueprint

## Sprint goal

Tighten the Add-Car **「正式提交办公室」** customer action so the three phases are obvious (still collecting → ready to submit → formally handed to office) **without** a heavy confirmation modal, then **systematize** Role C multi-turn runs aimed at that handoff line and harvest issues.

## Why now

- Handoff before the office needs a **clear explicit action**; copy and affordances were good but could be sharper on **queue vs 补充** and **truth after submit**.
- Role C is strong enough to act as a **bounded issue-finding instrument** for submit semantics, state, and reply alignment.

## Read-first (aligned)

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Add-Car wedge, Amazon/Zendesk/Intercom priority, service record as primary object.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical paths, safe-edit zones, guardrail gate.

## Scope

- Formal submit **wording**, **explainer**, **CTA subline**, **empty-input formal submit** (standard one-line customer text for API).
- Role C battery **preset** `handoff_loop` (C1–C5) + **richer trace** (`lifecycle_status`, `handoff_ready`, `case_id` presence).
- Lightweight sprint docs + honest validation notes.

## Non-scope

- CRM / workflow engine / full product redesign.
- Heavy modal confirmation flows.
- Broad simulation platform work beyond this battery preset.

## Target outcome

- Clearer customer mental model: **补充 ≠ 正式提交 ≠ 办公室已接手处理**.
- Repeatable Role C matrix for handoff/submit/follow-up regression and issue harvest.
