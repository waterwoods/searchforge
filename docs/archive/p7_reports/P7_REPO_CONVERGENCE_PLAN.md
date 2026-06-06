# P7 Repo Convergence and Lab Tiering Plan

**Sprint:** P7_REPO_CONVERGENCE_AND_LAB_TIERING  
**Authority chain:** `CURRENT_PRODUCT_SHAPE.md` (runtime) → P6 plan (physical baseline) → **this file** (P7 execution)  
**Started:** 2026-05-28

**Goal:** Reduce psychological platform gravity — isolate lab, converge topology, honest onboarding — **without** deleting R&D or changing runtime semantics.

---

## Frozen zones (non-negotiable)

- `triage.py` behavior
- PG schema / migrations
- Inbox routing, manifest contracts
- Auth/token semantics
- `deploy_paid_pilot.sh` runtime semantics
- Production API paths

---

## 1. CURRENT REAL PRODUCT

| Layer | Truth |
|-------|--------|
| **Product** | **Unified Intake** — paste → classify → case → broker workbench |
| **Flagship flow** | Add-car workflow, office handoff, broker confirms before send |
| **Deployment** | Vercel (UI) + Cloud Run (API) + Postgres (`SERVICE_RECORD_DATABASE_URL`) |
| **Auth** | Coarse intake + support API keys (not OAuth/SSO) |
| **Vectors** | Qdrant optional for core triage; notice/knowledge wedge when configured |
| **Default local** | `bash scripts/run_demo_local.sh` → product_only on port **8001** |
| **Paid pilot** | `UNIFIED_INTAKE_PRODUCT_ONLY=1`, Postgres-primary, `deploy_paid_pilot.sh` |

---

## 2. CURRENT REPO SHAPE

| Area | Count / note |
|------|----------------|
| Repo name | `searchforge` (heritage) vs product **Unified Intake** |
| Top-level dirs | ~49 (lab + product co-located) |
| `scripts/` flat | ~477 `.sh`/`.py` — **10 operator**, rest lab/regression |
| `scripts/operator/` | 10 wrappers (P6) |
| `scripts/founder/` | 3 wrappers (P7) |
| `scripts/lab/` | 9+ wrappers + LAB banner (P7) |
| `docs/` root | **133 → 47** markdown files (P7 archive batch) |
| `docs/archive/` | sprint_reports, platform, p7_reports, lab, broker_demo, mvp_era |
| Lab dirs | experiments, agents, autotuner, orchestrators, pipelines, engines, k8s, mcp, ml_models |
| UI | Workbench product; `/demo` RAG wedge; lab routes hidden in product_only |

---

## 3. WHAT IS PRODUCT

- `services/fiqa_api/inbox_triage/` — triage, cases, sessions
- `services/fiqa_api/deployment_profile.py` — posture truth
- `ui/` workbench routes (`/workbench/unified-intake`)
- `configs/clients/`, `configs/demo.env.example` PILOT block
- `docs/CURRENT_PRODUCT_SHAPE.md`, runbooks, trial package
- Operator scripts: run_demo, deploy_paid_pilot, guardrail, trial_launch_check, etc.
- Postgres migrations under product path

---

## 4. WHAT IS LAB

- SearchForge RAG: `/api/query`, `/demo`, Qdrant-heavy paths
- `platform_full` API (no `UNIFIED_INTAKE_PRODUCT_ONLY`)
- `RUN_DEMO_LAB=1`, Docker :8000, Makefile.lab
- experiments/, agents/, modules/autotuner/, orchestrators/, pipelines/, engines/
- GPU worker, AutoTuner, Metrics Hub, graph runners
- ~190 regression batteries under `scripts/run_*`
- jobhunter-clipper/, k8s/, mcp/, ml_models/

---

## 5. WHAT IS HISTORICAL

- `docs/archive/sprint_reports/` — 71 sprint reports
- `docs/archive/p7_reports/` — audit/time-slice reports from docs root
- `docs/archive/platform/` — blueprints, TRUSTED_ASSISTANT, FUTURE_SAAS
- `docs/sprints/` — execution archaeology (mostly)
- `docs/archive/README_LEGACY_SEARCHFORGE_LAB.md` — old 1,500-line README
- SearchForge naming in scripts/comments
- JSON case files as dev-only path

---

## 6. WHAT IS OPTIONAL

- Qdrant / embedding for **core intake triage**
- `/demo` RAG page vs workbench
- Local `platform_full` for R&D
- Docker compose full stack
- All lab directories listed above
- Macro blueprint (`UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`) for daily ops
- OpenClaw / agent tooling for product deploy

---

## 7. WHAT FOUNDERS SHOULD IGNORE

