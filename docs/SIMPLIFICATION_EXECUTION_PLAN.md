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
| Working branch | `reduction/p1-simplification-loops` (from `reduction/p0-hardening-loops`) |
| Started | 2026-05-26 |
| P0 hardening | 2026-05-26 — batches 1–4 below |
| P1 simplification | 2026-05-26 — batches 1–4 below |

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
| 3 | Node 22 / UI build gate | `.nvmrc`, `ui/.nvmrc`, `scripts/check_ui_node_version.sh`, `docs/*` | Low | Stop Vite/Node recurring failures | `node --version`, `check_ui_node_version.sh`, `npm run build`, madge | Revert nvmrc + script | **done** |
| 4 | Deploy script naming convergence | `scripts/deploy_cloud_run_core.sh`, `scripts/deploy_rag_demo.sh` (wrapper), wrappers, tests, deploy docs | Low–Med | Obvious paid-pilot entry; core impl named honestly | `trial_readiness_check`, `trial_launch_check`, `validate_pilot_deploy_env`, `bash -n` | Revert rename + wrapper | **done** |
| 5 | UI product-only surface | `ui/src/components/layout/AppSider.tsx`, `UnifiedIntakePage.tsx`, `productSurface.ts`, docs | Low | Broker UI = one product, not lab | `npm run build`, madge, grep `productSurface` | Revert UI gate commits | **done** |
| 6 | JSON/PG prod posture tightening | `scripts/validate_pilot_deploy_env.py`, tests, `configs/demo.env.example`, docs | Low | Wrong persistence path fails before deploy | `pytest tests/test_validate_pilot_deploy_env.py`, guardrail, regression | Revert validator/docs | **done** |
| P0-1 | Collapse `demo.env.example` | `configs/demo.env.example` | Low | One PILOT block + appendix sections | `validate_pilot_deploy_env --show-profile`, `trial_readiness_check` | Revert env template | **done** |
| P0-2 | Archive sprint noise (wave 2) | `docs/sprints/archive/**`, README | Low | 8 active root sprint docs remain | grep broken refs | `git mv` back | **done** |
| P0-3 | Node 22 PATH hardening | `with_node22_path.sh`, `NODE_22_SETUP.md`, trial scripts | Low | Trial UI build reliable on WSL/Cursor | `check_ui_node_version`, `npm run build`, madge | Revert scripts | **done** |
| P0-4 | Intake-core readiness | `deployment_profile.py`, `health/ready.py`, `summarize_readiness_posture.sh` | Low–Med | Qdrant optional for paid pilot `/readyz` | `trial_readiness_check` [9], pytest deployment_profile | Revert env flag + ready.py | **done** |
| P1-1 | Optional Qdrant deploy preflight | `deploy_cloud_run_core.sh`, `deploy_paid_pilot.sh`, `demo.env.example`, deploy docs | Low | Intake SaaS deploy without vectors | `trial_readiness_check`, `validate_pilot_deploy_env`, `bash -n` | Revert deploy scripts | **done** |
| P1-2 | Demote platform blueprints | `PROJECT_DOC_SYSTEM_MAP.md`, `CURRENT_PRODUCT_SHAPE.md`, `sprints/README.md` | Low | Less platform-fantasy authority | grep refs, self-review | Revert doc commit | **done** |
| P1-3 | Archive Add-Car sprint wave | `docs/sprints/archive/add_car_sprints/**`, convergence reports | Low | ~41 dirs archived; 6 active root sprints | grep broken refs, script paths | `git mv` back | **done** |
| P1-4 | Deploy/runtime messaging | `deploy_cloud_run_core.sh`, `DEPLOYMENT_READINESS.md`, trial scripts | Low | Operator story matches runtime | `trial_readiness_check`, `trial_launch_check`, `summarize_readiness_posture` | Revert messaging commits | **done** |
| P2-1 | Operator cheat sheet + truth maps | `docs/runbooks/OPERATOR_CHEAT_SHEET.md`, `DEPLOY_TRUTH_MAP.md`, `SUPPORT_TRUTH_MAP.md`, AGENTS, DOC_MAP | Low | 2am path in one page | grep refs, read lints | Revert doc commit | **done** |
| P2-2 | Health/readiness doc clarity | `DEPLOYMENT_READINESS.md`, `summarize_readiness_posture.sh` | Low | `/health/live` vs `/healthz` trap gone | `summarize_readiness_posture.sh`, trial checks | Revert docs/script | **done** |
| P2-3 | Lab UI isolation | `App.tsx`, `labPages.tsx`, `LabDevBanner.tsx`, `AppSider.tsx`, `AppLayout.tsx` | Low–Med | Lab not in product-only bundle/routes | `npm run build`, madge | Revert UI commits | **done** |
| P2-4 | Sprint archive wave 4 | `docs/sprints/archive/p2_*`, README, battery script paths | Low | ~50 fewer active sprint dirs | grep broken refs, guardrail | `git mv` back | **done** |
| P2-fix | Archive script path updates | `run_append_boundary_ab_scenarios.py`, `run_residual_copy_ab_scenarios.py`, `trial_readiness_check.sh` | Low | Guardrail/trial pass after archive | guardrail, trial_launch | Revert paths | **done** |
| P3-1 | Operator warning humanization | `deployment_profile.py`, `summarize_readiness_posture.sh`, `validate_pilot_deploy_env.py`, tests | Low | Scary `_v1` codes → plain English | pytest deployment_profile, trial_readiness | Revert deployment_profile | **done** |
| P3-2 | Support posture script + docs | `summarize_support_posture.sh`, OPERATOR_CHEAT_SHEET, SUPPORT_TRUTH_MAP, DEPLOYMENT_PLAYBOOK | Low | Support without decoding manifest JSON | bash summarize_support_posture | Revert script | **done** |
| P3-3 | Health naming + prod check wording | `app_main.py` healthz, `check_unified_intake_prod_posture.sh` | Low | Product-only says Unified Intake API | pytest health | Revert app_main | **done** |
| P4-1 | README collapse + legacy archive | `README.md`, `docs/archive/README_LEGACY_SEARCHFORGE_LAB.md`, archive INDEX | Low | Founder/README no longer SearchForge lab | `test_operator_surface_collapse.py`, line count | Restore README from archive | **done** |
| P4-2 | Operator surface SSOT | `docs/runbooks/OPERATOR_SURFACE.md` | Low | One page: 10 scripts, 10 docs, 5 endpoints | test + grep refs | Delete file | **done** |
| P4-3 | Entry doc wiring | `AGENTS.md`, `PROJECT_DOC_SYSTEM_MAP.md`, cheat sheet, ignore list | Low | 15-min paths discoverable | grep refs | Revert doc commit | **done** |
| P4-4 | Guard tests | `tests/test_operator_surface_collapse.py` | Low | Prevent README re-bloat | pytest | Revert test | **done** |
| P5-1 | Lab physical separation | Makefile/docker-compose banners, `Makefile.lab`, `docker-compose.lab.yml`, `docs/archive/platform/`, root archaeology → archive | Low | Lab feels opt-in at repo root | pytest operator_surface, trial checks | Revert + git mv back | **done** |
| P5-2 | Onboarding script convergence | `scripts/README.md`, `README_OPERATOR.md`, `LAB_ONLY_SCRIPTS.md`, start_all/dev_local banners | Low | One script story | pytest operator_surface | Revert scripts docs | **done** |
| P5-3 | Trial doc collapse | `docs/trial/INDEX.md`, `docs/trial/archive/specs/`, founder_pre_trial pointer | Low | One launch path | trial_readiness, trial_launch | git mv back | **done** |

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
| 1 | `9dabd01` | Execution control doc |
| 2 | `6677e85` | ~90 root `.md` + 16 dirs → `docs/sprints/archive/` |
| 3 | `9aa1436` | Node 22 gate (+ core rename landed here) |
| 4 | `a31bf28` | Deploy naming wrapper + docs |
| 5 | `2f3f575` | Product-only sidebar |
| 6 | `a9ecf93` | Validator tightening |
| fix | `dd9540b` | Test fixture PG_DUAL_WRITE |
| P0-1 | `9ffbb28` | PILOT ONE PATH + OPTIONAL/DEV/LAB/LEGACY/INTERNAL |
| P0-2 | `1e9c322` | 26 sprint md + workbench_handoff_readiness → archive |
| P0-3 | `c723c5b` | `with_node22_path.sh`, NODE_22_SETUP, trial Node gate |
| P0-4 | `8485629` | `UNIFIED_INTAKE_INTAKE_CORE_READINESS`, `/readyz` intake_core |
| P1-1 | `cb02a91` | `SKIP_QDRANT`/intake-core deploy preflight; QDRANT optional in paid pilot |
| P1-2 | `43a7d15` | Platform blueprints → Future exploration section |
| P1-3 | `07f5d0c` | ~41 Add-Car dirs + 6 convergence reports → archive |
| P1-4 | `02111cd` | Deploy summary + DEPLOYMENT_READINESS intake-only clarity |

