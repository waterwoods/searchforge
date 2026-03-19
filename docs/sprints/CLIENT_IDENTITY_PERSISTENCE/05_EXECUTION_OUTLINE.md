# Client Identity Persistence — Execution Outline

---

## Workstreams

| Workstream | Owner | Tasks |
|------------|-------|-------|
| Case persistence | Backend | Add client_id to save_case, _normalize_case |
| Append flow | Backend | triage_for_append(client_id), route passes case.client_id |
| API route | Backend | persist_case passes client_id; append uses case.client_id |
| Frontend | UI | appendFollowUpMessage optional clientId (fallback for legacy) |
| Validation | QA | Guardrail, test script |

---

## Implementation Order

1. **Loop 1:** Persist client_id on cases (save_case, case_store)
2. **Loop 2:** Wire append/follow-up to use case client_id (triage_for_append, route)
3. **Loop 3:** A/B demo hardening; verification test

---

## Test Plan

- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- New: append flow uses case client_id (manual or script)
- Manual: create case ?client=chen_kui, append with ?client=demo_broker open → draft stays chen_kui

---

## Loop Plan

- **Loop 1:** Persist client_id on save_case; route passes it
- **Loop 2:** triage_for_append(client_id); append route passes case.client_id
- **Loop 3:** Verification script; founder inspection notes
