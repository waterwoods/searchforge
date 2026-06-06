# P8 Deep Isolation Plan — Physical Separation Sprint

**Sprint:** P8_PHYSICAL_DEEP_ISOLATION_SPRINT  
**Authority chain:** `CURRENT_PRODUCT_SHAPE.md` → P7 audit → **this file**  
**Started:** 2026-05-28

**Goal:** Continue transforming the repo from "SearchForge R&D platform warehouse" into "Unified Intake SaaS with optional isolated lab capability" — **physical and psychological separation only**.

---

## Frozen zones (non-negotiable)

- Triage behavior, PG schema, manifest contracts
- Auth/token semantics, `deploy_paid_pilot.sh` semantics
- Production routes, API contracts, Cloud Run deploy behavior

---

## 1. CURRENT TRUE PRODUCT

| Layer | Truth |
|-------|--------|
| **Product** | **Unified Intake** — paste → classify → case → broker workbench |
| **Flagship flow** | Add-car workflow; broker confirms before send |
| **Deployment** | Vercel + Cloud Run + Postgres (`SERVICE_RECORD_DATABASE_URL`) |
| **Auth** | Coarse intake + support API keys |
| **Vectors** | Qdrant optional for core triage |
| **Default local** | `bash scripts/run_demo_local.sh` → product_only on **8001** |
| **Paid pilot** | `UNIFIED_INTAKE_PRODUCT_ONLY=1`, Postgres-primary, `deploy_paid_pilot.sh` |

---

## 2. CURRENT REPO SHAPE (post-P7, pre-P8 deep)

| Area | Count / note |
|------|----------------|
| Repo name | `searchforge` (heritage) vs **Unified Intake** |
| Top-level dirs | ~62 |
| `scripts/` flat | ~477 entries — tiers: operator/, founder/, lab/, deploy/, archive/ |
| `docs/sprints/` visible | **38 dirs** (P8 target: archive all → 7 live .md files) |
| `docs/` root | 50 markdown files (at bound) |
| Docker | `docker-compose.yml` = full lab; `docker-compose.lab.yml` symlink; **no product compose yet** |
| Lab dirs | experiments, agents, autotuner, orchestrators, pipelines, engines, k8s, mcp, ml_models, jobhunter-clipper |

---

## 3. CURRENT PRODUCT PATH

```
README.md → CURRENT_PRODUCT_SHAPE.md → run_demo_local.sh (:8001)
         → workbench/unified-intake
         → guardrail_inbox_triage.sh
         → validate_pilot_deploy_env.py → deploy_paid_pilot.sh
         → trial_launch_check.sh
```

**5 endpoints:** `/health/live`, `/readyz`, `/health`, deployment-manifest, `/api/inbox/triage`

---

## 4. CURRENT LAB PATH

```
RUN_DEMO_LAB=1 run_demo_local.sh  |  docker compose -f docker-compose.lab.yml up
Makefile.lab  |  scripts/lab/* wrappers (LAB ONLY banner)
POST /api/query  |  /demo RAG wedge  |  Qdrant/GPU/Milvus/graph/autotuner
```

---

## 5. WHAT STILL CREATES PLATFORM GRAVITY

1. Repo name `searchforge`
2. ~477 flat scripts at `scripts/` root
3. Full docker-compose at repo root (Milvus, GPU, retrieval-proxy visible on clone)
4. 38 visible sprint dirs under `docs/sprints/`
5. Makefile 59K lines at root
6. `.runs/` 453 subdirs with no README
7. Multiple deploy script names at flat root
8. `platform_full` naming
9. UI lab routes in source (hidden, not removed)
10. BROKER_* docs overlap at docs root

---

## 6. WHAT STILL SCARES FOUNDERS

1. Sprint directory wall on clone
2. docker-compose services list (GPU, Milvus, auto-tuner)
3. Choosing founder_pre_trial vs trial_launch_check
4. `/ready` vs `/readyz` confusion
5. Qdrant red implying outage
6. ~200 shell scripts visible
7. SearchForge strings in lab startup logs
8. Port 8000 vs 8001 vs 8011

---

## 7. WHAT STILL CONFUSES OPERATORS

1. Flat `scripts/` listing
2. Legacy deploy names at root
3. ETF `/api/query` in old CI scripts
4. Multiple health endpoints
5. docker-compose as default mental model
6. Sprint docs mistaken for wiring truth

---

## 8. WHAT STILL CONFUSES NEW ENGINEERS

