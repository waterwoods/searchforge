# Founder One Path — Single Canonical Flow

**Purpose:** ONE path from clone → local → validate → demo → deploy → trial → support.  
**Runtime truth:** [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md)  
**Operator surface:** [`runbooks/OPERATOR_SURFACE.md`](./runbooks/OPERATOR_SURFACE.md)  
**P9 plan:** [`P9_BROKER_SURFACE_PLAN.md`](./P9_BROKER_SURFACE_PLAN.md)

> **Historical paths archived:** `docs/archive/p9_broker_surface/founder/` — do not use for daily ops.

---

## 1. Run locally

```bash
bash scripts/run_demo_local.sh
# Workbench: http://localhost:5173/workbench/unified-intake
# Default: UNIFIED_INTAKE_PRODUCT_ONLY=1, port 8001
```

| Task | Command |
|------|---------|
| Pre-demo checklist | `bash scripts/demo_pre_checklist.sh` |
| Recovery (503 / embedding_warming) | `bash scripts/restore_8001_readiness.sh` |
| Lab opt-in (NOT for broker demo) | `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh` |

**Node 22** required for UI — [`runbooks/NODE_22_SETUP.md`](./runbooks/NODE_22_SETUP.md)

**Do not use for product demo:** `start_all.sh`, `dev_local.sh`, `docker compose up` (full lab stack)

---

## 2. Validate

```bash
bash scripts/guardrail_inbox_triage.sh          # intake regression — run before demo/trial
bash scripts/trial_readiness_check.sh           # posture + build
bash scripts/trial_launch_check.sh              # before first broker trial
bash scripts/summarize_readiness_posture.sh     # optional human summary
```

---

## 3. Demo

**Read:** [`DEMO_STORY.md`](./DEMO_STORY.md) + [`BROKER_DEMO_FLOW.md`](./BROKER_DEMO_FLOW.md)

```bash
bash scripts/demo_pre_checklist.sh
bash scripts/guardrail_inbox_triage.sh
bash scripts/run_demo_local.sh
```

Open http://localhost:5173/workbench/unified-intake → Load founder demo queue → Cancellation → Missing doc → Add-car.

**Broker materials:** [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md)

---

## 4. Deploy

```bash
cp configs/demo.env.example .env.cloudrun   # edit Postgres, keys, origins
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

**Vercel:** `VITE_API_BASE_URL=<Cloud Run URL>`, `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`

**Never use:** `deploy_rag_demo.sh`, `deploy_cloud_run.sh`, `scripts/deploy/*` legacy wrappers.

Details: [`runbooks/DEPLOY_TRUTH_MAP.md`](./runbooks/DEPLOY_TRUTH_MAP.md)

---

## 5. Trial

**Single entry:** `bash scripts/trial_launch_check.sh` — must PASS

**Read:** [`TRIAL_ONE_PATH.md`](./TRIAL_ONE_PATH.md)

**Give broker:** [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md) + [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md)

**Copy template:** [`trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`](./trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md)

**Post-trial:** [`trial/FIX_NOW_QUEUE_TEMPLATE.md`](./trial/FIX_NOW_QUEUE_TEMPLATE.md) → `results/trial_logs/`

---

## 6. Support

```bash
bash scripts/summarize_support_posture.sh <Cloud Run URL>
```

Read: [`runbooks/SUPPORT_TRUTH_MAP.md`](./runbooks/SUPPORT_TRUTH_MAP.md), [`ANDY_IF_SOMETHING_GOES_WRONG.md`](./ANDY_IF_SOMETHING_GOES_WRONG.md)

**Broker-facing language:** [`CUSTOMER_LANGUAGE_GUIDE.md`](./CUSTOMER_LANGUAGE_GUIDE.md)

---

## 7. Escalation

| Situation | Action |
|-----------|--------|
| Guardrail fails | Fix per script output before demo/trial |
| Broker stuck mid-trial | Switch to founder demo queue; show top 3 scenarios |
| Prod intake down | Check `/readyz` → `intake_path_ready`; run support posture script |
| Trust-breaking wrong triage | Log in observation log → fix-now queue → next sprint |

---

## 8. Rollback

| Layer | Rollback |
|-------|----------|
| Cloud Run | Redeploy previous revision from Cloud Console |
| Vercel | Promote previous deployment |
| Local | `git checkout` docs only if needed; restart `run_demo_local.sh` |
| Data | Postgres backups per your cloud provider — not automated in v1 |

Details: [`runbooks/DEPLOYMENT_PLAYBOOK.md`](./runbooks/DEPLOYMENT_PLAYBOOK.md)

---

## 9. Common false alarms

| Alarm | Reality |
|-------|---------|
| `/readyz` ok:false but `intake_path_ready:true` | Vectors down — **triage still runs** |
| Qdrant red on dashboard | Optional for core intake |
| 503 embedding_warming | Run `restore_8001_readiness.sh`; workbench may still work |
| `platform_inline_route_leak_count` | Auditor — 0 expected in product_only |
| Backend `/healthz` vs Cloud Run `/health/live` | Different probes — see cheat sheet |
| `/ready` fails | Legacy RAG gate — **ignore for intake** |

**Use `/readyz` not `/ready` for paid pilot intake.**

---

## 10. What to ignore

| Ignore | Why |
|--------|-----|
| `docs/archive/sprints/` | Historical execution notes |
| `docs/archive/p9_broker_surface/` | Pre-P9 broker/founder doc overlap |
| `docs/sprints/` (except convergence .md files) | Reduction plans — not daily wiring |
| `scripts/lab/*`, legacy deploy wrappers | Lab/R&D paths |
| `docker-compose.yml` GPU/Milvus | Lab stack |
| `GET /ready` | Legacy RAG gate |
| `/demo` RAG page | Separate wedge — not intake workbench |
| ~470 scripts at `scripts/` root | Only ~10 matter — OPERATOR_SURFACE |

Full list: [`runbooks/OPERATOR_IGNORE_LIST.md`](./runbooks/OPERATOR_IGNORE_LIST.md)

---

## 15-minute founder orientation

| Min | Step |
|-----|------|
| 0–3 | Read README + skim CURRENT_PRODUCT_SHAPE |
| 3–6 | `run_demo_local.sh` → workbench |
| 6–9 | `guardrail_inbox_triage.sh` |
| 9–12 | `trial_launch_check.sh` |
| 12–15 | Read TRIAL_ONE_PATH + BROKER_ONE_PAGER |

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

---

*Everything else points here. End of founder one path.*
