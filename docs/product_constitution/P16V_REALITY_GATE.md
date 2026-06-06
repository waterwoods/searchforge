# P16-V Phase 9 — Reality Gate

**Date:** 2026-06-01  
**Method:** POST_SPRINT_HEALTH_CHECK using **deployed URLs only**  
**Rule:** No local scoring, no assumptions, no vercel-curl-as-broker-proxy

---

## Deployed evidence inputs

| Source | Result |
|--------|--------|
| `curl -sI` Preview alias | HTTP **401** + `_vercel_sso_nonce` |
| `curl -sI` Production | HTTP **200** |
| `curl -sf` API `/readyz` | `intake_path_ready: true` |
| Cold browser Preview | Vercel Login wall |
| Cold browser Production | Stale customer-portal UI loads |
| `post_sprint_check.sh` | **8/10 FAIL** |

---

## Reality Gate questions

### 1. Can Andy test Preview?

**NO.**

| Evidence | Detail |
|----------|--------|
| Cold curl | 401 |
| Incognito browser | Redirect to `vercel.com/login` |
| Product UI | Not reachable without Vercel team auth |

Andy can test via `vercel curl` or logged-in Vercel session — **not** the trial experience brokers will see.

---

### 2. Can Andy send Preview to Chen Kui?

**NO.**

Chen Kui receives a Vercel authentication wall, not the broker paste trial. No shareable cold-access URL exists today.

| URL | Chen Kui experience |
|-----|----------------------|
| `ui-waterwoods` (Preview alias) | Vercel Login / SSO |
| `ui-smoky-beta` (Production) | Wrong UI (customer portal, no P16-O) |

---

### 3. Can Andy promote to Production?

**NO — not yet.**

| Blocker | Reason |
|---------|--------|
| Preview gate open | P16-R policy: promote only after Preview cold PASS + E2E |
| No Andy E2E log | Cannot validate paste loop on deployed URL |
| UX risk | product_only changes default tab (FP-016) |

Technically ready **after** Preview 10/10 + E2E (~25 min work).

---

### 4. Can Day 0 be scheduled?

**NO.**

Day 0 requires:

- Shareable broker URL with cold 200 ✅ content exists, ❌ access blocked
- Andy E2E on deployed URL ❌
- Observation log protocol ❌ not started
- Commercial pack ❌ incomplete (Day 7 item, not Day 0 blocker alone)

**Earliest path:** Andy SSO toggle (~5 min) → runner 10/10 → Andy E2E (~15 min) → schedule Day 0

---

## Deployed surface scorecard

| Surface | HTTP | Right bundle | Broker trial | Score |
|---------|------|--------------|--------------|-------|
| Preview | ❌ 401 | ✅ | ❌ unreachable | **~12/100** cold |
| Production | ✅ 200 | ❌ stale | ❌ wrong UX | **~35/100** |
| API | ✅ ready | N/A | ✅ engine works | **~90/100** |

---

## Reality Gate verdict

| Gate | Result |
|------|--------|
| POST_SPRINT_HEALTH_CHECK | **FAIL** (8/10) |
| Distribution ready | **NO** |
| Trial ready | **NO** |
| Commercial ready | **NO** (inherited) |

**All four founder questions: NO.**

---

*End of P16-V Phase 9 — Reality Gate*
