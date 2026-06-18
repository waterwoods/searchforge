# P16 Preview Environment Audit

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07  
**Project:** `andys-projects-1f411b73/ui` (Vercel CLI)

---

## Method

```bash
cd ui && vercel env ls
vercel env ls production
vercel env ls preview
vercel env ls development
```

Plus bundle inspection of deployed Preview (`index-CMdMnAqV.js` pre-fix, `index-Bb0VZ9fA.js` post-fix). **No secret values printed.**

---

## Vercel dashboard variables

| Variable | Production | Preview | Development |
|----------|:----------:|:-------:|:-----------:|
| `VITE_API_BASE_URL` | ✅ present (encrypted) | ❌ absent | ❌ absent |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ present (encrypted) | ❌ absent | ❌ absent |
| `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO` | ❌ absent | ❌ absent | ❌ absent |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | ❌ absent | ❌ absent | ❌ absent |

**Note:** Only two dashboard vars exist, both **Production-only**. Preview and Development have **zero** dashboard env vars.

---

## Answers

| Question | Answer |
|----------|--------|
| Was the API key available to the Preview build (pre-fix)? | **No** — baked as empty string |
| Was it Production-only? | **N/A** — key is not in Vercel dashboard at all (any environment) |
| Was it missing entirely? | **From dashboard: yes.** From deploy flags: depends on operator |
| Was it injected via deploy `-b` flag? | **Pre-fix deploy (router recovery): no.** Post-fix deploy: yes |
| Was the deployed bundle built without the key? | **Pre-fix: yes** (`const t="".trim()`). **Post-fix: no** (48-char key present, length only) |

---

## Pre-fix deploy build flags (P16 QA router recovery)

From `docs/trial/P16_QA_ROUTER_DEPLOY_REPORT.md`:

```text
VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1
VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1
```

**Missing:** `VITE_UNIFIED_INTAKE_INTAKE_API_KEY`

That deploy produced bundle `index-CMdMnAqV.js` aliased to `ui-waterwoods`.

---

## Established practice (prior successful Preview deploys)

`docs/trial/P16_PREVIEW_DEPLOY_REPORT.md` documents canonical Preview deploy:

```bash
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY="${UNIFIED_INTAKE_INTAKE_API_KEY}"  # from .env.cloudrun
```

Preview builds rely on **CLI `-b` flags**, not Vercel dashboard Preview scope.

---

## Local reference files (not committed)

| File | Purpose |
|------|---------|
| `.env.cloudrun` (repo root, gitignored) | Source for `UNIFIED_INTAKE_INTAKE_API_KEY` at deploy time |
| `ui/.vercel/.env.preview.local` | Local preview pull (gitignored) |

---

*End of P16 Preview Environment Audit*