- Platform blueprints, investor framing docs
- Makefile.ci, gpu-smoke, autotuner targets
- `start_all.sh`, `dev_local.sh`, port 8011 stack
- docs/sprints/* unless debugging a specific decision
- ~992 archived markdown files
- Repo name "searchforge"

---

## 8. WHAT OPERATORS SHOULD IGNORE

- `GET /ready` (legacy RAG gate)
- Qdrant red when `intake_path_ready:true`
- `deploy_rag_demo.sh`, `deploy_cloud_run_core.sh` as entries
- Lab sidebar routes (hidden in product_only)
- ETF `/api/query` smoke in old scripts
- scripts/lab/* except when explicitly doing R&D

---

## 9. WHAT SUPPORT SHOULD IGNORE

- Triage classification internals, PG schema
- Lab routers, tuner routes, graph endpoints
- Sprint reports and audit archaeology
- Vector collection names unless notice/knowledge ticket
- Multi-tenant / OAuth fantasies in old docs

---

## 10. WHAT NEW ENGINEERS SHOULD IGNORE

- First 60 seconds: **not** the whole repo
- experiments/, agents/, orchestrators/ until assigned lab work
- `docs/archive/platform/*BLUEPRINT*`
- run_* regression batteries (use guardrail first)
- jobhunter-clipper/, k8s/, mcp/
- Rewriting triage.py on day one

**Read instead:** `docs/15_MINUTE_ENGINEER_ONBOARDING.md`

---

## 11. WHAT SHOULD PHYSICALLY MOVE

| Batch | Action | Status |
|-------|--------|--------|
| Docs root collapse | 86 files → `docs/archive/{p7_reports,lab,broker_demo,mvp_era,platform_future}` | ✅ P7 |
| Script tier dirs | `scripts/founder/`, expand `scripts/lab/`, `scripts/archive/` stub | ✅ P7 |
| Lab READMEs | 11 directories self-identify as LAB ONLY | ✅ P7 |
| Sprint dirs | ~38 under `docs/sprints/` → archive | Deferred P8 |
| jobhunter-clipper/ | → `archive/` subtree | Deferred (import risk) |

---

## 12. WHAT SHOULD NEVER MOVE

- `services/fiqa_api/` product paths
- `scripts/run_demo_local.sh`, `deploy_paid_pilot.sh`, guardrail, trial checks (root paths)
- `docs/CURRENT_PRODUCT_SHAPE.md`, runbooks, trial/INDEX
- `configs/demo.env.example` PILOT block
- Postgres migrations
- `tests/test_operator_surface_collapse.py`, deployment profile tests
- `AGENTS.md`, root `README.md`

---

## 13. WHAT MUST NEVER BE BUILT (paid pilot)

OAuth, SSO, RBAC, Stripe, tenant admin UI, fake RLS, workflow engine, event bus, microservices split, multi-region HA, plugin marketplace, "AI operating system" layers.

---

## 14. TOP_50_REMAINING_CONFUSIONS

1. Repo name `searchforge` vs Unified Intake  
2. 477 flat scripts still look equal-priority  
3. Makefile 1,340 lines default help (partially redirected)  
4. Port 8000 vs 8001 vs 8011  
5. `/healthz` vs `/health/live` vs `/healthz` local probe in run_demo  
6. `/ready` vs `/readyz`  
7. `platform_full` sounds like production default  
8. `/demo` listed alongside workbench in ANDY_QUICK_START  
9. Docker compose appears in many old docs  
10. Qdrant feels mandatory from compose file at root  
11. `triage.sh` name collision (moved to lab — still in memory)  
12. Multiple deploy script names  
13. `deploy_cloud_run.sh` legacy  
14. JSON cases vs Postgres truth  
15. DEMO_MODE vs intake_core_readiness  
16. 47 docs at root still many for newcomers  
17. BROKER_* demo docs overlap  
18. trial/ 12+ core specs vs 15-min path  
19. PROJECT_DOC_SYSTEM_MAP still long  
20. UNIFIED_INTAKE_MASTER_OUTLINE vs CURRENT_PRODUCT_SHAPE  
21. Sidebar lab routes in source (hidden not deleted)  
22. ui/ dist includes lab chunks  
23. tests/ mix product + lab  
24. `.runs/` artifact sprawl  
25. poetry + requirements + pyproject  
26. 3 Dockerfiles at root  
27. Chinese Makefile comments  
28. constraints.txt orphan  
29. results/ mixed outputs  
30. configs/ 8 subdirs  
31. retrieval_proxy sibling service  
32. OPENCLAW docs at root (optional tooling)  
33. CHEN_KUI pack vs generic pilot  
34. Simulation assistant vs live intake  
35. Founder vs operator script duplication (intentional wrappers)  
36. scripts/archive/ empty stub — no historical scripts moved  
37. Lab wrappers don't cover all 190 run_* scripts  
38. docs/archive link rot from moves (partial stubs needed)  
39. PRODUCTION_LAUNCH_REPORT moved — canary script writes old path  
40. BROKER_REPORTS_INDEX still indexes hundreds  
41. sprints/ 38 dirs active  
42. VITE_UNIFIED_INTAKE_PRODUCT_ONLY must match API flag  
43. Embedding warming messages on lab path only — easy to miss  
44. Support manifest keys vs intake keys  
45. Cloud Run bare `/healthz` trap  
46. Node 20 vs 22 for UI  
47. `.env` vs `.env.cloudrun` precedence  
48. PILOT_DEPLOY_STRICT optional confusion  
49. Agent entry AGENTS.md vs 15-min doc  
50. Clone still feels "big" despite collapse  

---

## 15. TOP_30_PLATFORM_SMELLS

1. 49 top-level directories  
2. Makefile.lab symlink to giant Makefile  
3. docker-compose.lab.yml + full compose at root  
4. Milvus + Redis + GPU in compose  
5. orchestrators/ + pipelines/ + engines/ trilogy  
6. modules/autotuner/ platform module  
7. Plugin architecture docs in archive but code remains  
8. Graph/langsmith docs (archived) + code paths  
9. jobhunter vertical in same repo  
10. mcp/ + k8s/ infra fantasy dirs  
11. metrics hub / vitals routes  
12. Agent Studio UI chunks  
13. RankerLab / RetrieverLab pages  
14. ETF `/api/query` as historical default test  
15. `make ci` as onboarding trap  
16. start_all SearchForge branding  
17. 453 `.runs/` subdirs  
18. Multiple Dockerfile stories  
19. ecommerce dockerfile at root  
20. Platform inline route leak auditor  
21. Dual poetry/requirements  
22. Hardcoded ~/searchforge in some lab scripts  
23. Sprint report filename patterns at root (fixed P7)  
24. Investor blueprints (archived)  
25. TRUSTED_ASSISTANT naming in old code  
26. simulation_assistant parallel product language  
27. Multi-agent operating model doc (useful but platform-y)  
28. BROKER_REPORTS_INDEX platform scale  
29. UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE length  
30. Repo still cloneable as "everything platform"  

---

## 16. TOP_20_HIGHEST_ROI_REDUCTIONS

| # | Reduction | ROI | Risk |
|---|-----------|-----|------|
| 1 | Docs root 133→47 (P7) | Very high | Low |
| 2 | scripts/lab wrappers + LAB_SCRIPT_INDEX | High | Low |
| 3 | scripts/founder/ discoverability | Med | Low |
| 4 | 15-min engineer onboarding doc | High | Low |
| 5 | Lab directory READMEs (11 dirs) | Med | Low |
| 6 | Archive INDEX honesty | Med | Low |
| 7 | Wire README/AGENTS/OPERATOR_SURFACE | Med | Low |
| 8 | Extend operator_surface tests | Med | Low |
| 9 | Archive docs/sprints/ (~38 dirs) | High | Low |
| 10 | Stub redirects for moved docs (top 10 refs) | Med | Low |
| 11 | Collapse BROKER_DEMO_* to 3 live docs | Med | Low |
| 12 | English Makefile help banner (full rewrite deferred) | Med | Low |
| 13 | scripts/lab wrappers for top 20 run_* | Med | Low |
| 14 | Move jobhunter-clipper to archive/ | Med | Med |
| 15 | docker-compose product-only file | High | Med |
| 16 | Rename repo externally | High | High |
| 17 | ui/ lab route code split | High | Med |
| 18 | .runs/ gitignore + cleanup doc | Med | Low |
| 19 | Single requirements source of truth | Med | Med |
| 20 | trial/ spec collapse to 5 live + archive | Med | Low |

---

## 17. SAFE_BATCH_PLAN

| Batch | Scope | Validation |
|-------|-------|------------|
| **P7-A** | P7 plan + doc root archive | count ≤50; trial_readiness doc refs |
| **P7-B** | Script tiering founder/lab/archive | wrapper exec; LAB banner |
| **P7-C** | Lab READMEs (11 dirs) | test_lab_directories |
| **P7-D** | 15-min onboarding + wire refs | pytest surface |
| **P7-E** | Messaging honesty (banners only) | manual README skim |
| **P7-F** | P7_FINAL_AUDIT + validation suite | full Phase 7 commands |

---

## 18. VALIDATION_PLAN

```bash
python3 -m compileall -q services/fiqa_api
python3 -m compileall -q scripts
PYTHONPATH=. pytest tests/test_operator_surface_collapse.py tests/test_deployment_profile.py -q
bash scripts/guardrail_inbox_triage.sh
bash scripts/trial_readiness_check.sh
bash scripts/trial_launch_check.sh
```

Manual: README first impression, docs/ root count, scripts/{operator,founder,lab}/, archive INDEX, onboarding flow.

---

## 19. ROLLBACK_PLAN

```bash
# Full sprint rollback (if committed as one branch)
git checkout HEAD~1 -- docs/ scripts/ experiments/ agents/ modules/autotuner/ \
  jobhunter-clipper/ orchestrators/ pipelines/ engines/ k8s/ mcp/ ml_models/ \
  README.md AGENTS.md tests/

# Doc archive only
git mv docs/archive/p7_reports/* docs/archive/lab/* docs/archive/broker_demo/* \
  docs/archive/mvp_era/* docs/archive/platform_future/* docs/ 2>/dev/null || true

# Script tier dirs only
rm -rf scripts/founder scripts/archive
git checkout HEAD -- scripts/lab/*.sh scripts/LAB_SCRIPT_INDEX.md 2>/dev/null || true
```

---

*End of P7 plan*
