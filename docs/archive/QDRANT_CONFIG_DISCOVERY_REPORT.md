# Qdrant Config Discovery Report

**Generated**: 2026-03-06  
**Scope**: Insurance demo environment — find existing Qdrant config and prior working setup  
**Method**: Focused config-discovery pass (no product code changes)

---

## 1. Existing Config Files Found

| File | Exists | Qdrant-related vars | Secrets populated |
|------|--------|---------------------|-------------------|
| `.env.cloudrun` | ✅ Yes | QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION | ✅ Yes (real values) |
| `.env` | ✅ Yes | None | N/A |
| `.env.example` | ✅ Yes | QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION | Blank placeholders |
| `.env.current` | ✅ Yes | None (GPU/TORCH/OPENAI) | N/A |
| `configs/demo.env.example` | ✅ Yes | QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION | Blank placeholders |
| `.env.cloudrun.test` | ✅ Yes | Not checked | — |
| `.env.sample` | ✅ Yes | Not checked | — |
| `ui/.env.local` | ✅ Yes | N/A (frontend) | — |
| `ui/.env.example` | ✅ Yes | N/A | — |

### `.env.cloudrun` contents (Qdrant section)

```
QDRANT_URL=https://***.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=<from Qdrant Cloud dashboard>
QDRANT_COLLECTION=fiqa_10k_v1
```

**Conclusion**: Qdrant config exists and is populated. Qdrant Cloud URL and API key are set.

---

## 2. Existing Env Loading Paths

| Script / Component | Env loading | Uses Qdrant vars |
|--------------------|-------------|------------------|
| `scripts/run_demo_local.sh` | `source .env` then `source .env.cloudrun` (lines 21–29) | ✅ Inherited by child (uvicorn) |
| `services/fiqa_api/app_main.py` | `load_dotenv(Path(".env.cloudrun"))` then `load_dotenv()` (lines 28–33) | ✅ Loads into `os.environ` before imports |
| `scripts/deploy_rag_demo.sh` | `set -a; source .env.cloudrun; set +a` (lines 38–43) | ✅ |
| `scripts/run_demo_ingest_oneclick.sh` | `source .env` then `source .env.cloudrun` (lines 41–47) | ✅ |
| `scripts/e2e_zh_demo_check.sh` | `source .env` then `source .env.cloudrun` (lines 35–41) | ✅ |
| `scripts/run_auto_insurance_daily.sh` | `set -a; source .env.cloudrun` (lines 28–30) | ✅ |
| `scripts/restart_backend_with_translation.sh` | `source .env.cloudrun` (lines 39–44) | ✅ |
| `scripts/build_demo_core_collection.py` | `load_dotenv()` then `load_dotenv(.env.cloudrun)` (lines 48–52) | ✅ |
| `scripts/check_qdrant_env.py` | `load_dotenv()` then `load_dotenv(.env.cloudrun)` | ✅ |

### Current validation path vs env loading

The validation run used:

```bash
cd /home/andy/searchforge && (test -f .env && set -a && source .env && set +a; true) && (test -f .env.cloudrun && set -a && source .env.cloudrun && set +a; true) && TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn ...
```

**Issue**: The `( ... )` subshells run `source` in a child process. Exported vars do not persist to the parent shell. The `python3 -m uvicorn` process therefore did not inherit `QDRANT_URL` / `QDRANT_API_KEY` from the shell.

**Mitigation**: `app_main.py` loads `.env.cloudrun` via `load_dotenv(Path(".env.cloudrun"))` at startup. That reads from the filesystem and does not depend on shell env. So the Python process should still get Qdrant vars if:

1. CWD is the repo root when uvicorn starts
2. `.env.cloudrun` exists at `./.env.cloudrun`

**Correct path**: Use `bash scripts/run_demo_local.sh`, which sources `.env` and `.env.cloudrun` in the same shell before starting uvicorn, so the child process inherits all vars.

---

## 3. Existing Collection Names Found

| Collection | Where referenced | Purpose |
|------------|-----------------|---------|
| `auto_insurance_demo_core` | `routes/query.py`, `search_core.py`, `run_demo_ingest_oneclick.sh`, `build_demo_core_collection.py`, `e2e_zh_demo_validate.py` | **Insurance demo** — used when `mode=demo` |
| `demo_auto_insurance` | `routes/query.py`, `search_core.py` | Alias → `auto_insurance_demo_core` |
| `auto_insurance_v1` | `verify_auto_insurance_collection.py`, `sanity_check_auto_insurance_v1.py`, pipelines, reports | Older collection (17 docs in reports) |
| `auto_insurance_v2_clean` | `run_auto_insurance_daily.sh`, `search_core.py`, daily pipeline | Daily automation / quality gate |
| `fiqa_10k_v1` | `configs/demo.env.example`, `QDRANT_COLLECTION` default | FiQA demo |

