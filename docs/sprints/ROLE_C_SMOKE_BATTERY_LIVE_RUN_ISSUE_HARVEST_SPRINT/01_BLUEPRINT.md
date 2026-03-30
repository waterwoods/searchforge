# ROLE C SMOKE BATTERY LIVE RUN + ISSUE HARVEST — Blueprint

## Sprint goal

Run a **bounded live** Role C (controlled LLM customer) + Add-Car triage battery against a **real** backend, then **harvest and classify** issues—without redesigning the product or expanding architecture.

## Why now

Role C is LLM-backed, bounded, and aligned with the Add-Car path. The next leverage is **repeated live runs** to expose triage, handoff, and state weaknesses that only appear under multi-turn pressure.

## Read-first docs

- `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — service record, Add-Car wedge, simulation layer role.
- `docs/PROJECT_TRUTH_SWITCH.md` — canonical intake path, deploy/runtime truth, guardrails.

## Scope

- Live HTTP battery: `POST /api/inbox/simulation-role-c-customer` + `POST /api/inbox/triage`.
- Multi-turn runs with persona / difficulty / max_turns variants.
- Issue harvest into agreed buckets; rank top problems; recommend **one** next sprint from evidence.

## Non-scope

- Product redesign, new workflow engine, large battery platform, non–Add-Car expansion, broad UI polish, core engine refactors (this sprint is run-and-learn).

## Target outcome

- Five (or few more) live cases completed with captured state fields.
- Classified issue list + top 3–5 ranked issues.
- Founder-ready summary and a single evidence-backed “next sprint” recommendation.
