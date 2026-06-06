# P16 Push Plan

**Date:** 2026-06-06  
**Mission:** P16-REPO-COMMIT-AND-PRESERVE-SPRINT — Phase 6  
**Status:** PLAN ONLY — **do not push yet**

---

## Ref Verification (Local)

| Ref | SHA | Points To | On Origin? |
|-----|-----|-----------|:----------:|
| `sprint-a/broker-front-door` (HEAD) | `932b7d1` | Latest + 3 hygiene commits | ❌ (origin at `d05e94d`) |
| `release/p16-demo-ready-v1` | `517f728` | Frozen demo-ready snapshot | ❌ |
| `p16-demo-ready-v1` (tag) | `517f728` | Annotated release tag | ❌ |
| `archive/production-pre-p16-demo` | `85bacc6` | Rollback branch | ✅ |

---

## Exact Push Commands (Founder Approval Required)

Run in order after reviewing hygiene commits:

```bash
# 1. Push sprint branch (6 commits ahead of origin: 3 prior + 3 hygiene)
git push -u origin sprint-a/broker-front-door

# 2. Push frozen release branch (demo-ready pin at 517f728)
git push -u origin release/p16-demo-ready-v1

# 3. Push annotated release tag
git push origin p16-demo-ready-v1

# 4. Rollback branch already on origin — verify only
git ls-remote origin refs/heads/archive/production-pre-p16-demo
```

---

## What Each Push Preserves

| Push | Preserves |
|------|-----------|
| `sprint-a/broker-front-door` | Full P16 work + hygiene commits; current development line |
| `release/p16-demo-ready-v1` | Frozen demo-ready code at `517f728` (independent of hygiene docs) |
| `p16-demo-ready-v1` | Immutable tag for recovery: "what was demo-ready on 2026-06-06" |
| `archive/production-pre-p16-demo` | Already preserved; pre-P16 production rollback |

---

## Pre-Push Checklist

- [x] Commits A, B, C complete
- [x] Frozen demo state unchanged at `517f728` (release branch/tag)
- [x] Rollback branch on origin
- [ ] Founder reviews 3 hygiene commits (`git log --oneline 517f728..HEAD`)
- [ ] Optional: commit P16 report docs (this sprint's deliverables)
- [ ] No `.env` or secrets in staged paths

---

## Do NOT Push

- Do not force-push any branch
- Do not push to `main` in this sprint
- Do not delete branches

---

## Recovery From Scratch

After push, any clone can recover P16 demo state:

```bash
git clone <repo>
git checkout release/p16-demo-ready-v1   # or: git checkout p16-demo-ready-v1
bash scripts/run_demo_local.sh
```

Rollback to pre-P16 production:

```bash
git checkout archive/production-pre-p16-demo
```
