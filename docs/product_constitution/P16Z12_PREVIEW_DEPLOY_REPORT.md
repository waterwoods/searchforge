# P16-Z12 Phase 4 — Preview Deploy / Verify Report

**Date:** 2026-06-02

---

## Preview URL

https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app/workbench/unified-intake

*(Deployed P16-Z11; not redeployed in Z12 — backend parity blocked.)*

---

## Frontend bundle

| Check | Result |
|-------|--------|
| **Bundle marker** | `index-BbeKEpPA.js` |
| **API host in JS** | `fiqa-api-g7zatxrycq-uw.a.run.app` ✅ |
| **P16-O copy markers** | `请把您的需求发给我们`, `原样粘贴微信` ✅ |
| **`office_case_title` in bundle** | ✅ symbol present (UI ready for backend fields) |

---

## Product-only active

| Signal | Result |
|--------|--------|
| Customer-first paste copy | ✅ YES |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` in Vercel dashboard (Preview) | ❌ not set — build-time `-b` from last deploy assumed |
| Lab/sim markers absent in spot-check | ✅ YES (no `场景仿真` in bundle grep) |

**Product-only active:** **YES** (UI bundle evidence)

---

## CORS

Preflight from Preview origin:

```
OPTIONS https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage
Origin: https://ui-d7pyq2yau-andys-projects-1f411b73.vercel.app
→ HTTP 400 — Disallowed CORS origin
```

| Item | Result |
|------|--------|
| Preview host in local `.env.cloudrun` ALLOWED_ORIGINS | ❌ |
| Preview host in live Cloud Run ALLOWED_ORIGINS | ❌ |

**CORS:** **FAIL** (for this Preview deployment)

---

## SSO / Deployment Protection

| Check | Result |
|-------|--------|
| `curl -I` Preview root | HTTP **200**, no `401`, no SSO redirect |
| Workbench path | HTTP **200** |

**SSO:** **PASS** (cold URL loads HTML)

---

## Redeploy frontend?

Not required for API host (already Cloud Run). **Required after backend deploy:** add Preview origin to `ALLOWED_ORIGINS`, redeploy backend, optionally fresh `vercel deploy` with `-b` flags if URL hash changes.

Suggested command (after backend + CORS fix):

```bash
cd ui && vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

Then add new `ui-*.vercel.app` origin to `.env.cloudrun` before next backend deploy.