**Final validation (P0 sprint end):** compileall OK, pytest OK, guardrail OK, full_regression OK, trial_readiness OK, trial_launch OK, UI build OK, madge OK.

**Final validation (P1 sprint end):** compileall OK, pytest OK, guardrail OK, full_regression OK, trial_readiness OK, trial_launch OK, UI build OK, madge OK.

---

## Remaining simplification backlog (after P2 simplification)

| Priority | Item | Class |
|----------|------|-------|
| Next | Continue sprint archive (~38 remaining non-archived sprint dirs) | Low |
| Next | Demote `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE` when it reads like platform SSOT | Low |
| Deferred | Wire or delete `active_vehicle_resolver.py` | Medium |
| Deferred | `/ready` (app_main) still requires EMBED+Qdrant — intake uses `/readyz` only | Low |
| AFTER_REVENUE | Split `triage.py`, delete JSON path | High |

---

## P0 self-critique (per batch)

### P0-1 — demo.env.example

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — one PILOT block; anxiety flags in appendix |
| Added complexity? | No — vars preserved, only reorganized |
| Risky runtime? | No |
| Rollback? | Single revert |
| Easier to explain? | Yes — 1am deploy path is copy-paste obvious |
| Founder load ↓? | Yes |

### P0-2 — sprint archive

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — 8 root sprint files vs 34 |
| Added complexity? | Minimal — classification table in archive README |
| Risky runtime? | No |
| Rollback? | `git mv` from archive |
| Easier to explain? | Yes — README says what is historical |
| Founder load ↓? | Yes — less fear opening `docs/sprints/` |

