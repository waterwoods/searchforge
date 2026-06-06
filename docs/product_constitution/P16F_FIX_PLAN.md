# P16-F Phase 7 — Fix Plan (DO NOT APPLY WITHOUT ANDY APPROVAL)

**Date:** 2026-05-31  
**Status:** Proposed — **not executed**

---

## Root cause

Cloud Run `ALLOWED_ORIGINS` does not include the P16-E Preview hostname:

`https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app`

Browser CORS preflight returns `400 Disallowed CORS origin` → axios Network Error on `GET /api/inbox/cases` and `POST /api/inbox/triage`.

Frontend env and API URL are **correct**. Backend is **alive**. Auth key is **not** required.

---

## Exact fix (Option B)

### 1. Patch Cloud Run env (no redeploy required)

**DO NOT RUN until Andy approves.**

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app,https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app,https://ui-waterwoods-andys-projects-1f411b73.vercel.app'
```

Uses `^@^` delimiter because values contain commas (per `scripts/deploy_cloud_run_core.sh` convention).

### 2. Verify (safe to run after patch)

```bash
curl -si -X OPTIONS \
  https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/cases \
  -H "Origin: https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type"
# Expect: HTTP 200 + access-control-allow-origin: https://ui-fvxlrxp4u-…
```

Andy browser: hard refresh Preview workbench → queue should load → paste test message → triage should return 200.

### 3. Keep deploy bundle in sync (docs-only proposal for `.env.cloudrun`)

Add the two new origins to `ALLOWED_ORIGINS` in `.env.cloudrun` before next full backend deploy so a deploy does not revert the patch.

**Not applied in this sprint** (backend file change only when Andy approves follow-up commit).

---

## Rollback

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project optimal-disk-472305-e2 \
  --update-env-vars '^@^ALLOWED_ORIGINS=https://ui-smoky-beta.vercel.app,https://ui-ow4ovsfz4-andys-projects-1f411b73.vercel.app,https://ui-1qr8rzs2a-andys-projects-1f411b73.vercel.app,https://ui-git-main-andys-projects-1f411b73.vercel.app,https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app'
```

Restores prior live list (verified via `gcloud` at sprint time).

---

## Risk

| Risk | Level | Mitigation |
|------|-------|------------|
| Wrong origin added | Low | Exact URL from Vercel `vercel ls` / Andy address bar |
| Over-broad allowlist | Low | Only adding known deployment URLs |
| Full deploy overwrites env | Medium | Update `.env.cloudrun` before next `deploy_paid_pilot.sh` |
| Production deploy | None | **No production Vercel or backend deploy in this sprint** |

---

## Redeploy required?

**No Cloud Run redeploy** for env patch — `gcloud run services update` rolls new revision with updated env only.

**No Production Vercel deploy.**

Optional later: save `VITE_*` vars in Vercel Preview dashboard (frontend config, not CORS fix).

---

*End of P16-F Phase 7*
