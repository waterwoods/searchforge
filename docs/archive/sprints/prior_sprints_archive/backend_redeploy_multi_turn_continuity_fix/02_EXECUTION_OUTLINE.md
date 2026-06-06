# Backend Redeploy for Multi-Turn Continuity Fix — Execution Outline

## Validation Steps (Pre-Deploy)

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `PYTHONPATH=. python3 scripts/test_first_turn_continuity.py` | First-turn must not force handoff_ready |
| 2 | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Scenario pack passes |
| 3 | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | Multi-turn sims pass |
| 4 | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | State field accuracy |
| 5 | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | Speed routing |
| 6 | `bash scripts/guardrail_inbox_triage.sh` | Full guardrail |
| 7 | `bash scripts/unified_intake_smoke_check.sh` | Smoke check (includes guardrail) |

**Blocker rule:** If any fails, stop and explain. Do not deploy.

## Deploy Steps

| Step | Command | Purpose |
|------|---------|---------|
| 1 | Ensure `.env.cloudrun` exists and has required vars | Prereq |
| 2 | `bash scripts/deploy_rag_demo.sh` | Deploy fiqa-api to Cloud Run |

**Capture:** success/failure, backend URL, revision, warnings/errors.

## Verification Steps (Post-Deploy)

| Step | Check | Purpose |
|------|-------|---------|
| 1 | `curl $SERVICE_URL/healthz` | Health OK |
| 2 | `curl $SERVICE_URL/readyz` | Readiness OK |
| 3 | POST `/api/inbox/triage` with quote/add-car first turn | handoff_ready=false, asks for year/model/zip |
| 4 | POST `/api/inbox/triage` with payment first turn | handoff_ready=false, asks for notice/screenshot |
| 5 | POST `/api/inbox/triage` with missing-doc first turn | handoff_ready=false when more info needed |

## Likely Loop Count

- **Loop 1:** Pre-validate → Deploy → Verify
- **Loop 2 (optional):** Only if one small, high-value fix revealed during verification
