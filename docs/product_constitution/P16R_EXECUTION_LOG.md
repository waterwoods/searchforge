# P16-R Phase 8 — Execution Log

**Date:** 2026-06-01  
**Constraint:** Deploy/ops only — no features, no Constitution edits, no P17

---

## Changes executed

| Time (PDT) | Action | Result | Evidence |
|------------|--------|--------|----------|
| ~00:03 | Commit P16-O (`CustomerEntryTab`, `ui_copy.json`, `UnifiedIntakePage`) | ✅ `d05e94d` | `git log -1` |
| ~00:03 | Push `sprint-a/broker-front-door` | ✅ | `901b0df..d05e94d` on origin |
| ~00:03 | `vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY production` | ✅ | `vercel env ls` |
| ~00:03 | Preview env add (all branches) | ❌ Git not linked on Vercel project | CLI message |
| ~00:04 | `vercel deploy` (failed) | ❌ Missing Preview `VITE_API_BASE_URL` | build log |
| ~00:05 | `vercel deploy -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=…` | ✅ Preview Ready | https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app |
| ~00:06 | Cloud Run `ALLOWED_ORIGINS` + `ui-iwnyo9ufa` | ✅ revision `fiqa-api-00080-q48` | OPTIONS 200 |
| ~00:06 | Update `.env.cloudrun` ALLOWED_ORIGINS | ✅ | file diff (not committed) |

---

## Changes NOT executed (blocked / out of scope)

| Action | Reason |
|--------|--------|
| `vercel deploy --prod` | Phase 6 gate — explicit mission ban |
| Disable Vercel Deployment Protection | Requires Vercel dashboard / project settings — no CLI success |
| Persist Preview dashboard env vars | Vercel project has no Git connection |
| Andy browser E2E on Preview | SSO 401 |
| Stripe / payment ID fill | Ops — Andy |

---

## Artifacts

| Artifact | Location |
|----------|----------|
| New Preview deployment | `dpl_9zWWj1payFg4NuGdNVVe4C6aenwv` |
| New bundle | `index-CKPYkrkL.js` |
| waterwoods alias | Points to latest Preview (inspect) |
| Previous Preview | `ui-fvxlrxp4u` (superseded) |

---

## Rollback notes

| Rollback | How |
|----------|-----|
| Preview UI | `vercel redeploy ui-fvxlrxp4u-…` or promote prior deployment in dashboard |
| CORS | Restore previous `ALLOWED_ORIGINS` via `gcloud run services update` |
| Git | `git revert d05e94d` (not done) |

---

*End of P16-R Phase 8 — Execution Log*
