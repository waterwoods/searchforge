# P16-E Phase 3 — Preview Deployment

**Date:** 2026-05-31  
**Branch (git HEAD):** `sprint-a/broker-front-door` @ `c92cabf`  
**Sprint A commit (git):** `c2e3dff5eb6e25e14cd6ea2577bbf4ea61333853`  
**Node fix commit (git):** `c92cabfc364348ce30c5a882cdc1b720e51b7b69`

---

## Deploy command (Preview only)

```bash
cd ui
source ../scripts/with_node22_path.sh
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

---

## Deployment record

| Field | Value |
|-------|-------|
| **Preview URL** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app |
| **Path for review** | `/workbench/unified-intake` |
| **Full review URL** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Deployment ID** | `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN` |
| **Inspect** | https://vercel.com/andys-projects-1f411b73/ui/9g9SJYNDNxgKKE872M9Adq1REvKN |
| **Environment** | **Preview** (`target: preview`) |
| **Status** | Ready (~54s build) |
| **Alias** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` (team preview alias) |
| **Created** | 2026-05-31 ~02:55 PDT |

---

## Commit / artifact truth

| Question | Answer |
|----------|--------|
| Git-linked commit on Vercel? | **Not shown** — CLI deploy from local `ui/` upload (no git metadata in build log) |
| Intended code base | `c92cabf` branch including `c2e3dff` Sprint A |
| **Caveat** | **5 uncommitted `ui/` files** were in the uploaded tree (see P16E_CONTEXT_CHECK.md) |

---

## Build env (baked into bundle)

- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` ✅
- `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app` ✅

---

## Production impact

**Production changed: NO**

Evidence:

- No `vercel --prod` executed.
- `vercel ls` shows new deployment as **Preview** only; Production deployments remain 40+ days old.
- `ui-smoky-beta.vercel.app` unchanged (stale `age` header on probe).

---

## Access note

Preview URLs return **HTTP 401** without Vercel authentication (Deployment Protection). Andy must:

- Log in via Vercel SSO when opening the URL, **or**
- Use `vercel curl` / protection bypass token for automation.

CLI `vercel curl` successfully fetched HTML and JS with protection bypass.

---

*End of P16-E Phase 3*
