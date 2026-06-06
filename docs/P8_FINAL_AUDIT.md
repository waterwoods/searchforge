# P8 Final Audit — Deep Physical Isolation Sprint

**Sprint:** P8_PHYSICAL_DEEP_ISOLATION_SPRINT  
**Date:** 2026-05-28  
**Verdict:** Deep structural/cognitive separation **complete** — runtime untouched, lab further isolated, founder path collapsed.

---

## 1. TOP_30_CONFUSIONS_REMAINING

1. Repo name `searchforge` vs Unified Intake  
2. ~477 flat scripts still at root (tiers help discovery, not listing)  
3. ~170 `run_*` batteries without lab wrappers  
4. Makefile 59K lines at root  
5. Full docker-compose.yml still default-visible (product compose added but not default)  
6. Port 8000 / 8001 / 8011  
7. `run_demo_local.sh` probes `/healthz` locally vs `/health/live` on Cloud Run  
8. `/ready` still exists in API  
9. `platform_full` naming  
10. 50 docs at root (at bound after P6/P7 archive)  
11. BROKER_* doc overlap (10+ at root)  
12. trial/ deep tree (20 specs)  
13. Moved sprint links may 404 in old docs  
14. UI lab routes in source (hidden)  
15. `.runs/` 453 subdirs (README added)  
16. Dual dependency files  
17. 3 Dockerfiles at root  
18. jobhunter-clipper at root  
19. retrieval_proxy sibling  
20. start_demo_app.sh also uses port 8001 (lab legacy)  
21. founder vs operator wrapper duplication  
22. Env without PRODUCT_ONLY shows full_stack  
23. Clone size / directory count  
24. prior_sprints_archive deep nesting  
25. CHEN_KUI-specific vs generic paths  
26. Simulation assistant naming  
27. FOUNDER_DEMO_SOP vs FOUNDER_LAUNCH_PATH  
28. compileall scripts pre-existing SyntaxError  
29. deploy scripts at flat root AND deploy/ tier  
30. `archives/` vs `docs/archive/` naming  

---

## 2. TOP_20_PLATFORM_SMELLS_REMAINING

1. 62 top-level directories  
2. Makefile.lab → full Makefile  
3. Full docker-compose at root  
4. orchestrators/ + pipelines/ + engines/  
5. modules/autotuner/ volume  
6. Agent Studio UI chunks  
7. mcp/ + k8s/  
8. GPU/Milvus in compose  
9. retrieval-proxy service  
10. Multiple deploy names at flat root  
11. BROKER_REPORTS_INDEX size  
12. UNIFIED_INTAKE_MASTER_OUTLINE length  
13. Multi-agent operating model tone  
14. results/ mixed artifacts  
15. configs/ subdirs  
16. tests/ lab + product mixed  
17. SearchForge strings in some lab scripts  
18. auto-tuner compose service  
19. canary scripts at flat root  
20. `.qdrant/` at repo root  

---

## 3. WHAT_BECAME_SIMPLER

- **docs/sprints/ visible dirs:** 38 → **0** (7 live .md files only)  
- **Script tiers:** added `deploy/` (6) + 9 new `lab/` wrappers  
- **Founder path:** single `FOUNDER_LAUNCH_PATH.md`  
- **Root guide:** `ROOT_DIRECTORY_GUIDE.md` for clone-time orientation  
- **Docker:** `docker-compose.product.yml` minimal product stack  
- **Tier map:** `DEEP_SCRIPT_TIER_MAP.md` documents all tiers  

---

## 4. WHAT_BECAME_MORE_HONEST

- Lab startup logs (`dev_local.sh`, `start_all.sh`, `stop_all.sh`, `health_check.sh`) state LAB ONLY + product redirect  
- `start_demo_app.sh` banner clarifies not default product launcher  
- Sprint archive INDEX states CURRENT_PRODUCT_SHAPE wins  
- `results/README.md` and `.runs/README.md` explain ignore rules  
- Deploy wrappers print `deploy_paid_pilot.sh` guidance  
- Founder/trial scripts reference `FOUNDER_LAUNCH_PATH.md`  

---

## 5. WHAT_BECAME_MORE_PRODUCT_LIKE

