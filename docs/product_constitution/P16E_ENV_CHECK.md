# P16-E Phase 1 — Preview Environment Check

**Date:** 2026-05-31  
**Command:** `vercel env ls` (project `andys-projects-1f411b73/ui`)

---

## Saved Vercel environment variables

| Variable | Production | Preview | Development |
|----------|------------|---------|-------------|
| `VITE_API_BASE_URL` | ✅ Encrypted (80d ago) | ❌ Missing | ❌ Missing |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ❌ Missing | ❌ Missing | ❌ Missing |

---

## Answers

### 1. Is Preview product-only env set?

**In saved Vercel env: NO.**  
**In this deployment: YES** — injected at build time via CLI:

```bash
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
```

Bundle verification: `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` name absent (dead-code eliminated); product-only strings present (`经纪人：请在本页`, `显示产品说明`, `原样粘贴微信`, inline practice labels).

### 2. Is API base URL correct?

**YES for this Preview build.** `fiqa-api-g7zatxrycq-uw.a.run.app` found in deployed JS bundle (`index-97qCgvUS.js`).

### 3. Are we avoiding Production?

**YES.**

- Deploy command used `vercel deploy` only (no `--prod`).
- `vercel inspect` → `target: preview`.
- Latest `vercel ls` entry: Preview 2m ago; Production entries unchanged (40d+).
- Production alias `ui-smoky-beta.vercel.app` still `age: 82519` (cache header) — no new Production deployment.

### 4. Are we using build env flags or saved Vercel env?

**Build env flags (`-b`)** for this deployment. Saved Preview env remains empty; repeat deploys must pass `-b` flags unless vars are added to Vercel dashboard.

---

## Recommendation (post-review, not executed)

After Andy approval, add to Vercel **Preview** (and eventually Production with founder gate):

- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`
- `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`

---

*End of P16-E Phase 1*
