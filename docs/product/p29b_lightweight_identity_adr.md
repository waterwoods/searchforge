# ADR — P29B Lightweight Identity & Session Foundation

**Date:** 2026-07-19  
**Status:** Accepted — Implemented  
**Sprint:** P29B  
**Constitution:** `docs/product/p29b_lightweight_identity_constitution.md`  
**Related:** P29 Service Home (D-011) · One Active Case (D-001) · Decision Log D-012  

---

## Decision

Add the smallest OpenID → Active Case resume layer for Mini Program **Continue Current Task**. Do **not** build a Customer Account, profile, history, or multi-session product.

---

## Options considered

| Option | Verdict |
|--------|---------|
| **A. Opaque person_link + Active Case index** | **Accepted** |
| B. Full Customer Account + Profile Center | Rejected — out of scope; feature gravity |
| C. Local resume token only (status quo) | Rejected — fails return-later after storage clear / new device |
| D. Phone-mandatory login before claim | Rejected — blocks stressed first-time start |

---

## Files added

| File | Role |
|------|------|
| `services/fiqa_api/inbox_triage/mp_customer_identity.py` | wx code exchange, bind/lookup, resume |
| `services/fiqa_api/db/schema/migrations/005_p29b_mp_customer_active_case.sql` | Additive index table |
| `tests/test_p29b_lightweight_identity.py` | Focused correctness tests |
| `docs/product/p29b_lightweight_identity_constitution.md` | Product law |
| `docs/product/p29b_lightweight_identity_adr.md` | This ADR |

## Files modified

| File | Role |
|------|------|
| `services/fiqa_api/routes/h5_task_intake.py` | `POST /api/h5/customer/session`; `force_new` on start-claim |
| `services/fiqa_api/inbox_triage/p20_customer_start_claim.py` | Bind / resume / force_new |
| `services/fiqa_api/inbox_triage/p20_case_intake_command_service.py` | Safe source_text; entry_channel; person_link stamp |
| `services/fiqa_api/db/service_record_repository.py` | structured_payload keys |
| `miniapp/services/sessionIdentityAdapter.ts` | wx.login → session |
| `miniapp/services/startClaimApi.ts` | Opaque session + force_new |
| `miniapp/pages/service-home/service-home.ts` | Session lookup before Continue |
| `miniapp/app.ts` | Launch session warm |
| `miniapp/utils/storage.ts` | session_id + force_new markers |
| `miniapp/utils/startClaimEntry.ts` | Explicit Start New Claim → force_new |
| `miniapp/tests/miniprogramMocks.ts` | `wx.login` mock |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Source label; hide link keys |
| `ui/src/api/inboxTriage.ts` | `entry_channel` / `created_by_actor` types |
| `docs/product/decision_log.md` | D-012 |

---

## Startup simplicity verdict

**Yes — simple enough for first paying customers**, if we keep the freeze:

- One table (active-case pointer), no account product  
- OpenID never leaves the server exchange  
- Resume = existing signed token path  

Any Profile / History / Dashboard work must stay recorded-only until demand proves it.
