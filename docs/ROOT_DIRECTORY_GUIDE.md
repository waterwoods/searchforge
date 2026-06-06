# Root Directory Guide — What Matters at Clone Time

**Purpose:** Reduce "platform warehouse" feeling when opening the repo root.  
**Runtime truth:** [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md)  
**Founder path:** [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md)  
**Broker path:** [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md)

---

## What matters (product)

| Path | Role |
|------|------|
| [`README.md`](../README.md) | Front door — Unified Intake |
| [`AGENTS.md`](../AGENTS.md) | Agent/engineer entry |
| [`docs/CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md) | Runtime truth |
| [`docs/runbooks/`](./runbooks/) | Operator runbooks |
| [`docs/trial/`](./trial/) | Broker trial package |
| [`scripts/run_demo_local.sh`](../scripts/run_demo_local.sh) | Local product launcher |
| [`scripts/deploy_paid_pilot.sh`](../scripts/deploy_paid_pilot.sh) | Paid pilot deploy |
| [`services/fiqa_api/`](../services/fiqa_api/) | Backend (inbox triage) |
| [`ui/`](../ui/) | Workbench frontend |
| [`configs/demo.env.example`](../configs/demo.env.example) | Env template |
| [`scripts/operator/`](../scripts/operator/) | Product script tier |

---

## What does not matter (for paid pilot)

| Path | Label | Notes |
|------|-------|-------|
| [`experiments/`](../experiments/) | LAB ONLY | R&D benchmarks — README present |
| [`agents/`](../agents/) | LAB ONLY | Agent Studio — not mounted product_only |
| [`orchestrators/`](../orchestrators/) | LAB ONLY | SearchForge orchestration |
| [`pipelines/`](../pipelines/) | LAB ONLY | Offline pipelines |
| [`engines/`](../engines/) | LAB ONLY | Retrieval engines |
| [`modules/autotuner/`](../modules/autotuner/) | LAB ONLY | AutoTuner R&D |
| [`mcp/`](../mcp/) | LAB ONLY | MCP servers |
| [`k8s/`](../k8s/) | LAB ONLY / historical | K8s manifests — not paid pilot path |
| [`ml_models/`](../ml_models/) | LAB ONLY | Model artifacts |
| [`jobhunter-clipper/`](../jobhunter-clipper/) | LAB ONLY / unrelated | Different vertical experiment |
| [`results/`](../results/) | Scratch | Trial logs + old benchmarks — README present |
| [`.runs/`](../.runs/) | LAB ONLY | Tuner/experiment artifacts — README present |
| [`Makefile`](../Makefile) + [`Makefile.lab`](../Makefile.lab) | LAB | Use `run_demo_local.sh` for product |
| [`docker-compose.yml`](../docker-compose.yml) | LAB (full stack) | Use [`docker-compose.product.yml`](../docker-compose.product.yml) or no Docker |
| [`docker-compose.lab.yml`](../docker-compose.lab.yml) | LAB | Symlink → full stack |
| [`archives/`](../archives/) | Historical | Old snapshots — not docs/archive |
| [`.qdrant/`](../.qdrant/) | LAB / local | Vector storage when using local Qdrant |

---

## Founders should ignore

Platform blueprints (`docs/archive/platform/`), sprint archaeology (`docs/archive/sprints/`), Makefile.ci/gpu-smoke, `start_all.sh`/`dev_local.sh`, full docker-compose services list, jobhunter-clipper, ~992 archived markdown files, repo name "searchforge".

**Read instead:** [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md)

---

## Operators should ignore

`GET /ready`, Qdrant red with `intake_path_ready:true`, `scripts/lab/*`, legacy deploy names, lab UI routes, ETF smoke scripts, `.runs/`, experiments/.

**Read instead:** [`runbooks/OPERATOR_CHEAT_SHEET.md`](./runbooks/OPERATOR_CHEAT_SHEET.md)

---

## New engineers should ignore

Until assigned lab work: experiments/, agents/, orchestrators/, pipelines/, engines/, run_* regression batteries (use guardrail first), docs/archive/platform blueprints, rewriting triage.py on day one.

**Read instead:** [`15_MINUTE_ENGINEER_ONBOARDING.md`](./15_MINUTE_ENGINEER_ONBOARDING.md)

---

## Docker mental model

| File | Stack |
|------|-------|
| **None (default)** | `bash scripts/run_demo_local.sh` → :8001 — **recommended** |
| `docker-compose.product.yml` | Minimal rag-api, product_only — optional |
| `docker-compose.lab.yml` / `docker-compose.yml` | Full SearchForge lab — GPU, Milvus, Qdrant, retrieval-proxy |

---

## Script tiers at `scripts/`

| Tier | Path | Purpose |
|------|------|---------|
| Operator | `scripts/operator/` | 10 product scripts |
| Founder | `scripts/founder/` | Demo + trial wrappers |
| Deploy | `scripts/deploy/` | Deploy guidance wrappers |
| Lab | `scripts/lab/` | LAB ONLY banner wrappers |
| Archive | `scripts/archive/` | Stub / historical pointer |
| Flat root | `scripts/*.sh` | Historical paths preserved — use tiers for discovery |

Map: [`scripts/DEEP_SCRIPT_TIER_MAP.md`](../scripts/DEEP_SCRIPT_TIER_MAP.md)

---

## product_only mount truth

When `UNIFIED_INTAKE_PRODUCT_ONLY=1`:

- **Mounted / used:** fiqa_api inbox triage, workbench UI, Postgres, deployment profile
- **Not mounted:** lab routers, AutoTuner API, graph runners, Agent Studio routes (UI hidden), GPU worker

Lab directories remain in repo for R&D — they are **labeled**, not deleted.

---

*End of root directory guide*
