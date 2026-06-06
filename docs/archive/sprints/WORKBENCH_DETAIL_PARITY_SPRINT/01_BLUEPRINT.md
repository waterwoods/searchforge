# WORKBENCH DETAIL PARITY SPRINT — Blueprint

## Sprint goal

Bring the **office-side (broker workbench) Add-Car detail view** to much stronger parity with the **customer-side** closure/readiness model: same vocabulary for handoff state, clear **formal submission vs almost-ready**, bounded **timing** when the API provides it, scan-friendly **what’s missing** and **who acts next**, aligned with **`broker_next_step`**.

## Why now

Customer-side work already clarified collecting / handoff_pending / submitted, right-rail explanation, and submitted signal. If the office cannot answer “has this actually reached us?”, “when?”, “what’s missing?”, “can I act now?” without reading the full thread, the efficiency loop stays broken.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

- Office workbench **detail** (Add-Car): state/readiness parity, submission observability, action clarity.
- Bounded UI/copy; client-pack keys where appropriate.
- Lightweight sprint documentation only.

## Non-scope

- Full app redesign, CRM, workflow engine, DB redesign, non–Add-Car expansion, simulation redesign, generic polish.

## Target outcome

Office opens a saved Add-Car case and immediately sees: **handoff state**, **whether the record is formally received by the office (lifecycle-based)**, **honest timestamps** (`created_at` / `updated_at`), **process owner line** aligned with the customer rail, plus existing **readiness panel** and **broker_next_step**.
