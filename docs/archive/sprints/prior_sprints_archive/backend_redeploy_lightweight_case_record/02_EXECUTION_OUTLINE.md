# Backend Redeploy for Lightweight Case Record — Execution Outline

**Sprint**: Backend Redeploy for Lightweight Case Record  
**Created**: 2026-03-15

---

## 1. Validation Steps (Pre-Deploy)

| Step | Command | Pass Criteria |
|------|---------|---------------|
| Persistence | `PYTHONPATH=. python3 scripts/verify_inbox_case_persistence.py` | Exit 0 |
| Scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | All pass |
| Multi-turn | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | All pass |
| State audit | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | No new failures |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | OK |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | PASS |
| Smoke | `bash scripts/unified_intake_smoke_check.sh` | PASS or documented |

---

## 2. Deploy Steps

| Step | Command | Notes |
|------|---------|-------|
| 1 | Ensure .env.cloudrun exists | QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS |
| 2 | `bash scripts/deploy_rag_demo.sh` | Cloud Build + Cloud Run deploy |
| 3 | Capture SERVICE_URL | From deploy output |

---

## 3. Verification Steps (Post-Deploy)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 1 | `curl $SERVICE_URL/healthz` | 200 |
| 2 | `curl $SERVICE_URL/readyz` | JSON with ok field |
| 3 | POST /api/inbox/triage persist_case=true | Case returned with case_messages |
| 4 | POST /api/inbox/cases/{id}/append-message | Updated case with new messages |
| 5 | PATCH /api/inbox/cases/{id}/customer | Customer fields stored |
| 6 | GET /api/inbox/cases | Cases include case_messages, workflow, customer fields |

---

## 4. Likely Loop Count

- Loop 1: Pre-validate → Deploy → Verify
- Loop 2 (optional): Fix one small issue → Redeploy → Re-verify
