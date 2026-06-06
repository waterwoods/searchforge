# P16-V Phase 4 — Preview Protection Change

**Date:** 2026-06-01  
**Status:** **NOT APPLIED** — blocked on founder dashboard access

---

## Intended change

Disable Vercel Deployment Protection for Preview deployments on project `ui`.

| Environment | Before | After (planned) |
|-------------|--------|-----------------|
| Preview | SSO / HTTP 401 | HTTP 200 cold |
| Production | HTTP 200 (unchanged) | HTTP 200 (unchanged) |

---

## Execution attempt

| Method | Result |
|--------|--------|
| `vercel project inspect ui` | ✅ Project metadata only — no protection API |
| `vercel --help \| grep protect` | ❌ No CLI protection commands |
| `vercel project --help` | ❌ No `protection` subcommand |
| Vercel REST API | ❌ No `VERCEL_TOKEN` in agent environment |
| Dashboard `…/settings/deployment-protection` | ❌ Login wall — agent session not authenticated as Andy |

**Conclusion:** Phase 4 cannot be completed by agent. Change is **classified safe** (see P16V_PREVIEW_PROTECTION_PLAN.md) but requires **Andy manual toggle**.

---

## Before state (verified 2026-06-01)

```
$ curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app
HTTP/2 401
set-cookie: _vercel_sso_nonce=…
```

```
$ curl -sI https://ui-iwnyo9ufa-andys-projects-1f411b73.vercel.app
HTTP/2 401
set-cookie: _vercel_sso_nonce=…
```

```
$ bash scripts/post_sprint_check.sh
Checks passed: 8 / 10 (80%)
OVERALL ...................... FAIL
```

---

## After state (expected once Andy applies)

```
$ curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app
HTTP/2 200
(no _vercel_sso_nonce)
```

```
$ bash scripts/post_sprint_check.sh
Checks passed: 10 / 10 (100%)
OVERALL ...................... PASS
```

---

## After state (actual — P16-V close)

**Unchanged from Before.** Protection was not disabled during P16-V agent execution.

| Check | Actual |
|-------|--------|
| Preview cold curl | Still **401** |
| Runner score | Still **8/10** |
| Phase 4 complete? | **NO** |

---

## Founder action required

1. Log in to Vercel as `waterwoods`
2. Navigate to: `https://vercel.com/andys-projects-1f411b73/ui/settings/deployment-protection`
3. Disable Deployment Protection for **Preview** only
4. Re-run `bash scripts/post_sprint_check.sh`

---

*End of P16-V Phase 4 — Preview Protection Change (NOT APPLIED)*