### P0-3 — Node 22

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — one `source scripts/with_node22_path.sh` |
| Added complexity? | One small helper script (worth it) |
| Risky runtime? | No |
| Rollback? | Revert scripts; nvmrc unchanged |
| Easier to explain? | Yes — NODE_22_SETUP runbook |
| Founder load ↓? | Yes — trial scripts self-heal PATH |

### P0-4 — intake-core readiness

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — clear intake vs full_stack modes |
| Added complexity? | One env flag + small ready.py branch (documented) |
| Risky runtime? | Low — mirrors existing DEMO_MODE path; triage untouched |
| Rollback? | Unset `UNIFIED_INTAKE_INTAKE_CORE_READINESS` |
| Easier to explain? | Yes — “Can I run intake if Qdrant is down?” → yes with flag |
| Founder load ↓? | Yes — `summarize_readiness_posture.sh` + trial step [9] |

**Not fixed now (documented):** `/ready` (app_main) still requires EMBED+Qdrant; intake operators should use `/readyz` + support manifest. Deploy preflight fixed in P1-1.

---

## P1 self-critique (per batch)

### P1-1 — optional Qdrant deploy preflight

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — one deploy truth: intake SaaS ≠ vector mandatory |
| Added complexity? | Small `_skip_qdrant_deploy_preflight` helper (documented) |
| Risky runtime? | No — triage untouched; RAG path unchanged when QDRANT_URL set |
| Rollback? | Single revert; unset flag |
| Easier to explain? | Yes — “Can I deploy intake without Qdrant?” → yes via `deploy_paid_pilot.sh` |
| Founder load ↓? | Yes |

### P1-2 — demote platform blueprints

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — PRIMARY table no longer lists investor theater |
| Added complexity? | No — reclassification section only |
| Risky runtime? | No |
| Rollback? | Revert doc commit |
| Easier to explain? | Yes — Future exploration ≠ build list |
| Founder load ↓? | Yes |

### P1-3 — archive Add-Car wave

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — 6 active root sprint docs; ~41 Add-Car dirs archived |
| Added complexity? | Script path updates only (7 files) |
| Risky runtime? | No — scenario JSON preserved for regression |
| Rollback? | `git mv` from archive |
| Easier to explain? | Yes — product = STANDARD_SCENARIO_PACKAGE + code |
| Founder load ↓? | Yes — less fear in `docs/sprints/` |

### P1-4 — deploy/runtime messaging

| Q | Answer |
|---|--------|
| Complexity ↓? | Yes — deploy summary shows intake vs full-stack |
| Added complexity? | No — messaging only |
| Risky runtime? | No |
| Rollback? | Revert 4 files |
| Easier to explain? | Yes — DEPLOYMENT_READINESS matches CURRENT_PRODUCT_SHAPE |
| Founder load ↓? | Yes — no more ETF query as default post-deploy hint |

---

## Self-critique template (after each batch)

1. Did this reduce complexity?
2. Did this accidentally add complexity?
3. Did this touch risky runtime logic?
4. Can we rollback easily?
5. Did we make the product easier to explain?
6. Did we reduce founder cognitive load?
