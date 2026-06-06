# Andy Quick Start — Unified Intake (Local)

One file before running the **Unified Intake** workbench locally.

**Product:** inbox triage + case workbench — **not** the SearchForge RAG lab (that is optional at `/demo`).

**Runtime path:** Default = **8001** (`run_demo_local.sh`). Docker **8000** = legacy lab stack. Recovery = `bash scripts/restore_8001_readiness.sh`. See `docs/runbooks/RUNTIME_PATH_STANDARD.md`.

**Recommended local pilot posture** (matches Cloud Run; add to `.env`):

```bash
UNIFIED_INTAKE_PRODUCT_ONLY=1
UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
```

Intake triage works **without Qdrant**. Vectors are only for notice/knowledge wedge and the `/demo` page. See `configs/demo.env.example` — LOCAL RECOMMENDED block.

**Ignore list:** `docs/runbooks/OPERATOR_IGNORE_LIST.md`

## 1. Run demo prep

**Default (recommended):**
```bash
bash scripts/demo_pre_checklist.sh
```
Runs guardrail + validation (if backend up) + writes checklist. Output: `results/demo_pre_checklist/<timestamp>/CHECKLIST.md`.

**Quick (backend already up, ~30 sec):**
```bash
bash scripts/demo_prep_one_command.sh
```

- **If "Use Live path" or "Ready for Live Demo"** → Open http://localhost:5173/workbench/unified-intake (product) or http://localhost:5173/demo (optional RAG wedge).
- **If "Use Offline path"** → Either use offline (click recommended questions) or fix live (see below).

## 2. Start demo (if not already running)

```bash
bash scripts/run_demo_local.sh
```

Or, for **local Qdrant** (no Cloud):

```bash
USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh
```

*(Requires: `docker compose up -d qdrant` and `bash scripts/seed_local_qdrant.sh` first.)*

## 3. URLs

| URL | Use |
|-----|-----|
| **http://localhost:5173/workbench/unified-intake** | **Product** — intake workbench |
| http://localhost:5173/demo | Optional RAG Q&A wedge (needs vectors for live mode) |

## 4. If live fails

**embedding_warming / 503:** Run `bash scripts/restore_8001_readiness.sh` (one-command recovery). Requires local Qdrant + seeded collection.

**Other:** Use **Offline mode**: click the 5 recommended questions in order. Demo works with preset answers. (Offline pack has 5 questions; run `python3 scripts/snapshot_demo_answers.py` to refresh.)

See `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` and `docs/BROKER_DEMO_FALLBACK_SCRIPT.md`.

## 5. Full docs

- `docs/BROKER_DEMO_SCRIPT_15MIN.md` — demo flow
- `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` — offline mode
- `docs/ANDY_2MIN_BEFORE_DEMO.md` — 2-minute checklist
- `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` — troubleshooting
