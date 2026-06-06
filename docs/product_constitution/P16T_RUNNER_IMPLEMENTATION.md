# P16-T Phase 3 — Health Check Runner Implementation

**Date:** 2026-06-01  
**Deliverable:** `scripts/post_sprint_check.sh` v0.1  
**Design source:** `P16S_HEALTHCHECK_RUNNER_DESIGN.md`

---

## What was built

Single bash entry point that runs 10 mandatory checks and prints **PASS / FAIL** with FP-ID hints on failure.

```bash
bash scripts/post_sprint_check.sh
bash scripts/post_sprint_check.sh --preview URL --production URL --api URL --sprint P16-X
bash scripts/post_sprint_check.sh --markers "请把您的需求发给我们,自定义标记"
```

**Exit codes:** `0` = overall PASS · `1` = FAIL · `2` = usage error

---

## Check implementation

| # | Check ID | Logic | FP mapping |
|---|----------|-------|------------|
| 1 | `git_branch` | `git rev-parse --abbrev-ref HEAD` | FP-019 |
| 2 | `git_commit` | `git rev-parse --short HEAD` | FP-005 |
| 3 | `local_version` | `ui/package.json` version + commit date | FP-011 |
| 4 | `preview_url_reachable` | `curl -sI` → HTTP **200** | FP-004, FP-014 |
| 5 | `production_url_reachable` | `curl -sI` → HTTP **200** | FP-013 |
| 6 | `preview_protection_absent` | Fail on 401 / SSO headers | FP-004 |
| 7 | `product_only_flag` | Grep preview bundle for product-only markers | FP-003, FP-017 |
| 8 | `cors_preflight` | OPTIONS Preview origin → API `/api/inbox/cases` | FP-002 |
| 9 | `bundle_sprint_markers` | Grep bundle for `--markers` strings | FP-005, FP-008 |
| 10 | `cloud_run_health` | GET `/readyz` → `intake_path_ready` or `ok` | FP-006 |

---

## Defaults

| Variable | Default |
|----------|---------|
| Preview alias | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| Preview deploy | `https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app` |
| Production | `https://ui-smoky-beta.vercel.app` |
| API | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Markers | `请把您的需求发给我们,原样粘贴微信/通知文字，不用整理` |
| Product-only markers | `快速体验（可选）,原样粘贴微信/通知文字，不用整理` |

---

## Preview 401 handling

When cold curl returns 401 (FP-004):

- Checks 4 and 6 **FAIL** (correct — broker cannot cold-open)
- Bundle checks 7 and 9 use **`vercel curl`** fallback when CLI is linked to project
- Parity note prints Preview vs Production bundle hash mismatch

This matches operator reality: engineers can verify bundle content; brokers still blocked.

---

## Dependencies

| Tool | Required | Purpose |
|------|----------|---------|
| `curl` | Yes | HTTP checks |
| `git` | Yes | Branch/commit |
| `python3` | Yes | JSON parse for `/readyz` |
| `vercel` | Optional | Preview bundle when SSO on |
| `jq` | No | Not used in v0.1 |

---

## Reused scripts

| Script | Relationship |
|--------|--------------|
| `validate_pilot_deploy_env.py` | Optional WARN line (not in pass/fail count) |
| `guardrail_inbox_triage.sh` | Not called — local-only; future v0.2 |
| `demo_quick_validate.sh` | Not called — local-only; future v0.2 |

---

## Deferred to v0.2+

- Weighted health / risk scores from design doc
- `--json` machine output
- `--skip-local` / local demo phase
- `--commercial` invoice grep
- Vercel env API audit (FP-003 dashboard)
- Production product_only check after promote

---

## Sample output (2026-06-01)

```
POST SPRINT HEALTH CHECK v0.1 — P16-T
...
  preview_url_reachable        FAIL (HTTP 401)
  production_url_reachable     PASS (HTTP 200)
  preview_protection_absent    FAIL (SSO/401 detected (FP-004))
  product_only_flag            PASS (markers present on preview (index-CKPYkrkL.js))
  cors_preflight               PASS (OPTIONS 200 for preview origin)
  bundle_sprint_markers        PASS (preview bundle index-CKPYkrkL.js)
  cloud_run_health             PASS (/readyz intake_path_ready)

SCORES
  Checks passed: 8 / 10 (80%)

OVERALL ...................... FAIL
```

---

## Verification

```bash
chmod +x scripts/post_sprint_check.sh
bash scripts/post_sprint_check.sh --sprint P16-T
# Expect exit 1 until FP-004 resolved
```

---

*End of P16-T Phase 3 — Runner Implementation*
