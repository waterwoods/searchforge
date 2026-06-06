# Lab Script Index — SearchForge R&D

**Status:** LAB ONLY — not part of Unified Intake paid pilot path  
**Product operators:** [`scripts/README_OPERATOR.md`](./README_OPERATOR.md) (10 scripts)

---

## Wrappers in `scripts/lab/` (print LAB banner)

| Wrapper | Forwards to | Category |
|---------|-------------|----------|
| `start_all.sh` | `scripts/start_all.sh` | Legacy multi-service (port **8011**) |
| `dev_local.sh` | `scripts/dev_local.sh` | Full SearchForge local dev |
| `start_services.sh` | `scripts/start_services.sh` | Old multi-service bootstrap |
| `deploy_rag_demo.sh` | `scripts/deploy_rag_demo.sh` | Deprecated deploy name |
| `ci_smoke.sh` | `scripts/ci_smoke.sh` | ETF `/api/query` smoke |
| `warmup_for_demo.sh` | `scripts/warmup_for_demo.sh` | Vector/embed warming |
| `seed_local_qdrant.sh` | `scripts/seed_local_qdrant.sh` | Local Qdrant seed |
| `seed_qdrant.sh` | `scripts/seed_qdrant.py` | Qdrant seed (Python) |
| `run_full_regression.sh` | `scripts/run_full_regression.py` | Full regression battery |
| `run_canary_full_100.sh` | `scripts/run_canary_full_100.sh` | Canary lab |
| `wait_for_gpu_ready.sh` | `scripts/wait_for_gpu_ready.sh` | GPU readiness |
| `gpu_worker_smoke.sh` | `scripts/gpu_worker_smoke.py` | GPU smoke |
| `verify_milvus_lane.sh` | `scripts/verify_milvus_lane.sh` | Milvus lane |
| `graph_verify.sh` | `scripts/graph_verify.sh` | Graph verification |
| `autotuner_demo.sh` | `scripts/autotuner_demo.py` | AutoTuner demo |
| `stop_all.sh` | `scripts/stop_all.sh` | Paired with start_all |
| `health_check.sh` | `scripts/health_check.sh` | Lab stack health |
| `host_resource_triage.sh` | (local) | Host CPU/mem sampling |

**Full tier map:** [`DEEP_SCRIPT_TIER_MAP.md`](./DEEP_SCRIPT_TIER_MAP.md)

---

## High-confusion lab scripts (parent `scripts/` — no wrapper yet)

| Script | Why lab | Use instead |
|--------|---------|-------------|
| `stop_all.sh`, `health_check.sh` | Paired with `start_all.sh` | `run_demo_local.sh` |
| `deploy_cloud_run.sh` | Legacy SearchForge deploy | `deploy_paid_pilot.sh` |
| `deploy_cloud_run_core.sh` | Impl only | `deploy_paid_pilot.sh` |
| `deploy_and_verify_cloud_run.sh` | Old verify flow | `deploy_paid_pilot.sh` |
| `gpu_worker_smoke.py`, `wait_for_gpu_ready.sh` | GPU R&D | N/A for pilot |
| `run_*_simulation*.py`, `run_*_battery*.py` | Regression batteries | `guardrail_inbox_triage.sh` |
| `run_canary_full_100.sh` | Canary lab | N/A for pilot |
| `migrate_local_qdrant_to_cloud.py` | Vector migration | Optional wedge only |

---

## Makefile / Docker lab

| Entry | Note |
|-------|------|
| `make -f Makefile.lab help` | SearchForge lab targets |
| `docker compose -f docker-compose.lab.yml up rag-api` | Port **8000** legacy stack |
| `docker compose -f docker-compose.product.yml up rag-api` | Minimal product-only stack |
| `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh` | Full API surface on **8001** |

**Infra index:** [`docs/archive/platform/README_LAB_INFRA.md`](../docs/archive/platform/README_LAB_INFRA.md)

---

## Product path reminder

```bash
bash scripts/run_demo_local.sh                    # local workbench
bash scripts/deploy_paid_pilot.sh                 # Cloud Run paid pilot
bash scripts/trial_launch_check.sh                # before broker trial
bash scripts/guardrail_inbox_triage.sh            # intake guardrail
```

See: [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](../docs/runbooks/OPERATOR_IGNORE_LIST.md)
