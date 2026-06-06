# P16-V Phase 8 — Runner Delta

**Date:** 2026-06-01  
**Command:** `bash scripts/post_sprint_check.sh` (before and after P16-V agent work)

---

## Before (Phase 1 baseline)

```
Checks passed: 8 / 10 (80%)
OVERALL ...................... FAIL
Blockers:
  - HTTP 401
  - SSO/401 detected (FP-004)
```

**Exit code:** 1

---

## After (Phase 8 re-run — post P16-V documentation, no SSO fix)

```
Checks passed: 8 / 10 (80%)
OVERALL ...................... FAIL
Blockers:
  - HTTP 401
  - SSO/401 detected (FP-004)
```

**Exit code:** 1

---

## Check-by-check delta

| Check | Before | After | Delta |
|-------|--------|-------|-------|
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

**Delta: 0 checks changed.** P16-V agent work did not modify deployed state.

---

## Score trajectory

| Milestone | Score | Overall |
|-----------|-------|---------|
| P16-V Phase 1 baseline | 8/10 | FAIL |
| P16-V Phase 8 re-run | 8/10 | FAIL |
| Target (post Andy SSO toggle) | **10/10** | **PASS** |

---

## What would change the delta

| Action | Expected delta |
|--------|----------------|
| Andy disables Preview Deployment Protection | +2 PASS (`preview_url_reachable`, `preview_protection_absent`) |
| Production promote | Parity note may clear; no runner FAIL today |
| Code changes | None required for 10/10 |

---

## Runner delta verdict

**No improvement during P16-V.** Blocker unchanged. Runner correctly stable — no score inflation.

---

*End of P16-V Phase 8 — Runner Delta*
