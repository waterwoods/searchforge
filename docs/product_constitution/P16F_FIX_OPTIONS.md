# P16-F Phase 6 — Fix Options

**Date:** 2026-05-31  
**Problem:** Preview origin `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app` not in Cloud Run `ALLOWED_ORIGINS` → CORS → Network Error.

---

## Option A — Use stable production Vercel alias only

**Action:** Direct Andy/Chen Kui to `https://ui-smoky-beta.vercel.app` and avoid hash Preview URLs.

| | |
|--|--|
| **Upside** | CORS already passes for `ui-smoky-beta`; no Cloud Run change; zero backend risk |
| **Downside** | Production alias is **pre-Sprint A** code (40d+ old deploy) — wrong front door, wrong default tab, no product_only UX |
| **Risk** | High product mismatch — Andy reviews wrong surface; Chen Kui sees Add-Car portal not broker workbench |
| **Time cost** | ~0 operator time |
| **Verdict** | **Not recommended** for Sprint A Preview validation |

---

## Option B — Add current Preview URL to Cloud Run `ALLOWED_ORIGINS`

**Action:** Patch env to include `https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app` (and optionally `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`).

| | |
|--|--|
| **Upside** | Fixes Andy's exact URL; preserves Sprint A Preview build; env-only change; fast rollback |
| **Downside** | Each new Preview deploy may get new `ui-<hash>-…` hostname — repeat patches |
| **Risk** | Low — additive origin only; no triage/schema changes |
| **Time cost** | ~5 minutes (env update + verify OPTIONS) |
| **Verdict** | **Recommended for immediate Andy review** |

---

## Option C — Wildcard / regex for Vercel Preview origins

**Action:** Allow pattern like `https://ui-*-andys-projects-1f411b73.vercel.app` or maintain automated origin discovery.

| | |
|--|--|
| **Upside** | Stops per-deploy CORS patches; better DX for Preview-heavy sprints |
| **Risk** | FastAPI CORS uses explicit origin list today — regex needs code change or broad allowlist; overly wide pattern increases CSRF/credential surface slightly |
| **Time cost** | Medium (code + deploy + review) — **out of scope** for "do not change backend unless root cause confirmed" — root cause confirmed, but wildcard is policy change not env patch |
| **Verdict** | **Later** (post-P16-F); use Option B now |

---

## Recommendation

**Choose Option B** for this sprint.

Option A fails the Sprint A validation goal. Option C is the right medium-term hygiene but requires backend CORS logic discussion — defer.

After Andy approval, also update `.env.cloudrun` so the next full deploy does not drop the new origin.

---

*End of P16-F Phase 6*
