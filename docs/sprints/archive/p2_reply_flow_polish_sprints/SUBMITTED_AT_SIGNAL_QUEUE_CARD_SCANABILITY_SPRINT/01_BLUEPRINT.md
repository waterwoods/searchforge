# SUBMITTED AT SIGNAL + QUEUE CARD SCANABILITY — Blueprint

## Sprint goal

Improve **truthful** observability of when a service record last reflected office-side activity (bounded proxy: `updated_at`), and improve **office queue card scanability** for Add-Car so brokers can prioritize without opening every case.

## Why now

Prior sprints clarified collecting vs handoff_pending vs submitted and workbench detail parity. Remaining friction is **scan speed** and **trustworthy timing wording**—not more detail screens.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

- Submitted / received **wording** and **timestamp semantics** (honest labels).
- Queue card **one-line scan** + **compact preview** for Add-Car.
- Client-pack copy keys + UI wiring.
- Lightweight sprint docs + validation notes.

## Non-scope

- Full app redesign, CRM, workflow engine, DB schema for discrete submit events, non–Add-Car expansion, simulation redesign.

## Target outcome

- Customer closure and office **报送与送达** tell the same story: **no fake “exact submit” timestamp**; **`updated_at`** as primary visible office-activity proxy when appropriate.
- Queue cards surface **formal delivery phase** + **recent activity time** + existing readiness tags / preview.
