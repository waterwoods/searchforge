# P16-V Phase 1 — Baseline

**Date:** 2026-06-01  
**Command:** `bash scripts/post_sprint_check.sh --verbose`  
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
POST SPRINT HEALTH CHECK v0.1
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
  (preview bundle via vercel curl: index-CKPYkrkL.js)
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
| **WARN** | 1 | pilot_env_posture (local `.env.cloudrun` incomplete — not a runner FAIL) |

**Health score:** **80%** (8/10 automated checks)

**Overall gate:** **FAIL**

---

## Current FAILs (P16-V scope)

| # | Check | Detail | Pattern |
|---|-------|--------|---------|
| 1 | `preview_url_reachable` | Cold curl → HTTP 401 | FP-004 |
| 2 | `preview_protection_absent` | `_vercel_sso_nonce` cookie + SSO redirect | FP-004 |

**Both FAILs share one root cause:** Vercel Deployment Protection (SSO) on Preview.

---

## Informational (not runner FAIL)

| Note | Detail | Pattern |
|------|--------|---------|
| Bundle parity | preview=`index-CKPYkrkL.js` ≠ prod=`index-ctrXdUgj.js` | FP-001 / FP-013 |
| pilot_env_posture | Local file missing API keys | FP-011 (WARN only) |

---

## Baseline verdict

P16-V starts at **8/10 FAIL**, identical to P16-U/T/R. The sole automated path to **10/10 PASS** is closing **FP-004** (disable Preview Deployment Protection). All engine, bundle, and CORS checks already pass.

---

*End of P16-V Phase 1 — Baseline*
