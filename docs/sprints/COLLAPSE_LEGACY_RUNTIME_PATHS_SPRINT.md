# Collapse Legacy Runtime Paths Sprint

**Status:** Executed (2026-05-24)  
**Authority:** This sprint record. **Current runtime truth:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) — when they differ, CURRENT_PRODUCT_SHAPE wins.

**Goal:** Stop carrying two products, two persistence models, and two deployment realities inside one pilot SaaS runtime.

**Philosophy:** Delete ambiguity before adding capability.

---

## Phase 0 — SSOT

| Artifact | Role |
|----------|------|
| This file | Sprint execution record + discovery maps |
| `docs/CURRENT_PRODUCT_SHAPE.md` | Operator-facing current truth (updated) |
| `docs/sprints/README.md` | Sprint docs = historical |

---

## Phase 1 — Deep discovery

### 1. LEGACY_RUNTIME_BRANCH_MAP

| Fork | Branch A | Branch B | Detection | Collapse action (this sprint) |
|------|----------|----------|-----------|-------------------------------|
| Cloud deploy | Paid pilot (PG + product_only) | Demo cloud (DEMO_MODE) | `_is_paid_pilot_posture()` in `deploy_rag_demo.sh` | **Split entry:** `deploy_paid_pilot.sh` vs `deploy_demo_cloud_smoke.sh` |
| Local runtime | `run_demo_local.sh` :8001 | Docker `rag-api` :8000 | Port/docs | Documented in RUNTIME_PATH_STANDARD; unchanged |
| Persistence | Postgres-primary | JSON case file | `service_record_settings.py` flags | Validator rejects JSON writes/fallback on pilot; code labeled legacy/dev |
| API surface | `product_only` | `platform_full` | `UNIFIED_INTAKE_PRODUCT_ONLY` | Paid deploy forces `=1`; warnings remain |
| Readiness | Honest `/readyz` | Relaxed DEMO_MODE | `DEMO_MODE` env | Paid path never sets DEMO_MODE |
| Operator docs | CURRENT_PRODUCT_SHAPE | ~100+ sprint docs | README + headers | Pointers from runbooks/readiness; archive list below |

### 2. DEMO_VS_PILOT_RUNTIME_DIFF

| Dimension | Local founder demo | Demo cloud smoke | Paid pilot Cloud Run |
|-----------|-------------------|------------------|----------------------|
| Entry | `run_demo_local.sh` | `deploy_demo_cloud_smoke.sh` | `deploy_paid_pilot.sh` |
| DEMO_MODE | Often unset locally | **true** (injected) | **never** |
| PRODUCT_ONLY | Optional locally | Optional (unset by wrapper) | **required (1)** |
| Cases | JSON OK without DB | JSON-primary unless .env sets PG | Postgres-only |
| API keys | Optional locally | Often missing | **required** (validator) |
| `/readyz` | May relax if DEMO_MODE | Relaxed | Full honesty |
| CORS | Permissive if unset | Permissive fallback risk | Must set ALLOWED_ORIGINS |

### 3. JSON_SURVIVAL_DEPENDENCY_MAP

| Component | JSON role | Still needed? |
|-----------|-----------|---------------|
| `case_store.py` | Writes `unified_intake_cases.json` when `json_case_writes_enabled()` | **Local dev only** |
| `case_truth_repository.py` | Read fallback when `json_read_fallback_allowed()` | **Transition/dev** — off in pilot |
| `service_record_settings.json_case_writes_enabled()` | Gate | Production forces off via `is_production_mode()` |
| `UNIFIED_INTAKE_CASES_PATH` | Path override | Local demo |
| `deploy_rag_demo.sh` non-pilot branch | Passes optional JSON flags from .env | Demo cloud only |
| Tests / guardrails | Fixture cases | Keep |

**Paid pilot:** validator now requires `JSON_CASE_WRITES=0`, `JSON_READ_FALLBACK=0`, `DB_PRIMARY_READS=1`.

### 4. PLATFORM_FULL_DEPENDENCY_MAP

| Area | Behavior when PRODUCT_ONLY off |
|------|-------------------------------|
| `app_main.py` | Mounts extra routers; logs OPERATIONAL_RISK in prod-like |
| `platform_inline_routes.py` | Lab/RAG/tuner inline routes registered |
| `deployment_profile.py` | `deployment_profile=platform_full` banner; warning `platform_full_api_surface_in_production_like_mode_v1` |
| Docs / muscle memory | “SearchForge demo” mental model | **Misleading for broker pilot** |

