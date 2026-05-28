# Unified Intake — California Auto Insurance Broker SaaS

**What we ship:** broker intake — paste → classify → case → workbench. Postgres-backed cases; vectors optional.

**What this repo is not:** a platform, workflow engine, or multi-tenant operating system. The SearchForge R&D lab still lives here — **below the fold**, opt-in only.

---

## 15-minute onboarding

| Role | Read (in order) | Run |
|------|-----------------|-----|
| **Founder** | This file → [`docs/CURRENT_PRODUCT_SHAPE.md`](docs/CURRENT_PRODUCT_SHAPE.md) → [`docs/ANDY_QUICK_START.md`](docs/ANDY_QUICK_START.md) | `bash scripts/run_demo_local.sh` |
| **Operator** | [`docs/runbooks/OPERATOR_CHEAT_SHEET.md`](docs/runbooks/OPERATOR_CHEAT_SHEET.md) → [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](docs/runbooks/OPERATOR_IGNORE_LIST.md) | `bash scripts/trial_launch_check.sh` |
| **Support** | [`docs/runbooks/SUPPORT_TRUTH_MAP.md`](docs/runbooks/SUPPORT_TRUTH_MAP.md) → cheat sheet | `bash scripts/summarize_support_posture.sh <URL>` |
| **Engineer** | [`AGENTS.md`](AGENTS.md) → [`docs/CURRENT_PRODUCT_SHAPE.md`](docs/CURRENT_PRODUCT_SHAPE.md) | `bash scripts/guardrail_inbox_triage.sh` |

**Full operator surface (10 scripts, 10 docs, 5 endpoints):** [`docs/runbooks/OPERATOR_SURFACE.md`](docs/runbooks/OPERATOR_SURFACE.md)

---

## The product (5 bullets)

1. **Customer intake** — paste text/image → classify → ask for gaps → structured case
2. **Add-car workflow** — flagship path for vehicle scope and office handoff
3. **Broker workbench** — case list, triage, notes, drafts; broker confirms before send
4. **Postgres truth** — durable cases/sessions on paid pilot (`SERVICE_RECORD_DATABASE_URL`)
5. **Coarse API keys** — intake + support perimeter; deployment-manifest for posture without SSH

---

## Quick start (local)

```bash
bash scripts/run_demo_local.sh
# → http://localhost:5173/workbench/unified-intake
```

| Task | Command |
|------|---------|
| Pre-demo checklist | `bash scripts/demo_pre_checklist.sh` |
| Validate intake API | `bash scripts/guardrail_inbox_triage.sh` |
| Recovery (503 / embedding_warming) | `bash scripts/restore_8001_readiness.sh` |
| Before broker trial | `bash scripts/trial_launch_check.sh` |

**Agents (Cursor/OpenClaw):** [`AGENTS.md`](AGENTS.md)

---

## Deploy (paid pilot)

```bash
cp configs/demo.env.example .env.cloudrun   # first time — edit Postgres, keys, origins
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

**Vercel:** `VITE_API_BASE_URL=<Cloud Run URL>`, `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`

**Never use as operator entry:** `deploy_rag_demo.sh`, `deploy_cloud_run_core.sh` (impl only)

Details: [`docs/runbooks/DEPLOY_TRUTH_MAP.md`](docs/runbooks/DEPLOY_TRUTH_MAP.md)

---

## Health endpoints (5 that matter)

| Endpoint | Use |
|----------|-----|
| `/health/live` | **Liveness** — use on Cloud Run (not bare `/healthz`) |
| `/readyz` | **Intake readiness** — check `intake_path_ready: true` |
| `/health` | JSON detail + deployment_profile (debug) |
| `GET /api/inbox/support/deployment-manifest` | Support posture without SSH (support key) |
| `/api/inbox/triage` | Core product API (intake key) |

**Not an outage:** `/readyz` with `ok:false` when `intake_path_ready:true` — vectors down, triage still runs.

**Ignore for intake SaaS:** `GET /ready` (legacy full-stack RAG gate — needs Qdrant+embedding).

---

## What to ignore

| Ignore | Why |
|--------|-----|
| Qdrant red / vectors down | Optional for core triage; notice/knowledge wedge only |
| `docs/sprints/*` | Historical execution notes — not wiring truth |
| Sidebar lab routes (RAG Lab, Agent Studio, …) | Hidden when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` |
| `/demo` RAG page | Separate wedge — not the intake workbench |
| Platform blueprints (`TRUSTED_ASSISTANT_*`, FUTURE_SAAS) | Investor framing — not deploy truth |
| ~200 shell scripts | Only ~10 are operator entries — see OPERATOR_SURFACE |

**Full list:** [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](docs/runbooks/OPERATOR_IGNORE_LIST.md)

---

## Lab only (explicit opt-in)

| Item | When |
|------|------|
| `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh` | Full SearchForge API surface locally |
| `docker compose -f docker-compose.lab.yml up rag-api` on port **8000** | Legacy container stack |
| `make -f Makefile.lab help` | SearchForge lab targets (GPU, CI, Qdrant) |
| `POST /api/query` | RAG retrieval lab |
| http://localhost:5173/demo | RAG Q&A wedge |
| GPU worker, AutoTuner, Metrics Hub | R&D — not paid pilot |

**Legacy README (1,500+ lines):** [`docs/archive/README_LEGACY_SEARCHFORGE_LAB.md`](docs/archive/README_LEGACY_SEARCHFORGE_LAB.md)

---

## Runtime truth

| Doc | Purpose |
|-----|---------|
| [`docs/CURRENT_PRODUCT_SHAPE.md`](docs/CURRENT_PRODUCT_SHAPE.md) | What is deployed today |
| [`docs/runbooks/OPERATOR_CHEAT_SHEET.md`](docs/runbooks/OPERATOR_CHEAT_SHEET.md) | 2am operator path |
| [`docs/SIMPLIFICATION_MASTER_PLAN.md`](docs/SIMPLIFICATION_MASTER_PLAN.md) | Reduction roadmap (not runtime truth) |
| [`docs/PROJECT_DOC_SYSTEM_MAP.md`](docs/PROJECT_DOC_SYSTEM_MAP.md) | Doc navigation — START HERE table |

**Ports:** local dev **8001** (`run_demo_local.sh`); Docker lab **8000**; recovery `restore_8001_readiness.sh`.

---

## License

MIT — see [LICENSE](LICENSE).