- Visible sprint archaeology removed from `docs/sprints/`  
- Product docker compose option without GPU/Milvus/retrieval-proxy  
- README founder path → FOUNDER_LAUNCH_PATH  
- trial/INDEX points to canonical founder doc  
- scripts/README lists deploy tier  

---

## 6. WHAT_STILL_FEELS_LIKE_A_PLATFORM

- Repo size and top-level directory count  
- Makefile + full docker-compose as root citizens  
- Lab code co-located (READMEs only)  
- ui/ bundle lab lazy chunks  
- ~190 regression scripts at flat level  

---

## 7. WHAT_STILL_WASTES_FOUNDER_ENERGY

- BROKER_DEMO_* overlap at docs root  
- trial/ spec depth vs 15-min path  
- Env showing full_stack without PRODUCT_ONLY  
- Qdrant optional truth repeated in many places  
- Choosing between similar checklist docs  

---

## 8. WHAT_STILL_SCARES_OPERATORS

- Flat scripts/ listing length  
- Full docker-compose services visible  
- `/ready` endpoint still live  
- Multiple health endpoint names  
- Legacy deploy names at scripts root  

---

## 9. WHAT_FOUNDERS_SHOULD_IGNORE

Platform blueprints, docs/archive/sprints/, Makefile.ci, start_all/dev_local, jobhunter-clipper, ~992 archive markdown, full docker-compose service list.

---

## 10. WHAT_OPERATORS_SHOULD_IGNORE

