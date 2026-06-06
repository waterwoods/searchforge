# P16 Mainline Promotion Readiness

**Date:** 2026-06-05  
**Mission:** P16 Release Freeze — Phase 6 & 7  
**Mode:** Read-only governance  
**Candidate mainline:** `sprint-a/broker-front-door` @ `517f728`  
**Current `main`:** `31572ca` (2025-11-24, 98 commits behind)

---

## Verdict: **CONDITIONAL GO**

Promotion is **technically feasible** and **architecturally intended**, but **not safe today** without pre-promotion hygiene. Complete the ranked prerequisites below before merging to `main`.

| Gate | Status | Blocker? |
|------|--------|:--------:|
| Release baseline frozen locally | ✅ `release/p16-demo-ready-v1` @ `517f728` | No |
| Release baseline on origin | ❌ Local only | **Yes** — push first |
| Annotated tag on origin | ❌ Local only | **Yes** — push first |
| Archive rollback branch | ✅ `archive/production-pre-p16-demo` synced on origin | No |
| Deployment parity | ⚠️ CONDITIONAL PASS | Partial — backend 1 commit behind |
| Dirty working tree | ❌ 1,757 uncommitted paths | **Yes** — must resolve |
| Local ahead of origin (3 commits) | ⚠️ | **Yes** — push sprint branch first |
| Production frontend aligned | ❌ 45-day-old bundle | No for promotion; yes for broker demo gap |

---

## Promotion safety analysis

### 1. Dirty repo impact — **BLOCKER**

| Metric | Value |
|--------|-------|
| Uncommitted paths | **1,757** |
| Diff stat vs HEAD | 1,298 files, +1,529 / −116,975 lines |
| Nature | Large doc archival/deletions, config drift, unrelated Dockerfiles |

**Impact:** A promotion merge from current working tree would be **unreproducible**. The frozen SHA `517f728` is clean, but the checkout surrounding it is not.

**Required action:** Stash, commit, or discard working tree changes **before** any merge to `main`. Promotion should merge **commit objects only**, not uncommitted work.

---

### 2. Release preservation — **BLOCKER (remote)**

| Artifact | Local | Origin |
|----------|:-----:|:------:|
| `release/p16-demo-ready-v1` | ✅ @ `517f728` | ❌ |
| Tag `p16-demo-ready-v1` | ✅ @ `517f728` | ❌ |
| `archive/production-pre-p16-demo` | ✅ @ `85bacc6` | ✅ |

**Exact commands to preserve release on origin (DO NOT run automatically):**

```bash
# Push frozen release branch
git push -u origin release/p16-demo-ready-v1

# Push annotated tag
git push origin p16-demo-ready-v1
```

**Exact commands to sync active line (3 local commits not on origin):**

```bash
git push origin sprint-a/broker-front-door
```

---

### 3. Deployment parity — **CONDITIONAL**

See `P16_DEPLOYMENT_PARITY_REPORT.md`.

| Surface | Ready for post-promotion prod? |
|---------|-------------------------------|
| Preview alias (`ui-waterwoods`) | ✅ Demo today |
| Cloud Run API | ⚠️ Redeploy from `517f728` recommended |
| Production Vercel | ❌ Do not promote prod until founder E2E |

Backend redeploy after promotion (documentation only):

