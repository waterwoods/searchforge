# P16-F Phase 2 — Backend CORS / Origin Check

**Date:** 2026-05-31  
**Backend:** https://fiqa-api-g7zatxrycq-uw.a.run.app

---

## Health probes

```bash
curl -si https://fiqa-api-g7zatxrycq-uw.a.run.app/health/live
# HTTP/2 200  {"ok":true}

curl -si https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz
# HTTP/2 200  ok:true, intake_path_ready:true, demo_mode:true
```

Backend is **alive** and intake path is ready.

---

## CORS preflight — Preview origin (FAIL)

```bash
curl -si -X OPTIONS https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage \
  -H "Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization,x-intake-api-key"
```

```
HTTP/2 400
vary: Origin
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-credentials: true
access-control-allow-headers: content-type,authorization,x-intake-api-key
(body) Disallowed CORS origin
```

**No `access-control-allow-origin` header** for Preview hostname.

Same result for `OPTIONS /api/inbox/cases` (initial queue load) and for deployment alias `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`.

---

## CORS preflight — production alias (PASS)

```bash
curl -si -X OPTIONS … \
  -H "Origin: https://ui-smoky-beta.vercel.app" …
```

```
HTTP/2 200
access-control-allow-origin: https://ui-smoky-beta.vercel.app
(body) OK
```

---

## Live Cloud Run env (`gcloud run services describe`)

```
ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,
  https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,
  https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,
  https://ui-git-main-andys-projects-1f411b73.vercel.app,
  https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app
```

**Missing:** `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app` (current Preview)

Note: `.env.cloudrun` matches live value (also omits new Preview hash).

---

## Answers

### 1. Does backend respond to health?

**YES.** `/health/live` and `/readyz` both return 200.

### 2. Does OPTIONS preflight allow Preview origin?

**NO.** Returns HTTP 400 with body `Disallowed CORS origin`.

### 3. Are required headers allowed?

**YES (when origin is allowed).** `access-control-allow-headers` includes `content-type`, `authorization`, `x-intake-api-key`. Failure is origin rejection, not header rejection.

### 4. Is Network Error caused by CORS?

**YES.** Browser sends `Origin: https://ui-fvxlrxp4u-…` on queue load and triage. Preflight fails → axios sees no response → UI surfaces Network Error with CORS hint (matches Andy's report).

### 5. What exact origin needs to be added?

```
https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app
```

Optional (same deployment, also blocked today):

```
https://ui-waterwoods-andys-projects-1f411b73.vercel.app
```

For repeat Preview deploys, consider also adding branch-pattern URLs or adopting Option C (see `P16F_FIX_OPTIONS.md`).

---

*End of P16-F Phase 2*
