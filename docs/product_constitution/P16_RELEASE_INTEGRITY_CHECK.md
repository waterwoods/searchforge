# P16 Release Integrity Check

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 3  
**Verifier:** Local git inspection

---

## Ref Verification Table

| Ref | SHA | Commit Date | Purpose | On Origin? |
|-----|-----|-------------|---------|:----------:|
| `517f728` | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` | 2026-06-04 21:14:35 -0700 | **Frozen demo-ready code** — active case choice gate | via branch/tag below |
| `release/p16-demo-ready-v1` | `517f728` | 2026-06-04 21:14:35 -0700 | Movable branch pin for demo recovery | ❌ |
| `p16-demo-ready-v1` (annotated tag) | `517f728` | Tagged 2026-06-05 03:03:21 -0700 | Immutable demo snapshot label | ❌ |
| `archive/production-pre-p16-demo` | `85bacc639f174e0680d11d8486aa86b53ffa6986` | 2026-04-21 06:50:43 -0700 | Pre-P16 production rollback | ✅ |
| `sprint-a/broker-front-door` (HEAD) | `4d5bf46a…` | 2026-06-06 02:01:22 -0700 | Active dev line + hygiene commits | ⚠️ origin at `d05e94d` |

---

## Integrity Checks

### 1. Demo pin consistency

```bash
git rev-parse release/p16-demo-ready-v1    # → 517f728
git rev-parse p16-demo-ready-v1^{commit}   # → 517f728
```

✅ **PASS** — Branch and tag agree on demo SHA.

### 2. Hygiene commits do not move demo pin

`release/p16-demo-ready-v1` remains at `517f728`. Hygiene commits (`69bf9b0` → `4d5bf46`) sit on `sprint-a/broker-front-door` only.

✅ **PASS** — Demo freeze independent of doc hygiene.

### 3. Rollback branch

```bash
git rev-parse archive/production-pre-p16-demo           # → 85bacc6
git ls-remote origin refs/heads/archive/production-pre-p16-demo  # → 85bacc6
```

✅ **PASS** — Rollback branch matches origin.

### 4. Sprint branch ancestry

Commits on `sprint-a/broker-front-door` not on origin (7 total):

| SHA | Date | Message |
|-----|------|---------|
| `4d5bf46` | 2026-06-06 | chore(repo): commit safe hygiene paths and complete missed archive |
| `932b7d1` | 2026-06-06 | chore(repo): archive historical sprint artifacts |
| `50cce37` | 2026-06-06 | chore(repo): preserve release and deployment records |
| `69bf9b0` | 2026-06-06 | chore(repo): preserve governance and release documentation |
| `517f728` | 2026-06-04 | fix(p16): active case choice gate |
| `29a00f8` | 2026-06-04 | fix(p16): add-car triage parity and Wu Miss demo package |
| `b0d6073` | 2026-06-03 | fix(ui): restore missing getCompactQueuePreview import |

Origin `sprint-a/broker-front-door` stops at `d05e94d` (P16-O message-first customer entry).

✅ **PASS** — Ancestry is linear; no force-push detected.

### 5. Mainline relationship

```bash
git log --oneline release/p16-demo-ready-v1..main | wc -l   # → 0
git log --oneline main..release/p16-demo-ready-v1 | wc -l   # → 98
```

`main` has not advanced past the demo pin. P16 sprint line is 98 commits ahead of `main`.

✅ **PASS** — No mainline drift into demo pin.

---

## Annotated Tag Detail

```
tag p16-demo-ready-v1
Tagger: Andy <linanxin@me.com>
Date:   Fri Jun 5 03:03:21 2026 -0700

P16 demo-ready release snapshot v1 (sprint-a/broker-front-door)

commit 517f728 — fix(p16): active case choice gate
```

---

## Verdict

| Check | Result |
|-------|--------|
| Demo SHA integrity | ✅ PASS |
| Tag/branch alignment | ✅ PASS |
| Rollback preservation | ✅ PASS |
| Remote demo refs | ❌ FAIL — `release/p16-demo-ready-v1` and `p16-demo-ready-v1` not on origin |
| Sprint branch sync | ⚠️ 7 commits local-only |

**Overall:** Demo state is **locally intact** but **not remotely preserved** until push executes.

---

## Recovery Commands (post-push)

```bash
# Demo-ready code
git checkout release/p16-demo-ready-v1
# or
git checkout p16-demo-ready-v1

# Pre-P16 rollback
git checkout archive/production-pre-p16-demo
```
