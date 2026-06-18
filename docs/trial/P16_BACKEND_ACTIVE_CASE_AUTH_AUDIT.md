# P16 Backend Active-Case Auth Audit

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07  
**Backend:** https://fiqa-api-g7zatxrycq-uw.a.run.app

---

## Route under test

```http
GET /api/inbox/customer/active-case?phone={10-digit-us-phone}
```

Implementation: `services/fiqa_api/routes/inbox_triage.py` (`get_customer_active_case_by_phone`).  
Perimeter: `services/fiqa_api/security/intake_api_gate.py` — all `/api/inbox/*` except support/OAuth require shared secret when configured.

---

## Health / auth posture

```json
"intake_perimeter": {
  "intake_http_surface": "api_key_required",
  "intake_http_notes": "Inbox routes require UNIFIED_INTAKE_INTAKE_API_KEY via X-Unified-Intake-Api-Key or Authorization: Bearer ..."
}
```

Cloud Run has `UNIFIED_INTAKE_INTAKE_API_KEY` set. Backend is healthy (`ok: true`, phase `degraded` unrelated to this route).

---

## Test matrix

| Test | Phone | Auth header | HTTP status | Body summary |
|------|-------|-------------|-------------|--------------|
| No key | `2039935973` | none | **401** | `{"detail":"intake_api_unauthorized"}` |
| With key | `2039935973` | `X-Unified-Intake-Api-Key: <from .env.cloudrun>` | **200** | `has_active_case: true`, active case returned |
| With key | `6265551002` | same | **200** | `has_active_case: true`, `case_id: case_23e113d4b686` |
| With key | `5555551234` | same | **200** | `has_active_case: false` |
| CORS preflight | `2039935973` | OPTIONS from Preview origin | **200** | `OK` |

*(API key value not recorded in this doc.)*

---

## Answers

| Question | Answer |
|----------|--------|
| Does backend require API key? | **Yes** — `api_key_required` on Cloud Run |
| Does backend work with key? | **Yes** — HTTP 200 with valid key |
| Does backend reject without key? | **Yes** — HTTP 401 `intake_api_unauthorized` |
| Is route healthy? | **Yes** — not 404; returns structured JSON when authorized |

---

## Note on route docstring vs middleware

Route comment says "No auth; customer-facing." Middleware still applies because path is under `/api/inbox/`. In production-like Cloud Run deploys, **browser clients must send the intake API key** (via Vite build → `request.ts` interceptor).

---

*End of P16 Backend Active-Case Auth Audit*
