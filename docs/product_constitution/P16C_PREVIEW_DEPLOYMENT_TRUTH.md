# P16-C Phase 1 — Preview Deployment Truth

**Date:** 2026-05-31  
**Branch under test:** `sprint-a/broker-front-door`  
**Sprint A commit:** `c2e3dff5eb6e25e14cd6ea2577bbf4ea61333853`

---

## Summary

| Question | Answer |
|----------|--------|
| Vercel Preview exists for `sprint-a/broker-front-door`? | **NO** |
| Preview uses commit `c2e3dff`? | **NO** — no deployment tied to this branch |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on Vercel? | **NO** — not configured in any environment |
| `VITE_API_BASE_URL` on Vercel Preview? | **NO** — Preview env has zero variables |
| `VITE_API_BASE_URL` on Vercel Production? | **YES** — set 80d ago (encrypted) |
| Production alias live? | **YES** — `https://ui-smoky-beta.vercel.app` (200 OK) |
| Production includes Sprint A code? | **NO** — still pre-Sprint A UI |

---

## Git State

```
Branch:  sprint-a/broker-front-door
HEAD:    c2e3dff Sprint A broker front door implementation
Tracking: origin/sprint-a/broker-front-door
Dirty:   ~1,345 unrelated paths (reduction/archive) — not committed
```

---

## Vercel Deployment Inventory (`vercel ls`)

Latest deployments (2026-05-31 query):

| Age | URL | Environment | Status |
|-----|-----|-------------|--------|
| 26d | `https://ui-m7v0bbb5l-andys-projects-1f411b73.vercel.app` | Preview | Ready |
| 26d | `https://ui-29lrqx790-andys-projects-1f411b73.vercel.app` | Preview | Error |
| 40d | `https://ui-cupempwva-andys-projects-1f411b73.vercel.app` | Production | Ready |

**No deployment created after Sprint A push (`c2e3dff`).**  
Vercel Git integration did **not** auto-build `sprint-a/broker-front-door` (or branch was not connected / no webhook fired).

### Latest Preview inspect (`ui-m7v0bbb5l…`)

- **Created:** 2026-05-04 (26 days before Sprint A)
- **Target:** preview
- **Commit:** Not linked to `c2e3dff` (predates Sprint A by weeks)
- **Alias:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`

---

## Vercel Environment Variables (`vercel env ls`)

| Variable | Production | Preview | Development |
|----------|------------|---------|-------------|
| `VITE_API_BASE_URL` | ✅ Encrypted | ❌ Missing | ❌ Missing |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ❌ Missing | ❌ Missing | ❌ Missing |

**Critical:** Sprint A UI changes are **gated at build time** by `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` (`ui/src/config/productSurface.ts`). Without this variable baked into the bundle, Vercel builds show **full operator UI** (Simulation tab, 我的办理, 客户报送 default, engineer chrome).

---

## Production vs Sprint A (browser evidence)

| Check | Production (`ui-smoky-beta.vercel.app`) | Local product_only build (`c2e3dff` + env) |
|-------|----------------------------------------|-------------------------------------------|
| Default tab | 客户报送 | 办公室工作台 ✅ |
| 我的办理 tab | Visible | Hidden ✅ |
| 场景仿真 tab | Visible | Hidden ✅ |
| Inline practice | Absent | Present ✅ |
| Wayfinding banner | Absent | Present ✅ |

Production **does not reflect Sprint A** even if merged without env change.

---

## Cloud Run API (reference)

| Endpoint | Status |
|----------|--------|
| `https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz` | 200 OK |
| Triage API smoke | 5/5 messages returned 200 (see P16C_REAL_MESSAGE_SMOKE_TEST.md) |

**CORS note:** Local preview at `http://127.0.0.1:4173` could not complete demo queue E2E — likely `ALLOWED_ORIGINS` does not include localhost preview origin. Vercel Preview URLs must be in `ALLOWED_ORIGINS` for queue/demo to work.

---

## Preview URL for P16-C

| URL | Valid for Sprint A review? |
|-----|---------------------------|
| Vercel branch Preview | **None exists** |
| Production alias | **No** — wrong commit + wrong env |
| **Local product_only preview** | **Yes (code verification only)** — `http://127.0.0.1:4173/workbench/unified-intake` after build with env vars |

---

## Do NOT Deploy Automatically

Per P16-C rules: **Production not updated.**

---

## Exact Commands to Create Sprint A Preview

### Option A — CLI deploy with build-time env (recommended for immediate Andy review)

```bash
cd /home/andy/searchforge/ui
source ../scripts/with_node22_path.sh

vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

Then add the printed `https://ui-….vercel.app` origin to Cloud Run `ALLOWED_ORIGINS` if queue/API calls fail (CORS).

### Option B — Persist env in Vercel dashboard (required before Production)

```bash
cd ui
vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY production
# Enter: 1

vercel env add VITE_UNIFIED_INTAKE_PRODUCT_ONLY preview
# Enter: 1

# Confirm VITE_API_BASE_URL also exists for Preview:
vercel env add VITE_API_BASE_URL preview
# Enter: https://fiqa-api-g7zatxrycq-uw.a.run.app
```

Then redeploy from `sprint-a/broker-front-door`:

```bash
git checkout sprint-a/broker-front-door
cd ui && vercel deploy --yes   # preview
# OR after merge + env: vercel deploy --prod --yes
```

### Option C — Connect Git branch (long-term)

Vercel Project → Git → ensure `waterwoods/searchforge` connected → enable Preview Deployments for all branches → push `sprint-a/broker-front-door` triggers build (still needs Preview env vars from Option B).

---

*End of P16-C Phase 1 — Preview Deployment Truth*
