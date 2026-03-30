# RIGHT RAIL RECORD SUMMARY + FLOW EXPLAINER — Blueprint

## Sprint goal

Upgrade the Add-Car **record-first panel** (customer intake progress card + simulation right column) into a clearer **record summary + flow explainer + correction absorber**, without redesigning the whole app.

## Why now

Simulation and Role D validation are real; the remaining trust gap is **whether the product explains business state** (what is captured, what is missing, why this step, who acts next, what changed)—not more field chips alone.

## Read-first alignment

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — Add-Car wedge, service record primary, thread secondary, §4.6 simulation, §4.7 flow explanation, Amazon-style steps.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical intake path and safe edit zones.
- Related sprint themes: simulation tab + flow explanation implementation; Add-Car state/handoff/status-strip work (referenced in code paths).

## Scope

- Right-rail / record-panel information architecture for **Add-Car**.
- Received vs missing **separation and grouping** (vehicle / driver / contact / materials).
- **Why this step** and **next owner** copy, aligned with steps 1–3.
- **Correction / update** visibility when `follow_up_type === correction` or when new structured fields appear vs prior system turn.
- Shared component between **customer intake** (pre-handoff progress card) and **simulation** right column.
- Configurable section titles via `ui_copy` + `clientConfig` defaults.

## Non-scope

- CRM / workflow engine / DB redesign.
- Broad non–Add-Car product expansion.
- Generic visual redesign of the whole portal.

## Target outcome

Brokers and founders can scan one panel and answer: **step, rationale, captured, missing, last change, next owner, continue vs office path**.
