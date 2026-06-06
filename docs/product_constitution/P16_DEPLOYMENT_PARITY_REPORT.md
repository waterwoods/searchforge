# P16 Deployment Parity Report

**Date:** 2026-06-05  
**Mission:** P16 Release Freeze — Phase 4  
**Mode:** Read-only audit (live curl + gcloud + vercel inspect)  
**Baseline SHA:** `517f728` (`release/p16-demo-ready-v1`)

---

## Verdict: **CONDITIONAL PASS**

Preview demo path is **functionally aligned** for broker trial via the **`ui-waterwoods` alias**. Full three-surface parity (local = Preview = Production) is **not** achieved. Backend is **one commit behind** the frozen baseline.

| Surface | Aligned to baseline? | Notes |
|---------|:--------------------:|-------|
| Local git HEAD | ✅ | `517f728` |
| Preview (alias) | ✅ (content) | P16 markers present; cold 200 |
| Preview (raw deploy URL) | ⚠️ | CORS 400 — not in `ALLOWED_ORIGINS` |
| Cloud Run backend | ⚠️ | `29a00f8c7` — 1 commit behind baseline |
| Production Vercel | ❌ | 45-day-old bundle; pre-Sprint A UX |

---

## Comparison matrix

| Dimension | A. Frontend release | B. Cloud Run `GIT_SHA` | C. Cloud Run `SOURCE_REV` | D. Vercel deploy timestamp |
|-----------|---------------------|--------------------------|---------------------------|----------------------------|
| **Value** | `517f728`* (inferred) | `29a00f8c7` | `29a00f8c7` | **2026-06-04 21:14:40 PDT** |
| **Full commit** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37`* | `29a00f8c75320a2e28f67a961cebfa583bd89484` | same as B | — |
| **Commit date** | 2026-06-04 21:14:35 PDT | 2026-06-04 18:54:38 PDT | same as B | Thu Jun 04 2026 21:14:40 GMT-0700 |
| **Source** | Vercel Preview deploy timing + bundle build stamp | `gcloud run revisions describe fiqa-api-00085-tn2` | same revision | `vercel inspect ui-rfkvvg0sz…` |
| **Matches baseline?** | ✅ | ❌ (1 commit behind) | ❌ (1 commit behind) | ✅ (within 5 s of baseline commit) |

\*Frontend SHA is **inferred**, not read from bundle: `__BUILD_ID__` is incorrectly minified in `index-CJ0tCunS.js` (build-time ISO is present; commit hash is not). Deploy timestamp and local HEAD at deploy time strongly indicate `517f728`.

---

## Live environment snapshot

### A. Frontend — Preview (canonical demo URL)

| Field | Value |
|-------|-------|
| **Alias (use this)** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Deployment URL** | `https://ui-rfkvvg0sz-andys-projects-1f411b73.vercel.app` |
| **Deployment ID** | `dpl_JCuPNUHy6a3nDq64ea6SnYQQFLw6` |
| **Target** | Preview |
| **Status** | Ready |
| **Bundle** | `index-CJ0tCunS.js` |
| **Build time (in bundle)** | `2026-06-05T04:14:46.132Z` |
| **P16-O marker** | ✅ `请把您的需求发给我们` |
| **product_only marker** | ✅ `快速体验（可选）` |
| **API base (in bundle)** | `fiqa-api-g7zatxrycq-uw.a.run.app` ✅ |
| **Cold access** | HTTP 200 (no SSO) |

### A. Frontend — Production (stable alias)

| Field | Value |
|-------|-------|
| **Alias** | `https://ui-smoky-beta.vercel.app` |
| **Underlying deployment** | `ui-cupempwva-andys-projects-1f411b73.vercel.app` |
| **Deployment ID** | `dpl_FSUAGL5w8b1oUjZP6xYqJ8vLzJ87` |
| **Target** | Production |
| **Created** | **2026-04-21 07:15:17 PDT (45 days ago)** |
| **Bundle** | `index-ctrXdUgj.js` |
| **P16-O marker** | ❌ absent |
| **product_only marker** | ❌ absent |
| **Matches baseline?** | ❌ **FAIL** (FP-001 / FP-013) |

### B & C. Cloud Run backend

