# 15-Minute Engineer Onboarding — Unified Intake

**Goal:** Understand the product in 15 minutes. Ignore the rest of the repo until assigned.

**Runtime truth:** [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md)  
**Operator surface:** [`runbooks/OPERATOR_SURFACE.md`](./runbooks/OPERATOR_SURFACE.md)

---

## 1. What the product actually is

**Unified Intake** — California auto insurance broker SaaS:

1. Broker pastes customer message (text/image)
2. API classifies intent, asks for gaps, creates structured case
3. **Workbench** — case list, triage, notes, drafts
4. Broker confirms before send (no auto-send to carriers)
5. **Postgres** holds durable cases on paid pilot

**Not the product:** SearchForge RAG lab, workflow engine, multi-tenant OS, AutoTuner, graph demos.

---

## 2. What NOT to read

| Skip | Why |
|------|-----|
| `docs/archive/platform/*BLUEPRINT*` | Investor / platform speculation |
| `docs/sprints/*` (most) | Historical execution notes |
| `docs/archive/p7_reports/*` | Point-in-time audits |
| Old README lab sections | See `docs/archive/README_LEGACY_SEARCHFORGE_LAB.md` |
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Macro blueprint — major sprints only |
| ~992 files under `docs/archive/` | Archaeology |

---

## 3. What NOT to run

| Skip | Use instead |
|------|-------------|
| `scripts/lab/start_all.sh`, `dev_local.sh` | `bash scripts/run_demo_local.sh` |
| `make ci`, `make gpu-smoke` | `bash scripts/guardrail_inbox_triage.sh` |
| `deploy_rag_demo.sh` | `bash scripts/deploy_paid_pilot.sh` |
| `scripts/lab/*` regression batteries | Guardrail first |
| Docker :8000 as default | Local product :8001 |

---

## 4. The 5 endpoints

| Endpoint | Role |
|----------|------|
| `GET /health/live` | **Liveness** (Cloud Run — not bare `/healthz`) |
| `GET /readyz` | Intake readiness — **`intake_path_ready`** matters |
| `GET /health` | JSON detail + deployment_profile |
| `GET /api/inbox/support/deployment-manifest` | Support posture (support key) |
| `POST /api/inbox/triage` | Core intake API (intake key) |

**Ignore for intake SaaS:** `GET /ready` (legacy RAG — needs Qdrant+embedding).

---

## 5. The 10 scripts

| Script | When |
|--------|------|
| `bash scripts/run_demo_local.sh` | Start local workbench (:8001) |
| `bash scripts/deploy_paid_pilot.sh` | Paid pilot Cloud Run |
| `PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py` | Pre-deploy env gate |
| `bash scripts/guardrail_inbox_triage.sh` | Intake regression guardrail |
| `bash scripts/trial_launch_check.sh` | Before first broker trial |
| `bash scripts/trial_readiness_check.sh` | Posture + build readiness |
| `bash scripts/summarize_readiness_posture.sh` | Readiness summary |
| `bash scripts/summarize_support_posture.sh` | Support manifest summary |
| `bash scripts/restore_8001_readiness.sh` | Recovery 503 / embedding_warming |
| `bash scripts/demo_pre_checklist.sh` | Pre-demo checklist |

**Discoverable copies:** `scripts/operator/` (same behavior — wrappers only).

---

## 6. The 10 docs

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](../AGENTS.md) | Agent/engineer entry |
| [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md) | Runtime truth |
| [`runbooks/OPERATOR_CHEAT_SHEET.md`](./runbooks/OPERATOR_CHEAT_SHEET.md) | 2am operator path |
| [`runbooks/OPERATOR_IGNORE_LIST.md`](./runbooks/OPERATOR_IGNORE_LIST.md) | Cognitive load relief |
| [`runbooks/DEPLOY_TRUTH_MAP.md`](./runbooks/DEPLOY_TRUTH_MAP.md) | Which deploy script |
| [`runbooks/SUPPORT_TRUTH_MAP.md`](./runbooks/SUPPORT_TRUTH_MAP.md) | Manifest keys |
| [`ANDY_QUICK_START.md`](./ANDY_QUICK_START.md) | Local demo |
| [`goals/insurance_paid_pilot_goal.md`](./goals/insurance_paid_pilot_goal.md) | Scope in/out |
| [`runbooks/DEPLOYMENT_PLAYBOOK.md`](./runbooks/DEPLOYMENT_PLAYBOOK.md) | Release steps |
| [`trial/INDEX.md`](./trial/INDEX.md) | Broker trial package |

