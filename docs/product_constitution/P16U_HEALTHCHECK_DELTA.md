# P16-U Phase 5 — Health Check Delta (Before vs After)

**Date:** 2026-06-01  
**Before:** `post_sprint_check.sh --sprint P16-U`  
**After:** `post_sprint_check.sh --sprint P16-U-post-fix` (following `.env.cloudrun` sync)

---

## Score comparison

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Checks passed | 8 / 10 | 8 / 10 | **0** |
| Health score | **80%** | **80%** | **0** |
| OVERALL | **FAIL** | **FAIL** | unchanged |
| Exit code | 1 | 1 | unchanged |

---

## Check-by-check delta

| Check | Before | After | Changed? |
|-------|--------|-------|----------|
| git_branch | PASS | PASS | — |
| git_commit | PASS | PASS | — |
| local_version | PASS | PASS | — |
| preview_url_reachable | **FAIL** 401 | **FAIL** 401 | — |
| production_url_reachable | PASS | PASS | — |
| preview_protection_absent | **FAIL** FP-004 | **FAIL** FP-004 | — |
| product_only_flag | PASS | PASS | — |
| cors_preflight | PASS | PASS | — |
| bundle_sprint_markers | PASS | PASS | — |
| cloud_run_health | PASS | PASS | — |
| pilot_env_posture | WARN (8 errors) | WARN (2 errors) | **Improved** (not scored) |

---

## What changed (off-score)

| Item | Before | After |
|------|--------|-------|
| `validate_pilot_deploy_env.py` errors | 8 | 2 |
| `.env.cloudrun` PG_DUAL_WRITE | 1 (wrong) | 0 (correct) |
| `.env.cloudrun` PRODUCT_ONLY | missing | 1 |
| Deployed Preview SSO | 401 | 401 |
| Deployed bundle hashes | CKPYkrkL / ctrXdUgj | unchanged |

---

## Interpretation

The autonomous loop **correctly applied** the only safe fix available and **correctly did not** claim victory:

- Env posture drift (FP-011) partially closed locally
- P0 distribution blocker (FP-004) unchanged on deployed URLs
- Runner score is an honest reflection of **broker-facing reality**, not local file hygiene

**Expected delta after founder SSO fix:** +2 checks → **10/10 (100%)** on deploy section, then Production promote addresses parity note.

---

## Blockers remaining after auto-fix

```
Blockers:
  - HTTP 401
  - SSO/401 detected (FP-004)
```

---

*End of P16-U Phase 5 — Health Check Delta*
