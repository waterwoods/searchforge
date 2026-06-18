# P16 Main Promotion Final Gate

**Date:** 2026-06-06  
**Mission:** P16-GOVERNANCE-FINALIZATION-SPRINT — Phase 5  
**Candidate:** `sprint-a/broker-front-door` @ `d870ccc`  
**Current `main`:** `31572ca` (2025-11-24)  
**Evaluation only — no merge, no rebase, no branch modification**

---

## Verdict: **CONDITIONAL GO**

Main promotion is **technically feasible** but **not safe today**. Complete blockers before any merge.

---

## Gate Checklist

| Gate | Status | Blocker? | Evidence |
|------|--------|:--------:|----------|
| Merge conflicts vs `main` | ✅ PASS | No | `git merge-tree` dry-run: 0 conflicting files |
| Ahead/behind vs `main` | ✅ PASS | No | 102 ahead, 0 behind |
| Release preservation (local) | ✅ PASS | No | `release/p16-demo-ready-v1` + tag @ `517f728` |
| Release preservation (remote) | ❌ FAIL | **Yes** | Branch + tag not on origin |
| Archive rollback branch | ✅ PASS | No | `archive/production-pre-p16-demo` on origin @ `85bacc6` |
| Dirty working tree | ❌ FAIL | **Yes** | 53 unstaged runtime paths |
| Sprint branch sync | ❌ FAIL | **Yes** | 8 commits local-only |
| AC03/AC05/AC07 untouched | ✅ PASS | No | No diffs in triage acceptance paths |
| Business logic in committed HEAD | ✅ PASS | No | Hygiene + audit docs in latest commits |

---

## Question 1: If founder merged today, what could go wrong?

| Risk | Severity | Detail |
|------|:--------:|--------|
| **Unreproducible promotion** | High | 53 unstaged runtime diffs not in any commit — merge would promote `d870ccc` but working tree diverges |
| **Lost demo pin on team machines** | High | `517f728` not on origin — teammates cannot checkout demo baseline |
| **Large blast radius** | High | 102 commits, 2,616 files, +676K lines vs `main` — one-shot promotion |
| **Marker/copy changes land unreviewed** | Medium | `markers.json` and `ui_copy.json` unstaged — if committed ad-hoc before merge, classification/copy changes enter main without guardrail run |
| **Product-only default unreviewed** | Medium | `run_demo_local.sh` + `App.tsx` unstaged changes alter default demo posture |
| **Case store field additions** | Medium | `office_case_title` / `office_broker_next_step` unstaged — persistence contract change |
| **No merge conflicts** | Low | Technical merge is clean |

---

## Question 2: What blockers remain?

| # | Blocker | Required action |
|---|---------|-----------------|
| 1 | 53 unstaged runtime paths | P16-RUNTIME-COMMIT-GATE: commit or revert bundles |
| 2 | Demo refs not on origin | Execute 3 preservation pushes |
| 3 | 8 commits not on origin | Push `sprint-a/broker-front-door` |
| 4 | Founder business sign-off | 102-commit promotion is a product decision |
| 5 | Post-promotion validation | Run `trial_launch_check.sh` on promoted state |

---

## Question 3: What is the safest sequence?

```
1. Push preservation refs (3 commands)           ← eliminate laptop-loss risk
2. P16-RUNTIME-COMMIT-GATE                     ← resolve 53 paths → ≤2 dirty
3. Run guardrail + trial checks on clean tree
4. Tag post-runtime-commit state (optional)
5. Founder reviews full diff: main..sprint-a
6. Merge sprint-a/broker-front-door → main     ← dedicated promotion session
7. Push main
8. Verify demo recovery: checkout release/p16-demo-ready-v1
```

**Do NOT merge before steps 1–3.**

---

## Merge Conflict Analysis

```
git merge-base main HEAD  → 31572ca
git log --oneline main..HEAD | wc -l  → 102
git log --oneline HEAD..main | wc -l  → 0
```

`git merge-tree` dry-run: **0 files changed in both** (no conflicts).

Fast-forward or merge to `main` will not produce conflicts from committed objects. Risk is from **uncommitted state** and **business scope**, not git mechanics.

---

## GO / CONDITIONAL GO / NO GO Matrix

| Scenario | Verdict | When |
|----------|---------|------|
| Merge today with dirty tree | **NO GO** | Unreproducible; 53 paths unresolved |
| Merge after push only | **NO GO** | Runtime diffs still unstaged |
| Merge after push + runtime commit gate | **CONDITIONAL GO** | Pending founder review of 102-commit diff |
| Merge after push + clean tree + trial checks pass | **GO** | Safe promotion window |

---

## Evidence Summary

- **Technical merge:** Clean (0 conflicts)
- **Scope:** 102 commits — largest promotion in project history
- **Demo pin:** Locally intact, remotely missing
- **Runtime work:** 53 paths classified, 17 UNSURE, 1 REVERT (`prototypes/`)
- **Rollback:** `archive/production-pre-p16-demo` @ `85bacc6` on origin

---

*Phase 5 complete. No branches modified.*
