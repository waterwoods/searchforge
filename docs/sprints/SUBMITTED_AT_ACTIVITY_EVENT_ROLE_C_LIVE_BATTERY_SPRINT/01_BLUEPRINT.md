# SUBMITTED_AT ACTIVITY EVENT + ROLE C LIVE BATTERY — Blueprint

## Sprint goal

Make **正式提交后的时间与后续活动** more truthful and observable for Add-Car (bounded signal + UI), then pressure-test the state line with a live Role C multi-turn battery.

## Why now

Formal submit alignment fixed the semantic bug (`handoff_pending` vs real persistence). The next trust gap is **time story**: users could not cleanly see **first formal office-visible moment** vs **later writes** (follow-ups, notes). This sprint adds an explicit immutable `formal_submitted_at` and surfaces it next to `updated_at` / activity wording.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`
- `docs/PROJECT_TRUTH_SWITCH.md`

## Scope

- Immutable `formal_submitted_at` on first `save_case` (JSON pilot store + PG `extra` on dual-write).
- UI: portal closure card, office workbench snapshot, queue scan line, right-rail handoff snapshot, copy in `chen_kui` client pack.
- API test assertions for persist + append stability.
- Live Role C battery plan (same preset as `handoff_loop` / C1–C5).

## Non-scope

- Event bus, workflow engine, CRM expansion, simulation redesign, broad polish.

## Target outcome

- Stronger **first submit vs recent activity** story on persisted cases.
- Evidence from Role C runs (or explicit note if battery not executed in environment).
