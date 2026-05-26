# Current Product Shape — Single Source of Truth

**Authority:** This file is the **current runtime and deployment truth** for the California Auto Insurance Broker Assistant.  
**When in doubt:** Read this before sprint docs, old reports, or ad-hoc env notes.

---

## What we ship

| Layer | Truth |
|-------|--------|
| **Product** | **Unified Intake** (inbox triage, case workbench) + **Workbench UI** |
| **Not the product** | Platform/lab routers, SearchForge R&D endpoints, tuner/graph demos |
| **Deployment** | **Vercel** (frontend) + **Cloud Run** (backend) + **Postgres** (durable cases/sessions) |
| **Vector retrieval** | Qdrant for notice/knowledge-assisted flows — optional for core intake triage |

---

## Persistence truth

**Postgres is the only supported persistence truth for paid pilots.** Case and session
durable state lives in ``SERVICE_RECORD_DATABASE_URL`` (or Secret Manager binding).
JSON case files (``UNIFIED_INTAKE_CASES_PATH`` / ``data/demo_cases.json``) are a
**legacy/dev compatibility path** only — allowed on laptop demos without a DB URL;
forbidden when ``ENV=prod`` or PG-primary writes are on.

**platform_full** (``UNIFIED_INTAKE_PRODUCT_ONLY`` unset) is **legacy/dev mode** — full
SearchForge/lab API surface. Paid pilots must set ``UNIFIED_INTAKE_PRODUCT_ONLY=1``.

---

## Paid pilot requirements (hard, not advisory)

These are **required** for any paid broker pilot or `ENV=prod` Cloud Run deploy. Validators and deploy scripts **fail** when missing.

| Requirement | Env / flag | Why |
|-------------|------------|-----|
| Product-only API surface | `UNIFIED_INTAKE_PRODUCT_ONLY=1` | Hides platform_full routers |
| Postgres durable cases | `SERVICE_RECORD_DATABASE_URL` (or Secret Manager binding) | Multi-instance safe truth |
| PG-primary writes | `UNIFIED_INTAKE_DB_PRIMARY_WRITES=1` | Cases live in Postgres |
| PG-primary reads | `UNIFIED_INTAKE_DB_PRIMARY_READS=1` | No JSON-first reads |
| No JSON case writes | `UNIFIED_INTAKE_JSON_CASE_WRITES=0` | Filesystem cases forbidden in prod |
| No JSON read fallback | `UNIFIED_INTAKE_JSON_READ_FALLBACK=0` | No silent JSON authority |
| No dual-write | `UNIFIED_INTAKE_PG_DUAL_WRITE=0` | One write path |
| Intake perimeter | `UNIFIED_INTAKE_INTAKE_API_KEY` (24+ chars) | Broker-facing API gate |
| Support perimeter | `UNIFIED_INTAKE_SUPPORT_API_KEY` (24+ chars, ≠ intake key) | Support export gate |
| **No demo mode** | `DEMO_MODE` unset or `0` | Readiness must reflect real deps |

**Validate before deploy:**

```bash
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --show-profile
```

**Reference tuple:** `pilot_safe_default_profile_v1()` in `services/fiqa_api/deployment_profile.py`.

---

## Local / founder demo (explicit opt-in only)

Local dev and **non-paid** Cloud Run smoke deploys may use relaxed posture **only when not prod-like**:

| Allowed locally | Forbidden on paid pilot |
|-----------------|-------------------------|
| `bash scripts/run_demo_local.sh` (port 8001) | `DEMO_MODE=true` with `ENV=prod` |
| JSON case files when no DB URL | JSON case writes with PG-primary |
| `platform_full` (no `PRODUCT_ONLY`) | Anonymous support/intake on public URL |
| In-memory sessions (`UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1`) | Missing intake/support keys |

Set `PILOT_DEPLOY_STRICT=1` in `.env.cloudrun` to force paid-pilot validation even during staging experiments.

---

## Demo vs paid pilot

| | **Founder demo / local** | **Paid pilot / prod** |
|--|--------------------------|-------------------------|
| Purpose | Show product, iterate fast | Real broker, real cases |
| API surface | May use `platform_full` locally | **`UNIFIED_INTAKE_PRODUCT_ONLY=1` required** |
| Persistence | JSON-only OK on laptop | **Postgres-only** |
| Readiness | `DEMO_MODE` may relax `/readyz` | Full dependency honesty |
| Deploy script | `deploy_demo_cloud_smoke.sh` (DEMO_MODE) | `deploy_paid_pilot.sh` only |
| Docs | `docs/ANDY_QUICK_START.md` | This file + `configs/demo.env.example` PILOT ONE PATH |

---

## Deployment entry points

| Task | Command / doc |
|------|----------------|
| Start local demo | `bash scripts/run_demo_local.sh` |
| Pre-trial check | `bash scripts/trial_launch_check.sh` |
| Pilot env validate | `python3 scripts/validate_pilot_deploy_env.py` |
| **Paid pilot Cloud Run** | `bash scripts/deploy_paid_pilot.sh` |
| Demo cloud smoke only | `bash scripts/deploy_demo_cloud_smoke.sh` |
| Shared deploy impl | `scripts/deploy_rag_demo.sh` (called by wrappers — not the operator entry) |
| Release ops | `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` |
| Runtime ports | `docs/runbooks/RUNTIME_PATH_STANDARD.md` |

---

## Sprint docs are historical

Files under `docs/sprints/` are **execution records and discovery notes** from past work. They are **not** current runtime truth unless this file or `docs/PROJECT_DOC_SYSTEM_MAP.md` explicitly points to them.

When a sprint doc conflicts with this file, **this file wins**.

See also: `docs/sprints/README.md`.

---

## Related SSOT docs

| Doc | Role |
|-----|------|
| `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro product north star |
| `docs/goals/insurance_paid_pilot_goal.md` | Paid pilot scope |
| `configs/demo.env.example` | Env template — PILOT ONE PATH block |
| `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` | Release procedure |
| `docs/DEPRECATED_PATHS.md` | Removed flags and dead paths |
| `docs/SIMPLIFICATION_MASTER_PLAN.md` | Reduction roadmap (hide/archive/delete — not runtime truth) |