**Remaining implicit platform_full assumptions:** README examples using `/api/query`; deploy output still prints ETF query curl; old sprint deploy reports.

### 5. CURRENT_TRUTH_VS_OLD_DOC_CONTRADICTIONS

| Old doc / pattern | Says | Current truth |
|-------------------|------|---------------|
| Many sprint deploy reports | `deploy_rag_demo.sh` is THE path | Use `deploy_paid_pilot.sh` for brokers |
| `deploy_and_verify_cloud_run.sh` (pre-fix) | Always `DEMO_MODE=true` then deploy | Now calls `deploy_demo_cloud_smoke.sh` |
| `configs/demo.env.example` header (old) | `bash scripts/deploy_rag_demo.sh` | Points to paid vs demo wrappers |
| KILL_LEGACY sprint | Partially done | This sprint completes deploy identity split |
| `docs/CLOUD_RUN_DEPLOYMENT.md` (if exists) | May say always DEMO_MODE | Superseded by CURRENT_PRODUCT_SHAPE |
| Sprint “REAL_SAAS” headers claiming SSOT | Competing north stars | CURRENT_PRODUCT_SHAPE wins |

### 6. TOP_30_RUNTIME_AMBIGUITIES

1. Script name `deploy_rag_demo.sh` sounds demo but used for pilot  
2. Single script auto-detects posture — tired founder skips `.env` tuple  
3. `deploy_and_verify_cloud_run.sh` forced DEMO_MODE before deploy  
4. `.env.cloudrun` can have prod flags without PILOT_DEPLOY_STRICT  
5. Optional PRODUCT_ONLY in demo cloud branch  
6. SERVICE_RECORD_DATABASE_URL optional on demo cloud deploy bundle  
7. ALLOWED_ORIGINS omitted → permissive CORS  
8. Secret Manager vs plaintext QDRANT preflight confusion  
9. Two Cloud Run URLs (a.run.app vs regional) vs Vercel VITE_API_BASE_URL  
10. Port 8000 Docker vs 8001 local  
11. `ENV=prod` without PRODUCT_ONLY still starts (warns only)  
12. Dual-write flag still documented in demo.env.example comments  
13. JSON path default `data/demo_cases.json` on laptop  
14. In-memory sessions flag vs DB URL  
15. Intake vs support key optional locally, required for pilot  
16. Broker token HMAC optional complexity in same env file  
17. WeChat OAuth vars mixed with pilot tuple  
18. `platform_full` still default when flag unset  
19. `/healthz` vs `/health/live` on Cloud Run  
20. `/readyz` ok:false still “normal” in some runbooks  
21. Qdrant required in deploy script even for intake-only pilot  
22. `CLIENT_ID` default pack confusion  
23. Multiple “SSOT” sprint markdown files  
24. `PROJECT_TRUTH_SWITCH.md` vs CURRENT_PRODUCT_SHAPE  
25. `deploy_cloud_run.sh` legacy mortgage-agent name  
26. Trial readiness SKIP when no .env.cloudrun  
27. Founder may source `.env.cloudrun` in `run_demo_local.sh` accidentally  
28. GSM deploy without local QDRANT key skips preflight silently  
29. Auto-detect paid pilot if only one flag set in .env  
30. Release playbook still mentioned deploy_rag_demo in places (fixed partially)

### 7. TOP_20_SUPPORT_CONFUSIONS

1. “Cases disappeared” — JSON vs PG instance  
2. CORS empty workbench — ALLOWED_ORIGINS drift  
3. 401 on workbench — missing intake API key after pilot deploy  
4. Support export 401 — support key not configured  
5. `/readyz` red but demo “works” — DEMO_MODE off, Qdrant cold  
6. Wrong API URL in Vercel — two URL shapes  
7. “Deployed but old behavior” — revision not traffic target (rare)  
8. Office filter empty — case_office_enforcement without X-Org-Id  
9. Dual-write thought enabled — only one path actually writing  
10. platform_full endpoints in docs broker shouldn’t see  
11. Session lost on second instance — in-memory sessions  
12. Secret rotation without redeploy  
13. Confusion between demo queue JSON and live PG cases  
14. Broker token “unbound” warning ignored  
15. Intake key equals support key warning  
16. Thinking DEMO_MODE means “demo tenant” in prod  
17. Postgres URL in plaintext env visible to GCP viewers  
18. Simulation assistant vs live triage difference  
19. Client pack `chen_kui` vs `socal_precision`  
20. Health 404 on `/healthz` — operator tests wrong path  

