# P16 Repo Preservation — Final Summary

**Date:** 2026-06-06  
**Mission:** P16-REPO-COMMIT-AND-PRESERVE-SPRINT  
**Audience:** Founder — maximum 2 pages

---

## Mission Result: **SUCCESS** (preservation objective)

Three hygiene commits landed. Demo-ready state pinned. Rollback preserved. Push plan ready. No features built, no triage touched, no infrastructure deployed.

---

## 1. How many dirty files existed originally?

**1,775 paths** on `sprint-a/broker-front-door` @ `517f728`.

---

## 2. How many remain?

**100 paths** — all explicitly classified:

| Category | Count |
|----------|------:|
| REVIEW_REQUIRED (scripts, source, configs) | 93 |
| DO_NOT_COMMIT (generated/env) | 2 |
| MISSED_ARCHIVE (vitals docs, encoding-blocked) | 5 |

Plus 4 uncommitted P16 sprint report files from this mission.

---

## 3. What was preserved? (Commits A → B → C)

| Commit | SHA | Purpose |
|--------|-----|---------|
| **A** | `69bf9b0` | Governance, constitution, founder memos, repo census, audit reports (405 files) |
| **B** | `50cce37` | Release verification, deployment records, trial docs, runbooks (46 files) |
| **C** | `932b7d1` | Archive migration — 1,200+ sprint reports → `docs/sprints/archive/`, `docs/archive/` |

**Total committed:** ~1,679 documentation paths.

---

## 4. What was archived?

- 1,228 legacy sprint reports removed from `docs/` root index
- Content relocated to `docs/sprints/archive/`, `docs/archive/broker_demo/`, `docs/archive/platform/`, etc.
- Historical P7/P9/P11 audit material preserved under archive trees
- **No git history deleted**

---

## 5. What was intentionally excluded?

| Exclusion | Count | Why |
|-----------|------:|-----|
| Scripts (`run_demo_local.sh`, etc.) | 40 | Affects demo runtime |
| UI + API source | 24 | Product behavior |
| Configs / Docker / Makefile | 23 | Infrastructure |
| Tests | 3 | Product validation |
| `demo.env.example`, `demo_brain_report.html` | 2 | Local/generated |
| `triage.py`, AC03/05/07, Cloud Run, Vercel | — | Out of scope per mission |

---

## 6. What SHA is the frozen demo state?

**`517f728`** — `fix(p16): active case choice gate`

Pinned by:
- Branch: `release/p16-demo-ready-v1`
- Tag: `p16-demo-ready-v1`

Hygiene commits (`69bf9b0` → `932b7d1`) are **documentation only** and sit on top of this pin on `sprint-a/broker-front-door`.

---

## 7. What branch is the rollback state?

**`archive/production-pre-p16-demo`** @ **`85bacc6`** — already on origin.

---

## 8. What push commands should founder run?

```bash
git push -u origin sprint-a/broker-front-door
git push -u origin release/p16-demo-ready-v1
git push origin p16-demo-ready-v1
```

See `P16_PUSH_PLAN.md` for checklist. **Do not push until founder reviews.**

---

## 9. Is repo now promotion-ready?

**CONDITIONAL_GO** — merge to `main` has zero conflicts, but:

- 93 REVIEW_REQUIRED paths remain dirty
- Release refs not yet on origin
- Main merge not authorized this sprint

---

## Repository Health Score

| State | Score | Rationale |
|-------|------:|-----------|
| **Before** | **52 / 100** | Demo-ready HEAD, 1,775 dirty paths, unpushed release refs |
| **After** | **85 / 100** | 94% doc preservation committed, explicit 100-path blocker list, push plan ready |

Deductions: 93 unreviewed runtime paths (−10), unpushed refs (−5).

---

## Founder Verdict

The repository transitioned from **Demo Ready + Dirty Tree** to **Demo Ready + Mostly Clean Tree + Local Preservation**. P16 can be recovered from `release/p16-demo-ready-v1` @ `517f728`. Documentation archival is committed. Product code changes remain intentionally unstaged for founder review. Execute push plan when ready; defer main merge to a separate decision.

---

## Recommended Next Sprint

**P16-RUNTIME-REVIEW-AND-PUSH** — Single purpose:

1. Founder line-by-line review of 93 REVIEW_REQUIRED paths
2. Commit or revert runtime changes (separate from doc hygiene)
3. Execute push plan (sprint-a + release branch + tag)
4. Archive 4 remaining `vitals_*.md` files
5. Decision gate: merge to `main` yes/no

No new features. No triage changes. No deploy.