---

## 7. Product-only flow

```
Clone → read this file + CURRENT_PRODUCT_SHAPE
     → bash scripts/run_demo_local.sh   (default: PRODUCT_ONLY=1)
     → http://localhost:5173/workbench/unified-intake
     → bash scripts/guardrail_inbox_triage.sh
```

Paid pilot adds: Postgres URL, API keys, `deploy_paid_pilot.sh`, Vercel `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`.

---

## 8. Lab flow (explicit opt-in only)

```
RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh   # platform_full on 8001
docker compose -f docker-compose.lab.yml up rag-api   # legacy :8000
make -f Makefile.lab help
scripts/lab/* wrappers   # print LAB ONLY banner
```

See: [`scripts/LAB_SCRIPT_INDEX.md`](../scripts/LAB_SCRIPT_INDEX.md)

---

## 9. How to run locally

```bash
bash scripts/run_demo_local.sh
# Workbench: http://localhost:5173/workbench/unified-intake
```

Node **22** required for UI build — `source scripts/with_node22_path.sh`

Optional vectors (not required for triage): `USE_LOCAL_QDRANT=1` + seed scripts — lab path.

---

## 10. How to validate

```bash
bash scripts/guardrail_inbox_triage.sh
bash scripts/trial_readiness_check.sh
PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py   # scenario pack
python3 scripts/test_inbox_triage_api.py   # needs server on 8001
```

---

## 11. How to deploy

```bash
cp configs/demo.env.example .env.cloudrun   # edit Postgres, keys
PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun
bash scripts/deploy_paid_pilot.sh
```

Details: [`runbooks/DEPLOY_TRUTH_MAP.md`](./runbooks/DEPLOY_TRUTH_MAP.md)

---

## 12. Common false alarms

| Alarm | Reality |
|-------|---------|
| `/readyz` ok:false but `intake_path_ready:true` | Vectors down — **triage still runs** |
| Qdrant red on dashboard | Optional for core intake |
| `platform_inline_route_leak_count` | Auditor — 0 expected in product_only |
| Backend `/healthz` vs Cloud Run `/health/live` | Different probes — see cheat sheet |
| 503 embedding_warming | Run `restore_8001_readiness.sh` — workbench may still work |

---

## 13. Qdrant truth

- **Core intake triage:** does **not** require Qdrant
- **Notice/knowledge wedge:** uses vectors when `QDRANT_*` configured
- **`/demo` RAG page:** may use offline fallback without backend
- Paid pilot: `UNIFIED_INTAKE_INTAKE_CORE_READINESS=1` — Qdrant optional on `/readyz`

---

## 14. `/ready` vs `/readyz`

| Endpoint | Meaning |
|----------|---------|
| **`/readyz`** | Intake SaaS readiness — check `intake_path_ready` |
| **`/ready`** | Legacy **full-stack RAG** gate — needs Qdrant + embedding |

Operators: use `/readyz`. Ignore `/ready` for paid pilot intake.

---

## 15. Product vs lab mental model

```
PRODUCT (default)                    LAB (opt-in)
─────────────────                    ────────────
Unified Intake workbench             SearchForge RAG /api/query
PRODUCT_ONLY=1                       platform_full / RUN_DEMO_LAB=1
Postgres cases                       Qdrant experiments
deploy_paid_pilot.sh                 start_all.sh, make ci
/readyz intake_path_ready            GET /ready full-stack
scripts/operator/                    scripts/lab/
```

**When in doubt:** [`OPERATOR_IGNORE_LIST.md`](./runbooks/OPERATOR_IGNORE_LIST.md)

---

## Next steps (after 15 min)

1. Read [`goals/insurance_paid_pilot_goal.md`](./goals/insurance_paid_pilot_goal.md)
2. Skim `services/fiqa_api/inbox_triage/` entry points (do not rewrite triage.py on day one)
3. Run guardrail before any intake change

*End of onboarding*
