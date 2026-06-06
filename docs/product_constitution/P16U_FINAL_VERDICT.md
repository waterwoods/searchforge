# P16-U Final Verdict — Autonomous Reality Closure Loop

**Date:** 2026-06-01  
**Sprint:** P16-U — CDD + Reality Gate + Health Check Runner + Failure Pattern Library  
**Mission:** Problem Discovery → Problem Resolution (without P17)

---

## Executive summary

P16-U ran the full autonomous closure loop. The system **found the same P0 blocker in 7 seconds**, **mapped it to FP-004**, **applied the only safe auto-fix** (local env posture sync), **re-validated without score inflation**, and **produced evidence-backed NO-GO** on trial launch. **The runner works; deployed reality is still FAIL.**

---

## 1. Initial health score

**80%** (8/10 automated checks) — **OVERALL FAIL**

Blockers: Preview HTTP 401 ×2 (FP-004)

---

## 2. Final health score

**80%** (8/10) — **OVERALL FAIL** (unchanged on deployed checks)

Off-score improvement: `pilot_env_posture` WARN reduced 8 → 2 validate errors (FP-011 partial)

---

## 3. Failures discovered

| # | Failure | FP |
|---|---------|-----|
| 1 | Preview cold 401 | FP-004 |
| 2 | Preview SSO protection | FP-004 |
| 3 | Production bundle stale | FP-001, FP-013 |
| 4 | Production missing P16-O | FP-005 (residual on prod) |
| 5 | No Andy E2E on deployed URL | FP-010, FP-015 |
| 6 | Local env posture drift | FP-011 |
| 7 | Trial path compound failure | FP-014 |
| 8 | Reality gap (80% vs 12 cold) | FP-008 |

**Runner-native FAILs:** 2 (both FP-004)  
**Reality-layer FAILs:** 6+ (parity, evidence, trial flow)

---

## 4. Failures automatically fixed

| Fix | FP | Impact on deployed score |
|-----|-----|--------------------------|
| `.env.cloudrun` pilot posture sync | FP-011 | None (local); prevents future deploy drift |
| Bundle verification documented | FP-005 guard | None — confirmed Preview OK |
| P16-U artifact set | FP-015 | Evidence created |

**Automatically fixed on deployed URLs:** **0 / 2 runner FAILs**

This is **correct behavior** — the system did not pretend SSO was fixable by documentation.

---

## 5. Failures still open

**P0 (5):** FP-004 SSO, FP-013 prod stale, FP-014 trial flow, FP-008 reality gap, FP-016 prod default tab  
**P1 (4):** FP-010/015 E2E log, FP-003 Vercel env dashboard, FP-011 API keys local, FP-009 commercial  
**P2 (3):** FP-017, FP-007, FP-018

See `P16U_OPEN_ISSUES.md` for ranked list.

---

## 6. Biggest blocker

**FP-004 — Preview Deployment Protection (SSO wall)**

One Vercel setting blocks: cold Preview access, broker Day 0, Andy E2E on shareable URL, and masks all Preview bundle improvements from external users. **~5 minutes of founder time** — highest leverage in the entire P16 arc.

---

## 7. Trial readiness

| Dimension | Verdict |
|-----------|---------|
| Engine (API triage, CORS, cases) | **Ready** |
| Preview bundle content | **Ready** (authenticated path) |
| Broker cold URL | **Not ready** |
| Production public URL | **Not ready** (wrong UI) |
| Evidence (E2E log, observation) | **Not ready** |

**Trial readiness: NO** — unchanged from P16-R/T, now machine-proven.

---

## 8. Commercial readiness

**NO** — FP-009 inherited (invoice IDs, observation log, pricing proof). Product progress does not create payment evidence. Blocked upstream by trial URL failure.

---

## 9. Reality readiness

| Metric | Score |
|--------|-------|
| Runner deploy checks | 80% |
| Broker cold path (deployed) | ~12/100 |
| API engine (deployed) | ~85/100 |
| Weighted trial wedge | ~28/100 |

**Reality readiness: FAIL** — distribution failure masks engine (FP-008 key insight, confirmed again).

---

## 10. Recommended next sprint

**Do not start P17.**

**Next work unit:** **Founder Ops Sprint (≤1 hour)** — not a feature sprint:

1. Disable Preview SSO (FP-004) — 5 min  
2. Re-run `post_sprint_check.sh` until PASS — 1 min  
3. Andy Preview E2E log — 15 min  
4. Production promote with product_only — 15 min  
5. Supervised Chen Kui Day 0 screen-share — 30 min  

Then re-run P16-U loop (or `post_sprint_check.sh` alone) for GO on trial.

Optional follow-on: **P16-V Vercel env persistence** (FP-003 dashboard flags) — 10 min, prevents redeploy regression.

---

## System assessment

| Component | Operational? |
|-----------|--------------|
| CDD (Constitution Drift Detection) | ✅ Via FP library + runner markers |
| Reality Gate | ✅ FAIL verdict matches evidence |
| Health Check Runner | ✅ 7 sec, exit 1 on real blockers |
| Failure Pattern Library | ✅ Every FAIL mapped to FP-004/011/013 |
| Autonomous fix loop | ✅ Applied safe fixes; refused unsafe ones |

**Success criterion met:** *The system finds issues before Andy does* — SSO, parity, and env drift detected automatically. **Resolution criterion partial:** only local env auto-fixed; founder blockers correctly escalated.

---

## Artifacts produced

| Phase | Document |
|-------|----------|
| 1 | `P16U_HEALTHCHECK_BASELINE.md` |
| 2 | `P16U_FAILURE_MAPPING.md` |
| 3 | `P16U_FIX_CANDIDATES.md` |
| 4 | `P16U_FIX_EXECUTION.md` |
| 5 | `P16U_HEALTHCHECK_DELTA.md` |
| 6 | `P16U_REALITY_REVALIDATION.md` |
| 7 | `P16U_DEPLOYMENT_PARITY.md` |
| 8 | `P16U_OPEN_ISSUES.md` |
| 9 | `P16U_GO_NO_GO.md` |
| 10 | `P16U_FINAL_VERDICT.md` (this file) |

---

**Bottom line:** The autonomous loop is **live and honest**. Deployed product is **not trial-ready**. Turn off Preview SSO — everything else is downstream.

---

*End of P16-U Final Verdict*
