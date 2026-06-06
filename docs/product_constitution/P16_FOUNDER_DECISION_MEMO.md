# P16 Founder Decision Memo

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 7  
**Audience:** Andy (Founder)  
**Baseline:** `517f728` — P16 Demo Ready  
**Mode:** Read-only governance — no actions executed

---

## 1. Can P16 be promoted to main?

# **CONDITIONAL GO**

Promotion is **architecturally correct** and **technically a clean 98-commit fast-forward**, but **not safe today** without pre-promotion hygiene.

| Gate | Status |
|------|--------|
| Product demo-ready on Preview | ✅ |
| Frozen baseline locally | ✅ `517f728` |
| Frozen baseline on origin | ❌ |
| Working tree clean | ❌ 1,761 paths |
| Production aligned | ❌ |
| Rollback path documented | ✅ |

**Promote when:** dirty tree resolved, release branch + tag pushed, sprint branch synced to origin.

---

## 2. Top 5 risks

| # | Risk | Impact | Likelihood |
|---|------|--------|------------|
| **R1** | **1,761 uncommitted paths** — archival migration in progress | Merge from dirty checkout is unreproducible; could land or lose doc work | Certain if ignored |
| **R2** | **Release artifacts local-only** — branch + tag not on origin | Machine loss = loss of named P16 pin; no org-wide rollback | High until pushed |
| **R3** | **Production Vercel 45 days stale** — pre-Sprint A UX | Customer/broker hitting production sees wrong product | High if prod URL shared |
| **R4** | **`main` is 6 months stale** — 98-commit fast-forward | Large blast radius; hard to bisect if regression found | Medium |
| **R5** | **CORS on raw Vercel hash URLs** — new Preview deploys fail | Empty queue / broken demo if wrong URL shared | Medium |

---

## 3. Top 5 actions

| # | Action | Owner | Time | Blocks promotion? |
|---|--------|-------|------|:-----------------:|
| **A1** | **Finish + commit doc archival migration** — pair 1,228 deletes with archive additions; verify links | Agent / Andy | 2–4 h | **Yes** |
| **A2** | **Push preservation artifacts** — `release/p16-demo-ready-v1`, tag `p16-demo-ready-v1`, sprint branch (3 commits) | Andy | 15 min | **Yes** |
| **A3** | **Founder E2E on Preview alias** — `ui-waterwoods-andys-projects-1f411b73.vercel.app` + Wu Miss / add-car flows | Andy | 30 min | Yes (for prod) |
| **A4** | **Fast-forward `main` ← `sprint-a/broker-front-door`** — only from clean `517f728` checkout | Andy | 15 min | After A1+A2 |
| **A5** | **Optional Cloud Run redeploy** — SHA hygiene only (`29a00f8` → `517f728`); not required for API | Andy | 20 min | No |

---

## 4. What should Andy do next?

### Today (Day 0)

1. **Run broker demo on Preview alias** — confirm active case choice gate, add-car, workbench queue.
2. **Review dirty tree census** (`P16_DIRTY_TREE_CENSUS.md`) — approve archival batch or stash unrelated changes.
3. **Commit hygiene batch** — single commit: `docs: P16 simplification archival + operator surface`.
4. **Push preservation checklist** (from `P16_RELEASE_PRESERVATION_CHECK.md`):
   ```bash
   git push -u origin release/p16-demo-ready-v1
   git push origin p16-demo-ready-v1
   git push origin sprint-a/broker-front-door
   ```

### Day 1 (promotion)

5. Verify `git status` is clean.
6. Fast-forward merge sprint → main (PR or direct).
7. Rerun `bash scripts/post_sprint_check.sh --sprint P16-FREEZE` — target 10/10.

### Day 2+ (production alignment — separate decision)

8. Deploy Production Vercel only after E2E sign-off.
9. Schedule branch archaeology cleanup (59 local branches; 45+ safe deletion candidates).

---

## 5. What should wait?

| Item | Wait until | Reason |
|------|------------|--------|
| Production Vercel deploy | After Preview E2E + main promotion | Production is currently pre-P16; no urgency if demo uses Preview |
| Branch deletion (`auto-evolution/*`) | After promotion + 30 days | 58/59 merged; archaeology doc preserves context |
| `reduction/p1-simplification-loops` cleanup | After reviewing 1 unique commit | May need cherry-pick |
| `__BUILD_ID__` bundle fix | Post-promotion sprint | Cosmetic; deploy timestamp sufficient for now |
| Backend redeploy for SHA parity | Optional; anytime | Gap commit is frontend-only; API already correct |
| Feature work (AC03/AC05/AC07 changes) | Next product sprint | This sprint is governance only |
| JobHunter removal | Future reduction sprint | Not on demo path; low urgency |

---

## Decision summary

| Question | Answer |
|----------|--------|
| Is P16 demo-ready? | **Yes** — Preview alias @ `517f728` |
| Is P16 promotion-ready? | **Not yet** — hygiene + push required |
| Is backend broken? | **No** — healthy; 1 SHA label behind |
| Is production current? | **No** — intentionally deferred |
| Can we demo to a broker today? | **Yes** — use `ui-waterwoods` alias |

---

## Supporting documents

| Phase | Document |
|-------|----------|
| 1 | `P16_RELEASE_PRESERVATION_CHECK.md` |
| 2 | `P16_DIRTY_TREE_CENSUS.md` |
| 3 | `P16_MAINLINE_DIFF_REPORT.md` |
| 4 | `P16_DEPLOY_ALIGNMENT_AUDIT.md` |
| 5 | `P16_BRANCH_ARCHAEOLOGY_PREP.md` |
| 6 | `P16_RELEASE_FREEZE_VALIDATION.md` |
| Prior | `P16_RELEASE_BASELINE_REPORT.md`, `P16_DEPLOYMENT_PARITY_REPORT.md` |

---

*End of P16 Founder Decision Memo — Phase 7*
