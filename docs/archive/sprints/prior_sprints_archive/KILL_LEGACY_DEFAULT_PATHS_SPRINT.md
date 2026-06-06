# Kill Legacy Default Paths Sprint

**Authority:** Execution record for this sprint. **Current runtime truth:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md).  
**Date:** 2026-05-24  
**Principle:** Warnings are not enough. Validators are not enough. Wrong paths become **hard or impossible** in pilot/prod.

---

## Objective

Permanently reduce four recurring legacy risks:

1. `platform_full` default risk  
2. `DEMO_MODE=true` in pilot/prod deploy risk  
3. JSON persistence path surviving in prod  
4. Sprint-doc truth sprawl  

---

## Phase 1 — Discovery maps

### 1. LEGACY_DEFAULT_PATH_MAP

| Wrong default | Where it lived | Symptom | Sprint fix |
|---------------|----------------|---------|------------|
| `platform_full` when `UNIFIED_INTAKE_PRODUCT_ONLY` unset | `deployment_profile.py`, `app_main.py` router registration | Lab/search/tuner routes on public URL | Deploy defaults `PRODUCT_ONLY=1` for paid pilot; validator fails if missing |
| `DEMO_MODE=true` forced in deploy bundle | `deploy_rag_demo.sh` line 285 | `/readyz` lies; prod looks “ready” without deps | Removed from paid-pilot path; validator fails `ENV=prod` + `DEMO_MODE` |
| JSON case writes default on | `service_record_settings.json_case_writes_enabled()` default True | Ephemeral filesystem cases on Cloud Run | Runtime already blocks when `is_production_mode()`; validator + deploy defaults enforce `JSON_CASE_WRITES=0` |
| Optional `PRODUCT_ONLY` in deploy bundle | `deploy_rag_demo.sh` only adds if set in `.env.cloudrun` | Deploy drops product-only even when `.env` has it unset | Paid-pilot path always includes full tuple |
| `PILOT_DEPLOY_STRICT` optional validation | `deploy_rag_demo.sh` | Operators skip validator | Paid-pilot posture **always** validates |
| Sprint docs as SSOT | 115+ files in `docs/sprints/` | Agents copy stale
 env tuples | `CURRENT_PRODUCT_SHAPE.md` + `docs/sprints/README.md` |

### 2. PRODUCT_ONLY_DEFAULT_GAPS

| Gap | Before | After |
|-----|--------|-------|
| Deploy omits `UNIFIED_INTAKE_PRODUCT_ONLY` when unset in `.env.cloudrun` | Cloud Run runs `platform_full` | Paid-pilot deploy defaults to `1` and always passes in bundle |
| Local default | `is_unified_intake_product_only()` → False | Unchanged (local demo OK) |
| Validator | Fails missing product_only | Unchanged |
| Health warnings | `platform_full_api_surface_in_production_like_mode_v1` | Unchanged (still surfaces if misconfigured) |

### 3. DEMO_MODE_RISK_MAP

| Surface | Behavior |
|---------|----------|
| `deploy_rag_demo.sh` | Was **always** `DEMO_MODE=true` → now only on non-paid-pilot cloud demo path |
| `validate_pilot_deploy_env.py` | Failed `ENV=prod` + DEMO_MODE → extended to any paid-pilot signal |
| `health/ready.py` | DEMO_MODE relaxes Qdrant/embedding/GPU blocking — **intentional for local demo only** |
| `deployment_operator_warnings()` | `env_prod_with_demo_mode_truthy_v1` — unchanged |
| `configs/demo.env.example` | Documented deploy auto-set → updated to demo vs paid pilot |
| `docs/CLOUD_RUN_DEPLOYMENT.md`, README | Stale “always DEMO_MODE” — superseded by `CURRENT_PRODUCT_SHAPE.md` |

### 4. JSON_PERSISTENCE_SURVIVAL_MAP

| Path | Prod-like block | Sprint enforcement |
|------|-----------------|-------------------|
| `json_case_writes_enabled()` | Returns False when `is_production_mode()` | Validator requires `JSON_CASE_WRITES=0` |
| Deploy optional PG flags | Only sent if set in `.env.cloudrun` | Paid-pilot path defaults full PG-primary tuple |
| `UNIFIED_INTAKE_CASES_PATH` | Local only | Documented in `CURRENT_PRODUCT_SHAPE.md` |
| Dual-write | Warned in health | Validator rejects `PG_DUAL_WRITE=1` |
| JSON read fallback | Off in prod via `is_production_mode()` | Deploy default `JSON_READ_FALLBACK=0` |

### 5. DOC_TRUTH_SPRAWL_MAP

