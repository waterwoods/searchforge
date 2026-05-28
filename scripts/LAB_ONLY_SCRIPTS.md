# Lab-Only Scripts — Safe to Ignore for Paid Pilot

**Product path:** [`scripts/README_OPERATOR.md`](./README_OPERATOR.md)

These categories exist for SearchForge R&D history. They do **not** block broker trial or paid pilot.

---

## Legacy local dev (wrong ports / branding)

| Script | Why ignore |
|--------|------------|
| `start_all.sh` | SearchForge branding; backend **8011**; use `run_demo_local.sh` (**8001**) |
| `stop_all.sh`, `health_check.sh` | Paired with `start_all.sh` |
| `dev_local.sh` | Full SearchForge local dev surface |
| `start_services.sh` | Old multi-service bootstrap |

---

## Legacy deploy (superseded)

| Script | Use instead |
|--------|-------------|
| `deploy_rag_demo.sh` | `deploy_paid_pilot.sh` |
| `deploy_cloud_run_core.sh` | Impl only — `deploy_paid_pilot.sh` |
| `deploy_cloud_run.sh` | Legacy SearchForge name |
| `deploy_and_verify_cloud_run.sh` | Old verify flow |

---

## RAG / vector / GPU lab

| Pattern | Examples |
|---------|----------|
| Qdrant seed/migrate | `seed_local_qdrant.sh`, `migrate_local_qdrant_to_cloud.py` |
| GPU / proxy smoke | `gpu_worker_smoke.py`, `wait_for_gpu_ready.sh`, `quick_backend_smoke.sh` |
| ETF `/api/query` smoke | `ci_smoke.sh`, `smoke_cloud_run.sh` (old paths) |
| Experiment runners | `run_*_simulation*.py`, `run_*_battery*.py` |

---

## Sprint regression batteries

Most `run_add_car_*`, `run_*_ab_scenarios.py`, `run_*_sprint*.py` files are **engineering regression** — run via guardrail or CI, not at 2am.

---

## Makefile targets (lab)

Root [`Makefile`](../Makefile) / [`Makefile.lab`](../Makefile.lab): `make ci`, `make gpu-smoke`, `make proxy-smoke`, AutoTuner, graph steward, FiQA import.

**Index:** [`docs/archive/platform/README_LAB_INFRA.md`](../docs/archive/platform/README_LAB_INFRA.md)
