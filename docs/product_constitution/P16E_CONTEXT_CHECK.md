# P16-E Phase 0 — Context Check

**Date:** 2026-05-31  
**Sprint:** P16-E Vercel Preview Deploy + AI Simulation Review

---

## Git commands (recorded)

```text
git branch --show-current  → sprint-a/broker-front-door
git rev-parse HEAD         → c92cabfc364348ce30c5a882cdc1b720e51b7b69
git log --oneline -8       → c92cabf, c2e3dff, 66f7ed5, …
git branch -vv             → * sprint-a/broker-front-door c92cabf [origin/sprint-a/broker-front-door]
```

---

## Answers

### 1. Are we on the correct branch?

**YES.** Current branch is `sprint-a/broker-front-door`, tracking `origin/sprint-a/broker-front-door`.

### 2. Is the Node fix included?

**YES.** `c92cabf` ("Fix local demo startup with Node 22 helper") is `HEAD`. `git merge-base --is-ancestor c92cabf HEAD` → YES.

### 3. Is Sprint A included?

**YES.** `c2e3dff` ("Sprint A broker front door implementation") is an ancestor of `HEAD`. Both commits are on the pushed remote branch.

### 4. What files are dirty?

**~1,360 paths** repo-wide (reduction/archive doc moves, unrelated to Sprint A).

**Under `ui/` only (relevant to Vercel):**

| Path | Status |
|------|--------|
| `ui/src/App.tsx` | Modified |
| `ui/src/components/layout/AppLayout.tsx` | Modified |
| `ui/src/components/layout/AppSider.tsx` | Modified |
| `ui/src/components/layout/LabDevBanner.tsx` | Untracked |
| `ui/src/routes/` | Untracked |

### 5. Will dirty files affect Vercel deploy?

**Partially YES for `ui/`.** `vercel deploy` uploads the **local `ui/` tree**, not a clean git checkout. The Preview build therefore includes **5 uncommitted `ui/` paths** in addition to committed `c92cabf` / `c2e3dff` code.

Repo-root dirty docs/scripts do **not** enter the `ui/` deployment artifact.

**Production:** Not touched (no `vercel --prod`).

---

## Commit verification

| Commit | Expected | Present on branch |
|--------|----------|-------------------|
| `c2e3dff` | Sprint A | YES (ancestor of HEAD) |
| `c92cabf` | Node fix | YES (HEAD) |
| Remote pushed | YES | `[origin/sprint-a/broker-front-door]` at `c92cabf` |

---

*End of P16-E Phase 0*
