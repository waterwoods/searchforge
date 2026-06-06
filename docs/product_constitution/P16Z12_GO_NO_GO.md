# P16-Z12 Phase 9 — Go / No-Go

**Date:** 2026-06-02

---

## Sprint acceptance criteria

| Criterion | Status |
|-----------|--------|
| Backend deploy succeeds | ❌ **NO** — API keys |
| Preview uses latest backend | ❌ Stale `0c2ed6d59` |
| Preview without SSO | ✅ |
| CORS passes | ❌ |
| Case 1 payment/lapse | ❌ |
| Case 2 remove vehicle | ❌ |
| Case 3 claim | ❌ |
| Office value surface visible | ❌ |
| Role D ≥80 on deployed path | ❌ |
| Clear Preview URL printed | ✅ |

**Sprint pass:** **FAIL**

---

## Decisions

| # | Question | Verdict |
|---|----------|---------|
| 1 | Can Andy continue testing Preview? | **YES** — SSO off; use **local :8001** or fix CORS + deploy first for API fidelity |
| 2 | Can Chen Kui get a **supervised** demo? | **NO-GO** — wrong lanes on all three acceptance pastes on live API |
| 3 | Can we send Chen Kui the link **unsupervised**? | **NO-GO** — CORS + classification failures |
| 4 | Can we start **paid pilot**? | **NO-GO** — deploy blocked; engine not on Cloud Run |
| 5 | What blocks first **$49**? | Deploy secrets + CORS + backend parity + acceptance-case routing on production URL |

---

## Blocking chain (ordered)

1. Add `UNIFIED_INTAKE_INTAKE_API_KEY` + `UNIFIED_INTAKE_SUPPORT_API_KEY` to `.env.cloudrun`
2. `bash scripts/deploy_paid_pilot.sh`
3. Add each new Preview `ui-*.vercel.app` to `ALLOWED_ORIGINS`; redeploy backend
4. Re-run Z12 acceptance cases on Cloud Run
5. Optional: align payment marker with sprint paste wording (ship sprint — not Z12 scope)
6. Fix claim HTTP routing if still misclassified after deploy
7. Founder 15-min observation log on cold URL

---

## Honest status

**Do not fake success.** Preview URL loads; product is **not** ready for real Chen Kui testing on deployed path.
