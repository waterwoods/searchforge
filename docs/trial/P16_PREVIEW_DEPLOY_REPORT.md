# P16 Preview Deploy Report — Office Visibility

**Sprint:** P16-VERIFY-AND-DEPLOY-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Phase:** 3 — Deploy Preview (triggered: stale Preview lacked fix)

---

## Trigger

Phase 1 audit: Preview alias `ui-waterwoods` served **`index-CJ0tCunS.js`** (2026-06-05) **without** Office Visibility scoring or enhanced product-only cards.

---

## Deploy procedure (Preview only — no production)

```bash
cd ui
source ../scripts/with_node22_path.sh

# Build env from .env.cloudrun (gitignored)
set -a && source ../.env.cloudrun && set +a

vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY="${UNIFIED_INTAKE_INTAKE_API_KEY}"

vercel alias set ui-erdln9896-andys-projects-1f411b73.vercel.app \
  ui-waterwoods-andys-projects-1f411b73.vercel.app
```

### Build prerequisites applied

| Issue | Mitigation |
|-------|------------|
| `CustomerEntryTab.tsx` missing `p16z21` prototypes broke Vite build | Checked out buildable `CustomerEntryTab.tsx` from `d05e94d` for upload only |
| Queue 401 without API key header | Restored `ui/src/api/request.ts` intake-key interceptor |

**Production aliases:** Not touched. No `vercel --prod`.

---

## Deployment record (canonical)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL` |
| **Deployment URL** | `https://ui-erdln9896-andys-projects-1f411b73.vercel.app` |
| **Alias (use this)** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Workbench path** | `/workbench/unified-intake` |
| **Timestamp (Vercel)** | Sat Jun 06 2026 06:09:59 PDT |
| **Build stamp (bundle)** | `2026-06-06T13:10:04.774Z` |
| **Bundle hash** | `index-DMOKMAa_.js` |
| **Target** | Preview |
| **Status** | Ready |
| **Git SHA** | **Not git-linked** — CLI upload; base repo HEAD `b3c8ec3` + uncommitted visibility WIP |

### Intermediate deploy (superseded)

First deploy (`dpl_8rcteSMPHVV1S81wHcaJjThpX1tQ`, `index-xU09sFIl.js`) lacked API key in bundle → queue unauthorized. Superseded by final deploy above.

---

## Post-deploy checks

| Check | Result |
|-------|--------|
| Alias points to new deployment | ✅ |
| CORS preflight (`OPTIONS /api/inbox/cases`) | ✅ HTTP 200 |
| Bundle contains visibility markers | ✅ |
| Bundle contains intake API key | ✅ |
| Production `ui-smoky-beta.vercel.app` unchanged | ✅ |

---

## Deploy verdict

**Preview updated successfully.** Office Visibility UI fix is live on `ui-waterwoods` alias.
