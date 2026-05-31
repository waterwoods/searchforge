# P16-A Phase 3 — Remote Push Review

**Date:** 2026-05-31  
**Policy:** Do **not** push automatically. Commands provided for founder decision only.

---

## Remote Configuration

```
origin  git@github.com:waterwoods/searchforge.git (fetch)
origin  git@github.com:waterwoods/searchforge.git (push)
```

---

## Branch Tracking

| Branch | Upstream | Ahead/Behind |
|--------|----------|--------------|
| `reduction/p1-simplification-loops` (current) | **None** | Local-only |
| `main` | `origin/main` @ `31572ca` | Diverged from reduction branch |
| `checkpoint/before-simplification-execution-20260526-0346` | None | Local checkpoint branch |

**Current branch has never been pushed to origin.**

---

## Should `constitution-v1` Be Pushed?

### Recommendation: **YES — after constitution commit, push branch + tag**

| Factor | Assessment |
|--------|------------|
| Local-only risk | 🔴 High — laptop loss = no constitution in remote |
| Tag portability | Tags do not push with `git push` alone |
| Branch state | Mixed (staged archives + unstaged reduction) — **push only after constitution-only commit** |
| Remote backup value | Critical — first implementation sprint starting |
| Conflicts with `main` | Expected — reduction branch is intentional; do not merge to main yet |

### Why push

1. Constitution V1 is the **official pre-implementation baseline** — remote backup is the second half of "Freeze + Verify + Tag".
2. Rollback from another machine requires tag on origin.
3. Sprint A may run over multiple days — remote tag protects against local-only loss.

### Why not push immediately (without commit)

- Constitution docs are **untracked** — nothing to push yet.
- Pushing branch now would **not** include constitution files.

### What NOT to push blindly

- Do **not** `git push --force` to `main`.
- Do **not** push until constitution-only commit exists (avoid pushing empty baseline intent).

---

## Exact Commands (after Phase 2 commit + tag)

```bash
cd /home/andy/searchforge

# 1. Push branch (first time — set upstream)
git push -u origin reduction/p1-simplification-loops

# 2. Push annotated tag
git push origin constitution-v1

# 3. Verify remote tag
git ls-remote origin refs/tags/constitution-v1
```

### Optional: push tag only (if branch already on origin)

```bash
git push origin constitution-v1
```

---

## Alternative: Tag-only backup without pushing full branch

If founder prefers **not** to push the messy reduction branch state:

```bash
# After constitution commit on local branch:
git push origin constitution-v1

# Tag points to commit; recoverable via:
git fetch origin tag constitution-v1
git checkout -b recovery-from-constitution constitution-v1
```

**Caveat:** Full branch history (reduction commits) still local-only unless branch is pushed.

---

## Remote Safety Checklist

| Check | Command | Pass criteria |
|-------|---------|---------------|
| SSH auth | `ssh -T git@github.com` | Hi waterwoods! |
| Tag not duplicate | `git ls-remote origin refs/tags/constitution-v1` | Empty before first push |
| Commit is constitution-only | `git show --name-only HEAD` | Only `docs/product_constitution/*` |
| No secrets in commit | `git diff --cached \| grep -iE 'api_key\|password\|secret'` | No matches |

---

## Verdict

| Question | Answer |
|----------|--------|
| Push automatically? | **No** |
| Should founder push? | **Yes** — branch + tag after constitution commit |
| Push to main? | **No** — stay on reduction branch |
| Minimum viable backup | `git push origin constitution-v1` |

---

*End of P16-A Phase 3 — Remote Push Review*
