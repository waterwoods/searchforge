# P16 Mainline Diff Report

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 3  
**Mode:** Read-only comparison  
**Base:** `main` @ `31572ca` (2025-11-24)  
**Candidate:** `sprint-a/broker-front-door` @ `517f728` (2026-06-04)

---

## Commit counts

| Metric | Value |
|--------|------:|
| Commits on sprint not on main | **98** |
| Commits on main not on sprint | **0** |
| Files changed | **2,083** |
| Insertions | **+597,932** |
| Deletions | **−3,259** |

`sprint-a/broker-front-door` is a **pure fast-forward** over `main`. No divergent main commits.

---

## What would happen if merged today?

| Outcome | Assessment |
|---------|------------|
| Git merge conflict | **None** — fast-forward |
| `main` becomes P16 product | **Yes** — entire broker front door line lands |
| Production auto-updates | **No** — Vercel/Cloud Run are manual deploy paths |
| Lab code returns to main | **Partially** — lab is isolated in `docker-compose` / `docs/archive/lab/` but JobHunter pages remain in tree |
| Dirty tree merges | **Only if committed first** — uncommitted 1,761 paths do **not** merge automatically |

**Verdict:** A merge of **commit `517f728` only** (clean checkout) is technically a 98-commit fast-forward. A merge from **current working directory** would be **unsafe** due to 1,761 uncommitted paths.

---

## Major feature groups (98 commits)

| Group | Commits (approx) | Key SHAs | Description |
|-------|------------------|----------|-------------|
| **P16 broker front door** | ~8 | `c2e3dff` → `517f728` | Sprint A UI, product-only intake, message-first entry, active case choice gate |
| **Reduction / simplification** | ~14 | `9dabd01` → `84cc0db` | Doc archival, deploy script convergence, Node 22 gate, PG/JSON posture |
| **Frontend extraction** | ~6 | `2517640` → `879e807` | Customer entry, broker workbench, presentation components |
| **Auto-evolution intake** | ~35 | `25eac2a` → `606e5ec` | Add-car triage, entity resolution, PG persistence, latency cuts |
| **Productization** | ~5 | `0c2ed6d`, `f14f755` | Workbench queue, SaaS survivability, deployment drift warnings |
| **Lab isolation** | ~4 | `70b26f0`, `d64f782` | Separate lab infra from product path |
| **Constitution / governance** | ~3 | `66f7ed5`, `90e73f9` | Constitution V1, checkpoint restore points |
| **JobHunter (legacy)** | ~5 | `81f540a` → `1333016` | Chrome clipper, batch analysis — pre-P16 vertical |
| **Tests / scenarios** | ~8 | various | Chaos scenarios, destruction libraries, triage oracles |
| **Docs / chore** | ~10 | various | Trial doc collapse, operator README, deploy messaging |

---

## Directory impact (high-signal paths)

| Path | Files changed | Notes |
|------|-------------:|-------|
| `ui/` | ~389 | Unified Intake UI, DemoPage, broker workbench, customer entry |
| `services/` | ~200+ | Inbox triage API, PG persistence, intake core |
| `scripts/` | ~80+ | Guardrails, deploy wrappers, demo runners |
| `docs/` | ~1,000+ | Sprint reports, product constitution, runbooks |
| `configs/` | ~30+ | Chen Kui client, insurance markers, demo env |
| `experiments/` | few | Scenario libraries |

---

## Risk areas

| Risk | Severity | Detail |
|------|----------|--------|
| **Stale `main` perception** | High | `main` last moved Nov 2025; 6+ months of product work only on sprint branch |
| **Dirty working tree** | **Blocker** | 1,761 uncommitted paths — must not merge from dirty checkout |
| **Remote preservation gap** | High | Release branch, tag, 3 commits not on origin |
| **Production deploy lag** | High | Production Vercel is 45-day-old bundle (pre-P16) |
| **JobHunter surface in tree** | Medium | Legacy vertical code ships with merge; not on demo path but increases repo size |
| **Lab/product boundary** | Low | Isolation done in compose + docs; lab not default demo path |
| **CORS on raw Vercel URLs** | Medium | New Preview deploy hash URLs fail CORS unless added to `ALLOWED_ORIGINS` |
| **AC03/AC05/AC07** | None | No changes requested; baseline frozen at `517f728` |

---

## Breaking changes

No explicit breaking-change commits found. Notable behavioral shifts (documented, not API breaks):

| Change | Impact |
|--------|--------|
| Product-only intake mode | Demo/broker path only; lab features hidden |
| PG-primary case storage | JSON fallback disabled in production posture |
| Message-first customer entry (P16-O) | UX change, not API contract break |
| Active case choice gate (`517f728`) | Frontend-only; users with in-progress cases see continue/new prompt |
| Node 22 requirement | Local dev/build toolchain change |

---

## Rollback path

| Target | SHA | Remote | Command pattern |
|--------|-----|:------:|-----------------|
| Pre-P16 production | `85bacc6` | ✅ | `git checkout archive/production-pre-p16-demo` |
| P16 demo-ready | `517f728` | ❌ (push first) | `git checkout p16-demo-ready-v1` |
| Current main | `31572ca` | ✅ | `git checkout main` |

**Post-merge rollback:** If `main` is fast-forwarded to `517f728`, rollback = `git revert` range or reset `main` to `31572ca` (requires force push — avoid; prefer revert).

**Deploy rollback:**

```bash
# Backend — redeploy from archive branch
git checkout archive/production-pre-p16-demo
bash scripts/deploy_paid_pilot.sh

# Frontend — redeploy production Vercel from archive checkout
cd ui && vercel --prod
```

---

## Promotion prerequisites (from diff analysis)

1. Clean working tree (0 dirty paths).
2. Push `release/p16-demo-ready-v1` + tag `p16-demo-ready-v1` to origin.
3. Push `sprint-a/broker-front-door` (3 commits) to origin.
4. Fast-forward merge `sprint-a/broker-front-door` → `main` (or merge PR).
5. Redeploy Cloud Run + Vercel Production **after** founder E2E on Preview.

---

## Merge recommendation

| Scenario | Recommendation |
|----------|----------------|
| Merge today from dirty tree | **NO GO** |
| Merge `517f728` clean commit after hygiene | **CONDITIONAL GO** |
| Merge without remote preservation | **NO GO** |

---

*End of P16 Mainline Diff Report — Phase 3*
