# ROLE D — Branch-driven variation + live API + deploy (Blueprint)

## Sprint goal

Upgrade Role D from “one-line note decorates turn 1 only” to **keyword-driven, bounded branch variation on later turns**; confirm simulation replay uses the **real** Add-Car triage API path; **deploy** the frontend (and backend only if changed); run **smoke** checks.

## Why now

Role D v1 was demo-ready but did not prove that operator-entered customer flavor **changes the stress shape** across the thread. The next increment of value is **branch-driven variation** plus **live** `/api/inbox/triage` behavior—without opening a free-form AI sandbox.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — §4.6 Simulation / Scenario Replay, §4.7 Flow Explanation, Add-Car as flagship.
2. `docs/PROJECT_TRUTH_SWITCH.md` — canonical path: Unified Intake UI → `POST /api/inbox/triage` → `triage.py`; Vercel + Cloud Run deploy truth.
3. Related prior sprints (context only): simulation / network-error / deploy playbooks under `docs/sprints/` and `docs/runbooks/DEPLOYMENT_PLAYBOOK.md`.

## Scope

- Role D: keyword → branch family → **later-turn** text overlays (fixed suffix pools, deterministic slots, capped layers).
- Live API: no bypass—replay continues to call `triageMessage` → `/api/inbox/triage`.
- Deploy: frontend to Vercel when feasible; backend only if engine changes (none in this sprint).
- Smoke: UI loads, API reachable, sample triage POST.

## Non-scope

- Unconstrained LLM customer simulator.
- Simulation tab redesign.
- Workflow engine / CRM.
- Broad triage.py refactors or Stage 2 engine.
- Full semantic NLP for the one-line note.

## Target outcome

- Operators see **different later-turn customer text** when the note contains different keywords (within caps).
- Subtitle shows **which branch tags** fired (transparency).
- Production UI on Vercel builds with a **valid** `VITE_API_BASE_URL` (https Cloud Run, not localhost).
- Honest report of partials (e.g. branch depth, Vercel env must be set in dashboard for CLI-less builds).