| Category | Count | Status |
|----------|-------|--------|
| `docs/sprints/*.md` | 115+ | Marked historical via `docs/sprints/README.md` |
| Competing “SSOT” sprint headers | ~15 REAL_SAAS / OPERATIONAL / PRODUCT_ONLY sprints | Historical — `CURRENT_PRODUCT_SHAPE.md` wins |
| Runbooks pointing to stale deploy behavior | DEPLOYMENT_PLAYBOOK, demo.env.example | Updated to reference `CURRENT_PRODUCT_SHAPE.md` |
| `PROJECT_DOC_SYSTEM_MAP.md` | Primary index | Added `CURRENT_PRODUCT_SHAPE.md` |

### 6. TOP_20_RECURRING_CONFUSIONS

1. Sprint doc env tuple ≠ live Cloud Run env  
2. `deploy_rag_demo.sh` name implies “demo” but used for pilot  
3. `DEMO_MODE=true` interpreted as “founder demo” on prod URL  
4. `/readyz` ok=true treated as full RAG ready during DEMO_MODE  
5. Missing `PRODUCT_ONLY` in deploy bundle despite `.env` comment  
6. JSON cases “work” on single Cloud Run instance then vanish  
7. `platform_full` default when flag omitted  
8. Anonymous support routes when keys unset on public URL  
9. `PILOT_DEPLOY_STRICT=1` treated as optional nice-to-have  
10. Secret Manager DB URL not counted unless `CLOUD_RUN_USE_SECRET_MANAGER=1`  
11. CORS errors blamed on triage when `ALLOWED_ORIGINS` drifted  
12. `/healthz` 404 on Cloud Run edge vs app liveness  
13. Vercel `VITE_API_BASE_URL` stale after backend redeploy  
14. Dual-write without DB-primary reads → read-your-writes breaks  
15. `X-Org-Id` treated as tenant IAM  
16. In-memory sessions flag left on with DB URL  
17. `configs/demo.env.example` PILOT block commented out → deploy skips tuple  
18. Multiple “current architecture truth” sprint headers  
19. Local port 8001 vs Cloud Run 8080 env differences  
20. `trial_readiness_check.sh` skips pilot validation when `.env.cloudrun` not prod-like  

### 7. WHY_PREVIOUS_FIXES_DID_NOT_FINISH_THE_JOB

| Prior fix | What it did | Why insufficient |
|-----------|-------------|------------------|
| `pilot_safe_default_profile_v1()` | Documented tuple | Not enforced at deploy — optional `PILOT_DEPLOY_STRICT` |
| `validate_pilot_deploy_env.py` | Exit 1 on bad env | Only when strict flag set; deploy still pushed `DEMO_MODE=true` |
| `deployment_operator_warnings()` | Health/manifest codes | Warnings only — Cloud Run still ran wrong config |
| `is_production_mode()` JSON write block | Runtime guard | Could still deploy without DB URL + without validator |
| Product-only wire closure sprint | Gated platform routes | Default remained `platform_full` when env unset |
| OPERATIONAL_SAAS_HARDENING sprint | Support key + manifest truth | Deploy script unchanged |
| `trial_readiness_check.sh` partial validation | Validates prod-like `.env.cloudrun` | Did not change deploy defaults |

---

## Phase 2 — Implementation summary

| Target | Change |
|--------|--------|
| A. Product-only default | Paid-pilot deploy defaults `UNIFIED_INTAKE_PRODUCT_ONLY=1`; always in bundle |
| B. DEMO_MODE | Not forced on paid-pilot deploy; validator rejects paid-pilot + DEMO_MODE |
| C. PG-only | Deploy defaults PG-primary tuple; validator unchanged (already strict) |
| D. Doc truth | `CURRENT_PRODUCT_SHAPE.md`, `docs/sprints/README.md`, runbook pointers |

---

## Phase 3 — Tests added/updated

- `tests/test_validate_pilot_deploy_env.py` — prod+DEMO_MODE, JSON writes, missing DB  
- `tests/test_deploy_rag_demo_pilot_defaults.py` — deploy script paid-pilot posture  
- `tests/test_current_product_shape_doc.py` — SSOT exists + runbook reference  
- `tests/test_deployment_profile.py` — `pilot_safe_default_profile_v1` (existing)

---

## Phase 4 — Validation commands

```bash
python3 -m compileall -q services/fiqa_api tests
PYTHONPATH=. pytest tests/
bash scripts/guardrail_inbox_triage.sh
PYTHONPATH=. python3 scripts/run_full_regression.py
bash scripts/trial_readiness_check.sh
bash scripts/trial_launch_check.sh
cd ui && npm run build
cd ui && npx --yes madge --circular --extensions ts,tsx src
```

---

## Status

| Phase | Status |
|-------|--------|
| 0 — SSOT | Done |
| 1 — Discovery | Done (maps above) |
| 2 — Implement | Done |
| 3 — Tests | Done |
| 4 — Validation | See final report |
| 5 — Final output | See chat / below |
