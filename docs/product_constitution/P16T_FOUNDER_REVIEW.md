# P16-T Phase 7 — Founder Review

**Date:** 2026-06-01  
**Audience:** Andy (founder)  
**Context:** P16-T operationalizes P16-S; first live run of `post_sprint_check.sh`

---

## 1. What failures are now automatically detected?

| Failure | How detected | Time to detect |
|---------|--------------|----------------|
| Preview SSO wall (FP-004) | Cold curl → 401; `preview_protection_absent` FAIL | <5 sec |
| Preview unreachable to broker | `preview_url_reachable` FAIL | <5 sec |
| CORS origin missing (FP-002) | OPTIONS preflight FAIL | <5 sec |
| Sprint not on remote bundle (FP-005) | Marker grep FAIL | ~10 sec |
| Wrong build flags on Preview (FP-003) | product_only marker grep FAIL | ~15 sec |
| API down / not intake-ready (FP-006) | `/readyz` FAIL | <5 sec |
| Production URL down | HTTP status FAIL | <5 sec |
| Preview vs Production bundle drift | Parity note in output | automatic |
| Git branch/commit at check time | Recorded every run | automatic |

**Before P16-T:** These required manual P16-R-style audits (~2–4 hrs).  
**After P16-T:** One command, ~7 sec wall time.

---

## 2. What failures still require human judgment?

| Failure | Why manual | Checklist |
|---------|------------|-----------|
| FP-010 Founder assumption | Only Andy can certify incognito UX | REALITY Q1–Q2 |
| FP-007 UI complexity | 5-sec / 10-sec visual tests | P16-M/N pattern |
| FP-008 full reality gap | Score delta needs role simulation | P16-Q scorecard |
| FP-012 Capability regression | 7-cap scoring + tradeoff docs | POST_SPRINT § Capability |
| FP-014 Broken trial flow | Multi-day journey | TRIAL_ONE_PATH |
| FP-015 Missing evidence | E2E log, observation log, screenshots | REALITY Q21–23 |
| FP-018 Draft language | Chinese office quality | Paste + read draft |
| FP-009 Commercial | Payment IDs, relationship judgment | CM2, Q20 |
| FP-020 Scope creep | Trial freeze ethics | Git + calendar review |
| Browser paste loop | Network Error vs app bug disambiguation | P5, R4 manual |

**Rule unchanged:** Localhost PASS is necessary but not sufficient.

---

## 3. What failures cost the most time?

| Rank | Failure | Historical cost | Now |
|------|---------|-----------------|-----|
| 1 | FP-004 Preview SSO | ~30+ hrs misdiagnosed as "broken product" | Auto FAIL in 5 sec |
| 2 | FP-001 / FP-013 Deploy parity | ~50 hrs (P16-Q, P16-R) | Partial auto + parity note |
| 3 | FP-002 CORS whack-a-mole | ~14 hrs (P16-F–G) | Auto detect; patch still manual |
| 4 | FP-010 Founder local-only validation | ~20 hrs false confidence | Still manual — **highest remaining human cost** |
| 5 | FP-003 Flag drift on redeploy | ~15 hrs invisible sprint work | Partial — dashboard still manual |

**Biggest remaining time sink:** Founder not running 15-min Preview E2E after SSO fix — automation cannot substitute.

---

## 4. What should never happen again?

| Never again | Prevention |
|-------------|------------|
| Send Preview URL before cold curl | `post_sprint_check.sh` gate — exit 1 blocks GO |
| Sprint GO with local-only evidence | POST_SPRINT + REALITY checklists mandatory |
| Assume push = deploy | `bundle_sprint_markers` + explicit deploy step |
| Diagnose "product bug" during CORS/SSO outage | Runner classifies infra vs app (CORS + SSO checks first) |
| Production link in broker docs while 41d stale | Parity note + PR2/PR3 manual rows |
| Redeploy Vercel without `-b` flags | F3 fail until dashboard env persisted |
| Start P17 while FP-004 open | Reality Gate FAIL → P17 blocked |

---

## Founder action list (unchanged priority)

| # | Action | Time | Unblocks |
|---|--------|------|----------|
| 1 | Disable Vercel Preview Deployment Protection | 5 min | FP-004, Day 0 |
| 2 | Re-run `bash scripts/post_sprint_check.sh` → expect PASS on checks 4+6 | 1 min | Verification |
| 3 | Andy 15-min Preview E2E log (incognito) | 15 min | FP-010, FP-015 |
| 4 | Persist Vercel env vars Preview + Prod | 10 min | FP-003 |
| 5 | `vercel deploy --prod` after Preview PASS | 15 min | FP-001, FP-013 |

---

## One paragraph for Andy

P16-T gives you a **7-second truth check** before any sprint close or URL share. It will **FAIL loudly** on SSO and **PASS** on the things P16-R fixed (CORS, Preview bundle content, API health). It cannot click paste for you or fill invoice IDs. The next 30 minutes of founder time (SSO off + E2E log + env dashboard) unlock more than the last three UI sprints combined.

---

*End of P16-T Phase 7 — Founder Review*
