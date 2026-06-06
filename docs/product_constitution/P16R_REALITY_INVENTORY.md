# P16-R Phase 1 — Reality Inventory

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Method:** `git`, `vercel ls/inspect/env`, `vercel curl`, `curl`, `gcloud`, local `npm run build`, `guardrail_inbox_triage.sh`  
**Constraint:** Evidence only — no optimism

---

## Summary

| Environment | Commit (evidence) | Customer entry | Broker workbench | Cold URL works? |
|-------------|-------------------|----------------|------------------|-----------------|
| **Local** | `d05e94d` (P16-O committed) | P16-O | P16-I + product_only | ✅ `:8001` API; UI manual |
| **Preview (latest)** | `d05e94d` deploy `dpl_9zWWj1payFg4NuGdNVVe4C6aenwv` | P16-O in bundle | P16-I + product_only (CLI `-b`) | ❌ **401 SSO** |
| **Preview (previous)** | `901b0df` deploy `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN` | Pre-P16-O | P16-I (inferred) | ❌ 401 SSO |
| **Production** | Unknown SHA (41d deploy) | Pre-P16-N/O | Pre–Sprint A full dev | ✅ 200 — **wrong UI** |

---

## Local

| Field | Value | Evidence |
|-------|-------|----------|
| **Commit hash** | `d05e94da0855942c6143405720d65be35b3c5829` | `git rev-parse HEAD` |
| **Branch** | `sprint-a/broker-front-door` | `git branch --show-current` |
| **Build time** | 2026-06-01 ~00:09 PDT (on-demand `vite build`) | shell |
| **Backend env** | `UNIFIED_INTAKE_PRODUCT_ONLY=1` (demo scripts) | `demo.env.example` / runbooks |
| **Frontend env** | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL=http://127.0.0.1:8001` | `run_demo_local.sh` pattern |
| **Feature flags** | `isUnifiedIntakeProductOnlyUi()` true when flag set | `ui/src/config/productSurface.ts` |
| **Customer entry version** | **P16-O** (message-first empty state) | `CustomerEntryTab.tsx` + `ui_copy.json`; `git show HEAD` has `portalMessageFirstHeadline` |
| **Broker version** | **P16-I** (product-only workbench simplification) | commit `901b0df` + same branch |
| **UI score (customer)** | **79** | P16-O local validation; unchanged intent |
| **Capability score** | **Engine ~85** | `guardrail_inbox_triage.sh` PASS; `demo_quick_validate.sh` PASS |
| **Bundle markers** | `请把您的需求发给我们` in `dist/` (ui_copy chunk) | `grep -r` on `ui/dist/` |

---

## Preview (latest — post P16-R deploy)

| Field | Value | Evidence |
|-------|-------|----------|
| **URL** | https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app | `vercel deploy` 2026-06-01 |
| **Alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app | `vercel inspect` |
| **Deployment ID** | `dpl_9zWWj1payFg4NuGdNVVe4C6aenwv` | `vercel inspect` |
| **Status** | ● Ready (Preview) | `vercel ls` |
| **Build time** | 2026-06-01 00:04:23 PDT | `vercel inspect` |
| **Git SHA (Vercel)** | Not exposed in CLI | ⚠️ Unconfirmed link to `d05e94d` |
| **Repo commit deployed** | **Inferred `d05e94d`** — bundle contains P16-O strings not in `901b0df` Preview | bundle grep |
| **Env at build** | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app` | `vercel deploy -b …` |
| **Vercel dashboard env** | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` → **Production only**; Preview branch env **blocked** (no Git repo linked) | `vercel env ls` |
| **Customer entry version** | **P16-O** | bundle: `请把您的需求发给我们` ×1, `发送给办公室` ×1 |
| **Broker version** | **P16-I** | bundle: `粘贴客户消息` ×7 |
| **UI score (customer, bundle)** | **~72** | P16-O present; SSO blocks cold UX |
| **UI score (broker, bundle)** | **~74** | product_only strings present |
| **Cold HTTP** | **401** + `_vercel_sso_nonce` | `curl -I` |
| **API via bypass** | CORS **200** for `ui-iwnyo9ufa` origin | OPTIONS after Cloud Run patch |
| **Capability score** | **~80** (API reachable post-CORS) | OPTIONS evidence |

---

## Preview (previous — pre P16-R)

| Field | Value |
|-------|-------|
| **URL** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app |
| **Deployment ID** | `dpl_9g9SJYNDNxgKKE872M9Adq1REvKN` |
| **Age** | ~21h at sprint start |
| **Customer entry** | Pre-P16-O (`请把您的需求发给我们` ×0 in `index-97qCgvUS.js`) |
| **Superseded by** | `ui-iwnyo9ufa` (waterwoods alias moved) |

---

## Production

| Field | Value | Evidence |
|-------|-------|----------|
| **Alias URL** | https://ui-smoky-beta.vercel.app | `vercel inspect` |
| **Deployment ID** | `dpl_FSUAGL5w8b1oUjZP6xYqJ8vLzJ87` | `vercel inspect ui-smoky-beta` |
| **Deployment URL** | https://ui-cupempwva-andys-projects-1f411b73.vercel.app | inspect |
| **Build time** | 2026-04-21 (41d ago) | `vercel inspect` |
| **HTTP last-modified** | Sat, 30 May 2026 11:01:17 GMT | `curl -I` |
| **Bundle** | `index-ctrXdUgj.js` | HTML fetch |
| **Env (dashboard)** | `VITE_API_BASE_URL` only (until P16-R: added `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` **not yet redeployed**) | `vercel env ls` |
| **Customer entry version** | **Pre-P16-O** (3-button / 办理加车报价 hero) | bundle: P16-O strings ×0; `办理加车报价` ×8 |
| **Broker version** | **Pre–Sprint A / mixed** | 4 tabs; `?tab=broker` ignored (P16-Q) |
| **UI score** | **~38 customer / ~45 broker** | P16-Q Role C production snapshot |
| **Cold HTTP** | **200** | `curl -I` |
| **Capability score** | **~70** (API URL in bundle; CORS ok for smoky-beta) | prior P16-G |

---

## Feature flags (cross-environment)

| Flag | Local | Preview build | Production (live bundle) |
|------|-------|---------------|---------------------------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ runtime | ✅ CLI `-b` on latest deploy | ❌ not in 41d-old bundle |
| `VITE_API_BASE_URL` | localhost:8001 | Cloud Run | Cloud Run (encrypted) |
| Vercel Deployment Protection | N/A | ✅ **ON** (401 cold) | N/A (prod alias open) |

---

## UI / capability scores (reality lens)

| Environment | UI (trial surface) | Capability (engine + API) | Overall reality |
|-------------|-------------------|---------------------------|-----------------|
| Local | **77** | **85** | **79** |
| Preview (latest bundle) | **58** (SSO caps access) | **80** | **68** |
| Production | **40** | **70** | **52** |

---

*End of P16-R Phase 1 — Reality Inventory*
