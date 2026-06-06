# P16-T Phase 5 — Deploy Verification

**Date:** 2026-06-01  
**Command:** `bash scripts/post_sprint_check.sh --sprint P16-T`  
**Environment:** WSL2, node 22, vercel CLI 50.32.3  
**Git:** `sprint-a/broker-front-door` @ `d05e94d`

---

## Raw output

```
POST SPRINT HEALTH CHECK v0.1 — P16-T
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

## Check-by-check analysis

| Check | Result | Interpretation |
|-------|--------|----------------|
| git_branch | PASS | Sprint branch identifiable |
| git_commit | PASS | P16-O commit at HEAD |
| local_version | PASS | ui 0.1.0 + timestamp |
| preview_url_reachable | **FAIL** | Broker cannot cold-open — expected FP-004 |
| production_url_reachable | PASS | Prod serves HTML (wrong bundle age) |
| preview_protection_absent | **FAIL** | Vercel Deployment Protection ON |
| product_only_flag | PASS | Preview **bundle** correct (via vercel curl) |
| cors_preflight | PASS | Cloud Run allows current Preview origin |
| bundle_sprint_markers | PASS | P16-O strings in Preview bundle |
| cloud_run_health | PASS | API intake path ready |

---

## Supplementary evidence

### Bundle parity

| Environment | Bundle | P16-O marker | product_only marker |
|-------------|--------|--------------|---------------------|
| Preview | `index-CKPYkrkL.js` | 1× | 1× `快速体验（可选）` |
| Production | `index-ctrXdUgj.js` | 0× | 0× |

### API readiness (`/readyz` excerpt)

```json
{
  "ok": true,
  "intake_path_ready": true,
  "demo_mode": true
}
```

### CORS (Preview deploy origin)

```
HTTP/2 200
access-control-allow-origin: https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app
```

---

## What the runner correctly caught

1. **FP-004** — Preview SSO blocks cold access (2 related FAILs)
2. **FP-001/013** — Parity note: different bundle hashes
3. **FP-002** — CORS PASS (would catch regression)
4. **FP-003/005** — Preview bundle has correct flags and sprint strings

## What still requires human steps

- Andy 15-min E2E on Preview (after SSO off)
- Production promote decision
- Vercel dashboard env persistence audit
- Browser console / paste loop (Runtime R4–R5)

---

## Runner operational?

**Yes** — script runs end-to-end, exits non-zero on real blockers, produces actionable FP hints.

**Trial ready?** **No** — same blockers as P16-R, now machine-detected in <10 seconds.

---

*End of P16-T Phase 5 — Deploy Verification*
