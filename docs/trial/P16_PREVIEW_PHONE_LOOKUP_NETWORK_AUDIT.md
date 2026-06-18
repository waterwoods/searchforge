# P16 Preview Phone Lookup — Network Audit

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07  
**Preview URL (pre-fix):** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
**Bundle (pre-fix):** `index-CMdMnAqV.js`

---

## Test inputs

| Field | Value |
|-------|-------|
| Phone | `2039935973` |
| Name | `test` |
| Action | Continue / 继续 |

---

## Observed request (browser, pre-fix)

| Field | Value |
|-------|-------|
| **Request URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/customer/active-case?phone=2039935973&client_id=chen_kui` |
| **HTTP method** | `GET` |
| **Status code** | **401** |
| **Response body** | `{"detail":"intake_api_unauthorized"}` |
| **X-Unified-Intake-Api-Key** | **Absent** (not sent) |
| **VITE_API_BASE_URL (in bundle)** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` ✅ correct |

### Bundle evidence (pre-fix)

Request interceptor in `index-CMdMnAqV.js`:

```text
const t="".trim(); return t && (e.headers["X-Unified-Intake-Api-Key"]=t)
```

`VITE_UNIFIED_INTAKE_INTAKE_API_KEY` was baked as an **empty string** at build time.

### UI result (pre-fix)

After Continue, UI returned to entry screen with:

> 无法验证手机号，请稍后再试。

(`CustomerFirstEntryScreen.tsx` catch block on any API failure.)

---

## Direct reproduction (curl, no browser)

```bash
curl "https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/customer/active-case?phone=2039935973"
# → 401 {"detail":"intake_api_unauthorized"}
```

Browser `fetch()` without key (CDP, pre-fix): **401**, same body.

---

## Classification

| Hypothesis | Verdict |
|------------|---------|
| 401/403 auth failure | **YES — root cause** |
| 404 route missing | No — route exists, returns 401 not 404 |
| 500 backend error | No |
| CORS failure | No — request reaches Cloud Run; OPTIONS preflight returns 200 |
| Wrong API base URL | No — URL is correct Cloud Run host |
| Missing API key in Preview build | **YES — proximate cause** |

---

## Backend health context

`GET /health` reports `intake_http_surface: api_key_required` on Cloud Run. All `/api/inbox/*` routes (including `/customer/active-case`) require `X-Unified-Intake-Api-Key` when `UNIFIED_INTAKE_INTAKE_API_KEY` is set server-side.

---

*End of P16 Preview Phone Lookup Network Audit*
