# Execution Outline

**Sprint:** Add-Car Real Intake Lite V1  
**Purpose:** Workstreams, order, validation, deployment.

---

## 1. Workstreams

| # | Workstream | Owner | Scope |
|---|------------|-------|-------|
| 1 | Quote-ready status | Backend | Add quote_ready_status to triage output for add-car |
| 2 | Broker visibility | UI | Display quote_ready_status, improve add-car case card |
| 3 | Add-car intake card | UI | Lightweight collected/still-needed block during chat |
| 4 | Simulations | QA | Add add-car real-intake scenarios |

---

## 2. Implementation Order

1. **Backend:** Add `quote_ready_status` to triage; derive from _add_car_enough_for_handoff
2. **UI:** Add quote-ready badge to add-car cases; improve getQueueReadinessLabel for add-car
3. **UI:** Ensure collected/still-needed visible during chat (already partially present)
4. **Simulations:** Add configs/add_car_real_intake_simulations.json; extend run script

---

## 3. Simulation / Validation Plan

- `bash scripts/guardrail_inbox_triage.sh` — must pass
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — must pass
- New: `PYTHONPATH=. python3 scripts/run_add_car_real_intake_simulations.py` (if created)
- `cd ui && npm run build` — must pass

---

## 4. Deployment Approach

- Backend: Redeploy if triage.py changed
- Frontend: Redeploy if UnifiedIntakePage or related changed
- No database migration; additive only

---

*See also: 06_ACCEPTANCE_REAL_INTAKE_CRITERIA.md*
