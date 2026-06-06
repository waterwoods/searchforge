# P16 Dirty Tree Census

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 2  
**Mode:** Read-only inventory (no deletions)  
**Branch HEAD:** `517f728` (`sprint-a/broker-front-door`)  
**Total dirty paths:** **1,761**

---

## Executive summary

The working tree is **not promotion-safe**. Nearly all dirt is **documentation housekeeping** — a large archival migration moving legacy sprint reports and platform docs into `docs/archive/`. No code deletion storm; the committed HEAD at `517f728` is clean.

| Status code | Count | Meaning |
|-------------|------:|---------|
| `D` (deleted from index) | 1,228 | Files removed from working tree vs last commit |
| `??` (untracked) | 463 | New files not yet staged |
| `M` (modified) | 70 | Changed tracked files |
| **Total** | **1,761** | |

**Nature:** ~95% docs. This is **intentional simplification work in progress**, not random drift.

---

## Disposition summary (all paths)

| Disposition | Count | % | Recommended action |
|-------------|------:|--:|-------------------|
| **KEEP** | 387 | 22% | Commit with promotion hygiene sprint |
| **REVIEW** | 1,045 | 59% | Founder review before commit; batch by category |
| **ARCHIVE** | 328 | 19% | Commit as archival move (deleted root → `docs/archive/`) |
| **DELETE_CANDIDATE** | 1 | <1% | Defer; not urgent |

---

## Category breakdown

### 1. DOCS — 1,664 paths (94.5% of total)

| Disposition | Count |
|-------------|------:|
| KEEP | 384 |
| REVIEW | 995 |
| ARCHIVE | 285 |

**Status mix:** ~1,200 deletions of root-level `docs/*.md` sprint reports; ~400 new untracked files under `docs/archive/`, `docs/product_constitution/`, and operator docs.

**Examples:**

