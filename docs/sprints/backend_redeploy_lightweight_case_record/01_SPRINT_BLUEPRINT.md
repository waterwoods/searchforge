# Backend Redeploy for Lightweight Case Record — Sprint Blueprint

**Sprint**: Backend Redeploy for Lightweight Case Record  
**Created**: 2026-03-15  
**Scope**: Ship already-implemented case-record backend to production

---

## 1. Why This Redeploy Is Needed Now

The Lightweight Production Case Record sprint added:
- message-level history (`case_messages`)
- persisted workflow state
- lightweight customer linkage fields
- updated lifecycle status values
- lazy migration / backward compatibility

The founder report states: **backend changes exist; redeploy is still needed.** Until redeployed, production does not reflect the new case-record model.

---

## 2. What Must Be Live

| Item | Location | Verification |
|------|----------|--------------|
| case_messages | case_store.py, API response | Case creation returns case_messages |
| Workflow state | handoff_ready, collected_fields, etc. | Persisted on save/append |
| Customer linkage | update_case_customer, PATCH /customer | Can set name/phone/policy |
| Lifecycle values | CASE_STATUS_VALUES | waiting_customer, agent_followup, closed |
| Lazy migration | _normalize_case | Old cases get case_messages on read |

---

## 3. What Counts as Success

- Backend deploy completes (exit 0)
- /healthz returns 200
- /readyz returns (ok:true or ok:false acceptable for triage path)
- POST /api/inbox/triage with persist_case creates case with case_messages
- POST /api/inbox/cases/{id}/append-message adds messages
- PATCH /api/inbox/cases/{id}/customer accepts and stores customer fields
- GET /api/inbox/cases returns cases with case_messages, workflow fields, customer fields

---

## 4. Out of Scope

- New features
- Frontend polish
- Case storage persistence across Cloud Run restarts (ephemeral by design)
