# P16 Push Readiness

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 4  
**Status:** PLAN ONLY — **DO NOT PUSH YET**

---

## Current Git State

| Check | Value |
|-------|-------|
| **Branch** | `sprint-a/broker-front-door` |
| **HEAD** | `4d5bf46` |
| **Dirty paths** | 55 (53 NEEDS_FOUNDER_REVIEW + 2 DO_NOT_COMMIT) |
| **Remote** | `origin` → `git@github.com:waterwoods/searchforge.git` |
| **Tracking** | `[origin/sprint-a/broker-front-door: ahead 7]` |

---

## Preservation Ref Status

| Ref | Local SHA | On Origin? | Risk if laptop dies |
|-----|-----------|:----------:|---------------------|
| `sprint-a/broker-front-door` | `4d5bf46` | ⚠️ origin at `d05e94d` | **7 commits lost** |
| `release/p16-demo-ready-v1` | `517f728` | ❌ | **Demo pin lost** |
| `p16-demo-ready-v1` (tag) | `517f728` | ❌ | **Immutable label lost** |
| `archive/production-pre-p16-demo` | `85bacc6` | ✅ | Safe |

---

## Missing Preservation Refs (must push)

1. `release/p16-demo-ready-v1` — branch
2. `p16-demo-ready-v1` — annotated tag
3. `sprint-a/broker-front-door` — 7 commits ahead of origin

---

## Exact Push Commands

Run in order after founder approval:

```bash
# 1. Sprint branch — full P16 work + 4 hygiene commits
git push -u origin sprint-a/broker-front-door

# 2. Frozen demo branch (independent pin at 517f728)
git push -u origin release/p16-demo-ready-v1

# 3. Annotated release tag
git push origin p16-demo-ready-v1

# 4. Verify rollback (already on origin — no push needed)
git ls-remote origin refs/heads/archive/production-pre-p16-demo
# Expected: 85bacc639f174e0680d11d8486aa86b53ffa6986
```

### Optional — after this sprint's reports committed

```bash
# Commit Phase 1–6 deliverables (this sprint)
git add docs/product_constitution/P16_RUNTIME_REVIEW_REPORT.md \
        docs/product_constitution/P16_DIRTY_TREE_FINAL.md \
        docs/product_constitution/P16_RELEASE_INTEGRITY_CHECK.md \
        docs/product_constitution/P16_PUSH_READINESS.md \
        docs/product_constitution/P16_REMOTE_PRESERVATION_AUDIT.md \
        docs/product_constitution/P16_PUSH_OR_NOT_PUSH.md
git commit -m "docs(p16): runtime review and push readiness reports"
git push origin sprint-a/broker-front-door
```

---

## Pre-Push Checklist

| Item | Status |
|------|--------|
| Demo pin at `517f728` unchanged | ✅ |
| Hygiene commits A–D complete | ✅ |
| MISSED_ARCHIVE resolved | ✅ |
| No secrets in staged history | ✅ (manual spot-check `demo.env.example` unstaged) |
| No force-push required | ✅ |
| 53 runtime paths intentionally unstaged | ✅ |
| Founder reviewed 7 commits ahead of origin | ⬜ pending |

### Commits founder should review before push

```bash
git log --oneline origin/sprint-a/broker-front-door..HEAD
```

```
4d5bf46 chore(repo): commit safe hygiene paths and complete missed archive
932b7d1 chore(repo): archive historical sprint artifacts
50cce37 chore(repo): preserve release and deployment records
69bf9b0 chore(repo): preserve governance and release documentation
517f728 fix(p16): active case choice gate
29a00f8 fix(p16): add-car triage parity and Wu Miss demo package
b0d6073 fix(ui): restore missing getCompactQueuePreview import in broker workbench
```

---

## Do NOT

- Force-push any branch
- Push to `main`
- Delete branches
- Deploy Cloud Run or Vercel

---

## Verdict

### **CONDITIONAL_READY**

| Condition | Met? |
|-----------|:----:|
| Demo SHA locally pinned | ✅ |
| Hygiene committed | ✅ |
| Push commands verified | ✅ |
| Release refs exist locally | ✅ |
| Release refs on origin | ❌ |
| Working tree clean | ❌ (55 paths — acceptable if intentional) |
| Founder sign-off | ⬜ |

**Push is safe for preservation** (docs + demo pin + sprint history). The 55-path dirty tree does **not** block push — unstaged changes stay local until founder commits or reverts them.

**Upgrade to READY** after: founder reviews 7 commits + executes push commands.
