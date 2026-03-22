# Execution Outline

**Sprint:** Workbench Office Tool Professionalization

---

## 1. Workstreams

| Workstream | Scope |
|------------|-------|
| Queue / first-scan | Queue cards: next-step preview, follow-up prominence |
| Case detail | Section hierarchy, follow-up above fold |
| broker_next_step | Backend: edge-case improvements |
| Simulation | Broker trial stress, handoff timing |

---

## 2. Loop Plan

| Loop | Focus | Targets |
|------|-------|---------|
| 1 | Queue / first-scan | Next-step preview on cards; follow-up more prominent |
| 2 | Case detail / follow-up | Section hierarchy; follow-up block above fold |
| 3 | broker_next_step / trial | Edge-case improvements; simulation hardening |

---

## 3. Simulation / Validation Plan

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py`
- `cd ui && npm run build`

---

## 4. Deployment Approach

- Backend: triage.py, config — redeploy if changed
- Frontend: UnifiedIntakePage.tsx — redeploy if changed

---

*End of outline*
