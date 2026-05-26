# Simplification Execution Plan — Safe Batch Loops

**Purpose:** Control document for low-risk reduction batches. Not a feature roadmap.  
**Authority chain:** [`CURRENT_PRODUCT_SHAPE.md`](CURRENT_PRODUCT_SHAPE.md) (runtime) → [`SIMPLIFICATION_MASTER_PLAN.md`](SIMPLIFICATION_MASTER_PLAN.md) (backlog) → **this file** (execution status).

---

## Baseline checkpoint

| Item | Value |
|------|--------|
| Branch | `checkpoint/before-simplification-execution-20260526-0346` |
| Tag | `checkpoint/pre-reduction-safe-restore-point-20260526-0346` |
| Commit | `307585770b388430db0a672fc91c3d1aa4a1eb9b` |
| Working branch | `reduction/safe-batch-loops` |
| Started | 2026-05-26 |

**Rollback (full restore):**

```bash
git switch checkpoint/before-simplification-execution-20260526-0346
# or
git checkout checkpoint/pre-reduction-safe-restore-point-20260526-0346
```

**Rollback (single batch):** `git revert <batch-commit>` or cherry-pick from checkpoint.

---

## Frozen zones (do not touch in these batches)

- `services/fiqa_api/inbox_triage/triage.py` behavior
- PG schema / migrations
- Office/token semantics
- Case/session continuity / append flows
- Support manifest JSON contracts

---

## Execution table

| Batch | Task | Files likely touched | Risk | Expected benefit | Validation | Rollback | Status |
|-------|------|----------------------|------|------------------|------------|----------|--------|
| 0 | Branch + baseline doc | `docs/SIMPLIFICATION_EXECUTION_PLAN.md` | Low | Traceable restore point | `git log -1`, tag list | Switch to checkpoint tag | **done** |
| 1 | Master plan + execution table | `docs/SIMPLIFICATION_EXECUTION_PLAN.md` | Low | One control doc for all batches | `git diff --stat` (docs only) | Revert doc commit | **done** |
| 2 | Archive sprint doc noise | `docs/sprints/archive/**`, `docs/sprints/README.md`, moved sprint paths | Low | Less agent/founder confusion from stale sprints | `git status`, grep broken refs | `git mv` back from archive | **done** |
| 3 | Node 22 / UI build gate | `.nvmrc`, `ui/.nvmrc`, `scripts/check_ui_node_version.sh`, `docs/*` | Low | Stop Vite/Node recurring failures | `node --version`, `check_ui_node_version.sh`, `npm run build`, madge | Revert nvmrc + script | pending |
| 4 | Deploy script naming convergence | `scripts/deploy_cloud_run_core.sh`, `scripts/deploy_rag_demo.sh` (wrapper), wrappers, tests, deploy docs | Low–Med | Obvious paid-pilot entry; core impl named honestly | `trial_readiness_check`, `trial_launch_check`, `validate_pilot_deploy_env`, `bash -n` | Revert rename + wrapper | pending |
| 5 | UI product-only surface | `ui/src/components/layout/AppSider.tsx`, `UnifiedIntakePage.tsx`, `productSurface.ts`, docs | Low | Broker UI = one product, not lab | `npm run build`, madge, grep `productSurface` | Revert UI gate commits | pending |
| 6 | JSON/PG prod posture tightening | `scripts/validate_pilot_deploy_env.py`, tests, `configs/demo.env.example`, docs | Low | Wrong persistence path fails before deploy | `pytest tests/test_validate_pilot_deploy_env.py`, guardrail, regression | Revert validator/docs | pending |

---

## Validation commands (standard)

```bash
git diff --stat
git status --short

# Python
python3 -m compileall -q services/fiqa_api tests
PYTHONPATH=. pytest tests/
bash scripts/guardrail_inbox_triage.sh
PYTHONPATH=. python3 scripts/run_full_regression.py

# Trial / deploy posture
bash scripts/trial_readiness_check.sh
bash scripts/trial_launch_check.sh
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --show-profile

# UI (Node 22 required)
bash scripts/check_ui_node_version.sh
cd ui && npm run build
cd ui && npx --yes madge --circular --extensions ts,tsx src
```

---

## Batch completion log

| Batch | Commit | Notes |
|-------|--------|-------|
| 0 | — | Branch `reduction/safe-batch-loops` from checkpoint |
| 1 | pending | Docs-only execution table |
| 2 | pending | ~90 root `.md` + 16 dirs → `docs/sprints/archive/` |
| 3 | pending | |
| 4 | pending | |
| 5 | pending | |
| 6 | pending | |

---

## Remaining simplification backlog (after this sprint)

From [`SIMPLIFICATION_MASTER_PLAN.md`](SIMPLIFICATION_MASTER_PLAN.md) — not in scope for safe-batch-loops:

| Priority | Item | Class |
|----------|------|-------|
| Next | Collapse `demo.env.example` to PILOT block + appendix | Low |
| Next | Demote platform blueprints in `PROJECT_DOC_SYSTEM_MAP` | Low |
| Next | Intake-only readiness profile in trial scripts (Qdrant optional) | Low |
| Next | Continue sprint archive (800+ files remain) | Low |
| Deferred | Wire or delete `active_vehicle_resolver.py` | Medium |
| AFTER_REVENUE | Split `triage.py`, lazy-load lab routes, delete JSON path | High |

---

## Self-critique template (after each batch)

1. Did this reduce complexity?
2. Did this accidentally add complexity?
3. Did this touch risky runtime logic?
4. Can we rollback easily?
5. Did we make the product easier to explain?
6. Did we reduce founder cognitive load?
