# P6 Physical SaaS Convergence Plan

**Sprint:** P6_PHYSICAL_SAAS_CONVERGENCE  
**Authority chain:** `CURRENT_PRODUCT_SHAPE.md` (runtime) → `SIMPLIFICATION_MASTER_PLAN.md` (backlog) → **this file** (P6 execution)  
**Branch:** `reduction/p1-simplification-loops`  
**Started:** 2026-05-28

---

## Frozen zones (non-negotiable)

- `triage.py` behavior
- PG schema / migrations
- Office/token semantics, append flows
- Support manifest JSON contract keys
- Workbench continuity, intake API contracts
- `deploy_paid_pilot.sh` semantics

---

## Phase 0 — TOP_50_PHYSICAL_PLATFORM_SMELLS

| # | Smell | Category |
|---|-------|----------|
| 1 | Repo name `searchforge` vs product `Unified Intake` | Naming |
| 2 | 49 top-level directories on clone | Root pollution |
| 3 | 477 scripts at flat `scripts/` level | Scripts sprawl |
| 4 | Makefile 1,340 lines, Chinese help text | Giant Makefile |
| 5 | `make help` default target screams SearchForge lab | Startup confusion |
| 6 | `Makefile.lab` symlink to full Makefile | Lab leakage |
| 7 | `docker-compose.lab.yml` symlink | Lab leakage |
| 8 | docker-compose: Qdrant + Milvus + Redis + GPU worker | Compose complexity |
| 9 | Port 8000 vs 8001 vs 8011 confusion | Runtime paths |
| 10 | `experiments/` at repo root (50+ scripts) | Lab surface |
| 11 | `agents/` at repo root | Lab surface |
| 12 | `modules/autotuner/` | Platform module |
| 13 | `jobhunter-clipper/` | Unrelated vertical |
| 14 | `orchestrators/`, `pipelines/`, `engines/` | Platform dirs |
| 15 | `mcp/`, `k8s/`, `ml_models/` | Infra fantasy |
| 16 | `.runs/` 453 subdirs | Run artifact sprawl |
| 17 | `poetry.lock` + `requirements.txt` + `pyproject.toml` | Dependency confusion |
| 18 | 3 Dockerfiles (main + ecommerce + jobhunter) | Root clutter |
| 19 | `demo_brain_report.html` at root | Root archaeology |
| 20 | `triage.sh` at root (host sampling, not intake) | Naming confusion |
| 21 | 218 → 132 docs at `docs/` root (pre-P6) | Doc overload |
| 22 | 71 `*_SPRINT_REPORT.md` at docs root | Trial/doc archaeology |
| 23 | 8+ `*BLUEPRINT*.md` at docs root | Platform fantasy |
| 24 | 6 AutoTuner docs at docs root | Lab doc leakage |
| 25 | `PLUGIN_ARCHITECTURE_MAP.md` at docs root | Platform abstraction |
| 26 | `docs/sprints/` 38+ active sprint dirs | Sprint sprawl |
| 27 | `docs/trial/` 12+ core specs + kickoff subtree | Trial overload |
| 28 | `TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT` authority drift | Onboarding confusion |
| 29 | `PROJECT_DOC_SYSTEM_MAP` 150+ lines | Doc map intimidation |
| 30 | Multiple founder trial entry paths | Trial confusion |
| 31 | `start_all.sh` / `dev_local.sh` wrong ports | Script confusion |
| 32 | `deploy_rag_demo.sh` vs `deploy_paid_pilot.sh` | Deploy confusion |
| 33 | `/health`, `/healthz`, `/ready`, `/readyz`, `/health/live` | Health overload |
| 34 | `GET /ready` requires Qdrant+embedding | Health trap |
| 35 | UI lab pages (RankerLab, RetrieverLab, AgentStudio…) | Lab UI leakage |
| 36 | `RUN_DEMO_LAB=1` opt-in buried in env docs | Lab isolation |
| 37 | SearchForge branding in `start_all.sh` output | Branding |
| 38 | `platform_full` vs `PRODUCT_ONLY` naming | Mode confusion |
| 39 | `results/` mixed trial + lab + sprint outputs | Artifact sprawl |
| 40 | `configs/` 8 subdirs — hard to know what's pilot | Config intimidation |
| 41 | `services/retrieval_proxy/` sibling to fiqa-api | Platform sibling |
| 42 | `ui/` 40+ lazy-loaded lab page chunks in dist | Bundle archaeology |
| 43 | `tests/` includes lab-only tests mixed with product | Test sprawl |
| 44 | `BROKER_REPORTS_INDEX.md` indexes hundreds of reports | Report overload |
| 45 | `DOC_INDEX_RECOMMENDED.md` lists archived paths as live | Doc honesty |
| 46 | `~/searchforge` hardcoded in lab scripts | Path assumption |
| 47 | Chinese comments in Makefile / triage.sh | Locale confusion |
| 48 | `constraints.txt` orphan at root | Root clutter |
| 49 | `triage.sh` name collides with intake triage | Semantic collision |
| 50 | Clone → "this is an AI platform" first impression | Psychological |

---

## Phase 0 — TOP_30_HIGHEST_ROI_PHYSICAL_REDUCTIONS

