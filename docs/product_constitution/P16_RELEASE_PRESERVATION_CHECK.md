# P16 Release Preservation Check

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 1  
**Mode:** Read-only (no push, no tag creation)  
**Remote:** `origin` → `git@github.com:waterwoods/searchforge.git`

---

## Executive answer

| Question | Answer |
|----------|--------|
| **Safe?** | **Partially safe locally; not safe on origin** |
| **Missing?** | `release/p16-demo-ready-v1` on origin; annotated tag `p16-demo-ready-v1` on origin; 3 sprint commits on origin |
| **What must be pushed?** | See [Push checklist](#push-checklist-do-not-run-automatically) below |

---

## Branch verification

### 1. `sprint-a/broker-front-door` (active product line)

| Field | Value |
|-------|-------|
| **Local SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Origin SHA** | `d05e94da0855942c6143405720d65be35b3c5829` |
| **Commit** | `fix(p16): active case choice gate` |
| **Date** | 2026-06-04 21:14:35 -0700 |
| **Ahead of origin** | **3** |
| **Behind origin** | **0** |
| **Current HEAD** | Yes (checked out) |

**Local commits not on origin:**

| SHA | Subject |
|-----|---------|
| `517f728` | fix(p16): active case choice gate |
| `29a00f8` | fix(p16): add-car triage parity and Wu Miss demo package |
| `b0d6073` | fix(ui): restore missing getCompactQueuePreview import in broker workbench |

---

### 2. `release/p16-demo-ready-v1` (frozen baseline)

| Field | Value |
|-------|-------|
| **Local SHA** | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` |
| **Origin** | **Does not exist** |
| **Matches sprint local HEAD** | ✅ Yes (identical commit) |
| **Purpose** | Immutable P16 demo-ready release pointer |

---

### 3. `archive/production-pre-p16-demo` (pre-P16 rollback)

| Field | Value |
|-------|-------|
| **Local SHA** | `85bacc639f174e0680d11d8486aa86b53ffa6986` |
| **Origin SHA** | `85bacc639f174e0680d11d8486aa86b53ffa6986` |
| **Commit** | `feat(simulation): add one-click auto replay with image-step support` |
| **Date** | 2026-04-21 06:50:43 -0700 |
| **Ahead of origin** | **0** |
| **Behind origin** | **0** |
| **Purpose** | Pre-Sprint A production snapshot for rollback |

---

## Tag verification

| Tag | Points to | On origin? |
|-----|-----------|:----------:|
| `p16-demo-ready-v1` | `517f7281…` | **No** (local only) |

---

## Preservation matrix

| Artifact | Local | Origin | In sync? | Risk if lost |
|----------|:-----:|:------:|:--------:|--------------|
| `sprint-a/broker-front-door` | ✅ `517f728` | ⚠️ `d05e94d` | ❌ 3 commits local-only | **High** — active line not fully remote |
| `release/p16-demo-ready-v1` | ✅ `517f728` | ❌ | ❌ | **High** — no remote release pointer |
| `p16-demo-ready-v1` (tag) | ✅ `517f728` | ❌ | ❌ | **High** — no remote pin for rollback |
| `archive/production-pre-p16-demo` | ✅ `85bacc6` | ✅ `85bacc6` | ✅ | Low — preserved |

---

## Canonical P16 demo-ready SHA

```
517f7281ebdf136fda8e2d6ab884b26ce0e5cf37
```

**Subject:** `fix(p16): active case choice gate`  
**Branches at this SHA:** `sprint-a/broker-front-door` (local), `release/p16-demo-ready-v1` (local)

---

## Push checklist (DO NOT run automatically)

These commands preserve the release baseline on origin. **Not executed in this sprint.**

```bash
# 1. Push frozen release branch
git push -u origin release/p16-demo-ready-v1

# 2. Push annotated tag
git push origin p16-demo-ready-v1

# 3. Sync active sprint line (3 commits)
git push origin sprint-a/broker-front-door
```

**Order matters:** Push release branch and tag before or with sprint branch so remote always has a named rollback point at `517f728`.

---

## Verdict

| Level | Assessment |
|-------|------------|
| **Local preservation** | ✅ **SAFE** — all three branches and tag exist locally at expected SHAs |
| **Remote preservation** | ❌ **NOT SAFE** — release branch, tag, and 3 sprint commits are local-only |
| **Rollback readiness** | ⚠️ **PARTIAL** — `archive/production-pre-p16-demo` is on origin; P16 pin is not |

**Bottom line:** The demo-ready state is frozen and reproducible **on this machine**. It is **not yet trustworthy as an organization-wide release baseline** until the push checklist is executed.

---

*End of P16 Release Preservation Check — Phase 1*
