# P16-F.5 Phase 1 — CORS Plan

**Date:** 2026-05-31  
**Sprint:** P16-F.5 Preview Unblock + Full Capability Revalidation  
**Status:** Validated — **CORS still blocking Preview** (fix not applied since P16-F)

---

## Current URLs

| Item | Value |
|------|-------|
| **Preview URL (P16-E deploy)** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app |
| **Preview alias (same deployment)** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Cloud Run API** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Production alias (CORS OK, pre-Sprint A)** | https://ui-smoky-beta.vercel.app |

---

## Live `ALLOWED_ORIGINS` (gcloud, 2026-05-31)

```
https://ui-smoky-beta.vercel.app,
https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,
https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,
https://ui-git-main-andys-projects-1f411b73.vercel.app,
https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app
```

**Missing (confirmed blocked):**

- `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app` ← current Sprint A Preview
- `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` ← deployment alias

---

## ROOT_CAUSE

Cloud Run CORS middleware rejects the **page origin** sent by the browser on Preview. The P16-E Preview hostname was never added to `ALLOWED_ORIGINS`. Preflight returns HTTP 400 with body `Disallowed CORS origin` and **no** `access-control-allow-origin` header.

This is **not**:

- Wrong `VITE_API_BASE_URL` — bundle contains only `fiqa-api-g7zatxrycq-uw.a.run.app` ✅
- Backend down — `/health/live` and `/readyz` return 200; `intake_path_ready: true` ✅
- Auth key required — `POST /api/inbox/triage` succeeds without key from curl ✅

Axios in `BrokerWorkbenchTab.tsx` surfaces this as `Network Error（若控制台有 CORS 提示…）` on initial `GET /api/inbox/cases`.

---

## Endpoint verification (Preview origin)

All OPTIONS preflights from `Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app`:

| Endpoint | Method | OPTIONS | Notes |
|----------|--------|---------|-------|
| `/api/inbox/cases` | GET | **400 Disallowed** | Initial queue load — first failure users see |
| `/api/inbox/triage` | POST | **400 Disallowed** | Paste → triage |
| `/api/inbox/cases/{id}` | GET | **400 Disallowed** | Case detail after open |
| `/health/live` | GET | **400 Disallowed** | Not used by workbench UI today |
| `/readyz` | GET | **400 Disallowed** | Not used by workbench UI today |

**Control (production alias):** `Origin: https://ui-smoky-beta.vercel.app` → OPTIONS `/api/inbox/cases` → **200** + `access-control-allow-origin: https://ui-smoky-beta.vercel.app`.

**Control (older Preview in allowlist):** `Origin: https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app` → **200** — but that deployment is **not** the Sprint A Preview bundle.

Direct POST/GET to Cloud Run **without** browser Origin header works; backend engine is healthy.

---

## FIX

**Recommended: Option B (env patch only)** — same as `P16F_FIX_PLAN.md`. Add current Preview origins to Cloud Run `ALLOWED_ORIGINS`:

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app,https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app,https://ui-waterwoods-andys-projects-1f411b73.vercel.app'
```

**Follow-up (before next full backend deploy):** Add the same origins to `.env.cloudrun` so `deploy_paid_pilot.sh` does not revert the patch.

**Not recommended for Sprint A validation:** Option A (send users to `ui-smoky-beta`) — CORS passes but UI is **pre-Sprint A** (wrong default tab, no product_only).

**Deferred:** Option C (wildcard Vercel preview pattern) — requires CORS policy discussion; out of scope for validation-only sprint.

---

## VALIDATION

After env patch:

```bash
# 1. Preflight must return 200 + allow-origin
curl -si -X OPTIONS https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/cases \
  -H "Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type"
# Expect: HTTP 200, access-control-allow-origin: https://ui-fvxlrxp4u-…

# 2. Triage preflight
curl -si -X OPTIONS https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage \
  -H "Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
# Expect: HTTP 200

# 3. Browser (Andy authenticated on Preview)
# - Hard refresh /workbench/unified-intake
# - Queue loads (no Network Error banner)
# - Paste cancellation text → 开始整理 → case + draft visible
# - 加载演示队列 → progress → cancellation case auto-opens
```

Guardrail (engine regression): `bash scripts/guardrail_inbox_triage.sh` — **PASS** at validation time (unchanged by CORS env patch).

---

## ROLLBACK

Restore prior live allowlist (5 origins, verified 2026-05-31):

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app'
```

No Cloud Run redeploy required for apply or rollback — `gcloud run services update` rolls a new revision with updated env only.

---

*End of P16-F.5 Phase 1*
