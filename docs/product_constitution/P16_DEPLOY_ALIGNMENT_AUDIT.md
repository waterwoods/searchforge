# P16 Deploy Alignment Audit

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 4  
**Mode:** Read-only (git diff + prior live audit from `P16_DEPLOYMENT_PARITY_REPORT.md`)  
**Baseline:** `517f728` (`release/p16-demo-ready-v1`)

---

## Verdict: **CONDITIONAL PASS**

Preview demo path is **functionally aligned** for broker trial. Backend SHA lags baseline by one commit, but that commit is **frontend-only** — backend redeploy is **not required** for API or triage parity. Production Vercel remains **pre-P16** and is out of scope for today's demo.

---

## SHA comparison

| Surface | SHA | Full commit | Date (PDT) | Aligned? |
|---------|-----|-------------|------------|:--------:|
| **Frontend (Preview)** | `517f728` | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` | 2026-06-04 21:14:35 | ✅ |
| **Backend (Cloud Run)** | `29a00f8` | `29a00f8c75320a2e28f67a961cebfa583bd89484` | 2026-06-04 18:54:38 | ⚠️ |
| **Release branch** | `517f728` | same | 2026-06-04 21:14:35 | ✅ |
| **Production Vercel** | ~`85bacc6` era | pre-Sprint A bundle | 2026-04-21 | ❌ |

**Gap:** Backend is **1 commit behind** baseline. Frontend deployed **~2 h 18 min after** backend.

---

## 1. Exact commit difference

```
29a00f8  fix(p16): add-car triage parity and Wu Miss demo package   ← Cloud Run
    ↓
517f728  fix(p16): active case choice gate                          ← Frontend / baseline
```

| Field | `29a00f8` (backend) | `517f728` (frontend/baseline) |
|-------|---------------------|--------------------------------|
| Parent | `b0d6073` | `29a00f8` |
| Author date | 2026-06-04 18:54:38 PDT | 2026-06-04 21:14:35 PDT |
| Files changed | multiple (prior commit) | **1 file** |

---

## 2. Files changed (`29a00f8..517f728`)

```
ui/src/features/intake/components/CustomerEntryTab.tsx | 223 insertions, 42 deletions
```

**Only change:** `CustomerEntryTab.tsx` — active case choice gate UX.

No Python, no API routes, no `services/` changes in the gap commit.

---

## 3. Is backend redeploy required?

| Question | Answer |
|----------|--------|
| API contract changed? | **No** |
| Triage logic changed? | **No** (change is in `29a00f8`, already deployed) |
| New env vars needed? | **No** |
| `/readyz` affected? | **No** — `intake_path_ready: true` |
| SHA label parity desired? | **Yes** — cosmetic `GIT_SHA` mismatch |

**Conclusion:** Backend redeploy is **not required** for functional parity. Redeploy from `517f728` is **recommended for SHA hygiene** and post-promotion production alignment, not for fixing a broken API.

---

## 4. User-visible behavior difference

| Behavior | Backend `29a00f8` + Frontend `517f728` | Both at `29a00f8` |
|----------|------------------------------------------|-------------------|
| Add-car triage parity | ✅ (from `29a00f8`) | ✅ |
| Wu Miss demo package | ✅ (from `29a00f8`) | ✅ |
| Active case choice gate | ✅ (frontend `517f728`) | ❌ Missing |
| Message-first entry (P16-O) | ✅ | ✅ |
| Product-only markers | ✅ | ✅ |
| CORS on `ui-waterwoods` alias | ✅ | ✅ |
| CORS on raw deploy hash URL | ❌ | ❌ |

**User-visible delta:** The **active case choice gate** — when a customer has an in-progress add-car case, they see "继续办理" vs "开始新的加车报价" instead of auto-resuming or a single inline hint. This is **already live** on Preview because frontend is at `517f728`.

---

## Deployment surfaces

| Surface | URL / ID | Status |
|---------|----------|--------|
| Preview alias (demo) | `ui-waterwoods-andys-projects-1f411b73.vercel.app` | ✅ Use this |
| Preview hash URL | `ui-rfkvvg0sz-andys-projects-1f411b73.vercel.app` | ⚠️ CORS 400 |
| Cloud Run API | `fiqa-api-g7zatxrycq-uw.a.run.app` | ✅ Healthy |
| Production Vercel | `ui-smoky-beta.vercel.app` | ❌ Pre-P16 UX |

---

## Manifest / release branch alignment

| Artifact | Points to `517f728`? | Notes |
|----------|:--------------------:|-------|
| `release/p16-demo-ready-v1` | ✅ | Local only |
| Tag `p16-demo-ready-v1` | ✅ | Local only |
| `sprint-a/broker-front-door` (local) | ✅ | Current HEAD |
| `origin/sprint-a/broker-front-door` | ❌ | `d05e94d` (3 behind) |
| Cloud Run `GIT_SHA` | ❌ | `29a00f8c7` |
| Vercel Preview bundle | ✅ (inferred) | Deploy timestamp matches commit |

---

## Automated gate score

`post_sprint_check.sh --sprint P16-FREEZE`: **9/10 PASS**

| Check | Result |
|-------|--------|
| git_commit | PASS |
| preview_url_reachable | PASS |
| preview_protection_absent | PASS |
| product_only_flag | PASS |
| bundle_sprint_markers | PASS |
| cors_preflight (hash URL) | FAIL |
| cloud_run_health | PASS |
| pilot_env_posture | PASS |

---

## Verdict rationale

| Level | Met? | Reason |
|-------|:----:|--------|
| **PASS** | ❌ | Production frontend diverges; SHA labels mismatch |
| **CONDITIONAL PASS** | ✅ | Preview alias serves baseline UX; API healthy; gap commit is frontend-only; demo viable today |
| **FAIL** | ❌ | Would apply if API down, SSO blocked, or markers absent |

---

## Closure actions (documentation only — not executed)

1. **Optional SHA hygiene:** Redeploy Cloud Run from `517f728` → `bash scripts/deploy_paid_pilot.sh`
2. **Production parity:** `cd ui && vercel deploy --prod` after founder E2E
3. **CORS:** Share `ui-waterwoods` alias only, or append new hash origins to `ALLOWED_ORIGINS`
4. **Remote preservation:** Push release branch + tag (see `P16_RELEASE_PRESERVATION_CHECK.md`)

---

*End of P16 Deploy Alignment Audit — Phase 4*
