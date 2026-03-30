# PERSIST / FORMAL-SUBMIT ALIGNMENT — Blueprint

## Sprint goal

Align Add-Car **“正式提交办公室”** with **real case persistence** so `handoff_pending` means “ready but not yet formally submitted,” and the workbench only receives a service record after the customer (or broker direct paste) performs formal submit.

## Why now

Copy and UI already described a three-phase story (collecting → ready to submit → formally submitted). The API still persisted as soon as `handoff_ready`, so the office could see a case before the customer’s formal submit step—undermining trust in the Add-Car loop.

## Read-first

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

**In scope:** Add-Car persistence timing, `formal_submit` request flag, customer portal + broker workbench callers, bounded route logic, validation scripts, deploy + smoke.

**Out of scope:** CRM/workflow engine, non–Add-Car product expansion, Postgres cutover, simulation redesign, broad UI polish.

## Target outcome

- In-session `handoff_pending` does not create a JSON/Postgres-visible case until `formal_submit`.
- After formal submit, saved cases remain `lifecycle_status: handed_off` in store (office receipt).
- Broker workbench paste and demo queue still persist in one step (`formal_submit: true`).
