# Operator Cheat Sheet — Unified Intake (1 page)

**Product:** broker intake SaaS — paste → classify → case → workbench. **Not** SearchForge R&D platform.

**Operator surface (10 scripts · 10 docs · 5 endpoints):** [`OPERATOR_SURFACE.md`](./OPERATOR_SURFACE.md)

**Runtime truth:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)

---

## At 2am — do this in order

| Step | Command / URL |
|------|----------------|
| 1. Is API alive? | `curl -sf <URL>/health/live` → `{"ok":true}` |
| 2. Can intake run? | `curl -sf <URL>/readyz` → check `intake_path_ready: true` (Qdrant optional on paid pilot) |
| 3. Posture without SSH | `GET /api/inbox/support/deployment-manifest` (support key) |
| 4. Local posture summary | `bash scripts/summarize_readiness_posture.sh --probe http://127.0.0.1:8001` |
| 4b. Support posture (live) | `bash scripts/summarize_support_posture.sh <URL>` |
| 5. Before broker trial | `bash scripts/trial_launch_check.sh` |

**Do not panic on:** `/readyz` with `ok:false` when `intake_path_ready:true` — vectors down, triage still works.

---

## Deploy (paid pilot only)

```bash
cp configs/demo.env.example .env.cloudrun   # first time
# Edit: Postgres URL, OPENAI_API_KEY, intake/support keys, ALLOWED_ORIGINS
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

**Vercel:** `VITE_API_BASE_URL=<Cloud Run URL>`, `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`

**Never use as operator entry:** `deploy_rag_demo.sh`, `deploy_cloud_run_core.sh` (impl only)

---

## Validate after change

```bash
bash scripts/guardrail_inbox_triage.sh
bash scripts/trial_readiness_check.sh
source scripts/with_node22_path.sh && cd ui && npm run build
```

---

## Health endpoints (operator)

| Endpoint | Use |
|----------|-----|
| `/health/live` | **Liveness** — use this on Cloud Run |
| `/api/healthz` | Same liveness (alias; use if tool insists on "healthz") |
| `/readyz` | **Intake readiness** — `intake_path_ready` matters more than `ok` |
| `/health` | JSON detail + deployment_profile (founder/debug) |
| `/ready` | **Legacy full-stack** — requires Qdrant+embed; ignore for intake SaaS |
| `/health/ready` | Route/artifacts gate — not intake triage gate |

**Trap:** bare `/healthz` on Cloud Run often 404 at Google edge — use `/health/live`.

---

## Env vars that matter (paid pilot)

| Required | Optional |
|----------|----------|
| `UNIFIED_INTAKE_PRODUCT_ONLY=1` | `QDRANT_*` (notice/knowledge only) |
| `SERVICE_RECORD_DATABASE_URL` | `ALLOWED_ORIGINS` |
| `UNIFIED_INTAKE_DB_PRIMARY_READS/WRITES=1` | |
| `UNIFIED_INTAKE_JSON_*` all off | |
| `UNIFIED_INTAKE_INTAKE_API_KEY` | |
| `UNIFIED_INTAKE_SUPPORT_API_KEY` | |
| `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` (set by deploy_paid_pilot) | |
| `OPENAI_API_KEY` | |

Full tuple: `python3 scripts/validate_pilot_deploy_env.py --show-profile`

---

## Legacy / lab-only (do not ship to brokers)

| Thing | Class |
|-------|-------|
| `platform_full` (no PRODUCT_ONLY) | Dev/local only — **opt-in lab** |
| `DEMO_MODE=1` on prod | Forbidden |
| JSON case files with PG URL | Forbidden |
| Sidebar lab routes (RAG Lab, Agent Studio, …) | Hidden when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| `/demo` RAG page | Separate wedge; not intake workbench |
| `GET /ready` | Legacy RAG — needs Qdrant; **ignore** for intake |
| Sprint docs under `docs/sprints/` | Historical — not wiring truth |
| Qdrant down with `intake_path_ready:true` | **Not an outage** for triage |

**Full ignore list:** [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md) — SAFE TO IGNORE / NOT FOR PAID PILOT / LAB ONLY / HISTORICAL

---

## More detail

- Ignore list: [`OPERATOR_IGNORE_LIST.md`](./OPERATOR_IGNORE_LIST.md)
- Deploy: [`DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md)
- Support: [`SUPPORT_TRUTH_MAP.md`](./SUPPORT_TRUTH_MAP.md)
- Panic fixes: [`docs/ANDY_IF_SOMETHING_GOES_WRONG.md`](../ANDY_IF_SOMETHING_GOES_WRONG.md)