| Field | Value |
|-------|-------|
| **Service** | `fiqa-api` |
| **Region** | `us-west1` |
| **Project** | `optimal-disk-472305-e2` |
| **URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **Latest revision** | `fiqa-api-00085-tn2` |
| **Revision created** | `2026-06-05T01:56:41Z` (2026-06-04 18:56 PDT) |
| **`GIT_SHA`** | `29a00f8c7` |
| **`SOURCE_REV`** | `29a00f8c7` |
| **`/version` commit** | `29a00f8c7` (source: env) |
| **`/readyz`** | ✅ `intake_path_ready: true`, `intake_core_readiness: true` |
| **Gap to baseline** | Missing `517f728` (active case choice gate) |

**Commit between backend and baseline:**

| SHA | Subject |
|-----|---------|
| `517f728` | fix(p16): active case choice gate |

Backend was deployed **~2 h 18 min before** the baseline commit and Preview frontend deploy.

---

## CORS parity

| Origin tested | OPTIONS `/api/inbox/cases` | In `ALLOWED_ORIGINS`? |
|---------------|---------------------------|:---------------------:|
| `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` | **200** + allow-origin | ✅ |
| `https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app` | **200** | ✅ |
| `https://ui-rfkvvg0sz-andys-projects-1f411b73.vercel.app` | **400** | ❌ |

**Operator rule:** Share the **`ui-waterwoods` alias**, not the raw deployment hash URL. Raw hash URLs fail CORS and produce empty queues.

Recent Preview deploys (`ui-rfkvvg0sz`, `ui-8om1gd3ze`, etc.) are **not** in live `ALLOWED_ORIGINS`. Only aliases listed in Cloud Run env are safe entry points.

---

## Automated gate (2026-06-05)

```
bash scripts/post_sprint_check.sh --sprint P16-FREEZE \
  --preview-deploy https://ui-rfkvvg0sz-andys-projects-1f411b73.vercel.app
```

| Check | Result |
|-------|--------|
| git_commit | PASS (`517f728`) |
| preview_url_reachable (alias) | PASS HTTP 200 |
| preview_protection_absent | PASS (cold 200) |
| product_only_flag | PASS |
| bundle_sprint_markers | PASS |
| cors_preflight (default deploy URL) | FAIL HTTP 400 |
| cloud_run_health | PASS |
| pilot_env_posture | PASS |
| **Score** | **9 / 10** |

---

## Parity scorecard

| Dimension | Local | Preview (alias) | Preview (hash) | Production | Cloud Run |
|-----------|:-----:|:---------------:|:--------------:|:----------:|:---------:|
| SHA / revision | `517f728` | `517f728`* | `517f728`* | pre-P16 (~Apr 21) | `29a00f8c7` |
| Bundle hash match | — | `index-CJ0tCunS.js` | same | `index-ctrXdUgj.js` ❌ | — |
| P16-O strings | ✅ | ✅ | ✅ | ❌ | N/A |
| product_only | ✅ | ✅ | ✅ | ❌ | ✅ (env) |
| Cold broker access | ✅ | ✅ | ✅ | ✅ (wrong UX) | N/A |
| API health | ✅ | ✅ | ✅ | ✅ | ✅ |
| CORS | ✅ | ✅ | ❌ | ✅ | — |
| **Aligned to baseline** | ✅ | ✅ | ⚠️ | ❌ | ⚠️ |

---

## Closure paths (documentation only — not executed)

1. **Backend parity:** Redeploy from `517f728` checkout → `bash scripts/deploy_paid_pilot.sh` (would set `GIT_SHA`/`SOURCE_REV` to `517f728…`).
2. **Production frontend parity:** `cd ui && vercel deploy --prod` with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` and correct `VITE_API_BASE_URL` after founder E2E on Preview.
3. **CORS hygiene:** After each Preview deploy, either use alias only **or** append new hash origins to `ALLOWED_ORIGINS` in `.env.cloudrun` and patch Cloud Run.
4. **BUILD_ID fix:** Repair `ReleaseIdentityBar` / Vite define so deployed bundles embed commit SHA (minifier currently conflates `__BUILD_ID__` with env helper).

---

## Verdict rationale

| Level | Reason |
|-------|--------|
| **PASS** | Not met — Production frontend and backend SHA both diverge from baseline |
| **CONDITIONAL PASS** | **Selected** — Preview alias serves baseline content; API healthy; operator can demo today on `ui-waterwoods` + Cloud Run; gaps are documented and closable without code changes |
| **FAIL** | Would apply if Preview were blocked (SSO), API down, or markers absent — none of those are true |

---

*End of P16 Deployment Parity Report — Phase 4*
