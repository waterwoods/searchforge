# P16 Release Preservation Verification

**Date:** 2026-06-06  
**Mission:** P16-GOVERNANCE-FINALIZATION-SPRINT — Phase 2  
**Verifier:** Local + `git ls-remote` inspection  
**HEAD at verification:** `d870ccc` (`sprint-a/broker-front-door`)

---

## Ref Verification Table

| Ref | SHA | Exists (local)? | On `origin`? | Commit date |
|-----|-----|:---------------:|:------------:|-------------|
| `release/p16-demo-ready-v1` | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` | ✅ | ❌ | 2026-06-04 |
| `p16-demo-ready-v1` (annotated tag) | `517f728` | ✅ | ❌ | Tagged 2026-06-05 |
| `archive/production-pre-p16-demo` | `85bacc639f174e0680d11d8486aa86b53ffa6986` | ✅ | ✅ | 2026-04-21 |
| `sprint-a/broker-front-door` | `d870ccc` | ✅ | ⚠️ `d05e94d` | 2026-06-06 |

---

## Integrity Checks

### Demo pin consistency

```bash
git rev-parse release/p16-demo-ready-v1     # → 517f728
git rev-parse p16-demo-ready-v1^{commit}    # → 517f728
```

✅ **PASS** — Branch and tag agree.

### Hygiene commits do not move demo pin

`release/p16-demo-ready-v1` remains at `517f728`. Commits `69bf9b0` → `d870ccc` sit on `sprint-a/broker-front-door` only.

✅ **PASS** — Demo freeze independent of governance work.

### Rollback branch

```bash
git rev-parse archive/production-pre-p16-demo                          # → 85bacc6
git ls-remote origin refs/heads/archive/production-pre-p16-demo        # → 85bacc6
```

✅ **PASS** — Rollback branch matches origin exactly.

### Sprint branch ancestry

8 commits on `sprint-a/broker-front-door` not on origin:

| SHA | Message |
|-----|---------|
| `d870ccc` | chore(repo): preserve governance audit reports |
| `4d5bf46` | chore(repo): commit safe hygiene paths and complete missed archive |
| `932b7d1` | chore(repo): archive historical sprint artifacts |
| `50cce37` | chore(repo): preserve release and deployment records |
| `69bf9b0` | chore(repo): preserve governance and release documentation |
| `517f728` | fix(p16): active case choice gate |
| `29a00f8` | fix(p16): add-car triage parity and Wu Miss demo package |
| `b0d6073` | fix(ui): restore missing getCompactQueuePreview import |

✅ **PASS** — Linear ancestry; no force-push detected.

---

## Risk If Laptop Dies Today

| Asset | Risk level | Consequence |
|-------|:------------:|-------------|
| Demo pin (`517f728`) | 🔴 Critical | Cannot recover from GitHub; must rebuild from memory |
| 8 sprint commits | 🔴 Critical | Hygiene + product fixes + audit reports lost |
| 53 unstaged runtime diffs | 🟡 Medium | Product-only surface work lost |
| Rollback branch | 🟢 Low | Fully on origin |
| `main` | 🟢 Low | Fully on origin |
| Stale origin sprint-a (`d05e94d`) | 🟡 Medium | Partial recovery only — missing demo pin + hygiene |

---

## What IS Recoverable (from origin today)

| Asset | How to recover |
|-------|----------------|
| Pre-P16 production state | `git fetch origin archive/production-pre-p16-demo && git checkout archive/production-pre-p16-demo` |
| Stale P16 sprint line | `git fetch origin sprint-a/broker-front-door` → stops at `d05e94d` |
| Main branch | `git fetch origin main` |
| All tags except 3 local-only | `git fetch --tags origin` |

---

## What is NOT Recoverable (from origin today)

| Asset | Gap |
|-------|-----|
| `release/p16-demo-ready-v1` @ `517f728` | Branch not pushed |
| `p16-demo-ready-v1` tag | Tag not pushed |
| Commits `b0d6073` → `d870ccc` | 8 commits ahead of origin |
| 53 unstaged runtime file diffs | Never committed |
| 2 DO_NOT_COMMIT paths | Local only (acceptable) |
| 60+ `auto-evolution/*` local branches | Optional archaeology; not pilot-critical |

---

## Verdict

| Check | Result |
|-------|--------|
| Local demo integrity | ✅ PASS |
| Tag/branch alignment | ✅ PASS |
| Rollback on origin | ✅ PASS |
| Remote demo preservation | ❌ FAIL |
| Remote sprint sync | ❌ FAIL (8 commits local-only) |

**Overall:** Demo state is **locally intact** but **not remotely preserved**. Three push commands required to eliminate critical risk.

---

*Phase 2 complete. Verification only — no push executed.*