| Status | Path | Disposition |
|--------|------|-------------|
| `M` | `docs/ANDY_QUICK_START.md` | KEEP |
| `M` | `docs/CURRENT_PRODUCT_SHAPE.md` | KEEP |
| `M` | `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | KEEP |
| `D` | `docs/AUTOTUNER_ALG_DELIVERY.md` | ARCHIVE (moved to `docs/archive/platform/`) |
| `D` | `docs/ADD_CAR_NEW_QUOTE_FLOW_SCOUTING_REPORT.md` | ARCHIVE |
| `??` | `docs/15_MINUTE_ENGINEER_ONBOARDING.md` | KEEP |
| `??` | `docs/FOUNDER_ONE_PATH.md` | KEEP |
| `??` | `docs/archive/lab/` | ARCHIVE |
| `??` | `docs/product_constitution/P16_*.md` | KEEP |

**Risk:** Medium — wrong commit could drop operator-critical docs or leave broken links.  
**Recommended action:** Commit as a single `docs: P16 archival migration` batch after link check. Do **not** merge to main with dirty tree.

---

### 2. SCRIPTS — 39 paths

| Disposition | Count |
|-------------|------:|
| REVIEW | 39 |

**Examples:**

| Status | Path |
|--------|------|
| `M` | `scripts/README_OPERATOR.md` |
| `M` | `scripts/check_unified_intake_prod_posture.sh` |
| `??` | `scripts/post_sprint_check.sh` |
| `??` | `scripts/guardrail_cloudrun_runtime.sh` |

**Risk:** Low–medium — script changes affect deploy gates.  
**Recommended action:** Review diffs; commit operator-surface scripts with docs batch.

---

### 3. CONFIGS — 9 paths

| Disposition | Count |
|-------------|------:|
| REVIEW | 9 |

**Examples:**

| Status | Path |
|--------|------|
| `M` | `configs/demo.env.example` |
| `M` | `configs/industries/insurance/markers.json` |
| `??` | `configs/p16y_50_cases.json` |
| `??` | `configs/p16z20_add_car_customers.json` |

**Risk:** Medium — env example changes affect deploy posture documentation.  
**Recommended action:** Validate with `validate_pilot_deploy_env.py` before commit.

---

### 4. DOCKER — 4 paths

| Disposition | Count |
|-------------|------:|
| REVIEW | 4 |

**Examples:** `docker-compose.yml`, `Dockerfile.ecommerce`, `Dockerfile.jobhunter`, `?? docker-compose.product.yml`

**Risk:** Low — lab/product separation changes; not on paid-pilot deploy path.  
**Recommended action:** Commit with lab-isolation batch or stash if unrelated to promotion.

---

### 5. EXPERIMENTS — 1 path

| Disposition | Count |
|-------------|------:|
| DELETE_CANDIDATE | 1 |

**Example:** `?? experiments/README.md`

**Risk:** None.  
**Recommended action:** Delete later during branch archaeology cleanup.

---

### 6. AUTO-EVOLUTION — 0 dirty paths

No uncommitted changes under `auto-evolution/` prefix. Evolution work is captured in **local branches** (see `P16_BRANCH_ARCHAEOLOGY_PREP.md`), not the working tree.

---

### 7. GENERATED — 0 dirty paths

No `node_modules/`, `dist/`, `__pycache__/`, or build artifacts in the dirty set. `.gitignore` is working.

---

### 8. OTHER — 44 paths

| Disposition | Count |
|-------------|------:|
| KEEP | 3 |
| REVIEW | 41 |

**Examples:**

| Status | Path | Disposition |
|--------|------|-------------|
| `M` | `AGENTS.md` | KEEP |
| `M` | `README.md` | KEEP |
| `M` | `Makefile` | KEEP |
| `D` | `demo_brain_report.html` | REVIEW |
| `??` | `agents/README.md` | REVIEW |

**Risk:** Low for promotion (entry-point doc updates are valuable).  
**Recommended action:** Include `AGENTS.md` / `README.md` in docs hygiene commit.

---

## Untracked file breakdown (463 `??` paths)

| Directory | Count |
|-----------|------:|
| `docs/` | 427 |
| `scripts/` | 16 |
| `configs/` | 6 |
| `ui/` | 5 |
| other | 9 |

Most untracked docs are **archive destinations** for deleted root-level files — the delete + untrack pair is an in-progress `git mv` migration.

---

## Risk matrix

| Category | Count | Risk | Blocks promotion? |
|----------|------:|------|:-----------------:|
| docs archival | 1,664 | Medium (link rot) | **Yes** — tree must be clean |
| scripts | 39 | Low–medium | No (if HEAD is clean) |
| configs | 9 | Medium | No (if HEAD is clean) |
| docker | 4 | Low | No |
| other | 44 | Low | No |
| experiments | 1 | None | No |

---

## Recommended action sequence

1. **Do not promote** with 1,761 dirty paths — merge would be unreproducible.
2. **Finish archival migration** — pair `D` deletions with `??` archive additions; run link check.
3. **Commit in one hygiene PR** — `docs: P16 simplification archival + operator surface updates`.
4. **Verify clean tree** — `git status` must show 0 paths before mainline promotion.
5. **Defer DELETE_CANDIDATE** — `experiments/README.md` can wait for branch archaeology sprint.

---

## What the 1,757 files actually are

> Prior report cited ~1,757; current count is **1,761** (4 additional paths since last census).

They are **not** random corruption or build artifacts. They are:

1. **~1,228 deleted legacy docs** — sprint reports, platform blueprints, AutoTuner delivery docs being moved out of runtime authority paths.
2. **~427 new untracked docs** — mostly `docs/archive/*` destinations plus new operator/onboarding docs (`FOUNDER_ONE_PATH.md`, `15_MINUTE_ENGINEER_ONBOARDING.md`, etc.).
3. **~70 modified tracked files** — operator entry points (`AGENTS.md`, runbooks, demo env example).
4. **~16 new scripts** — guardrails and post-sprint checks from P16 freeze work.
5. **~6 new config fixtures** — simulation/customer JSON for P16 acceptance cases.

**Zero business-logic Python or TypeScript source files** appear in the dirty set at the application layer — the committed code at `517f728` is the product truth.

---

*End of P16 Dirty Tree Census — Phase 2*