### Insurance demo collection

- **Active collection**: `auto_insurance_demo_core`
- **Selection**: `mode=demo` in `/api/query` forces `collection_name = "demo_auto_insurance"` → `auto_insurance_demo_core`
- **`QDRANT_COLLECTION`**: Not used for demo mode. Demo always uses `auto_insurance_demo_core` regardless of `QDRANT_COLLECTION`.

---

## 4. Prior Evidence of Working Setup

| Source | Evidence |
|--------|----------|
| `results/demo_quick_validate/2026-02-21_223652/REPORT.md` | **PASS** — all 3 questions with gov+insurer diversity |
| `results/auto_insurance/FINAL_DEPLOYMENT_SECRETS_SUMMARY.md` | `.env.cloudrun` created, QDRANT_URL/API_KEY set |
| `results/auto_insurance/SECRET_MANAGEMENT_REPORT.md` | QDRANT_URL, QDRANT_API_KEY validated |
| `results/auto_insurance/CLOUD_UPSERT_REPORT.md` | Collection `auto_insurance_v1` created in Qdrant Cloud |
| `results/opencrawl_demo_ingest/2026-02-21_152711/INGEST_REPORT.md` | Ingest to `auto_insurance_demo_core` |
| `docs/QDRANT_CLOUD_MIGRATION.md` | Same cluster URL format as `.env.cloudrun` |
| `results/auto_insurance/CLOUD_UPSERT_REPORT.md` (line 122) | Example: `QDRANT_URL` + `QDRANT_API_KEY` used successfully |

---

## 5. Why the Current Validation Missed It

| Factor | Explanation |
|--------|-------------|
| **Wrong startup path** | Validation used a manual uvicorn start with subshell `source`; vars were not inherited. |
| **Timing** | `embedding_warming` occurs because queries ran before `EMBED_READY` (embedding warmup in background). |
| **Async startup** | `_do_startup()` is scheduled with `create_task()` and not awaited; server accepts requests before clients are ready. |
| **Config not missing** | `.env.cloudrun` exists with valid Qdrant Cloud URL and API key. |
| **CWD** | If uvicorn was started from a different CWD, `Path(".env.cloudrun")` might not resolve to the repo root. |

### Root cause summary

1. **embedding_warming**: Queries hit the API before the embedding model finished warming (background thread).
2. **qdrant_connected: false**: Either clients were not initialized yet (async startup) or the readiness check ran before `initialize_clients()` completed.

---

## 6. Smallest Fix to Restore Prior Working Setup

### Option A (recommended): Use the existing launcher

```bash
cd /home/andy/searchforge
bash scripts/run_demo_local.sh
```

- Sources `.env` and `.env.cloudrun` in the same shell
- Starts backend on 8001 and UI on 5173
- Child process inherits `QDRANT_URL`, `QDRANT_API_KEY`

Then, in another terminal:

```bash
# Wait 90–120 seconds for embedding warmup
sleep 90
bash scripts/demo_quick_validate.sh
```

### Option B: Manual start with correct env loading

```bash
cd /home/andy/searchforge
set -a
[ -f .env ] && source .env
[ -f .env.cloudrun ] && source .env.cloudrun
set +a
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

Then wait 90–120 seconds before running `demo_quick_validate.sh`.

### Option C: Ensure CWD for `load_dotenv`

If starting from a different directory, use an absolute path:

```bash
cd /home/andy/searchforge
TRANSLATION_ENABLED=1 TRANSLATION_PROVIDER=argos python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8001
```

`load_dotenv(Path(".env.cloudrun"))` uses CWD; running from the repo root is sufficient.

### Checklist

- [ ] Use `run_demo_local.sh` or source `.env.cloudrun` in the same shell as uvicorn
- [ ] Wait 90–120 seconds after backend start before validation
- [ ] Ensure `auto_insurance_demo_core` has data: `bash scripts/run_demo_ingest_oneclick.sh` if needed
- [ ] No changes to `.env.cloudrun` required; config is already correct
