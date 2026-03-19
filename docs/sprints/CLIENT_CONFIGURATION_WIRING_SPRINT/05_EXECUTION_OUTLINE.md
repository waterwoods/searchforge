# Client Configuration Wiring — Execution Outline

**Sprint:** Client Configuration Wiring Sprint  
**Created:** 2026-03-18

---

## Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|---------------|
| Config boundary | Config worker | get_ui_copy(client_id), get_active_client_id |
| Backend | Backend worker | GET /api/inbox/client-config |
| Frontend | Frontend worker | useClientConfig, wire UnifiedIntakePage, AppLayout |
| Second client | Config worker | configs/clients/demo_broker/ |
| QA | QA worker | guardrail, build, manual variation check |

---

## Implementation Order

1. **config_loader:** Add `get_ui_copy(client_id)`, `get_active_client_id()`
2. **Backend:** Add GET /api/inbox/client-config
3. **Frontend:** Add getClientConfig API, useClientConfig hook
4. **Frontend:** Wire UnifiedIntakePage and AppLayout to use config
5. **Second client:** Create demo_broker ui_copy.json
6. **Validation:** guardrail_inbox_triage.sh, npm run build

---

## Test Plan

- `bash scripts/guardrail_inbox_triage.sh` — PASS
- `cd ui && npm run build` — PASS
- Manual: Load ?client=chen_kui (default) — Chen Kui copy
- Manual: Load ?client=demo_broker — Demo broker copy

---

## Loop Plan

- **Loop 1:** Wire UI copy (API + frontend load)
- **Loop 2:** Wire handoff/runtime; client selection
- **Loop 3:** Second demo client; variation demo hardening
