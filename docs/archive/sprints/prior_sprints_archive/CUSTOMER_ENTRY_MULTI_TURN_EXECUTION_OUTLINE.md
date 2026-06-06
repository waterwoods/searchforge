# Customer Entry Multi-Turn Repair — Execution Outline

**Sprint:** Customer Entry True Multi-Turn Repair + Guardrail Sprint

---

## Audit + Repair Workstreams

| Workstream | Scope | Order |
|------------|-------|-------|
| **Backend continuity** | inbox_triage route, triage_conversation path | 1 |
| **Similar-bug search** | triage_for_append, frontend, case_store | 2 |
| **Frontend continuity** | handoff_ready UX, input visibility | 2 |
| **Guardrail docs** | Multi-Turn Continuity Guardrail Spec | 3 |

---

## Implementation Order

1. **Baseline audit** — Reproduce continuity failure across 5 scenarios; document exact behavior
2. **Loop 1** — Fix primary backend bug: first message through `triage_conversation`
3. **Loop 2** — Search for similar continuity breaks; fix highest-value ones
4. **Loop 3** — Optional refinement (regression test, UI wording)
5. **Redeploy** — Backend + frontend if changed
6. **Post-deploy verification** — Confirm production behavior

---

## Test Plan

| Test | Command | Purpose |
|------|---------|---------|
| Inbox triage scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | Category/urgency regression |
| Multi-turn simulations | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | Handoff timing |
| State field accuracy | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` | State model |
| Speed routing | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` | Routing sanity |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | Full guardrail |
| Unified intake smoke | `bash scripts/unified_intake_smoke_check.sh` | End-to-end smoke |

---

## Likely Loop Count

- **Loop 1:** Primary fix (required)
- **Loop 2:** Similar-bug search (required)
- **Loop 3:** Optional refinement (only if clear low-risk improvement)

---

*End of outline*
