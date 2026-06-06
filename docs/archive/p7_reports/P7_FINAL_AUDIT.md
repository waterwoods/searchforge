# P7 Final Audit — Repo Convergence and Lab Tiering

**Sprint:** P7_REPO_CONVERGENCE_AND_LAB_TIERING  
**Date:** 2026-05-28  
**Verdict:** Structural/cognitive refactor **complete** — runtime untouched, lab isolated, product surface clearer.

---

## 1. TOP_30_CONFUSIONS_REMAINING

1. Repo name `searchforge` vs product Unified Intake  
2. ~477 flat scripts still imply equal priority  
3. Only 9 lab wrappers — 180+ `run_*` scripts un-wrapped  
4. Makefile 1,340 lines; `make help` still lab-adjacent  
5. docker-compose at root with Qdrant/Milvus/GPU  
6. Port 8000 / 8001 / 8011  
7. `run_demo_local.sh` probes `/healthz` locally vs `/health/live` on Cloud Run  
8. `/ready` still exists in codebase  
9. `platform_full` naming sounds like default  
10. ANDY_QUICK_START still mentions `/demo` alongside workbench  
11. 49 docs at root — better but still intimidating  
12. BROKER_* docs overlap (10+ kept at root)  
13. trial/ 12 core + 6 launch specs — deep tree  
14. docs/sprints/ ~38 dirs not archived  
15. PROJECT_DOC_SYSTEM_MAP length  
16. Moved docs may break deep links (no redirect stubs)  
17. `run_canary_full_100.sh` writes `docs/PRODUCTION_LAUNCH_REPORT.md` (now archived path)  
18. UI lab routes in source (hidden, not removed)  
19. `.runs/` sprawl  
20. Dual dependency files (poetry + requirements)  
21. 3 Dockerfiles at root  
22. jobhunter-clipper/ still at root  
23. retrieval_proxy sibling service  
24. OpenClaw docs at root (optional tooling)  
25. CHEN_KUI-specific vs generic pilot paths  
26. Simulation assistant naming parallel to product  
27. Founder vs operator wrapper duplication (intentional but subtle)  
28. scripts/archive/ is stub only  
29. Env without PRODUCT_ONLY shows `full_stack` in readiness (honest but scary)  
30. Clone size / directory count still "platform scale"  

---

## 2. TOP_20_PLATFORM_SMELLS_REMAINING

1. 49 top-level directories  
2. Makefile.lab → full Makefile  
3. Full docker-compose complexity  
4. orchestrators/ + pipelines/ + engines/  
5. modules/autotuner/ code volume  
6. Agent Studio / RankerLab UI chunks  
7. mcp/ + k8s/ directories  
8. metrics/vitals code paths  
9. ETF `/api/query` in old CI scripts  
10. GPU worker compose service  
11. Plugin architecture code (docs archived)  
12. LangGraph code paths (docs archived)  
13. Multiple deploy script names  
14. BROKER_REPORTS_INDEX hundreds of entries  
15. UNIFIED_INTAKE_MASTER_OUTLINE length  
16. Multi-agent operating model doc tone  
17. results/ mixed artifacts  
18. configs/ many subdirs  
19. tests/ lab + product mixed  
20. SearchForge strings in lab scripts  

---

## 3. WHAT_BECAME_SIMPLER

- **docs/ root:** 133 → **49** markdown files (target ≤50 met)  
- **Script tiers:** `operator/` (10), `founder/` (3), `lab/` (9 wrappers + index)  
- **Engineer onboarding:** single `15_MINUTE_ENGINEER_ONBOARDING.md`  
- **Archive INDEX:** P7 subdirs documented  
- **Lab dirs:** 11 READMEs with consistent LAB ONLY banners  
- **Tests:** doc root bound, lab READMEs, founder/lab wrappers enforced  

---

## 4. WHAT_BECAME_MORE_HONEST

- Lab wrappers print **LAB ONLY — not part of Unified Intake paid pilot path**  
- `trial_readiness_check.sh` banner states workbench-first product identity  
- README engineer path points to 15-min doc, not entire repo  
- AGENTS.md leads with onboarding doc  
- OPERATOR_SURFACE documents script tiers and LAB_SCRIPT_INDEX  
- Archive INDEX states CURRENT_PRODUCT_SHAPE wins over archaeology  
- Lab directory READMEs state product_only mount status explicitly  

---

## 5. WHAT_BECAME_MORE_PRODUCT_LIKE

- README first impression unchanged (already good from P6) — reinforced engineer path  
- docs root no longer dominated by sprint reports and platform blueprints  
- Physical `scripts/operator/` and `scripts/founder/` grouping  
- Onboarding collapses engineer path to 10 scripts, 10 docs, 5 endpoints  
- OPERATOR_SURFACE engineer path = 15 min doc + guardrail  

---

## 6. WHAT_STILL_FEELS_LIKE_A_PLATFORM

- Repo size and top-level directory count  
- Makefile + docker-compose as first-class citizens at root  
- Lab code co-located with product (READMEs only — no physical split)  
- ui/ bundle still contains lab lazy chunks  
- ~190 regression scripts at flat `scripts/` level  

---

## 7. WHAT_STILL_WASTES_FOUNDER_ENERGY