```bash
git checkout release/p16-demo-ready-v1   # or sprint-a/broker-front-door @ 517f728
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

---

### 4. Rollback path — **READY**

| Rollback target | SHA | Remote | Use when |
|-----------------|-----|:------:|----------|
| `archive/production-pre-p16-demo` | `85bacc6` | ✅ | Revert to pre-P16 production UX |
| Tag `p16-demo-ready-v1` | `517f728` | ❌ (push first) | Pin known-good P16 demo |
| `main` (current) | `31572ca` | ✅ | Last canonical default (stale) |

**Rollback command pattern (after tag is on origin):**

```bash
git checkout p16-demo-ready-v1
# redeploy backend + frontend from this SHA
```

---

### 5. Archive branch existence — **PASS**

`archive/production-pre-p16-demo` exists locally and on origin, 0 ahead / 0 behind. Matches production Vercel deploy era (2026-04-21).

---

## Can `sprint-a/broker-front-door` safely become `main`?

**Yes, with conditions.**

| Factor | Assessment |
|--------|------------|
| **Code maturity** | 98 commits of P16 work; active through 2026-06-04; guardrails pass locally |
| **Scope** | Entire paid-pilot product line — this is the intended mainline |
| **Risk** | Large blast radius (98 commits); mitigated by release branch + tag + archive |
| **Stale `main`** | Promotion is overdue; keeping `main` stale increases operator confusion |

**Merge approach (documentation only — not executed):**

```bash
# After: clean working tree, release branch + tag pushed, founder sign-off
git checkout main
git pull origin main
git merge --no-ff sprint-a/broker-front-door -m "Promote P16 broker front door line to main"
git push origin main
```

Use `--no-ff` to preserve promotion merge commit for archaeology.

---

## Phase 7 — Founder recommendation

### 1. What must be done before promotion?

Ranked by priority:

| Rank | Action | Why | Est. effort |
|:----:|--------|-----|-------------|
| **1** | **Resolve dirty working tree** (commit, stash, or branch the doc archival work separately) | Promotion must be SHA-pure; 1,757 paths of drift is a reproducibility blocker | 1–2 h |
| **2** | **Push `release/p16-demo-ready-v1` to origin** | Remote release anchor before any main merge | 2 min |
| **3** | **Push tag `p16-demo-ready-v1` to origin** | Immutable rollback pointer for team + CI | 1 min |
| **4** | **Push `sprint-a/broker-front-door`** (3 commits ahead of origin) | Origin must match local baseline before merge | 1 min |
| **5** | **Redeploy Cloud Run from `517f728`** | Close backend parity gap (`29a00f8c7` → `517f728`) | 15–30 min |
| **6** | **Founder E2E on Preview alias** (`ui-waterwoods`) | Confirm active case choice gate + paste loop before calling prod | 15 min |
| **7** | **Merge `sprint-a/broker-front-door` → `main`** (after 1–4) | Establish canonical default branch | 5 min |

### 2. What can wait until after promotion?

| Rank | Action | Why defer |
|:----:|--------|-----------|
| 1 | Production Vercel promote (`vercel deploy --prod`) | Preview alias suffices for trial; prod is intentionally frozen |
| 2 | `auto-evolution/*` branch archaeology (49 local branches) | Unmerged experiments; no promotion dependency |
| 3 | Secret Manager migration for plain-text API keys on Cloud Run | Live posture is acceptable for pilot |
| 4 | BUILD_ID minification fix in frontend bundle | Observability gap only; deploy timing proves SHA |
| 5 | Bulk deletion of merged stale branches (`feat/phase-b`, etc.) | Housekeeping; see `P16_REPO_CENSUS_REPORT.md` |
| 6 | CORS allowlist automation for every Preview hash URL | Alias strategy works; document operator rule |
| 7 | Merge `reduction/p1-simplification-loops` | Parallel simplification track; separate sprint |

### 3. Safest next sprint

**Recommended: P16-PROMOTE — Mainline Promotion & Prod Align (1–2 days)**

Goal: Execute ranks 1–7 above in order, then optionally promote Production Vercel.

| Day | Focus |
|-----|-------|
| **Day 0 AM** | Clean tree → push release branch + tag + sprint branch |
| **Day 0 PM** | Redeploy Cloud Run @ `517f728`; rerun `post_sprint_check.sh` → target 10/10 |
| **Day 1 AM** | Founder E2E on Preview; merge to `main` |
| **Day 1 PM** | (Optional) `vercel deploy --prod` + update founder bookmark |

**Do not start:** `auto-evolution` archaeology, new features, or branch deletion until promotion merge is complete and tagged on origin.

---

## Decision matrix for founder

| Decision | Recommendation | When |
|----------|----------------|------|
| Push release branch? | **Yes** — `git push -u origin release/p16-demo-ready-v1` | Before main merge |
| Create tag? | **Already exists locally** — push only: `git push origin p16-demo-ready-v1` | Same session as release branch push |
| Promote main? | **After** tree clean + remote preservation + backend redeploy | Day 1 of P16-PROMOTE sprint |
| Begin branch archaeology? | **After** main promotion + prod align | Week 2 |

---

## Related reports

| Report | Path |
|--------|------|
| Release baseline | `docs/product_constitution/P16_RELEASE_BASELINE_REPORT.md` |
| Deployment parity | `docs/product_constitution/P16_DEPLOYMENT_PARITY_REPORT.md` |
| Environment preservation | `docs/product_constitution/P16_ENVIRONMENT_PRESERVATION_REPORT.md` |
| Repo census | `docs/product_constitution/P16_REPO_CENSUS_REPORT.md` |

---

*End of P16 Mainline Promotion Readiness — Phase 6 & 7*
