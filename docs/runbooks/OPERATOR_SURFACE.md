# Operator Surface — Unified Intake (Target Mental Model)

**Purpose:** The ONLY things a normal operator, founder, support engineer, or new contractor should realistically know.  
**Runtime truth:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)  
**2am path:** [`OPERATOR_CHEAT_SHEET.md`](./OPERATOR_CHEAT_SHEET.md) · **Ignore list:** [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md)

---

## THE PRODUCT (≤5 bullets)

1. **Unified Intake** — broker-office SaaS: paste → classify → case → workbench
2. **Postgres** is persistence truth on paid pilot (`SERVICE_RECORD_DATABASE_URL`)
3. **API keys** gate intake and support perimeters (coarse auth — not OAuth/SSO)
4. **Vectors optional** — core triage runs without Qdrant; notice/knowledge wedge uses vectors when configured
5. **Broker control** — office confirms before send; no auto-send to carriers

---

## THE ONLY IMPORTANT SCRIPTS (≤10)

| # | Script | When |
|---|--------|------|
| 1 | `bash scripts/run_demo_local.sh` | Start local workbench (:8001) |
| 2 | `bash scripts/deploy_paid_pilot.sh` | Paid pilot Cloud Run deploy |
| 3 | `PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py` | Pre-deploy env gate |
| 4 | `bash scripts/guardrail_inbox_triage.sh` | Intake regression guardrail |
| 5 | `bash scripts/trial_launch_check.sh` | Before first broker trial |
| 6 | `bash scripts/trial_readiness_check.sh` | Posture + build readiness |
| 7 | `bash scripts/summarize_readiness_posture.sh` | Local/live readiness summary |
| 8 | `bash scripts/summarize_support_posture.sh` | Support manifest human summary |
| 9 | `bash scripts/restore_8001_readiness.sh` | Recovery from 503 / embedding_warming |
| 10 | `bash scripts/demo_pre_checklist.sh` | Pre-demo founder checklist |

**Not operator entries:** `deploy_rag_demo.sh`, `deploy_cloud_run_core.sh`, `deploy_cloud_run.sh`, ~190 other `.sh` files — see [`scripts/README_OPERATOR.md`](../../scripts/README_OPERATOR.md).

---

## THE ONLY IMPORTANT DOCS (≤10)

