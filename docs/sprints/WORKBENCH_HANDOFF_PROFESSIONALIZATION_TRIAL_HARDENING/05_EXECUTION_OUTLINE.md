# Execution Outline

**Sprint:** Workbench Handoff Professionalization + Trial Hardening

---

## 1. Workstreams

| Workstream | Scope |
|------------|-------|
| **Signal visibility** | Queue cards + case detail: quote_ready, contact, attachment, correction, already_sent, urgency |
| **broker_next_step** | Triage logic: more specific, scenario-adapted |
| **Trial hardening** | Broker-side simulations: correction, already_sent, attachment, quote-ready combos |

---

## 2. Implementation Order

1. **Loop 1** — Key signal visibility (queue cards + case detail)
2. **Loop 2** — broker_next_step specificity (triage.py)
3. **Loop 3** — Realistic broker review simulations + hardening

---

## 3. Simulation / Validation Plan

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/run_broker_trial_stress_simulations.py`
- `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py`
- `cd ui && npm run build`

---

## 4. Deployment Approach

- **Backend:** Redeploy if triage.py or case_store changed
- **Frontend:** Redeploy if UnifiedIntakePage.tsx changed
- **No DB migration** — JSON case store only

---

*End of outline*
