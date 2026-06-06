# P16-R Phase 9 — Revalidation

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Compare:** P16-Q scores (pre) → P16-R (post Phase 8)

---

## Tests re-run

| Test | Environment | Result |
|------|-------------|--------|
| `guardrail_inbox_triage.sh` | Local API | **PASS** |
| `demo_quick_validate.sh` | Local API :8001 | **PASS** |
| Bundle grep P16-O | Preview `index-CKPYkrkL.js` | **PASS** (1× headline, 1× CTA) |
| Bundle grep P16-O | Production `index-ctrXdUgj.js` | **FAIL** (0×) |
| Cold HTTP Preview | `ui-waterwoods` | **FAIL** 401 |
| Cold HTTP Production | `ui-smoky-beta` | **PASS** 200 — wrong UI |
| CORS OPTIONS | Preview `ui-iwnyo9ufa` | **PASS** 200 |

---

## Role scores (revalidated)

| Role / dimension | P16-Q | P16-R | Δ | Notes |
|------------------|-------|-------|---|-------|
| **Founder journey (local)** | 65 | **72** | +7 | P16-O committed; validate PASS |
| **Founder journey (Preview URL)** | 12 | **25** | +13 | Bundle fixed; SSO still blocks |
| **Customer (local)** | 79 | **79** | 0 | P16-O now in git |
| **Customer (Preview bundle)** | 38 | **72** | +34 | Deployed P16-O strings |
| **Customer (Production)** | 38 | **38** | 0 | No prod deploy |
| **Broker (local product_only)** | 74 | **74** | 0 | Unchanged |
| **Broker (Preview bundle)** | 70 inferred | **74** | +4 | Latest deploy + CORS |
| **Broker (Preview cold)** | 12 | **12** | 0 | SSO |
| **Broker (Production)** | 45 | **45** | 0 | Stale bundle |
| **Assistant** | 50 | **52** | +2 | Preview API path ok post-CORS |
| **Chen Kui** | 48 | **50** | +2 | Bundle better; URL still blocked |
| **Role C (Production)** | 42 | **42** | 0 | Unchanged |
| **Trial readiness** | 46 | **58** | +12 | Preview parity progress |
| **Overall reality** | 64 | **68** | +4 | Not parity yet |

---

## Founder journey (revalidation summary)

| Step | Local P16-R | Preview P16-R | Production |
|------|-------------|---------------|------------|
| Customer entry P16-O | ✅ | ✅ bundle / ❌ cold UI | ❌ |
| Submit → triage | ✅ | 🟡 API ok if SSO passed | 🟡 API |
| Broker queue | ✅ | ✅ bundle | ❌ tabs |
| Draft → copy | ✅ | 🟡 not E2E proven | 🟡 |
| Follow-up append | ✅ | 🟡 | 🟡 |

---

## Simulations (not re-run in browser)

| Simulation | P16-Q doc | P16-R update |
|------------|-----------|--------------|
| Role C | `P16Q_ROLE_C_SIMULATION.md` | Production unchanged — still fail |
| Chen Kui | `P16Q_CHEN_KUI_SIMULATION.md` | Preview bundle improved; URL still unusable cold |
| Assistant | `P16Q_ASSISTANT_SIMULATION.md` | Same SSO blocker |
| Customer | P16-O local only | Preview bundle now matches — **access not** |

---

## Parity score (Local = Preview = Production)

| Pair | P16-Q | P16-R |
|------|-------|-------|
| Local = Preview | ❌ | **🟡** (~85% bundle; 0% cold URL) |
| Preview = Production | ❌ | ❌ |
| Local = Production | ❌ | ❌ |

---

*End of P16-R Phase 9 — Revalidation*
