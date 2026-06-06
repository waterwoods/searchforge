# Client-Aware Handoff Wiring — Execution Outline

---

## Workstreams

| Workstream | Owner | Tasks |
|------------|-------|-------|
| Config loader | Backend | Add `get_handoff_phrases(client_id)`, `get_reply_templates(client_id)` | 
| Triage engine | Backend | Pass `client_id` through `triage_conversation`, use client-aware phrases |
| API route | Backend | Add `client_id` to TriageRequest, pass to triage |
| demo_broker config | Config | Create `handoff_phrases.json` for demo_broker |
| Frontend | UI | Pass `client_id` from ClientConfigContext to triage API |
| Validation | QA | Update tests, add A/B API test |

---

## Implementation Order

1. **Config loader** — `get_handoff_phrases(client_id)` with fallback to chen_kui
2. **Triage** — `triage_conversation(client_id=...)`, `_get_handoff_phrases(client_id)`
3. **API** — TriageRequest.client_id, pass to triage
4. **demo_broker** — Create handoff_phrases.json
5. **Frontend** — triageMessage(..., clientId)
6. **Tests** — Guardrail, API test with client_id

---

## Test Plan

- `bash scripts/guardrail_inbox_triage.sh` — must pass
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` — must pass
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` — must pass
- New: `scripts/test_client_aware_handoff.py` — A/B variation via API

---

## Loop Plan

- **Loop 1:** Wire client_id into triage path
- **Loop 2:** Wire client-aware handoff phrases
- **Loop 3:** A/B variation demo hardening (demo_broker config, frontend, tests)

---

*End of Outline*
