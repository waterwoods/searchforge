# SearchForge Lab Infrastructure — Physical Separation Index

**Status:** LAB ONLY — not Unified Intake paid pilot  
**Product path:** [`README.md`](../../README.md) → `bash scripts/run_demo_local.sh` (port **8001**)

---

## What lives here (root-level lab history)

| Item | Purpose | Product alternative |
|------|---------|---------------------|
| [`Makefile`](../../Makefile) / [`Makefile.lab`](../../Makefile.lab) | SearchForge R&D: GPU, AutoTuner, Qdrant CI, graph steward, proxy smoke | `bash scripts/run_demo_local.sh` |
| [`docker-compose.yml`](../../docker-compose.yml) / [`docker-compose.lab.yml`](../../docker-compose.lab.yml) | Full lab stack: Qdrant, Milvus, Redis, GPU worker, rag-api on **8000** | Local dev without compose on **8001** |
| [`experiments/`](../../experiments/) | RAG / tuner / proxy experiments | Not needed for intake triage |
| [`modules/autotuner/`](../../modules/autotuner/) | AutoTuner brain | Hidden in product-only UI |
| [`jobhunter-clipper/`](../../jobhunter-clipper/) | Separate chrome extension lab | Ignore for broker pilot |
| [`docs/archive/README_LEGACY_SEARCHFORGE_LAB.md`](../README_LEGACY_SEARCHFORGE_LAB.md) | Old 1,500-line README | Current [`README.md`](../../README.md) |

---

## When to use lab infra

- Local RAG experiments (`POST /api/query`, `/demo` page)
- Qdrant seeding, GPU worker, retrieval proxy benchmarks
- `RUN_DEMO_LAB=1 bash scripts/run_demo_local.sh`

---

## When NOT to use (paid pilot / broker trial)

| Do instead | Not this |
|------------|----------|
| `bash scripts/deploy_paid_pilot.sh` | `make up`, `deploy_cloud_run.sh` |
| `GET /health/live` + `/readyz` (`intake_path_ready`) | `GET /ready` (full RAG gate) |
| `bash scripts/trial_launch_check.sh` | `make ci`, `make gpu-smoke` |

---

## Related

- [`docs/runbooks/OPERATOR_IGNORE_LIST.md`](../../runbooks/OPERATOR_IGNORE_LIST.md)
- [`docs/archive/root_archaeology/INDEX.md`](../root_archaeology/INDEX.md) — old root audit/recon reports