| # | Doc | Who |
|---|-----|-----|
| 1 | [`AGENTS.md`](../../AGENTS.md) | Agents / engineers — default entry |
| 2 | [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) | Everyone — runtime truth |
| 3 | [`docs/runbooks/OPERATOR_CHEAT_SHEET.md`](./OPERATOR_CHEAT_SHEET.md) | Operators — 2am |
| 4 | [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md) | Operators — cognitive load |
| 5 | [`docs/runbooks/DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md) | Which deploy script |
| 6 | [`docs/runbooks/SUPPORT_TRUTH_MAP.md`](./SUPPORT_TRUTH_MAP.md) | Support manifest keys |
| 7 | [`docs/ANDY_QUICK_START.md`](../ANDY_QUICK_START.md) | Founders — local demo |
| 8 | [`docs/goals/insurance_paid_pilot_goal.md`](../goals/insurance_paid_pilot_goal.md) | Scope in/out |
| 9 | [`docs/runbooks/DEPLOYMENT_PLAYBOOK.md`](./DEPLOYMENT_PLAYBOOK.md) | Release steps |
| 10 | [`docs/trial/INDEX.md`](../trial/INDEX.md) | Real broker trial package |

**Macro blueprint (major sprints only):** [`docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`](../UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md)

---

## THE ONLY IMPORTANT ENDPOINTS (≤5)

| Endpoint | Role |
|----------|------|
| `GET /health/live` | Liveness (Cloud Run — not bare `/healthz`) |
| `GET /readyz` | Intake readiness — **`intake_path_ready`** matters |
| `GET /health` | Detail + deployment_profile (debug) |
| `GET /api/inbox/support/deployment-manifest` | Support posture (support key) |
| `POST /api/inbox/triage` | Core intake API (intake key) |

---

## THINGS TO IGNORE

See [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md). Summary:

- `GET /ready` (legacy RAG full-stack gate)
- `/readyz` `ok:false` when `intake_path_ready:true`
- Qdrant red on paid pilot intake-only deploy
- `docs/sprints/*` unless linked from CURRENT_PRODUCT_SHAPE
- Platform blueprints (TRUSTED_ASSISTANT, FUTURE_SAAS)
- ETF `/api/query` smoke in old scripts
- ~992 archived sprint markdown files

---

## THINGS THAT ARE LAB ONLY

| Item | Opt-in |
|------|--------|
| `platform_full` (no `UNIFIED_INTAKE_PRODUCT_ONLY`) | Local R&D |
| `RUN_DEMO_LAB=1` | Full lab API on local demo |
| `docker compose up rag-api` :8000 | Legacy container stack |
| `POST /api/query` | RAG retrieval |
| `/demo` page | RAG Q&A wedge |
| GPU worker, AutoTuner, Metrics Hub | SearchForge R&D |
| [`docs/archive/README_LEGACY_SEARCHFORGE_LAB.md`](../archive/README_LEGACY_SEARCHFORGE_LAB.md) | Old 1,500-line README |

---

## THINGS THAT ARE HISTORICAL

| Item | Note |
|------|------|
| `docs/sprints/` (most files) | Execution records — archive mindset |
| `docs/archive/` | Point-in-time reports |
| FUTURE_SAAS / LONG_HORIZON docs | Investor framing — archived |
| SearchForge naming in old scripts | Repo heritage |
| `deploy_cloud_run.sh` | Legacy SearchForge deploy name |

---

## THE 15-MINUTE ONBOARDING PATH

### Founder (~15 min)

1. Read [`README.md`](../../README.md) (this repo root) — 3 min
2. Read [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) — 5 min
3. Read [`docs/ANDY_QUICK_START.md`](../ANDY_QUICK_START.md) — 3 min
4. Run `bash scripts/run_demo_local.sh` → open workbench — 4 min

### Operator (~15 min)

1. Read [`OPERATOR_CHEAT_SHEET.md`](./OPERATOR_CHEAT_SHEET.md) — 5 min
2. Read [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md) — 3 min
3. Read [`DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md) — 4 min
4. Run `bash scripts/trial_readiness_check.sh` — 3 min

### Support (~15 min)

1. Read [`SUPPORT_TRUTH_MAP.md`](./SUPPORT_TRUTH_MAP.md) — 5 min
2. Read [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md) — 3 min
3. Run `bash scripts/summarize_support_posture.sh <URL>` — 2 min
4. Skim [`docs/ANDY_IF_SOMETHING_GOES_WRONG.md`](../ANDY_IF_SOMETHING_GOES_WRONG.md) — 5 min

### Engineer (~15 min)

1. Read [`AGENTS.md`](../../AGENTS.md) — 3 min
2. Read [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md) — 5 min
3. Read [`docs/goals/insurance_paid_pilot_goal.md`](../goals/insurance_paid_pilot_goal.md) — 3 min
4. Run `bash scripts/guardrail_inbox_triage.sh` — 4 min

---

## WHAT MUST NEVER BE BUILT (for paid pilot)

OAuth, SSO, RBAC, Stripe billing, tenant admin UI, fake RLS, workflow engine, event bus, microservices split, multi-region HA, plugin marketplace, "AI operating system" layers.

See [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../SIMPLIFICATION_MASTER_PLAN.md) § STOP_BUILDING.

---

## Related

- [`docs/PROJECT_DOC_SYSTEM_MAP.md`](../PROJECT_DOC_SYSTEM_MAP.md) — full doc hierarchy
- [`docs/SIMPLIFICATION_MASTER_PLAN.md`](../SIMPLIFICATION_MASTER_PLAN.md) — reduction backlog
