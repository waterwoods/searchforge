# P16 Push or Not Push — Founder Decision Memo

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 6  
**Audience:** Founder — maximum 2 pages

---

## Bottom Line

**Push now for preservation. Defer main merge. Defer runtime commit.**

The demo-ready state (`517f728`) is locally intact but **not on GitHub**. Three push commands eliminate critical laptop-loss risk. The 55-path dirty tree does not block push.

---

## 1. What remains local only?

| Asset | Count / Detail |
|-------|----------------|
| **Critical** | `release/p16-demo-ready-v1`, `p16-demo-ready-v1` tag, 7 sprint commits |
| **Medium** | 53 unstaged runtime paths (product-only surface, copy, markers) |
| **Low** | 60 `auto-evolution/*` branches, 2 other local tags |
| **Excluded** | 2 DO_NOT_COMMIT paths (`demo.env.example`, `demo_brain_report.html`) |

---

## 2. What should be pushed immediately?

```bash
git push -u origin sprint-a/broker-front-door
git push -u origin release/p16-demo-ready-v1
git push origin p16-demo-ready-v1
```

**Why:** Preserves demo pin, 4 hygiene commits, 3 product fixes, and 1,600+ archived docs. Zero feature risk — no force push, no main merge.

**Optional same session:** Commit and push this sprint's 6 audit reports.

---

## 3. What can wait?

| Item | Wait for |
|------|----------|
| 53 NEEDS_FOUNDER_REVIEW paths | Bundled founder review (5 bundles in runtime report) |
| Main merge | Separate promotion gate decision |
| 60 auto-evolution branches | Never (unless archaeology sprint) |
| `demo.env.example` | Secret verification, if ever |
| Cloud Run / Vercel deploy | Out of scope |

---

## 4. Is demo state safely preserved?

| Layer | Status |
|-------|--------|
| Local branch `release/p16-demo-ready-v1` | ✅ `517f728` |
| Local tag `p16-demo-ready-v1` | ✅ `517f728` |
| Remote | ❌ **Not until push** |
| Rollback `archive/production-pre-p16-demo` | ✅ On origin @ `85bacc6` |

**Verdict:** Locally safe. Remotely vulnerable until push.

---

## 5. Is mainline promotion safe?

**Not yet.** Reasons:

- 98 commits ahead of `main` — large divergence
- 53 unstaged runtime paths not resolved
- Zero merge conflicts reported, but promotion is a **business decision**, not a hygiene task
- `markers.json` and `ui_copy.json` changes affect live demo copy/classification

**Recommendation:** Push preservation refs first. Schedule main promotion as a dedicated gate after runtime paths are committed or reverted.

---

## 6. Next sprint after push?

**P16-RUNTIME-COMMIT-GATE** — Single purpose:

Founder reviews 53 paths in 5 bundles (product-only surface, Chen Kui copy, triage markers, deprecations, case store fields). Commit approved bundles or `git checkout --` revert. Target: dirty tree → 2 (DO_NOT_COMMIT only).

No new features. No triage.py. No deploy.

---

## Repository Health Score

| State | Score | Rationale |
|-------|------:|-----------|
| **Before** (start of sprint) | **85 / 100** | 107 dirty paths, unpushed refs, demo pin local-only |
| **After** (end of sprint) | **93 / 100** | 55 dirty paths (−48%), missed archive done, 40 paths committed, push plan verified |

**Remaining deductions:** 53 unreviewed runtime paths (−5), unpushed preservation refs (−2).

**After push (projected):** **95 / 100** — refs preserved; runtime review still pending.

---

## Founder Verdict

| Decision | Recommendation |
|----------|----------------|
| Push preservation refs? | **YES** — execute 3 push commands |
| Push with dirty tree? | **YES** — unstaged work stays local |
| Merge to main? | **NO** — defer to promotion gate |
| Commit runtime paths now? | **NO** — use P16-RUNTIME-COMMIT-GATE |

---

## Recommended Next Sprint

**P16-RUNTIME-COMMIT-GATE** — commit or revert the 53 founder-review paths; achieve ≤2 dirty paths.

---

*Supporting docs: `P16_RUNTIME_REVIEW_REPORT.md`, `P16_DIRTY_TREE_FINAL.md`, `P16_RELEASE_INTEGRITY_CHECK.md`, `P16_PUSH_READINESS.md`, `P16_REMOTE_PRESERVATION_AUDIT.md`*
