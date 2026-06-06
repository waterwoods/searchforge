# P16-U Phase 1 — Health Check Baseline

**Date:** 2026-06-01  
**Command:** `bash scripts/post_sprint_check.sh --sprint P16-U`  
**Environment:** WSL2, vercel CLI authenticated (`waterwoods`)  
**Git:** `sprint-a/broker-front-door` @ `d05e94d`

---

## URLs under test

| Surface | URL |
|---------|-----|
| Preview alias | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| Preview deploy (CORS origin) | https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app |
| Production | https://ui-smoky-beta.vercel.app |
| API | https://fiqa-api-g7zatxrycq-uw.a.run.app |

---

## Raw runner output

```
POST SPRINT HEALTH CHECK v0.1 — P16-U
Repo:    /home/andy/searchforge
Preview: https://ui-waterwoods-andys-projects-1f411b73.vercel.app
Prod:    https://ui-smoky-beta.vercel.app
API:     https://fiqa-api-g7zatxrycq-uw.a.run.app

GIT / LOCAL
  git_branch                   PASS (sprint-a/broker-front-door)
  git_commit                   PASS (d05e94d)
  local_version                PASS (ui@0.1.0 commit=d05e94d date=2026-06-01 00:03:44 -0700)

DEPLOY / REMOTE
  preview_url_reachable        FAIL (HTTP 401)
  production_url_reachable     PASS (HTTP 200)
  preview_protection_absent    FAIL (SSO/401 detected (FP-004))
  product_only_flag            PASS (markers present on preview (index-CKPYkrkL.js))
  cors_preflight               PASS (OPTIONS 200 for preview origin)
  bundle_sprint_markers        PASS (preview bundle index-CKPYkrkL.js)
  (parity note: preview=index-CKPYkrkL.js prod=index-ctrXdUgj.js — FP-001/FP-013)

RUNTIME / API
  cloud_run_health             PASS (/readyz intake_path_ready)
  pilot_env_posture .......... WARN (validate_pilot_deploy_env.py)

SCORES
  Checks passed: 8 / 10 (80%)

OVERALL ...................... FAIL
Blockers:
  - HTTP 401
  - SSO/401 detected (FP-004)
```

**Exit code:** 1

---

## Result summary

| Status | Count | Checks |
|--------|-------|--------|
| **PASS** | 8 | git_branch, git_commit, local_version, production_url_reachable, product_only_flag, cors_preflight, bundle_sprint_markers, cloud_run_health |
| **FAIL** | 2 | preview_url_reachable, preview_protection_absent |
| **WARN** | 1 | pilot_env_posture (local `.env.cloudrun` incomplete — not a deployed blocker) |

**Health score:** **80%** (8/10 automated checks)

**Overall gate:** **FAIL**

---

## Warnings (non-blocking but tracked)

| Warning | Detail |
|---------|--------|
| `pilot_env_posture` | `validate_pilot_deploy_env.py` failed on local `.env.cloudrun` — missing API keys + wrong PG_DUAL_WRITE before P16-U fix |
| Parity note | Preview bundle `index-CKPYkrkL.js` ≠ Production `index-ctrXdUgj.js` (informational, FP-001/FP-013) |

---

## What the runner proved (deployed reality)

| Claim | Deployed evidence |
|-------|-------------------|
| P16-O strings on Preview | ✅ `请把您的需求发给我们` in `index-CKPYkrkL.js` (via vercel curl fallback) |
| product_only on Preview | ✅ `快速体验（可选）` present |
| CORS for current Preview | ✅ OPTIONS 200, allow-origin matches `ui-iwnyo9ufa` |
| API intake path | ✅ `/readyz` → `intake_path_ready: true` |
| Broker cold open Preview | ❌ HTTP 401 + `_vercel_sso_nonce` |
| Production current | ✅ HTTP 200 but **41-day-old bundle** without P16-O markers |

---

## Baseline verdict

The Health Check Runner is **operational** and correctly surfaces the same P0 blocker as P16-R/P16-T: **Preview SSO (FP-004)**. Engine and Preview bundle content are healthy; **distribution is not**.

---

*End of P16-U Phase 1 — Health Check Baseline*