GET /ready, Qdrant red with intake_path_ready:true, scripts/lab/*, legacy deploy as entry, lab UI routes, ETF smoke.

---

## 11. WHAT_SUPPORT_SHOULD_IGNORE

Triage internals, PG schema, lab routers, sprint reports, vector archaeology, platform blueprints.

---

## 12. WHAT_NEW_ENGINEERS_SHOULD_IGNORE

experiments/, agents/, orchestrators/ until assigned; run_* batteries; archive platform docs; rewriting triage.py day one.

---

## 13. THE_10_SCRIPTS_THAT_MATTER

run_demo_local.sh, deploy_paid_pilot.sh, validate_pilot_deploy_env.py, guardrail_inbox_triage.sh, trial_launch_check.sh, trial_readiness_check.sh, summarize_readiness_posture.sh, summarize_support_posture.sh, restore_8001_readiness.sh, demo_pre_checklist.sh

---

## 14. THE_10_DOCS_THAT_MATTER

AGENTS.md, CURRENT_PRODUCT_SHAPE.md, 15_MINUTE_ENGINEER_ONBOARDING.md, FOUNDER_LAUNCH_PATH.md, OPERATOR_CHEAT_SHEET.md, OPERATOR_IGNORE_LIST.md, DEPLOY_TRUTH_MAP.md, SUPPORT_TRUTH_MAP.md, insurance_paid_pilot_goal.md, trial/INDEX.md

---

## 15. THE_5_ENDPOINTS_THAT_MATTER

/health/live, /readyz, /health, GET /api/inbox/support/deployment-manifest, POST /api/inbox/triage

---

## 16. WHAT_MUST_NEVER_BE_BUILT

OAuth, SSO, RBAC, Stripe, tenant admin, fake RLS, workflow engine, event bus, microservices, multi-region HA, plugin marketplace, AI OS layers.

---

## 17. SAFEST_NEXT_BATCH (P9 recommendation)

1. Collapse BROKER_DEMO_* root docs → 3 live + archive  
2. Top 20 `run_*` lab wrappers  
3. Redirect stubs for broken sprint links  
4. Test asserting docs/sprints has zero subdirs  
5. Makefile.product one-screen help  
6. Move P8 plan to archive after P9 starts  

---

## 18. NEXT_30_DAY_CONVERGENCE_PATH

Week 1: BROKER doc collapse + link stubs  
Week 2: run_* wrapper batch + Makefile.product  
Week 3: First broker trial using FOUNDER_LAUNCH_PATH only  
Week 4: P9 audit — consider physical lab/ top-level (high risk, defer if trial active)  

---

## 19. FINAL_VERDICT

**P8 succeeded** at deep physical isolation without runtime changes. Sprint archaeology is archived. Script/deploy/docker tiers clarify product vs lab. Founder path is one document. Validation should remain green except pre-existing compileall failure.

---

## 20. FINAL_ONE_LINE

**Unified Intake owns the front door; SearchForge lab is in the basement with a map on the wall.**

---

## Phase batch summaries

### Phase 1 — Sprint archive

| Field | Value |
|-------|-------|
| ROOT_CAUSE | 38 visible sprint dirs created archaeology gravity |
| HUMAN_IMPACT | Founders/engineers mistook sprints for wiring truth |
| WHY_HIGH_ROI | Zero runtime risk; immediate visual relief |
| WHY_SAFE | git mv only; INDEX + README updated |
| FILES_CHANGED | 38 dirs → docs/archive/sprints/; INDEX.md; sprints/README.md |
| VALIDATION | Manual ls docs/sprints/ |
| ROLLBACK | git checkout HEAD~1 -- docs/sprints/ docs/archive/sprints/ |

### Phase 2 — Script tiering

| Field | Value |
|-------|-------|
| ROOT_CAUSE | Flat scripts/ implied equal priority |
| FILES_CHANGED | scripts/deploy/* (6), scripts/lab/* (+9), DEEP_SCRIPT_TIER_MAP.md |
| WHAT_DID_NOT_CHANGE | Root script implementations |
| VALIDATION | Wrapper exec forwards; lab banner grep |

### Phase 3 — Docker split

| Field | Value |
|-------|-------|
| ROOT_CAUSE | Root compose looked like research cluster |
| FILES_CHANGED | docker-compose.product.yml; docker-compose.yml banner |
| WHAT_DID_NOT_CHANGE | docker-compose.yml services; lab symlink |
| ROLLBACK | rm docker-compose.product.yml |

### Phase 4 — Root convergence

| Field | Value |
|-------|-------|
| FILES_CHANGED | results/README.md, .runs/README.md, ROOT_DIRECTORY_GUIDE.md |
| WHAT_DID_NOT_CHANGE | Lab directory code |

### Phase 5 — Founder collapse

| Field | Value |
|-------|-------|
| FILES_CHANGED | FOUNDER_LAUNCH_PATH.md; trial/INDEX; script headers |
| WHAT_DID_NOT_CHANGE | founder_pre_trial_checklist.sh behavior |

### Phase 6 — Startup honesty

| Field | Value |
|-------|-------|
| FILES_CHANGED | dev_local.sh, start_all.sh, stop_all.sh, health_check.sh, start_demo_app.sh |
| WHAT_DID_NOT_CHANGE | Runtime semantics, ports, env |

---

## Validation results (Phase 8)

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api` | **PASS** |
| `python3 -m compileall -q scripts` | **FAIL** (pre-existing: `run_demo_pack_original.py` SyntaxError — unchanged) |
| `pytest test_operator_surface_collapse + test_deployment_profile` | **PASS** (27 tests) |
| `guardrail_inbox_triage.sh` | **PASS** (after battery path fix for archived sprints) |
| `trial_readiness_check.sh` | **PASS** |
| `trial_launch_check.sh` | **PASS** |
| docs/ root count | **50** (≤50 bound) |
| docs/sprints/ visible subdirs | **0** (7 live .md files) |
| Sprint dirs archived (P8) | **38** |
| scripts/deploy/ | 6 wrappers |
| scripts/lab/ | 18 wrappers |
| docker-compose.product.yml | created |

**Post-archive fix:** Guardrail battery scripts updated to `docs/archive/sprints/` paths (path only — no triage change).

---

## Rollback commands

```bash
# Full P8 rollback
git checkout HEAD~1 -- docs/ scripts/ docker-compose.yml docker-compose.product.yml \
  results/README.md .runs/README.md README.md

# Sprint archive only
git checkout HEAD~1 -- docs/sprints/ docs/archive/sprints/

# Script tiers only
rm -rf scripts/deploy
git checkout HEAD~1 -- scripts/lab/run_canary_full_100.sh scripts/lab/wait_for_gpu_ready.sh \
  scripts/lab/gpu_worker_smoke.sh scripts/lab/verify_milvus_lane.sh scripts/lab/graph_verify.sh \
  scripts/lab/autotuner_demo.sh scripts/lab/seed_qdrant.sh scripts/lab/stop_all.sh \
  scripts/lab/health_check.sh scripts/LAB_SCRIPT_INDEX.md scripts/DEEP_SCRIPT_TIER_MAP.md
```

---

*End of P8 final audit*
