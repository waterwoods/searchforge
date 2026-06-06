# P16-T Phase 6 — Reality Gate

**Date:** 2026-06-01  
**Method:** `POST_SPRINT_HEALTH_CHECK.md` filled with 2026-06-01 live data + runner output  
**Preview URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app  
**Production URL:** https://ui-smoky-beta.vercel.app  
**Reviewer:** P16-T agent run

---

## Section results

### Deploy

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| L1 | Demo starts | ☐ N/A | Not run this session (systems sprint) |
| L2 | Guardrail | ☐ N/A | Not run |
| L3 | Quick validate | ☐ N/A | Not run |
| L4 | Product-only local | ☐ Pass (prior) | P16-R local evidence |
| L5 | Sprint strings local | ☐ Pass | `d05e94d` P16-O |
| P1 | Cold access Preview | **Fail** | HTTP 401 — `post_sprint_check.sh` |
| P2 | Bundle deployed | **Pass** | `请把您的需求发给我们` in `index-CKPYkrkL.js` |
| P3 | Bundle hash | **Partial** | Preview new; git SHA not exposed by Vercel CLI |
| P4 | CORS | **Pass** | OPTIONS 200 |
| P5 | E2E paste loop | **Fail** | Blocked by SSO (no browser test) |
| PR1 | Production accessible | **Pass** | HTTP 200 |
| PR2 | Not stale | **Fail** | `index-ctrXdUgj.js` unchanged |
| PR3 | Correct UI prod | **Fail** | No product_only / P16-O on prod |
| PR4 | Promotion gate | **Fail** | Deferred — not promoted |
| PA1 | Local ≈ Preview | **Fail** | Cold access 12 vs local ~78 |
| PA2 | Preview ≥ Production | **Pass** | Preview bundle strictly newer |
| PA3 | Git = Deploy | **Partial** | Markers match; timestamp unconfirmed |
| PA4 | No FP-001 symptoms | **Fail** | Prod divergence |

**Deploy section:** **Fail**

---

### Environment

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| V1 | PRODUCT_ONLY in dashboard | **Fail** | Preview scope missing (P16R audit) |
| V2 | API_BASE in dashboard | **Fail** | Preview scope missing |
| V3 | Deployment Protection | **Fail** | 401 cold |
| V4 | Git link | **Fail** | CLI-only deploy |
| C1 | Preview in ALLOWED_ORIGINS | **Pass** | `.env.cloudrun` |
| C2 | `.env.cloudrun` synced | **Pass** | Includes iwnyo9ufa + waterwoods |
| C3 | Pilot posture | **Warn** | Local file missing secrets for full validate |
| G1 | Branch pushed | **Pass** | `sprint-a/broker-front-door` on remote (P16-R) |
| G2 | Clean ui/ | **Pass** | No uncommitted ui drift at run time |
| F1 | Build flags match | **Pass** | Preview bundle markers |
| F2 | Backend PRODUCT_ONLY | **Pass** | Cloud Run posture (prior audit) |
| F3 | No flag regression | **Fail** | Redeploy without `-b` would regress |

**Environment section:** **Fail**

---

### Runtime

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| R1 | Console clean | **Fail** | Not testable — SSO |
| R2 | No CORS errors | **Pass** | OPTIONS OK |
| R3 | API reachable | **Pass** | `/readyz` intake_path_ready |
| R4 | Demo queue | **Fail** | Not testable — SSO |
| R5 | Triage POST | **Pass** | API healthy (curl path) |
| R6 | Readiness | **Pass** | `/readyz` |
| R7 | No 503 warm | **Pass** | API ready |
| R8 | Draft language | **N/A** | Not tested this run |

**Runtime section:** **Fail** (R4; browser path blocked)

---

### Capability

Baseline P16-R unchanged on **deployed** URLs. Local engine ~85; deployed distribution ~12–68 depending on metric.

**Capability section:** **Fail** (CP3 — deployed URL does not prove claim for broker cold path)

---

### Reality

| Role | Check | Result |
|------|-------|--------|
| Founder | Cold URL without SSO | **Fail** |
| Founder | 15-min E2E log | **Fail** (not published) |
| Role C | Broker workbench | **Pass** (bundle); **Fail** (access) |
| Role C | No engineer chrome | **Partial** (product_only build) |
| Broker | Empty state paste | **Fail** (SSO) |
| Broker | 5-min loop | **Fail** (SSO) |

**Reality section:** **Fail**

---

### Commercial

| # | Check | Result |
|---|-------|--------|
| CM1–CM5 | All | **N/A** | P16-T is systems sprint |

**Commercial section:** **N/A**

---

## Section summary

| Section | Result |
|---------|--------|
| Deploy | **Fail** |
| Environment | **Fail** |
| Runtime | **Fail** |
| Capability | **Fail** |
| Reality | **Fail** |
| Commercial | N/A |

---

## Overall verdict

| | |
|---|---|
| **Overall** | **Fail** |
| Sprint ID | P16-T |
| Date | 2026-06-01 |
| Preview URL tested | ui-waterwoods alias |
| Production URL tested | ui-smoky-beta |

---

## Can we advance?

### P16-T (this sprint)

**Yes — close P16-T.** Deliverable was operational runner + reality documentation, not trial launch.

### Trial / Chen Kui Day 0

**No — blocked.**

| Blocker | FP |
|---------|-----|
| Preview SSO 401 | FP-004 |
| Production stale wrong UI | FP-001, FP-013 |
| No Andy E2E log | FP-010, FP-015 |
| Vercel env not persisted | FP-003 |

### P17

**Remain blocked** per mission constraint and P16-S/P16-R verdict — trial gates not met.

---

## Gate decision

```
POST_SPRINT_HEALTH_CHECK → FAIL
post_sprint_check.sh     → FAIL (exit 1)
REALITY_VALIDATION       → FAIL (Q1, Q13–14, Q24, Q28–30)

ADVANCE trial?  NO
ADVANCE P17?    NO
CLOSE P16-T?    YES (runner operational)
```

---

*End of P16-T Phase 6 — Reality Gate*