| # | Reduction | Batch | ROI | Risk |
|---|-----------|-------|-----|------|
| 1 | Archive 71 sprint reports → `docs/archive/sprint_reports/` | E | High | Low |
| 2 | Archive platform blueprints → `docs/archive/platform/` | E | High | Low |
| 3 | `scripts/operator/` wrappers for 10 scripts | B | High | Low |
| 4 | `scripts/lab/README.md` + move root `triage.sh` | B/A | High | Low |
| 5 | `experiments/README.md` LAB banner | D | Med | Low |
| 6 | `agents/README.md` LAB banner | D | Med | Low |
| 7 | Makefile `help` product redirect banner | C/D | Med | Low |
| 8 | Dockerfile.ecommerce/jobhunter LAB banners | A | Med | Low |
| 9 | Move `demo_brain_report.html` to archive | A | Med | Low |
| 10 | Update OPERATOR_IGNORE_LIST with archive paths | C | Med | Low |
| 11 | Update PROJECT_DOC_SYSTEM_MAP archive refs | C | Med | Low |
| 12 | ANDY_QUICK_START workbench-first URL | C | Med | Low |
| 13 | Extend `test_operator_surface_collapse.py` | — | Med | Low |
| 14 | README_LAB_INFRA index expansion | D | Med | Low |
| 15 | Archive AutoTuner docs to platform/ | E | Med | Low |
| 16 | root_archaeology INDEX update | A | Low | Low |
| 17 | docs/archive/INDEX sprint_reports entry | A | Low | Low |
| 18 | DOC_INDEX_RECOMMENDED archive paths | C | Low | Low |
| 19 | CHEN_KUI_TRIAL_PACK remove platform ref | E | Low | Low |
| 20 | SIMPLIFICATION_MASTER_PLAN archive path | C | Low | Low |
| 21 | Continue sprint dir archive (~38 dirs) | Deferred | High | Low |
| 22 | `scripts/lab/` symlink wrappers for start_all | Deferred | Med | Med |
| 23 | modules/autotuner/README LAB banner | Deferred | Med | Low |
| 24 | Collapse founder trial docs to 3 files | Deferred | Med | Low |
| 25 | Root `.env.*` count documentation | Deferred | Low | Low |
| 26 | Rename repo (external) | Out of scope | High | High |
| 27 | Split docker-compose product vs lab files | Deferred | High | Med |
| 28 | Move `jobhunter-clipper/` to archive | Deferred | Med | Med |
| 29 | English-only Makefile help | Deferred | Low | Low |
| 30 | `docs/` root target ≤50 markdown files | Next sprint | High | Low |

---

## Execution batches

### P6-A — Root structure cleanup ✅

| Field | Detail |
|-------|--------|
| Root cause | Root files/dirs signal AI lab, not broker SaaS |
| Human impact | Clone sees fewer scary artifacts; lab Dockerfiles labeled |
| Why high ROI | First 60 seconds of repo browse |
| Why safe | git mv only; no runtime changes |
| Validation | pytest operator_surface; trial checks |
| Rollback | `git mv` back from archive |

**Actions:** `demo_brain_report.html` → archive; `triage.sh` → `scripts/lab/host_resource_triage.sh`; LAB banners on Dockerfile.ecommerce/jobhunter.

---

### P6-B — Scripts physical convergence ✅

| Field | Detail |
|-------|--------|
| Root cause | 477 flat scripts = equal priority illusion |
| Human impact | `scripts/operator/` discoverable; lab README separates R&D |
| Why high ROI | Operators find the 10 scripts physically grouped |
| Why safe | Wrappers exec parent scripts; historical paths preserved |
| Validation | `bash scripts/operator/trial_launch_check.sh --help` or dry run |
| Rollback | Remove `scripts/operator/` dir |

**Actions:** 11 wrapper scripts in `scripts/operator/`; `scripts/lab/README.md`.

---

### P6-C — Onboarding collapse ✅

| Field | Detail |
|-------|--------|
| Root cause | Doc refs pointed at platform blueprints at docs root |
| Human impact | Ignore list + doc map honest about archives |
| Why high ROI | Stops engineers reading investor blueprints as SSOT |
| Why safe | Doc-only |
| Validation | grep refs; pytest |
| Rollback | Revert doc commits |

**Actions:** Updated CURRENT_PRODUCT_SHAPE, OPERATOR_IGNORE_LIST, PROJECT_DOC_SYSTEM_MAP, DOC_INDEX, ANDY_QUICK_START.

---

### P6-D — Lab isolation ✅

| Field | Detail |
|-------|--------|
| Root cause | experiments/agents/Makefile feel like co-equal product |
| Human impact | LAB ONLY READMEs; Makefile help redirects to product |
| Why high ROI | Lab feels optional |
| Why safe | README + help banner only |
| Validation | test_lab_directories_have_readme |
| Rollback | Delete READMEs; revert Makefile help |

---

### P6-E — Trial/doc surface collapse ✅

| Field | Detail |
|-------|--------|
| Root cause | 71 sprint reports + 8 blueprints at docs root |
| Human impact | docs/ root 218 → 132 markdown files |
| Why high ROI | Biggest single doc intimidation reduction |
| Why safe | git mv; INDEX files; live docs updated |
| Validation | trial_readiness (doc existence checks) |
| Rollback | `git mv` back |

---

## Validation commands

```bash
python3 -m compileall -q services/fiqa_api
PYTHONPATH=. pytest tests/test_operator_surface_collapse.py tests/test_deployment_profile.py -q
bash scripts/guardrail_inbox_triage.sh
bash scripts/trial_readiness_check.sh
bash scripts/trial_launch_check.sh
```

---

## Batch completion log

| Batch | Status | Notes |
|-------|--------|-------|
| P6-A | done | Root archaeology + Dockerfile banners |
| P6-B | done | scripts/operator + scripts/lab |
| P6-C | done | Doc path honesty |
| P6-D | done | experiments/agents README + Makefile help |
| P6-E | done | 71 sprint reports + 15 platform docs archived |

---

## Deferred (next sprint)

- Archive remaining ~38 `docs/sprints/` dirs
- `docs/` root target ≤50 files
- `modules/autotuner/README.md`
- Optional docker-compose physical split (not symlink)
- English Makefile help rewrite

---

*End of P6 plan*
