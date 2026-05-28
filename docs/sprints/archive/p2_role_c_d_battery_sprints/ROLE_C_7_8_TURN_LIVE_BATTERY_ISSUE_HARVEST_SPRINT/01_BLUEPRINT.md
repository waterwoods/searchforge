# ROLE C 7–8 Turn Live Battery + Issue Harvest — Blueprint

## Purpose

Pressure-test **live** Role C (OpenAI customer simulation) on **Add-Car** for **7–8 turns** per case, then **harvest and rank** product issues. No redesign; learn-and-rank only.

## Alignment

- **Unified Intake** north star: service record, state-driven Add-Car, office handoff, right rail as primary scan surface (`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`).
- **Truth switch**: live path `POST /api/inbox/triage`, Role C `POST /api/inbox/simulation-role-c-customer`; formal submit and `formal_submitted_at` vs `updated_at` semantics (`docs/PROJECT_TRUTH_SWITCH.md`).

## Loops

1. **Battery setup review** — script contract, endpoints, personas, turn bounds (3–8).
2. **Live runs** — HTTP battery against a reachable API with working OpenAI.
3. **Issue harvest** — group under realism / triage / handoff / lifecycle / demo clarity.
4. **Ranking** — top 3–5 by trust, demo, broker usefulness.
5. **Founder summary** — strengths, weaknesses, next sprint hint.

## Out of scope

Architecture changes, new knobs, large implementation work, non–Add-Car features.