### 8. TOP_20_FOUNDATION_SIMPLIFICATIONS (done or queued)

| # | Simplification | Status |
|---|----------------|--------|
| 1 | `deploy_paid_pilot.sh` entry | **Done** |
| 2 | `deploy_demo_cloud_smoke.sh` entry | **Done** |
| 3 | Validator: DEMO_MODE, JSON writes, JSON fallback, DB reads | **Done** |
| 4 | CURRENT_PRODUCT_SHAPE persistence + platform_full sections | **Done** |
| 5 | Legacy comments on JSON settings | **Done** |
| 6 | Trial readiness checks deploy entry + SSOT | **Done** |
| 7 | Runbooks point to CURRENT_PRODUCT_SHAPE | **Done** |
| 8 | deploy_and_verify uses demo wrapper only | **Done** |
| 9 | Tests for entry scripts | **Done** |
| 10 | Sprint README historical banner | Exists |
| 11 | Deprecate direct `deploy_rag_demo.sh` in operator docs | **Done** |
| 12 | Flip default PRODUCT_ONLY at import | **Deferred** (blast radius) |
| 13 | Delete JSON code paths | **Deferred** |
| 14 | Rename `deploy_rag_demo.sh` → `deploy_cloud_run_core.sh` | **Later** |
| 15 | Remove `/api/query` from deploy success output | **Later** |
| 16 | Require ALLOWED_ORIGINS in paid validator | **Later** |
| 17 | Archive sprint doc batch | List below |
| 18 | Delete `deploy_cloud_run.sh` | **Later** |
| 19 | Single port standard everywhere | **Later** |
| 20 | Auto-fail startup if prod-like without PRODUCT_ONLY | **Later** |

### 9. WHY_OLD_PATHS_KEEP_SURVIVING

- **Name inertia:** `deploy_rag_demo`, `demo.env.example`, DEMO_MODE “worked” for smoke tests  
- **Fear of breaking local demo:** JSON and platform_full kept as escape hatches  
- **Sprint doc archaeology:** Each sprint added truth; none removed old commands  
- **Auto-detect posture:** Feels flexible but hides wrong deploy at 2AM  
- **Qdrant/RAG heritage:** Insurance product still carries SearchForge deploy trappings  
- **No failing validator until recently:** Misconfig was warn-only in logs  

### 10. WHAT_CAN_BE_COLLAPSED_NOW_SAFELY

| Change | Safe because |
|--------|--------------|
| Deploy wrapper split | Core script unchanged; wrappers only export env |
| Stricter validator | Only blocks prod-like .env / explicit pilot path |
| Doc pointer updates | No runtime change |
| Comments on JSON | No behavior change |
| trial_readiness file checks | Additive |

**Not safe yet:** Default PRODUCT_ONLY=1 globally; delete JSON modules; rename core deploy script in CI.

---

## Phase 2 — Implemented reductions

### A. Deploy split

- `scripts/deploy_paid_pilot.sh` — forces paid tuple, `unset DEMO_MODE`, runs validator via core  
- `scripts/deploy_demo_cloud_smoke.sh` — `DEMO_MODE=true`, unsets pilot strict flags  
- `scripts/deploy_rag_demo.sh` — shared implementation; header points to wrappers  

### B. JSON → legacy/dev labeling

- `service_record_settings.py` module + `json_case_writes_enabled` docstrings  
- `CURRENT_PRODUCT_SHAPE.md` persistence truth section  
- Validator rejects JSON writes + read fallback for pilot  

### C. product_only convergence

- `deploy_paid_pilot.sh` exports `UNIFIED_INTAKE_PRODUCT_ONLY=1`  
- `deployment_profile.py` module doc clarifies platform_full = legacy/dev  

### D. Sprint-doc simplification

**Structure proposal:**

```
docs/
  CURRENT_PRODUCT_SHAPE.md     ← operator SSOT
  sprints/
    README.md                  ← historical banner + archive index
    COLLAPSE_LEGACY_RUNTIME_PATHS_SPRINT.md
    archive/                   ← future: move completed sprint dirs here
```

