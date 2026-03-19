# Agent Entry Point — California Auto Insurance Broker Assistant

**For Cursor / OpenClaw:** Read this first when working on the broker project. This file is the single default entry point.

---

## 1. Read First

| Order | Doc | Purpose |
|-------|-----|---------|
| 1 | `docs/PROJECT_DOC_SYSTEM_MAP.md` | Full doc map: goals, standards, runbooks, guardrails |
| 2 | `docs/goals/insurance_paid_pilot_goal.md` | Master goal, scope, what’s in/out |
| 3 | `docs/ANDY_QUICK_START.md` | How to run demo, ports, recovery |
| 4 | `docs/STANDARD_SCENARIO_PACKAGE.md` | Sellable package: 7 scenarios, broker value, demo path |

---

## 2. Default Execution Path

| Task | Command |
|------|---------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Pre-demo checklist** | `bash scripts/demo_pre_checklist.sh` |
| **Recovery** (503 / embedding_warming) | `bash scripts/restore_8001_readiness.sh` |
| **Validate live** | `bash scripts/demo_quick_validate.sh` |
| **Unified Intake guardrail** | `bash scripts/guardrail_inbox_triage.sh` |
| **Trial readiness check** | `bash scripts/trial_readiness_check.sh` |
| **Trial launch check** | `bash scripts/trial_launch_check.sh` — single entry before first broker trial |
| **Founder pre-trial** | `bash scripts/founder_pre_trial_checklist.sh` |
| **Unified Intake scenarios** | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| **Unified Intake API test** | `python3 scripts/test_inbox_triage_api.py` (server on 8001) |

---

## 3. Runtime Paths

| Path | Port | When |
|------|------|------|
| **Default** | **8001** | Local dev, demo, validation (run_demo_local.sh) |
| **Docker** | 8000 | `docker compose up rag-api` |
| **Recovery** | 8001 | After `restore_8001_readiness.sh` |

Details: `docs/runbooks/RUNTIME_PATH_STANDARD.md`

---

## 4. Key Docs by Category

| Category | Path | Use |
|----------|------|-----|
| Goals | `docs/goals/` | What we’re building |
| Standards | `docs/standards/` | Quality bar before demo |
| Runbooks | `docs/runbooks/` | How to run, meeting pack |
| Guardrails | `docs/guardrails/` | Drift checks, when to run |
| Reports | `docs/BROKER_REPORTS_INDEX.md` | Sprint reports, diagnosis; archive at `docs/archive/` |
| **Trial** | `docs/trial/INDEX.md` | Real broker trial: blueprint, runbook, handoff, observation |

---

## 5. Multi-Agent Collaboration

**How Cursor, OpenClaw, ChatGPT, and Andy work together:** `docs/MULTI_AGENT_OPERATING_MODEL_V1.md`

- Roles and responsibilities
- Default working loop
- What to do autonomously vs when to ask Andy

---

## 6. Scope Guardrail

- **In scope:** Broker demo, auto insurance RAG, demo UI, validation scripts, Unified Intake MVP (inbox triage)
- **Out of scope:** Stripe, auth, multi-tenant, other verticals
- **Before changes:** Read relevant goal/standard; prefer small inspect→integrate→retest loops

---

*Full map: `docs/PROJECT_DOC_SYSTEM_MAP.md`*
