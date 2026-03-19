# Add-Car Quote 80% Completion Deploy Sprint — Execution Outline

**Sprint:** Add-Car Quote 80% Completion Deploy Sprint  
**Date:** 2025-03-16

---

## Validation Steps

1. Inspect `services/fiqa_api/inbox_triage/triage.py` — confirm `_add_car_enough_for_handoff`, `_get_next_ask_for_add_car`
2. Inspect `configs/customer_entry_multi_turn_simulations.json`, `configs/simulation_assistant_scenarios.json`
3. Inspect `ui/src/config/simulation_assistant_scenarios.json` — sync with backend config
4. Run: `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
5. Run: `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
6. Run: `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py`
7. Run: `PYTHONPATH=. python3 scripts/verify_speed_routing.py`
8. Run: `bash scripts/guardrail_inbox_triage.sh`
9. Run: `bash scripts/unified_intake_smoke_check.sh`

---

## Backend Deploy Steps

1. Ensure `.env.cloudrun` exists and has required vars (QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, ALLOWED_ORIGINS)
2. Run: `bash scripts/deploy_rag_demo.sh`
3. Capture: success/failure, backend URL, revision, health/readyz output

---

## Frontend Deploy Steps

1. Inspect whether frontend-visible config or scenario changes matter for founder inspection
2. If needed: `cd ui && npm run build` then `vercel --prod`
3. Capture: success/failure, production URL, deployment URL

---

## Production Verification Steps

1. Backend health: `curl <BACKEND_URL>/healthz` and `curl <BACKEND_URL>/readyz`
2. Add-car first turn: POST to inbox triage with "我想加一台X5" → expect ask for ZIP/year, not handoff
3. Add-car second turn: "想加一台X5" + "90210" → expect ask for delivery/driver, not handoff
4. Add-car third turn: add delivery → expect handoff
5. Confirm frontend points at production backend

---

## Likely Loop Count

- **Loop 1:** Pre-deploy validation → backend deploy → frontend judgment → production verification
- **Loop 2 (optional):** Only if one small, high-value fix revealed (config mismatch, deploy target)

---

*See: SPRINT_BLUEPRINT.md, ACCEPTANCE_CRITERIA.md*
