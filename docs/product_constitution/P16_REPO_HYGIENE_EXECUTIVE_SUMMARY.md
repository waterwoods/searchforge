# P16 Repo Hygiene Executive Summary

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 7  
**Branch:** `sprint-a/broker-front-door` @ `517f728`  
**Audience:** Founder — 5-minute read

---

## 1. What exactly are the 1,769 files?

An **intentional documentation archival migration** in progress. The committed HEAD is clean; the working tree is not.

| What | Count | % |
|------|------:|--:|
| Documentation (docs, reports, sprint artifacts, archives) | 1,672 | 94.5% |
| Scripts | 40 | 2.3% |
| Source code | 24 | 1.4% |
| Configs / infrastructure | 23 | 1.3% |
| Generated / local artifacts | 3 | 0.2% |
| Tests | 3 | 0.2% |
| Unknown | 4 | 0.2% |

**Status:** 1,228 deletions (legacy `docs/*.md` sprint reports), 471 untracked (new `docs/sprints/archive/` + `docs/product_constitution/`), 70 modifications.

**Not random drift.** This is simplification housekeeping started during P16, not accidental corruption.

---

## 2. What should be committed?

**1,672 paths** classified SAFE_TO_COMMIT — primarily:

- Sprint reports moving to `docs/sprints/archive/`
- 384+ `docs/product_constitution/P16_*.md` governance artifacts
- Operator runbooks and onboarding docs
- Trial and deployment documentation

**94 paths** need founder review first (scripts, configs, UI source).

**Commit in 3 batches** (see `P16_COMMIT_PLAN.md`):

1. **A** — governance and operator docs
2. **B** — release manifests and deployment records
3. **C** — bulk archival + reviewed code/scripts

---

## 3. What should NOT be committed?

| Path | Reason |
|------|--------|
| `demo_brain_report.html` | Generated local HTML report |
| `docs/archive/root_archaeology/demo_brain_report.html` | Duplicate generated artifact |
| `configs/demo.env.example` | REVIEW_REQUIRED — verify no secrets first |

No `.env`, credentials, `node_modules`, or IDE caches are currently dirty.

---

## 4. What should be pushed?

After local commits are clean:

```bash
git push origin sprint-a/broker-front-door          # 3 unpushed commits
git push -u origin release/p16-demo-ready-v1          # frozen release branch
git push origin p16-demo-ready-v1                     # annotated tag
```

**Do not push** until hygiene commits land and validation passes.

---

## 5. What should remain local?

- `demo_brain_report.html` and generated HTML reports
- Any deferred REVIEW_REQUIRED items founder chooses not to include
- IDE/local config (none currently dirty)

---

## 6. Is repo promotion-ready?

**CONDITIONAL GO** — not today.

| Blocker | Status |
|---------|--------|
| Dirty tree (1,769 paths) | ❌ Must commit first |
| Release branch on origin | ❌ Local only |
| Tag on origin | ❌ Local only |
| Merge conflicts vs main | ✅ Zero |
| Rollback branch on origin | ✅ `archive/production-pre-p16-demo` |

Promotion is feasible after hygiene commits + push sequence. Do **not** merge to main in this sprint.

---

## 7. Is demo state safely preserved?

**Yes, locally.**

| Artifact | SHA | Status |
|----------|-----|--------|
| `sprint-a/broker-front-door` | `517f728` | ✅ Demo-ready HEAD |
| `release/p16-demo-ready-v1` | `517f728` | ✅ Frozen branch |
| `p16-demo-ready-v1` (tag) | `517f728` | ✅ Annotated tag |
| `archive/production-pre-p16-demo` | `85bacc6` | ✅ On origin |

**Gap:** Release branch and tag are **not on origin**. Push required for team-wide preservation.

---

## 8. Top 5 Risks

1. **Promoting with dirty tree** — would make the merge unreproducible and may drop archival work
2. **Release artifacts local-only** — machine loss or clone from origin loses demo-ready pin
3. **Bulk doc commit breaks links** — 1,228 deletions need path verification before Commit C
4. **Script changes in dirty tree** — 40 modified scripts could affect demo if committed without review
5. **50 auto-evolution branches** — cognitive load; no deletion yet, but clutter increases confusion

---

## 9. Next 5 Actions

1. **Founder review** of 94 REVIEW_REQUIRED paths (especially `scripts/` and `configs/`)
2. **Execute Commits A → B → C** per `P16_COMMIT_PLAN.md`
3. **Run validation** — `demo_pre_checklist.sh` + `guardrail_inbox_triage.sh`
4. **Push preservation refs** — sprint-a, release branch, tag (founder approval)
5. **Schedule branch archaeology sprint** — archive 44 auto-evolution/reduction branches (no deletion yet)

---

## Repository Health Score

| State | Score | Rationale |
|-------|------:|-----------|
| **Current** | **52 / 100** | Demo-ready HEAD but dirty tree, unpushed release refs, 87 branches |
| **After proposed cleanup** | **88 / 100** | Clean tree, preserved releases on origin, promotion-ready pending main merge decision |

Deductions from 100: unpushed refs (−15), branch clutter (−10), 94 unreviewed paths (−5 post-cleanup residual).

---

## Founder Verdict

The repository is **demo-ready at HEAD** (`517f728`) but **not promotion-ready** due to 1,769 uncommitted documentation paths and release artifacts that exist only locally. The dirt is 94.5% documentation from an intentional archival migration — not code corruption. Execute the 3-commit hygiene plan, push release preservation refs, then promotion to `main` becomes a low-risk fast-forward with zero merge conflicts. No features, no triage changes, no UI work required.

---

## Recommended Next Sprint

**P16-REPO-COMMIT-AND-PRESERVE** — Single-purpose sprint:

1. Founder review of 94 REVIEW_REQUIRED paths
2. Execute Commits A, B, C
3. Validate demo + guardrails
4. Push sprint-a, release branch, and tag to origin
5. Produce clean-tree confirmation report

No new features. No main merge. No branch deletion.