1. Clone size / directory count
2. experiments/, agents/, orchestrators/ without context
3. docs/sprints/ archaeology
4. run_* regression batteries vs guardrail
5. Dual dependency files (poetry + requirements)
6. When to use Docker vs run_demo_local.sh

---

## 9. WHAT STILL LOOKS LIKE A PLATFORM

1. 62 top-level directories
2. orchestrators/ + pipelines/ + engines/
3. modules/autotuner/ volume
4. k8s/, mcp/, ml_models/
5. retrieval_proxy sibling service
6. GPU worker in compose
7. Makefile.lab → full Makefile
8. Multi-agent operating model doc tone

---

## 10. WHAT SHOULD PHYSICALLY MOVE

| Batch | Action | P8 status |
|-------|--------|-----------|
| Sprint dirs → `docs/archive/sprints/` | git mv 38 dirs | ✅ |
| `docs/sprints/archive/` → `docs/archive/sprints/prior_sprints_archive/` | consolidate | ✅ |
| `scripts/deploy/` wrappers | 6 deploy wrappers | ✅ |
| `scripts/lab/` deeper wrappers | canary, GPU, milvus, graph, autotuner, qdrant | ✅ |
| `docker-compose.product.yml` | minimal product stack | ✅ |
| `results/README.md`, `.runs/README.md` | root dir honesty | ✅ |
| `docs/FOUNDER_LAUNCH_PATH.md` | single founder flow | ✅ |
| `docs/ROOT_DIRECTORY_GUIDE.md` | root convergence | ✅ |
| `scripts/DEEP_SCRIPT_TIER_MAP.md` | tier map | ✅ |

---

## 11. WHAT SHOULD NEVER MOVE

- `services/fiqa_api/inbox_triage/` (product core)
- `deploy_paid_pilot.sh` implementation semantics
- PG migrations, manifest contract code
- Production API route mounting logic
- `configs/demo.env.example` PILOT block
- Live convergence docs at `docs/sprints/*.md` (7 files)
- `docs/trial/` package
- `docs/runbooks/` operator surface

---

## 12. WHAT SHOULD NEVER BE BUILT

OAuth, SSO, RBAC, Stripe, tenant admin UI, fake RLS, workflow engine, event bus, microservices split, multi-region HA, plugin marketplace, "AI operating system" layers.

---

## 13. TOP_50_REMAINING_CONFUSIONS

1. Repo name vs product name  
2. Flat scripts/ implies equal priority  
3. ~180 run_* batteries un-wrapped  
4. Makefile size at root  
5. docker-compose.yml still default-visible full lab  
6. Port 8000/8001/8011  
7. `/healthz` local vs `/health/live` Cloud Run  
8. `/ready` vs `/readyz`  
9. `platform_full` sounds default  
10. ANDY_QUICK_START mentions `/demo`  
11. 50 docs at root (at bound)  
12. BROKER_* overlap  
13. trial/ deep tree  
14. PROJECT_DOC_SYSTEM_MAP length  
15. Moved sprint links may 404  
16. UI lab routes in bundle  
17. `.runs/` sprawl  
18. Dual dependency files  
19. 3 Dockerfiles at root  
20. jobhunter-clipper at root  
21. retrieval_proxy service  
22. OpenClaw docs at root  
23. CHEN_KUI vs generic pilot  
24. Simulation assistant naming  
25. founder vs operator wrapper duplication  
26. scripts/archive/ stub only  
27. Env without PRODUCT_ONLY shows full_stack  
28. Clone size  
29. docker-compose.product.yml not yet canonical in README  
30. compileall scripts fails on pre-existing syntax error  
31. Can still `docker compose up` full lab by accident  
32. deploy scripts at flat root AND deploy/ tier  
33. prior_sprints_archive deep nesting  
34. results/ mixed artifacts  
35. SearchForge in stop_all success message (fixed P8)  
36. start_demo_app.sh port 8001 collides mentally with product 8001  
37. Multiple trial checklist docs  
38. FOUNDER_DEMO_SOP vs FOUNDER_LAUNCH_PATH  
39. Legacy README links to moved sprint paths  
40. tests/ lab + product mixed  
41. configs/ many subdirs  
42. metrics/vitals code paths  
43. LangGraph code (docs archived)  
44. Plugin architecture code  
45. BROKER_REPORTS_INDEX size  
46. UNIFIED_INTAKE_MASTER_OUTLINE length  
47. Multi-agent doc for daily ops  
48. `.qdrant/` at root  
49. `archives/` vs `docs/archive/`  
50. Symlink docker-compose.lab.yml → full stack  

