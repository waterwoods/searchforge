# P16 Release Verification

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 4  
**Mode:** Read-only verification

---

## Summary

| Artifact | Exists | SHA | Date | Purpose | Origin |
|----------|:------:|-----|------|---------|:------:|
| `release/p16-demo-ready-v1` (branch) | ✅ | `517f728` | 2026-06-04 21:14:35 -0700 | Frozen demo-ready release line | ❌ Local only |
| `p16-demo-ready-v1` (annotated tag) | ✅ | `517f728` (peeled) | 2026-06-04 21:14:35 -0700 | Immutable release snapshot | ❌ Local only |
| `archive/production-pre-p16-demo` (branch) | ✅ | `85bacc6` | 2026-04-21 06:50:43 -0700 | Pre-P16 production rollback point | ✅ On origin |
| `sprint-a/broker-front-door` (branch) | ✅ | `517f728` | 2026-06-04 21:14:35 -0700 | Active sprint / promotion candidate | ⚠️ Local ahead by 3 |

**Integrity verdict:** Local release preservation is **complete and consistent**. Remote preservation is **incomplete** — release branch and tag exist only locally.

---

## Artifact Detail

### 1. `release/p16-demo-ready-v1`

| Field | Value |
|-------|-------|
| **SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Date** | 2026-06-04 21:14:35 -0700 |
| **Message** | `fix(p16): active case choice gate` |
| **Purpose** | Named release branch pointing at demo-ready HEAD |
| **Unique commits vs main** | 98 ahead, 0 behind |
| **Remote** | Not on `origin` |

### 2. `p16-demo-ready-v1` (tag)

| Field | Value |
|-------|-------|
| **Tag object** | `5a2ab39df4d0d01256e4a1f8070be4b47f8c0501` |
| **Peels to commit** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Type** | Annotated tag |
| **Message** | `P16 demo-ready release snapshot v1 (sprint-a/broker-front-door)` |
| **Date** | 2026-06-04 21:14:35 -0700 |
| **Purpose** | Immutable pointer for rollback and audit |
| **Remote** | Not on `origin` |

**Cross-check:** Tag peels to same commit as `release/p16-demo-ready-v1` and local `sprint-a/broker-front-door`. ✅ Consistent.

### 3. `archive/production-pre-p16-demo`

| Field | Value |
|-------|-------|
| **SHA** | `85bacc639f174e0680d11d8486aa86b53ffa6986` |
| **Date** | 2026-04-21 06:50:43 -0700 |
| **Message** | `feat(simulation): add one-click auto replay with image-step support` |
| **Purpose** | Pre-P16 demo production state for rollback |
| **Unique commits vs main** | 25 ahead, 0 behind |
| **Remote** | ✅ `origin/archive/production-pre-p16-demo` @ same SHA |

### 4. `sprint-a/broker-front-door`

| Field | Value |
|-------|-------|
| **Local SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Remote SHA** | `d05e94da0855942c6143405720d65be35b3c5829` |
| **Local date** | 2026-06-04 21:14:35 -0700 |
| **Remote date** | 2026-06-01 00:03:44 -0700 |
| **Purpose** | Active development and promotion candidate |
| **Drift** | Local is **3 commits ahead** of origin; 0 behind |

**Remote lag commits (local-only, not yet pushed):**

```
517f728 fix(p16): active case choice gate
(+ 2 additional commits between d05e94d and 517f728)
```

---

## Integrity Checks

| Check | Result |
|-------|--------|
| Tag peels to release branch HEAD | ✅ Pass |
| Release branch = local sprint-a HEAD | ✅ Pass |
| Archive branch matches origin | ✅ Pass |
| Demo HEAD is reachable from sprint-a | ✅ Pass |
| All release refs on origin | ❌ Fail — branch + tag local only |
| sprint-a local = origin | ❌ Fail — 3 commits unpushed |

---

## Recommended Push Sequence (DO NOT RUN — founder approval required)

```bash
# 1. Push sprint branch first (brings origin current)
git push origin sprint-a/broker-front-door

# 2. Push frozen release branch
git push -u origin release/p16-demo-ready-v1

# 3. Push annotated tag
git push origin p16-demo-ready-v1
```

**Order matters:** Push sprint branch before tagging origin to avoid remote lag confusion.