- Choosing between founder_pre_trial vs trial_launch_check (documented but repetitive)  
- BROKER_DEMO_* doc overlap at root  
- trial/ spec depth vs 15-min path  
- Env posture showing `full_stack` when `.env` lacks PRODUCT_ONLY  
- Qdrant optional truth repeated in many places (necessary until single banner everywhere)  

---

## 8. WHAT_STILL_SCARES_OPERATORS

- Flat scripts/ directory listing  
- docker-compose services visible at clone  
- `/ready` endpoint still live in API  
- Multiple health endpoint names  
- deploy_rag_demo.sh name at scripts root (wrapper in lab/ only)  

---

## 9. WHAT_FOUNDERS_SHOULD_IGNORE

Platform blueprints, docs/archive/p7_reports, Makefile.ci, start_all/dev_local, docs/sprints archaeology, jobhunter-clipper, ~992 archive markdown files.

---

## 10. WHAT_OPERATORS_SHOULD_IGNORE

GET /ready, Qdrant red with intake_path_ready:true, scripts/lab/*, deploy_rag_demo as entry, lab UI routes, ETF smoke scripts.

---

## 11. WHAT_SUPPORT_SHOULD_IGNORE

Triage internals, PG schema, lab routers, sprint reports, vector collection archaeology, platform blueprints.

---

## 12. WHAT_NEW_ENGINEERS_SHOULD_IGNORE

experiments/, agents/, orchestrators/ until assigned; run_* batteries; archive platform docs; rewriting triage.py day one. **Read:** `15_MINUTE_ENGINEER_ONBOARDING.md`.

---

## 13. THE_10_SCRIPTS_THAT_MATTER

run_demo_local.sh, deploy_paid_pilot.sh, validate_pilot_deploy_env.py, guardrail_inbox_triage.sh, trial_launch_check.sh, trial_readiness_check.sh, summarize_readiness_posture.sh, summarize_support_posture.sh, restore_8001_readiness.sh, demo_pre_checklist.sh

---

## 14. THE_10_DOCS_THAT_MATTER

AGENTS.md, CURRENT_PRODUCT_SHAPE.md, 15_MINUTE_ENGINEER_ONBOARDING.md, OPERATOR_CHEAT_SHEET.md, OPERATOR_IGNORE_LIST.md, DEPLOY_TRUTH_MAP.md, SUPPORT_TRUTH_MAP.md, ANDY_QUICK_START.md, insurance_paid_pilot_goal.md, trial/INDEX.md

---

## 15. THE_5_ENDPOINTS_THAT_MATTER

/health/live, /readyz, /health, GET /api/inbox/support/deployment-manifest, POST /api/inbox/triage

---

## 16. WHAT_MUST_NEVER_BE_BUILT

OAuth, SSO, RBAC, Stripe, tenant admin, fake RLS, workflow engine, event bus, microservices split, multi-region HA, plugin marketplace, AI OS layers.

---

## 17. SAFEST_NEXT_BATCH (P8 recommendation)

1. Archive `docs/sprints/` (~38 dirs) → `docs/archive/sprints/`  
2. Redirect stubs for top 10 moved doc paths  
3. Expand `scripts/lab/` wrappers for top 20 `run_*` batteries  
4. Collapse BROKER_DEMO_* root docs to 3 live + archive rest  
5. `run_canary_full_100.sh` write path → archive or results/  
6. English Makefile help one-screen product redirect  
7. Optional docker-compose.product.yml physical split  

---

## 18. FINAL_VERDICT

**P7 succeeded** at its stated goal: reduce psychological platform gravity without deleting R&D or changing runtime semantics. Docs root and script tiers are materially clearer. Lab is labeled, not removed. Validation suite green (except pre-existing `run_demo_pack_original.py` syntax error blocking full `compileall scripts`).

---

## 19. FINAL_ONE_LINE

**Unified Intake is now readable at the front door; SearchForge lab is still in the building but has name tags on the doors.**

---

## Validation results (Phase 7)

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api` | **PASS** |
| `python3 -m compileall -q scripts` | **FAIL** (pre-existing: `run_demo_pack_original.py` SyntaxError — not introduced by P7) |
| `pytest test_operator_surface_collapse + test_deployment_profile` | **PASS** (27 tests) |
| `guardrail_inbox_triage.sh` | **PASS** |
| `trial_readiness_check.sh` | **PASS** |
| `trial_launch_check.sh` | **PASS** |
| docs/ root count | **49** (≤50) |
| scripts/operator/ | 10 wrappers |
| scripts/founder/ | 3 wrappers |
| scripts/lab/ | 9 wrappers + LAB_SCRIPT_INDEX |

---

## Rollback commands

```bash
# Full P7 rollback (if single commit)
git checkout HEAD~1 -- docs/ scripts/ experiments/ agents/ modules/autotuner/ \
  jobhunter-clipper/ orchestrators/ pipelines/ engines/ k8s/ mcp/ ml_models/ \
  README.md AGENTS.md tests/

# Doc archive only — move back from P7 archive subdirs
for d in p7_reports lab broker_demo mvp_era platform_future; do
  git mv docs/archive/$d/*.md docs/ 2>/dev/null || true
done

# Script tiers only
rm -rf scripts/founder scripts/archive
git checkout HEAD -- scripts/lab/*.sh scripts/LAB_SCRIPT_INDEX.md scripts/lab/README.md 2>/dev/null || true
```

---

*End of P7 final audit*
