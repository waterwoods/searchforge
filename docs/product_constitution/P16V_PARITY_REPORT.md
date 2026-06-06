# P16-V Phase 6 — Deployment Parity Report

**Date:** 2026-06-01  
**Git HEAD:** `d05e94d` on `sprint-a/broker-front-door`  
**Patterns:** FP-001, FP-013, FP-016

---

## Environment snapshot

| Environment | Bundle | Access | P16-O marker | product_only | Default UX |
|-------------|--------|--------|--------------|--------------|------------|
| **Local** (source @ d05e94d) | — | localhost | ✅ source | ✅ | Broker paste trial |
| **Preview** (`ui-waterwoods` → `ui-iwnyo9ufa`) | `index-CKPYkrkL.js` | **401 SSO** | ✅ (1× grep) | ✅ | Broker (bundle) |
| **Production** (`ui-smoky-beta`) | `index-ctrXdUgj.js` | **200** | ❌ (0× grep) | ❌ | Customer portal (stale) |

---

## Bundle hash comparison

```
Preview:    index-CKPYkrkL.js  (P16-R deploy, 2026-06-01)
Production: index-ctrXdUgj.js  (~41 days stale)
Match:      NO — FP-001 / FP-013
```

### Marker grep (deployed bundles)

| Marker | Preview | Production |
|--------|---------|------------|
| `请把您的需求发给我们` (P16-O) | ✅ 1 | ❌ 0 |
| `快速体验（可选）` (product_only) | ✅ | ❌ |
| `原样粘贴微信/通知文字，不用整理` (runner default) | ✅ | ❌ |

---

## Entry path comparison

| Path | Local | Preview | Production |
|------|-------|---------|------------|
| `/workbench/unified-intake` cold | ✅ broker UI | ❌ 401 | ✅ loads (wrong tab) |
| Customer entry (`?tab=customer`) | Hidden in product_only | ❌ unreachable | ✅ visible (stale GTM) |
| Broker paste trial | ✅ | ✅ in bundle only | ❌ wrong UI |
| API `/readyz intake_path_ready` | N/A | ✅ | ✅ |

---

## product_only mode

| Surface | Flag baked | Evidence |
|---------|------------|----------|
| Preview | ✅ | `快速体验（可选）` in bundle; runner PASS |
| Production | ❌ | Marker absent; customer tabs visible in browser |
| Cloud Run backend | ✅ | `intake_path_ready: true`, demo_mode |

Preview **content** matches local Sprint A / P16-O / P16-I intent. Production does **not**.

---

## CORS / API parity

| Check | Result |
|-------|--------|
| OPTIONS from `ui-iwnyo9ufa` origin | ✅ 200 |
| `access-control-allow-origin` matches preview | ✅ |
| Cloud Run ALLOWED_ORIGINS includes preview hosts | ✅ |

Backend aligned with Preview UI origin. Frontend **not aligned across three surfaces**.

---

## Parity score

| Dimension | Aligned? |
|-----------|----------|
| Bundle hash Preview = Production | ❌ |
| P16-O strings | ❌ |
| product_only | ❌ |
| Cold access model | ❌ |
| Broker trial entry | ❌ |
| API health | ✅ |
| CORS | ✅ |

**Score: 2 / 7 → FAIL**

---

## FP-001 status

FP-001 (Deployment Parity) is **not a runner FAIL** but remains open:

- Preview has **new** bundle with sprint work
- Production has **old** bundle without sprint work
- No single URL serves both cold access **and** current sprint content

**Closure path:** FP-004 first (Preview cold 200) → Andy E2E → `vercel deploy --prod` with product_only flags

---

## Parity verdict

| Relationship | Result |
|--------------|--------|
| Local ≈ Preview (content) | ✅ via vercel curl |
| Preview ≈ Production | ❌ |
| Local ≈ Production | ❌ |
| Shareable broker trial URL | ❌ does not exist |

---

*End of P16-V Phase 6 — Deployment Parity Report*
