# P16-F Phase 0 — Context

**Date:** 2026-05-31  
**Sprint:** P16-F Preview Network Debug + Role-C Simulation Test  
**Branch:** `sprint-a/broker-front-door`

---

## Confirmed inputs

| Item | Value |
|------|-------|
| **Preview URL** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app |
| **Expected API** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Product-only flag** | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` (injected at Preview build via `vercel deploy -b`, not saved in Vercel dashboard) |
| **Deployment ID** | `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN` (Preview, ~3h old at sprint time) |
| **Deployment alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app (also **not** in `ALLOWED_ORIGINS`) |

---

## Answers

### 1. What Preview URL is being tested?

**https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app**

Path under test: `/workbench/unified-intake`

### 2. What backend URL should it call?

**https://fiqa-api-g7zatxrycq-uw.a.run.app**

Verified in deployed bundle (`index-97qCgvUS.js`) and matches P16-E deploy flags.

### 3. What exact user-facing error appeared?

Andy reported:

> **Network Error（若控制台有 CORS 提示，请确认地址栏域名与后端 ALLOWED_ORIGINS 一致，优先打开生产别名 URL。）**

This string is emitted by `BrokerWorkbenchTab.tsx` when the initial queue load (`GET /api/inbox/cases`) fails with an axios network error — typically browser-blocked CORS, not an HTTP 401/500 body.

### 4. What are the likely causes?

| Cause | Likelihood | Evidence |
|-------|------------|----------|
| **CORS — Preview origin missing from Cloud Run `ALLOWED_ORIGINS`** | **Confirmed** | OPTIONS preflight returns `400 Disallowed CORS origin`; live `ALLOWED_ORIGINS` omits `ui-fvxlrxp4u-…` |
| Wrong `VITE_API_BASE_URL` in bundle | Ruled out | Bundle contains only `fiqa-api-g7zatxrycq-uw.a.run.app` |
| Backend down | Ruled out | `GET /health/live` → 200; `GET /readyz` → 200, `intake_path_ready: true` |
| Intake API key required | Ruled out | `UNIFIED_INTAKE_INTAKE_API_KEY` unset on Cloud Run; direct `POST /api/inbox/triage` succeeds without key |
| Vercel Deployment Protection | Secondary friction | Unauthenticated curl → SSO; Andy can log in but automation cannot |

**Primary root cause:** Cloud Run CORS allowlist does not include this Preview hostname.

---

*End of P16-F Phase 0*
