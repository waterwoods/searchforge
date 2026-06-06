> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/FOUNDER_ONE_PATH.md`](../../../FOUNDER_ONE_PATH.md)

# Founder Launch Path — Single Canonical Flow

**Purpose:** ONE path for founders from clone → local demo → validation → deploy → broker trial.  
**Runtime truth:** [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md)  
**Operator surface:** [`runbooks/OPERATOR_SURFACE.md`](./runbooks/OPERATOR_SURFACE.md)

> **Deprecated alternate paths** (still work — do not delete):  
> - `bash scripts/founder_pre_trial_checklist.sh` → depth rehearsal; use `trial_launch_check.sh` for first launch  
> - `bash scripts/demo_pre_checklist.sh` → pre-demo only; subset of launch path  
> - `docs/FOUNDER_DEMO_SOP.md` → historical SOP; this doc wins

---

## 1. 15-minute launch path

| Min | Step | Action |
|-----|------|--------|
| 0–3 | Orient | Read [`README.md`](../README.md) + skim [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md) |
| 3–6 | Local | `bash scripts/run_demo_local.sh` → http://localhost:5173/workbench/unified-intake |
| 6–9 | Validate | `bash scripts/guardrail_inbox_triage.sh` |
| 9–12 | Trial prep | `bash scripts/trial_launch_check.sh` — must PASS |
| 12–15 | Launch docs | Read [`trial/FOUNDER_LAUNCH_NOTES.md`](./trial/FOUNDER_LAUNCH_NOTES.md) + bring [`trial/BROKER_TRIAL_ONE_PAGER.md`](./trial/BROKER_TRIAL_ONE_PAGER.md) |

**Single trial entry command:** `bash scripts/trial_launch_check.sh`

---

## 2. Local run

```bash
bash scripts/run_demo_local.sh
# Default: UNIFIED_INTAKE_PRODUCT_ONLY=1, intake_core_readiness=1, port 8001
# Workbench: http://localhost:5173/workbench/unified-intake
```

| Task | Command |
|------|---------|
| Pre-demo checklist | `bash scripts/demo_pre_checklist.sh` |
| Recovery (503 / embedding_warming) | `bash scripts/restore_8001_readiness.sh` |
| Lab opt-in (NOT default) | `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh` |

**Node 22** required for UI build — [`runbooks/NODE_22_SETUP.md`](./runbooks/NODE_22_SETUP.md)

**Do not use for product demo:** `start_all.sh`, `dev_local.sh`, `docker compose up` (full lab stack)

---

## 3. Validation

```bash
bash scripts/guardrail_inbox_triage.sh          # intake regression
bash scripts/trial_readiness_check.sh           # posture + build
bash scripts/trial_launch_check.sh              # before first broker trial
bash scripts/summarize_readiness_posture.sh     # optional human summary
```

---

## 4. Deploy

```bash
cp configs/demo.env.example .env.cloudrun   # edit Postgres, keys, origins
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

**Vercel:** `VITE_API_BASE_URL=<Cloud Run URL>`, `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`

**Never use as founder deploy entry:** `deploy_rag_demo.sh`, `deploy_cloud_run.sh`, `scripts/deploy/*` legacy wrappers (they redirect here).

Details: [`runbooks/DEPLOY_TRUTH_MAP.md`](./runbooks/DEPLOY_TRUTH_MAP.md)

---

## 5. Trial

After `trial_launch_check.sh` PASS:

1. Read [`trial/FOUNDER_LAUNCH_NOTES.md`](./trial/FOUNDER_LAUNCH_NOTES.md)
2. Copy [`trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`](./trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md)
3. Run SIM1–SIM3 in workbench Simulation Assistant
4. Post-trial: [`trial/FIX_NOW_QUEUE_TEMPLATE.md`](./trial/FIX_NOW_QUEUE_TEMPLATE.md) → `results/trial_logs/`

**Trial index:** [`trial/INDEX.md`](./trial/INDEX.md)

---

## 6. Support escalation

```bash
bash scripts/summarize_support_posture.sh <Cloud Run URL>
```

Read: [`runbooks/SUPPORT_TRUTH_MAP.md`](./runbooks/SUPPORT_TRUTH_MAP.md), [`ANDY_IF_SOMETHING_GOES_WRONG.md`](./ANDY_IF_SOMETHING_GOES_WRONG.md)

---

## 7. False alarms

| Alarm | Reality |
|-------|---------|
| `/readyz` ok:false but `intake_path_ready:true` | Vectors down — **triage still runs** |
| Qdrant red on dashboard | Optional for core intake |
| 503 embedding_warming | Run `restore_8001_readiness.sh`; workbench may still work |
| `platform_inline_route_leak_count` | Auditor — 0 expected in product_only |
| Backend `/healthz` vs Cloud Run `/health/live` | Different probes — see cheat sheet |

---

## 8. What to ignore

| Ignore | Why |
|--------|-----|
| `docs/archive/sprints/` | Historical execution notes |
| `docs/sprints/` (except 7 convergence .md files) | Reduction plans — not daily wiring |
| `scripts/lab/*`, `scripts/deploy/*` legacy wrappers | Lab/R&D paths |
| `docker-compose.yml` GPU/Milvus services | Lab stack — use `run_demo_local.sh` |
| `GET /ready` | Legacy RAG gate |
| `/demo` RAG page | Separate wedge — not intake workbench |
| ~470 scripts at `scripts/` root | Only ~10 matter — see OPERATOR_SURFACE |

Full list: [`runbooks/OPERATOR_IGNORE_LIST.md`](./runbooks/OPERATOR_IGNORE_LIST.md)

---

## 9. Qdrant truth

- **Core intake triage:** does **not** require Qdrant
- **Notice/knowledge wedge:** uses vectors when `QDRANT_*` configured
- **`/demo` RAG page:** may use offline fallback
- Paid pilot: `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` — Qdrant optional on `/readyz`

---

## 10. `/ready` vs `/readyz`

| Endpoint | Meaning |
|----------|---------|
| **`/readyz`** | Intake SaaS readiness — check **`intake_path_ready`** |
| **`/ready`** | Legacy **full-stack RAG** gate — needs Qdrant + embedding |

**Founders and operators:** use `/readyz`. Ignore `/ready` for paid pilot intake.

**Cloud Run liveness:** `GET /health/live` (not bare `/healthz`)

---

## Script map (founder tier)

| Script | When |
|--------|------|
| `scripts/run_demo_local.sh` | Start local workbench |
| `scripts/demo_pre_checklist.sh` | Pre-demo checklist |
| `scripts/founder_pre_trial_checklist.sh` | Depth rehearsal (optional) |
| `scripts/trial_launch_check.sh` | **Before first broker trial** |
| `scripts/trial_readiness_check.sh` | Posture check |
| `scripts/deploy_paid_pilot.sh` | Cloud Run paid pilot |

Discoverable copies: `scripts/founder/`, `scripts/operator/`

---

*End of founder launch path*
