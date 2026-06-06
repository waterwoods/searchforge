# P16-R Phase 3 — Environment Audit

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Systems:** Vercel (`ui`), Cloud Run (`fiqa-api`), GitHub

---

## Vercel project `ui`

| Field | Value |
|-------|-------|
| Project ID | `prj_EKrXJgchOmcIMNNVhYiLIcg5B7TO` |
| Owner | andys-projects-1f411b73 |
| Node | 24.x |
| Framework | Vite |
| Git integration | **Not connected** (`vercel env add preview <branch>` fails) |
| Deploy model | CLI `vercel deploy` from `ui/` directory |

---

## Vercel environment variables (`vercel env ls`)

| Variable | Production | Preview | Notes |
|----------|------------|---------|-------|
| `VITE_API_BASE_URL` | ✅ Encrypted (81d) | ❌ **Missing** | Preview builds fail without CLI `-b` |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ Added P16-R (encrypted) | ❌ **Missing** | Production **not redeployed** after add |

### P16-R execution changes

| Action | Result |
|--------|--------|
| `vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY production --value 1` | ✅ Saved |
| `vercel env add … preview` (all / branch) | ❌ Blocked — no Git repo on project |
| `vercel deploy -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=…` | ✅ Latest Preview build |

**Rollback risk:** Next `vercel deploy` **without** `-b` flags reverts Preview to full dev UI unless dashboard Preview env is fixed or Git linked.

---

## Preview-only settings

| Setting | State | Impact |
|---------|-------|--------|
| **Deployment Protection (SSO)** | **ON** | Cold `curl` → **401** on Preview + `ui-waterwoods` alias |
| **Bypass** | `vercel curl --deployment <url>` works | Automation only — not broker-accessible |
| **Per-deploy hash URL** | New origin each deploy | Requires Cloud Run `ALLOWED_ORIGINS` patch (ops) |

---

## Cloud Run `fiqa-api` (us-west1)

| Variable | Value (2026-06-01 post P16-R) |
|----------|-------------------------------|
| `ALLOWED_ORIGINS` | `ui-smoky-beta`, `ui-ow4ovsfz4`, `ui-1qr8rzs2a`, `ui-git-main`, `ui-m7v0bbb5l`, `ui-fvxlrxp4u`, **`ui-iwnyo9ufa`**, `ui-waterwoods` |
| API URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |

| Check | Result |
|-------|--------|
| OPTIONS `ui-iwnyo9ufa` origin | **200** + `access-control-allow-origin` |
| OPTIONS `ui-fvxlrxp4u` (old preview) | **200** (still listed) |

**Drift risk:** `.env.cloudrun` updated P16-R with `ui-iwnyo9ufa`; full `deploy_cloud_run_core.sh` must keep complete list or patch reverts.

---

## GitHub

| Field | Value |
|-------|-------|
| Remote | `github.com:waterwoods/searchforge.git` |
| Branch | `sprint-a/broker-front-door` |
| Remote HEAD | `d05e94d` (post P16-R push) |
| Vercel ↔ Git | **Disconnected** — deploys are manual CLI |

---

## Runtime env summary by environment

| Env | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `VITE_API_BASE_URL` | `ALLOWED_ORIGINS` includes UI origin |
|-----|-----------------------------------|---------------------|--------------------------------------|
| Local demo | `1` | `http://127.0.0.1:8001` | N/A (permissive / local) |
| Preview latest | `1` (build) | Cloud Run (build) | ✅ after patch |
| Production live | **unset in bundle** | Cloud Run (dashboard) | ✅ smoky-beta only |

---

## Focus variables — pass/fail

| Variable | Required for parity | Status |
|----------|-------------------|--------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | Preview + Production persisted | **FAIL** Preview; **PARTIAL** Production (saved, not deployed) |
| `VITE_API_BASE_URL` | Preview + Production | **FAIL** Preview dashboard |
| `ALLOWED_ORIGINS` | Every Preview hash + aliases | **PASS** (after P16-R patch) |

---

## Recommendations (no production deploy)

1. Link Vercel project to GitHub **or** document mandatory `vercel deploy -b …` checklist.
2. Add Preview env vars via dashboard (all branches) once Git linked.
3. Disable Deployment Protection for Preview **or** issue shareable bypass link for Chen Kui trial.
4. Keep `.env.cloudrun` ALLOWED_ORIGINS in sync with `vercel ls` latest Preview URL.

---

*End of P16-R Phase 3 — Environment Audit*
