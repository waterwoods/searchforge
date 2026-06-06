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
| No in-memory sessions with DB | `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS` off when DB URL set | Multi-instance session truth |
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
| `platform_full` (no `PRODUCT_ONLY`) — **lab opt-in** | Anonymous support/intake on public URL |
| In-memory sessions (`UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS=1`) | Missing intake/support keys |

**Recommended local pilot posture** (trial prep — matches Cloud Run; add to `.env`):

```bash
UNIFIED_INTAKE_PRODUCT_ONLY=1
UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
```

Without `RUN_DEMO_LAB=1`, `run_demo_local.sh` **defaults** to the flags above (paid-pilot parity). Lab stack: `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh`. See `configs/demo.env.example` LOCAL block and `docs/runbooks/OPERATOR_IGNORE_LIST.md`.

Set `PILOT_DEPLOY_STRICT=1` in `.env.cloudrun` to force paid-pilot validation even during staging experiments.

---

## Demo vs paid pilot

| | **Founder demo / local** | **Paid pilot / prod** |
|--|--------------------------|-------------------------|
| Purpose | Show product, iterate fast | Real broker, real cases |
| API surface | May use `platform_full` locally | **`UNIFIED_INTAKE_PRODUCT_ONLY=1` required** |
| Persistence | JSON-only OK on laptop | **Postgres-only** |
| Readiness | `DEMO_MODE` relaxes `/readyz` (local/demo cloud) | `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` + `PRODUCT_ONLY` — Qdrant optional on `/readyz`; triage never required vectors |
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
| Shared deploy impl | `scripts/deploy_cloud_run_core.sh` (called by wrappers — not the operator entry) |
| Legacy name | `scripts/deploy_rag_demo.sh` prints deprecation warning → core impl |
| Release ops | `docs/runbooks/DEPLOYMENT_PLAYBOOK.md` |
| Runtime ports | `docs/runbooks/RUNTIME_PATH_STANDARD.md` |

---

## UI build (Node 22 required)

Vite 7 requires **Node 22.x**. Canonical setup: [`docs/runbooks/NODE_22_SETUP.md`](runbooks/NODE_22_SETUP.md).

```bash
source scripts/with_node22_path.sh
bash scripts/check_ui_node_version.sh
cd ui && npm run build
```

## Readiness modes (intake SaaS vs RAG lab)

| Mode | Env | `/readyz` | Intake triage |
|------|-----|-----------|---------------|
| **intake_core** | `DEMO_MODE=1` (local/demo cloud) or `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` + `UNIFIED_INTAKE_PRODUCT_ONLY=1` | Qdrant/embedding optional; `intake_path_ready: true` | Works without Qdrant |
| **full_stack** | Default platform/RAG | Qdrant + embedding required | N/A for vectors |

```bash
bash scripts/summarize_readiness_posture.sh
bash scripts/summarize_readiness_posture.sh --probe http://127.0.0.1:8001
```

**Paid pilot:** do not use `DEMO_MODE` on `ENV=prod`. Use **intake-core readiness** when vectors are down but Postgres + API keys are healthy. `deploy_paid_pilot.sh` sets `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` — **Qdrant is optional** for deploy and `/readyz`; add `QDRANT_*` only when notice/knowledge retrieval is needed.

Default shell Node 20 will fail the UI build — run the check script before Vercel/local builds.

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

**Not runtime truth (future exploration / investor framing):** `docs/archive/platform/TRUSTED_ASSISTANT_PLATFORM_BLUEPRINT.md`, archived `FUTURE_SAAS_*` and `LONG_HORIZON_SAAS_*` sprint docs — see `docs/PROJECT_DOC_SYSTEM_MAP.md` § Future exploration.
