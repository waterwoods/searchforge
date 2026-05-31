# P16-A Phase 0 — Repository Reality Audit

**Date:** 2026-05-31  
**Auditor:** P16-A Execution Baseline  
**Purpose:** Document repo state before Constitution V1 freeze. No code changes.

---

## Summary

| Field | Value |
|-------|-------|
| **Current branch** | `reduction/p1-simplification-loops` |
| **HEAD commit** | `d64f7829158ebf738ca2150e1f039c264ddb278b` |
| **Upstream tracking** | **None** — branch has no `@{u}` configured |
| **Remote** | `origin` → `git@github.com:waterwoods/searchforge.git` |
| **Working tree** | **Dirty** — large mixed state (see below) |
| **constitution-v1 tag** | **Does not exist** |

---

## Branch

```
* reduction/p1-simplification-loops  d64f782  (no upstream)
```

Other active work branches include `reduction/p0-hardening-loops`, `main` (tracks `origin/main`), and many `auto-evolution/*` branches. Constitution baseline should be created on the current reduction branch unless founder chooses otherwise.

---

## Staged Files (1,225)

**Critical:** The index currently holds **1,225 staged paths**, almost entirely **docs archive migrations** (renames from `docs/` → `docs/archive/broker_demo/`, `docs/archive/lab/`, `docs/archive/mvp_era/`, `docs/archive/p7_reports/`, etc.).

These are **P1 simplification / doc cleanup** work — **not** Constitution V1 content.

**Rule for P16 baseline commit:** Do **not** include staged archive migrations in the Constitution V1 commit.

---

## Modified (Unstaged) — 95 files

Representative categories:

| Category | Examples |
|----------|----------|
| Entry / onboarding docs | `AGENTS.md`, `docs/ANDY_QUICK_START.md`, `docs/CURRENT_PRODUCT_SHAPE.md` |
| Deploy / runtime | `docker-compose.yml`, `Makefile`, `configs/demo.env.example` |
| Archive index updates | `docs/archive/INDEX.md`, p9 broker surface docs |
| Scripts | Various under `scripts/` |
| UI (reduction work) | Possible touched files from P1 batches |

These are **ongoing reduction work** — separate from Constitution freeze.

---

## Untracked Files — 127 paths

Notable untracked groups:

| Group | Path pattern | Notes |
|-------|--------------|-------|
| **Constitution (entire tree)** | `docs/product_constitution/` | **26 files — all untracked** |
| Trial / broker docs | `docs/BROKER_ONE_PAGER.md`, `docs/TRIAL_ONE_PATH.md`, etc. | P15 outputs, not yet committed |
| Operator runbooks | `docs/runbooks/OPERATOR_*` | Related but outside constitution folder |
| Onboarding | `docs/15_MINUTE_ENGINEER_ONBOARDING.md`, `docs/FOUNDER_ONE_PATH.md` | Operator surface |
| Product compose | `docker-compose.product.yml` | Deploy artifact |

**Constitution docs exist on disk but have never been committed.**

---

## Remote Status

```
origin  git@github.com:waterwoods/searchforge.git (fetch)
origin  git@github.com:waterwoods/searchforge.git (push)
```

| Check | Result |
|-------|--------|
| Remote reachable | Assumed yes (SSH origin configured) |
| Current branch pushed | **No upstream** — local-only |
| `reduction/p1-simplification-loops` on origin | Not configured |
| Latest `main` on origin | `31572ca` — diverged from current branch |

---

## Last 20 Commits (current branch)

```
d64f782 Wire operator surface guards and document P5 lab-isolation batches.
141f693 Collapse trial docs to one launch path via INDEX and archived specs.
a3980cf Collapse script onboarding to README_OPERATOR and label lab-only launchers.
70b26f0 Physically separate SearchForge lab infra from product onboarding path.
84cc0db docs: record P1 simplification batch log and self-critique
02111cd reduction: batch 4 — align deploy/runtime operator messaging
07f5d0c reduction: batch 3 — archive Add-Car sprints and stale deploy noise
43a7d15 reduction: batch 2 — demote platform blueprints from runtime authority
cb02a91 reduction: batch 1 — optional Qdrant deploy preflight for intake SaaS
796b798 docs: record P0 hardening batch log and self-critique
8485629 reduction: batch 4 — intake-core readiness profile (Qdrant optional)
c723c5b reduction: batch 3 — stabilize Node 22 PATH and trial UI gate
1e9c322 reduction: batch 2 — archive second wave of sprint noise
9ffbb28 reduction: batch 1 — collapse demo.env.example to PILOT ONE PATH
926ca22 docs: record batch commit SHAs in execution plan log
dd9540b fix: include PG_DUAL_WRITE=0 in minimal pilot env test fixture
a9ecf93 reduction: batch 6 — JSON/PG prod posture tightening
2f3f575 reduction: batch 5 — UI product-only surface
a31bf28 reduction: batch 4 — deploy script naming convergence
9aa1436 reduction: batch 3 — Node 22 UI build gate
```

Reduction/hardening lineage — appropriate pre-implementation branch, but **constitution docs not yet in git history**.

---

## Existing Tags

```
backup-20251108-221444
checkpoint/pre-reduction-safe-restore-point-20260526-0346
infra-buildkit-ready
jobhunter-snapshot-20251217-1423
pre-langgraph-20251110
proxy-mvp-pass
py311-baseline
temp-pre-restore-20251108-231012
v1.0-bestpack
v1.0.0-fiqa-freeze
v1.4.0-m2
```

**No `constitution-v1` tag.** Nearest conceptual predecessor: `checkpoint/pre-reduction-safe-restore-point-20260526-0346` (pre-simplification, not constitution).

---

## Can We Safely Create Constitution V1?

| Criterion | Status | Notes |
|-----------|--------|-------|
| Constitution files exist on disk | ✅ Yes | 26 files under `docs/product_constitution/` |
| Clean isolated commit possible | ⚠️ **Conditional** | Must **exclude** 1,225 staged archive renames |
| Branch choice acceptable | ✅ Yes | Reduction branch is correct pre-implementation context |
| Tag name available | ✅ Yes | `constitution-v1` unused |
| Rollback without constitution | ✅ Yes | HEAD `d64f782` is pre-constitution state |
| Risk of mixing concerns | 🔴 **High if careless** | Staging `git add -A` would poison baseline |

### Verdict

**Yes — Constitution V1 can be safely created** using a **constitution-only commit**:

1. Do **not** commit staged archive migrations in the same commit.
2. `git add docs/product_constitution/` only (includes P16-A audit docs).
3. Tag `constitution-v1` on that commit immediately after.

**Optional pre-step:** Stash or unstage archive work if founder wants a clean `git status` before Sprint A:

```bash
# Option A: keep staged archive work for later P1 commit
git commit -m "..." --only docs/product_constitution/   # NOT valid git syntax

# Correct approach: add only constitution folder
git add docs/product_constitution/
git commit -m "..."
# Staged archive renames remain staged for separate commit
```

---

*End of P16-A Phase 0 — Repository Reality Audit*
