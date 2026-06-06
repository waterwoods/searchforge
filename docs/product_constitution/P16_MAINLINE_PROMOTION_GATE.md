# P16 Mainline Promotion Gate

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 6  
**Candidate mainline:** `sprint-a/broker-front-door` @ `517f728`  
**Current `main`:** `31572ca` (2025-11-24, **98 commits behind**)

---

## Verdict: **CONDITIONAL GO**

Promotion from `sprint-a/broker-front-door` to `main` is **technically feasible** and **architecturally intended**, but **not safe today**. Complete the blockers below before any merge to `main`.

---

## Gate Checklist

| Gate | Status | Blocker? | Detail |
|------|--------|:--------:|--------|
| Merge conflicts vs `main` | ✅ PASS | No | 0 conflicts (`git merge-tree` dry-run) |
| Ahead/behind vs `main` | ✅ PASS | No | 98 ahead, 0 behind |
| Release preservation (local) | ✅ PASS | No | `release/p16-demo-ready-v1` + tag @ `517f728` |
| Release preservation (remote) | ❌ FAIL | **Yes** | Branch + tag not on origin |
| Archive rollback branch | ✅ PASS | No | `archive/production-pre-p16-demo` on origin @ `85bacc6` |
| Dirty working tree | ❌ FAIL | **Yes** | 1,769 uncommitted paths |
| Local vs origin sprint-a | ⚠️ WARN | **Yes** | Local 3 commits ahead of origin |
| Rollback readiness | ✅ PASS | No | Archive branch + tag provide rollback |
| Business logic untouched | ✅ PASS | No | This sprint made no logic changes |

---

## Merge Conflict Analysis

```
git merge-tree $(git merge-base main sprint-a/broker-front-door) main sprint-a/broker-front-door
→ "changed in both" count: 0
```

**Diff stat:** 2,083 files changed, +597,932 / −3,259 lines across 98 commits.

Fast-forward or merge to `main` will **not produce conflicts** from committed objects. Risk is entirely from **uncommitted working tree state**, not from branch divergence.

---

## Dirty Tree Impact

| Metric | Value |
|--------|-------|
| Uncommitted paths | **1,769** |
| Documentation | 94.5% |
| Code | 1.5% |
| Safe to commit | 94.5% |

**Impact:** HEAD commit `517f728` is clean and demo-ready. The surrounding checkout is not. Any promotion performed while the tree is dirty would be **unreproducible** and could accidentally include or exclude archival work.

**Required:** Commit or stash all hygiene work **before** merging to `main`. Promotion must merge **commit objects only**.

---

## Release Preservation Status

| Artifact | Local | Origin | Required for GO |
|----------|:-----:|:------:|:---------------:|
| `release/p16-demo-ready-v1` | ✅ `517f728` | ❌ | Push before merge |
| Tag `p16-demo-ready-v1` | ✅ `517f728` | ❌ | Push before merge |
| `archive/production-pre-p16-demo` | ✅ `85bacc6` | ✅ | Done |
| `sprint-a/broker-front-door` | ✅ `517f728` | ⚠️ `d05e94d` | Push 3 commits first |

---

## Rollback Readiness

| Scenario | Rollback Target | Available |
|----------|-----------------|:---------:|
| Post-promotion regression | `archive/production-pre-p16-demo` @ `85bacc6` | ✅ On origin |
| Demo state restore | Tag `p16-demo-ready-v1` @ `517f728` | ✅ Local |
| Pre-simplification restore | `checkpoint/before-simplification-execution-20260526-0346` | ✅ Local |

Rollback paths exist. Remote tag push is required for team-wide rollback.

---

## Prerequisites for Full GO

Ranked in execution order:

1. **Commit hygiene work** — 3 commits (A/B/C per `P16_COMMIT_PLAN.md`); resolve 94 REVIEW_REQUIRED paths
2. **Push sprint-a** — `git push origin sprint-a/broker-front-door` (3 commits)
3. **Push release branch** — `git push -u origin release/p16-demo-ready-v1`
4. **Push tag** — `git push origin p16-demo-ready-v1`
5. **Run validation** — `bash scripts/demo_pre_checklist.sh` + `bash scripts/guardrail_inbox_triage.sh`
6. **Merge to main** — founder-approved PR or direct merge (out of scope for this sprint)

---

## Why Not NO_GO

- Zero merge conflicts
- Demo-ready HEAD is frozen and tagged locally
- Archive rollback exists on origin
- 98-commit divergence is intentional product evolution, not accidental drift

## Why Not Full GO

- 1,769-path dirty tree is a hard blocker
- Release artifacts not on origin
- 3 unpushed commits on sprint-a create remote/local ambiguity