**Recommended archive list (move, do not delete):**  
Sprint dirs/files that are pure execution reports superseded by CURRENT_PRODUCT_SHAPE:

- `docs/sprints/KILL_LEGACY_DEFAULT_PATHS_SPRINT.md` (superseded by this sprint)  
- `docs/sprints/PILOT_TO_REAL_SAAS_TRANSITION_SPRINT.md`  
- `docs/sprints/archive/PRODUCT_ONLY_SAAS_SKELETON_SPRINT.md` (archived — grep refs only)  
- `docs/sprints/LONG_HORIZON_SAAS_OPERATING_SYSTEM_SPRINT.md`  
- `docs/sprints/backend_redeploy_*` (all execution-only report dirs)  
- `docs/sprints/ROLE_C_BACKEND_DEPLOY_SMOKE_CHECK_SPRINT/`  
- `docs/sprints/REMOTE_DEMO_ENV_REBASELINE_PRECHECK_SPRINT/`  
- `docs/sprints/HEALTH_ENDPOINT_ROOT_CAUSE_PERMANENT_FIX/` (keep gotcha pointer in runbook)  

**Do not mass-move in this sprint** — list only; operator moves when convenient.

**Cross-links added:** DEPLOYMENT_PLAYBOOK, DEPLOYMENT_READINESS, demo.env.example, trial_readiness.

---

## Phase 3 — Tests

| Test file | Covers |
|-----------|--------|
| `tests/test_deploy_entry_scripts.py` | Wrapper posture + SSOT references |
| `tests/test_deploy_rag_demo_pilot_defaults.py` | Core script paid-pilot bundle |
| `tests/test_validate_pilot_deploy_env.py` | Validator tuple + DEMO_MODE + JSON |
| `tests/test_deployment_profile.py` | Warnings (existing) |

---

## Phase 4 — Validation log (2026-05-24)

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api tests` | PASS |
| `PYTHONPATH=. pytest tests/` | PASS (1 skipped) |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS (assertions passed) |
| `bash scripts/trial_readiness_check.sh` | PASS |
| `bash scripts/trial_launch_check.sh` | PASS |
| `cd ui && npm run build` (Node 22 via nvm) | PASS |
| `madge --circular` | PASS (no cycles) |

**Post-source posture:** `DEPLOY_ENTRY=paid_pilot|demo_smoke` re-applied in `deploy_rag_demo.sh` after `.env.cloudrun` load so wrappers win over stale file keys.

---

## Simulations (operator mental model)

### Simulation 1 — New founder deploy at 2AM

| Mistake | Before | After |
|---------|--------|-------|
| DEMO_MODE on prod | Possible via mixed script | `deploy_paid_pilot` unsets; validator fails |
| platform_full on prod | Possible | Wrapper sets PRODUCT_ONLY=1 |
| JSON-primary pilot | Possible if .env wrong | Validator fails JSON flags |
| Missing keys | Partial | Validator fails intake/support |
| Wrong script name | deploy_rag_demo → ambiguous | deploy_paid_pilot is obvious |

**Still possible:** Skip validator by calling `deploy_rag_demo.sh` directly with demo posture — mitigated by header warning.

### Simulation 2 — Small broker pilot

Broker should hear: **Unified Intake on Cloud Run + Postgres + Vercel UI.**  
Keys: intake API key (browser), support key (exports).  
Data: Postgres only.  
Deploy: founder runs `deploy_paid_pilot.sh` after filling PILOT ONE PATH in `.env.cloudrun`.

### Simulation 3 — Future self in 6 months

Read order: `CURRENT_PRODUCT_SHAPE.md` → `deploy_paid_pilot.sh` → `validate_pilot_deploy_env.py --show-profile`.  
Ignore sprint docs unless debugging history.

---

## Phase 5 — Summary (see chat final output for live validation results)

**One true paid-pilot path:**  
`cp configs/demo.env.example .env.cloudrun` → fill PILOT block → `validate_pilot_deploy_env.py` → `bash scripts/deploy_paid_pilot.sh`

**Local/dev only:** `run_demo_local.sh`, JSON cases, `deploy_demo_cloud_smoke.sh`, optional `platform_full`.

---

## FINAL_ONE_LINE (intent)

Paid-pilot deploy is now a named script with a enforced env tuple and Postgres-only truth — not a mood detected inside `deploy_rag_demo.sh`.
