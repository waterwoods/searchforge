# P16-T Phase 2 — Reality Closure Audit (FP-001–004)

**Date:** 2026-06-01  
**Method:** Live `curl`, `vercel curl`, bundle grep, `.env.cloudrun` inspect  
**Branch:** `sprint-a/broker-front-door` @ `d05e94d`  
**URLs tested:**

| Role | URL |
|------|-----|
| Preview alias | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| Preview deploy | https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app |
| Production | https://ui-smoky-beta.vercel.app |
| API | https://fiqa-api-g7zatxrycq-uw.a.run.app |

---

## FP-001 — Deployment Parity Failure

**Status:** ❌ **OPEN (Partial fix)**

| Dimension | Local | Preview | Production |
|-----------|-------|---------|------------|
| Git commit | `d05e94d` (P16-O) | Inferred `d05e94d` (bundle markers) | Unknown (~2026-04-21) |
| Bundle hash | N/A (on-demand build) | `index-CKPYkrkL.js` | `index-ctrXdUgj.js` |
| P16-O string `请把您的需求发给我们` | ✅ dist grep | ✅ 1× (vercel curl) | ❌ 0× |
| product_only UI strings | ✅ | ✅ | ❌ |
| Cold HTTP | N/A | 401 SSO | 200 |

**Evidence:**

```bash
# Preview bundle (vercel curl bypass)
index-CKPYkrkL.js — P16-O + product_only markers present

# Production bundle (cold curl)
index-ctrXdUgj.js — pre-P16-O, pre-product_only
```

**Verdict:** Preview **content** matches local intent; **access** and **Production** do not. Parity delta remains >10 points (engine ~85 local vs distribution ~12 cold Preview).

**Fix still required:** Promote Preview bundle to Production after FP-004 cleared.

---

## FP-002 — CORS Origin Block

**Status:** ✅ **CLOSED (latent risk)**

| Check | Result | Evidence |
|-------|--------|----------|
| OPTIONS from Preview deploy origin | **200** | `access-control-allow-origin: https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app` |
| Preview alias in ALLOWED_ORIGINS | ✅ | `.env.cloudrun` line 34 includes `ui-iwnyo9ufa` and `ui-waterwoods` |
| Production origin CORS | **200** | OPTIONS from `ui-smoky-beta.vercel.app` |

**Latent risk:** Next `vercel deploy` with new hash subdomain requires manual ALLOWED_ORIGINS patch unless wildcard/hook added.

**Verdict:** Current Preview deploy origin is allowlisted. Pattern remains whack-a-mole on redeploy.

---

## FP-003 — Feature Flag Drift

**Status:** ⚠️ **PARTIAL**

| Flag | Local | Preview (live bundle) | Preview (dashboard) | Production (live bundle) |
|------|-------|----------------------|---------------------|--------------------------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ runtime | ✅ CLI `-b` at deploy | ❌ not in Preview scope | ❌ not in 41d bundle |
| `VITE_API_BASE_URL` | localhost:8001 | ✅ Cloud Run in bundle | ❌ Preview dashboard missing | ✅ encrypted |

**Positive markers on Preview bundle (`index-CKPYkrkL.js`):**

| Marker | Count |
|--------|-------|
| `快速体验（可选）` | 1 |
| `原样粘贴微信/通知文字，不用整理` | 1 |
| `请把您的需求发给我们` | 1 |

**Negative on Production bundle:**

| Marker | Preview | Production |
|--------|---------|------------|
| `快速体验（可选）` | 1 | 0 |
| `请把您的需求发给我们` | 1 | 0 |

**Verdict:** Latest Preview **build** has correct flags via CLI `-b`. Dashboard persistence still missing — redeploy without `-b` would regress (FP-003 recurrence risk).

---

## FP-004 — Preview Protection (SSO Wall)

**Status:** ❌ **OPEN**

| Check | Result | Evidence |
|-------|--------|----------|
| `curl -sI` Preview alias | **401** | `HTTP/2 401`, Vercel server |
| `curl -sI` Preview deploy URL | **401** | Same |
| Cold HTML fetch | SSO wall | No product bundle via cold curl |
| `vercel curl` bypass | **200** | Returns `index-CKPYkrkL.js` HTML |

**Impact:** Chen Kui cold score remains ~12/100. Broker cannot open documented Preview link without Vercel account.

**Verdict:** **#1 trial blocker unchanged since P16-J.** Founder action required: disable Deployment Protection on Preview OR publish bypass URL separately.

---

## Summary table

| FP | Name | P16-R status | P16-T status | Blocker? |
|----|------|--------------|--------------|----------|
| FP-001 | Deployment Parity | Partial | **Partial** — Preview content OK, Prod stale | Yes (Production) |
| FP-002 | CORS | Latent | **Closed** for current deploy | No (today) |
| FP-003 | Feature Flag Drift | Partial | **Partial** — CLI deploy OK, dashboard not | Yes (process) |
| FP-004 | Preview SSO | **Yes** | **Yes** — 401 on cold curl | **Yes (P0)** |

---

## Reality closure score

| Pattern | Closed? |
|---------|---------|
| FP-001 | No |
| FP-002 | Yes (current origin) |
| FP-003 | No (process) |
| FP-004 | No |

**3 of 4 still open or partial.** P16-R deploy work improved **bundle content** on Preview but did **not** close distribution blockers.

---

## Required actions before trial URL share

1. **FP-004:** Disable Preview Deployment Protection → re-run cold curl → expect 200
2. **FP-003:** Persist Vercel env vars (Preview + Production scopes)
3. **FP-001/013:** `vercel deploy --prod` after Preview gates pass
4. **FP-002:** Verify CORS after any new Preview subdomain

---

*End of P16-T Phase 2 — Reality Closure Audit*
