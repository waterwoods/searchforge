# Runtime Path Standard — Broker Demo

Single source of truth for backend ports. **Andy should not have to think about ports during normal work.**

| Path | Port | When to use |
|------|------|-------------|
| **Default local dev/demo/validation** | **8001** | `run_demo_local.sh`, demo prep, broker regression, validation scripts |
| **Docker / alternate** | 8000 | `docker compose up rag-api`, containerized backend |
| **Recovery** | 8001 | When 8001 returns 503 `embedding_warming` (Qdrant Cloud down) |

## Rules

1. **Default path = 8001.** Use `bash scripts/run_demo_local.sh` for broker demo. Vite proxy targets 8001.
2. **Docker path = 8000.** If using Docker backend, set `VITE_API_PROXY_TARGET=http://127.0.0.1:8000` for UI; validation scripts accept `--port 8000`.
3. **Recovery path:** If 8001 is not ready (embedding_warming, Qdrant path issues):
   ```bash
   bash scripts/restore_8001_readiness.sh
   ```
   Requires local Qdrant + seeded collection (`docker compose up -d qdrant`, `bash scripts/seed_local_qdrant.sh`).

## Quick reference

- Start demo: `bash scripts/run_demo_local.sh` → backend 8001, UI 5173
- Validate: `bash scripts/demo_quick_validate.sh` (default 8001)
- Recovery: `bash scripts/restore_8001_readiness.sh`
- Troubleshooting: `docs/ANDY_IF_SOMETHING_GOES_WRONG.md`
