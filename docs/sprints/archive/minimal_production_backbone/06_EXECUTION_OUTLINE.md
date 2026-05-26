# Execution Outline — Minimal Production Backbone

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| **Backbone formalization** | Backend | workflow_state, lifecycle_status, schema |
| **Persistence coherence** | Backend | session/case consistency |
| **Contract documentation** | Docs | Schema spec, API contract |
| **Guardrails** | QA | Regression tests, validation |

---

## 2. Implementation Order

1. **Baseline audit** — Document current state
2. **Loop 1** — Formalize core backbone (workflow_state, lifecycle_status)
3. **Loop 2** — Persistence/contract/boundary hardening
4. **Loop 3** (optional) — One refinement (guardrail, schema cleanup)
5. **Validation** — Run all scripts
6. **Report** — Final convergence

---

## 3. Test Plan

| Script | When |
|--------|------|
| run_inbox_triage_scenarios.py | After each loop |
| run_multi_turn_simulations.py | After each loop |
| audit_state_field_accuracy.py | After loop 1 |
| verify_speed_routing.py | After loop 1 |
| guardrail_inbox_triage.sh | After each loop |
| unified_intake_smoke_check.sh | Final |
| test_inbox_triage_api.py | Final (server on 8001) |
| verify_inbox_case_persistence.py | Final |

---

## 4. Likely Loop Count

- **Loop 1:** Core backbone (workflow_state, lifecycle_status)
- **Loop 2:** Persistence contract, origin_session_id
- **Loop 3:** Optional — one guardrail or schema validation

---

*See also: `07_ACCEPTANCE_SLA_CRITERIA.md`*
