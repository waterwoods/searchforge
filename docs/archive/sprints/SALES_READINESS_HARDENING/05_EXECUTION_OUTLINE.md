# Execution Outline

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| **Talk to Agent** | Talk-to-Agent worker | Triggers, wording, handoff payload, free-text detection |
| **Edge cases** | Edge-case worker | Billing "我发你了", Talk to Agent mid-flow, late correction |
| **Handoff / office** | Workbench worker | customer_requested_human display, context badges |
| **QA / simulation** | QA worker | Run scenarios, guardrails, smoke check |

---

## 2. Implementation Order

| Phase | Work | Deliverables |
|-------|------|---------------|
| **Loop 1** | Talk to Agent: free-text markers, handoff payload, office display | triage.py markers; handoff_phrases; UI case focus for customer_requested_human |
| **Loop 2** | Edge cases: billing "我发你了" verify; Talk to Agent mid-flow | Config/scenario verify; triage early check for human request |
| **Loop 3** | Handoff hardening: customer_requested_human badge; summary alignment | UI badge; ensure prior context in handoff |

---

## 3. Test Plan

| Test | Command / Action |
|------|------------------|
| Inbox triage | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| Multi-turn | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| Smoke | `bash scripts/unified_intake_smoke_check.sh` |
| State field | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` |
| API test | `python3 scripts/test_inbox_triage_api.py` (server on 8001) |
| UI build | `cd ui && npm run build` |

---

## 4. Loop Plan

- **Loop 1:** Talk to Agent strengthening (highest value)
- **Loop 2:** 1–2 edge cases (billing "我发你了", Talk to Agent mid-flow)
- **Loop 3:** Handoff/trust hardening (badges, context)
- **Loop 4:** Optional; only if clearly valuable, low-risk refinement remains

---

*End of Execution Outline*
