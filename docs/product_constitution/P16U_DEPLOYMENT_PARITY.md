# P16-U Phase 7 — Deployment Parity Audit

**Date:** 2026-06-01  
**Method:** Bundle hash + marker grep across Local git HEAD, Preview, Production  
**Patterns:** FP-001, FP-013, FP-005

---

## Environment snapshot

| Environment | Bundle | Git / deploy | Last-modified signal |
|-------------|--------|--------------|----------------------|
| **Local (git HEAD)** | source @ `d05e94d` | P16-O commit 2026-06-01 | Same commit as Preview content |
| **Preview** (`ui-waterwoods` → `ui-iwnyo9ufa`) | `index-CKPYkrkL.js` | P16-R deploy | Cold: **401**; bundle via vercel curl |
| **Production** (`ui-smoky-beta`) | `index-ctrXdUgj.js` | Frozen ~41 days | `last-modified: Sat, 30 May 2026` (cache age ~44h on HTML) |

---

## Parity matrix

| Dimension | Local | Preview | Production | Aligned? |
|-----------|-------|---------|------------|----------|
| Bundle hash | — | `index-CKPYkrkL.js` | `index-ctrXdUgj.js` | ❌ |
| P16-O marker `请把您的需求发给我们` | ✅ (source) | ✅ (1×) | ❌ (0×) | ❌ |
| product_only `快速体验（可选）` | ✅ | ✅ | ❌ | ❌ |
| Sprint markers (runner default) | ✅ | ✅ | ❌ | ❌ |
| Cold HTTP access | localhost | **401 SSO** | **200** | ❌ |
| CORS origin registered | N/A | ✅ `ui-iwnyo9ufa` | ✅ prod origin | ✅ |
| API `/readyz` | N/A | ✅ | ✅ | ✅ |
| Default tab / GTM | broker (local product_only) | broker (bundle) | customer portal (stale) | ❌ |

**Parity score:** **2 / 8 dimensions aligned** → **FAIL**

---

## Access parity (critical)

| User action | Local | Preview | Production |
|-------------|-------|---------|------------|
| Cold curl HTML | ✅ | ❌ 401 | ✅ 200 |
| Unauthenticated browser | ✅ localhost | ❌ SSO login | ✅ wrong UI |
| Broker trial link | ✅ local demo | ❌ | ⚠️ misleading (works but wrong) |

**Preview has the right bundle but wrong access model.**  
**Production has the right access model but wrong bundle.**

---

## API / backend parity

| Check | Cloud Run deployed | Local `.env.cloudrun` post-P16-U |
|-------|-------------------|----------------------------------|
| `intake_path_ready` | ✅ | N/A |
| CORS ALLOWED_ORIGINS | Includes Preview + Production hosts | ✅ synced |
| PRODUCT_ONLY posture | ✅ (live `/readyz`) | ✅ synced (flags) |
| API keys in local file | N/A | ❌ (Secret Manager) |

Backend **aligned with Preview UI origin**. Frontend **not aligned across three surfaces**.

---

## FP mapping

| Gap | Pattern | Owner |
|-----|---------|-------|
| Preview ≠ Production hash | FP-001, FP-013 | Founder — prod promote |
| Preview 401 | FP-004 | Founder — SSO off |
| Production wrong UI | FP-016 + FP-013 | Founder — prod promote with flags |
| Git pushed but prod stale | FP-005 (partial) | Deploy engineer |

---

## Promotion gate status (from P16-R)

| Gate | Status |
|------|--------|
| Preview cold 200 | ❌ |
| Preview E2E logged | ❌ |
| Preview bundle markers | ✅ |
| CORS | ✅ |
| Production promote | **Blocked** |

---

## Parity verdict

**Local ≈ Preview (content)** — yes, via authenticated/vercel path  
**Preview ≈ Production** — **no**  
**Local ≈ Production** — **no**  
**Broker-facing single URL** — **does not exist**

---

*End of P16-U Phase 7 — Deployment Parity Audit*
