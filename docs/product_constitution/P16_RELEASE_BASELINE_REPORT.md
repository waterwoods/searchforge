# P16 Release Baseline Report

**Date:** 2026-06-05  
**Mission:** P16 Release Freeze & Promotion Readiness — Phase 1  
**Mode:** Read-only governance (no merges, pushes, tags, or deploys)  
**Remote:** `origin` → `git@github.com:waterwoods/searchforge.git`

---

## Executive summary

| Branch | SHA | On origin? | Demo readiness |
|--------|-----|:----------:|----------------|
| `sprint-a/broker-front-door` (local) | `517f7281…` | Partial (origin is 3 commits behind local) | **Demo-ready** (local + Preview alias) |
| `release/p16-demo-ready-v1` | `517f7281…` | **No** (local only) | **Frozen baseline** — matches local sprint HEAD |
| `archive/production-pre-p16-demo` | `85bacc639…` | Yes (in sync) | **Not P16 demo-ready** — pre-Sprint A production snapshot |

**Canonical P16 demo-ready SHA:** `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37`  
**Commit:** `fix(p16): active case choice gate`  
**Commit date:** 2026-06-04 21:14:35 -0700

---

## Branch inventory

### 1. `sprint-a/broker-front-door`

| Field | Value |
|-------|-------|
| **Full SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Short SHA** | `517f728` |
| **Commit date** | 2026-06-04 21:14:35 -0700 |
| **Subject** | `fix(p16): active case choice gate` |
| **Local** | Yes (current HEAD) |
| **Origin** | Yes — `origin/sprint-a/broker-front-door` @ `d05e94da0855942c6143405720d65be35b3c5829` |
| **Ahead of origin** | **3** |
| **Behind origin** | **0** |
| **Ahead of `main`** | **98** commits |
| **Purpose** | Active P16 product line — broker front door, unified intake, paid-pilot posture. De facto mainline since `main` last moved 2025-11-24. |
| **Demo readiness** | **DEMO READY (local + Preview)** — see evidence below |

**Local commits not yet on origin:**

| SHA | Subject |
|-----|---------|
| `517f728` | fix(p16): active case choice gate |
| `29a00f8` | fix(p16): add-car triage parity and Wu Miss demo package |
| `b0d6073` | fix(ui): restore missing getCompactQueuePreview import in broker workbench |

**Demo readiness evidence (2026-06-05):**

| Check | Result |
|-------|--------|
| `post_sprint_check.sh --sprint P16-FREEZE` | 9/10 PASS (CORS fail only when testing raw deployment hash URL; alias passes) |
| Preview alias cold access | HTTP 200, no SSO (FP-004 resolved on alias) |
| Preview bundle | `index-CJ0tCunS.js` — P16-O + product_only markers present |
| Preview deploy time | 2026-06-04 21:14:40 PDT (matches commit within 5 s) |
| Cloud Run `/readyz` | `intake_path_ready: true` |
| `.env.cloudrun` validation | PASS |
| Production alias | **Not demo-ready** — 45-day-old bundle, pre-Sprint A UX |

---

### 2. `release/p16-demo-ready-v1`

| Field | Value |
|-------|-------|
| **Full SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Short SHA** | `517f728` |
| **Commit date** | 2026-06-04 21:14:35 -0700 |
| **Subject** | `fix(p16): active case choice gate` |
| **Local** | Yes |
| **Origin** | **No** |
| **Ahead/behind origin** | N/A (branch not on remote) |
| **Purpose** | Permanent, reproducible P16 demo-ready baseline before mainline promotion. Immutable release pointer for rollback and archaeology. |
| **Demo readiness** | **FROZEN BASELINE** — identical commit to local sprint HEAD; intended release snapshot |

---

### 3. `archive/production-pre-p16-demo`

| Field | Value |
|-------|-------|
| **Full SHA** | `85bacc639f174e0680d11d8486aa86b53ffa6986` |
| **Short SHA** | `85bacc6` |
| **Commit date** | 2026-04-21 06:50:43 -0700 |
| **Subject** | `feat(simulation): add one-click auto replay with image-step support` |
| **Local** | Yes |
| **Origin** | Yes — `origin/archive/production-pre-p16-demo` @ same SHA |
| **Ahead of origin** | **0** |
| **Behind origin** | **0** |
| **Commits behind sprint line** | **73** (from archive → `517f728`) |
| **Purpose** | Pre-P16 production rollback anchor. Matches era of live `ui-smoky-beta` production deploy (2026-04-21). |
| **Demo readiness** | **NOT P16 demo-ready** — pre-Sprint A product surface; valid rollback target only |

---

## Annotated tag (related baseline artifact)

| Field | Value |
|-------|-------|
| **Tag name** | `p16-demo-ready-v1` |
| **Points to** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Tagger message** | `P16 demo-ready release snapshot v1 (sprint-a/broker-front-door)` |
| **Local** | Yes |
| **Origin** | **No** |

---

## Relationship diagram

```
main (31572ca, 2025-11-24, stale)
  └── … 98 commits …
        └── archive/production-pre-p16-demo (85bacc6, 2026-04-21) ← production rollback
              └── … 73 commits …
                    └── origin/sprint-a/broker-front-door (d05e94d, 2026-06-01)
                          └── b0d6073 → 29a00f8 → 517f728 ← LOCAL sprint + release branch + tag
```

---

## Stale-main context

| Branch | Last commit | Status |
|--------|-------------|--------|
| `main` | 2025-11-24 | Stale — 98 commits behind active line |
| `sprint-a/broker-front-door` | 2026-06-04 | Active P16 line (33 commits in last 30 days) |

Promotion of `sprint-a/broker-front-door` → `main` would bring 98 commits of P16 work onto the canonical default branch.

---

## Working tree note (does not change branch SHAs)

Current checkout has **1,757 uncommitted path changes** (mostly doc archival/deletions). Branch tip SHAs above are **clean commit objects**; dirty tree affects promotion safety (see `P16_MAINLINE_PROMOTION_READINESS.md`).

---

*End of P16 Release Baseline Report — Phase 1*
