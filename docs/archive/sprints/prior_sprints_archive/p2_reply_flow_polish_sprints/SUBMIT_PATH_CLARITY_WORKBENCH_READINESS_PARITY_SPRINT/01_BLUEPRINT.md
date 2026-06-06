# SUBMIT PATH CLARITY + WORKBENCH READINESS PARITY — Blueprint

## Sprint goal

Make **when a case is ready to hand off to the office** and **what each side should do next** obvious on both the customer Add-Car path and the office workbench—without redesigning the product or expanding scope into CRM/workflow engines.

## Why now

The bottleneck is no longer simulation volume; it is **clarity of the handoff line**: `handoff_pending` vs submit, “继续补充” vs “交给办公室”, and office-side scanability of readiness vs missing items. Commercial trust depends on a clean, legible handoff.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

- Submit-path and CTA wording when lifecycle is `handoff_pending`
- Customer-facing process explanation (flow explainer + right-rail alignment)
- Workbench “readiness mirror” for Add-Car (same lifecycle vocabulary as customer)
- Queue chip for Add-Car when `handoff_pending` (`待客户提交`)
- Client-pack copy (`configs/clients/chen_kui/ui_copy.json`) + `DEFAULT_UI_COPY` fallbacks

## Non-scope

- New workflow engine, CRM, or database redesign
- Broad UI restyling
- Simulation/Role C/D expansion
- Non–Add-Car generalization beyond shared copy keys

## Target outcome

- Customer: clear distinction between **still collecting**, **ready but not yet submitted**, and **submitted to office**
- Office: at-a-glance **ready vs waiting on customer submit**, plus **missing fields** where relevant
- Both sides: same record, same process language