---

## 14. TOP_30_PLATFORM_SMELLS

1. 62 top-level directories  
2. Makefile.lab → 59K Makefile  
3. Full docker-compose at root  
4. orchestrators/ + pipelines/ + engines/  
5. modules/autotuner/  
6. Agent Studio UI chunks  
7. mcp/ + k8s/  
8. metrics/vitals paths  
9. ETF `/api/query` in ci_smoke  
10. GPU worker compose  
11. Milvus etcd/minio trio  
12. retrieval-proxy service  
13. Multiple deploy names  
14. BROKER_REPORTS_INDEX  
15. UNIFIED_INTAKE_MASTER_OUTLINE  
16. Multi-agent operating model  
17. results/ artifacts  
18. configs/ subdirs  
19. tests/ mixed  
20. SearchForge lab script names  
21. auto-tuner compose service  
22. gpu-smoke compose service  
23. graph runners  
24. canary scripts at root  
25. `.runs/` tuner state  
26. experiments/ volume  
27. 3 Dockerfiles  
28. jobhunter-clipper  
29. ml_models/  
30. `.idea/` + `.cache/` visible  

---

## 15. TOP_20_HIGHEST_ROI_NEXT_MOVES

1. ✅ Archive sprint dirs (P8)  
2. ✅ docker-compose.product.yml (P8)  
3. ✅ scripts/deploy/ tier (P8)  
4. ✅ Expand lab wrappers top 10 confusion scripts (P8)  
5. ✅ FOUNDER_LAUNCH_PATH.md (P8)  
6. ✅ ROOT_DIRECTORY_GUIDE.md (P8)  
7. Redirect stubs for top 10 broken doc links  
8. Collapse BROKER_DEMO_* to 3 live + archive  
9. English one-screen Makefile.product help  
10. Move deploy_* flat scripts to print tier banner on invoke  
11. Archive docs root files 51–60 if new files added  
12. `run_canary_full_100.sh` output → results/ not docs/  
13. Symlink `docker-compose.yml` banner only (keep compat)  
14. Test asserting sprint dir count ≤ 0 visible subdirs  
15. CI job using product compose only  
16. `.runs/` gitignore expansion  
17. scripts/run_* top 20 wrappers  
18. Physical `lab/` top-level dir (future — high risk)  
19. Rename repo (founder decision — not P8)  
20. Strip lab chunks from product UI bundle (runtime — out of scope)  

---

## 16. SAFE_BATCH_PLAN

| Phase | Scope | Risk |
|-------|-------|------|
| 0 | Plan doc | None |
| 1 | git mv sprint dirs | Link rot — mitigated by INDEX |
| 2 | Wrapper/stub scripts only | None — exec forwards |
| 3 | New compose file + comments | None — backward compat |
| 4 | README banners only | None |
| 5 | Doc + script header banners | None |
| 6 | Startup log/comment text | None — no semantics |
| 7 | Audit doc | None |
| 8 | Validation suite | Read-only |

---

## 17. VALIDATION_PLAN

```bash
python3 -m compileall -q services/fiqa_api
python3 -m compileall -q scripts   # pre-existing failure OK if unchanged
PYTHONPATH=. pytest tests/test_operator_surface_collapse.py tests/test_deployment_profile.py -q
bash scripts/guardrail_inbox_triage.sh
bash scripts/trial_readiness_check.sh
bash scripts/trial_launch_check.sh
```

Manual: repo root, docs/sprints/, scripts/{operator,lab,deploy}, compose files, founder path.

---

## 18. ROLLBACK_PLAN

```bash
# Full P8 rollback (single commit)
git checkout HEAD~1 -- docs/ scripts/ docker-compose.yml docker-compose.product.yml results/ .runs/

# Sprint archive only
git checkout HEAD~1 -- docs/sprints/ docs/archive/sprints/

# Script tiers only
rm -rf scripts/deploy scripts/lab/run_canary_full_100.sh scripts/lab/wait_for_gpu_ready.sh \
  scripts/lab/gpu_worker_smoke.sh scripts/lab/verify_milvus_lane.sh scripts/lab/graph_verify.sh \
  scripts/lab/autotuner_demo.sh scripts/lab/seed_qdrant.sh scripts/lab/stop_all.sh scripts/lab/health_check.sh
```

---

*End of P8 deep isolation plan*
