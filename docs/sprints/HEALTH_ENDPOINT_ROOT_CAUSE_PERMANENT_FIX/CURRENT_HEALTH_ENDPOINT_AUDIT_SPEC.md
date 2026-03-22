# Current Health Endpoint Audit Spec

**Date:** 2026-03-22  
**App entrypoint (Cloud Run):** `uvicorn services.fiqa_api.app_main:app` (`services/fiqa_api/Dockerfile.cloudrun`)

## Questions this audit must answer

| # | Question | Answer (evidence-based) |
|---|----------|-------------------------|
| 1 | Is `/healthz` defined in app code? | **Yes**, twice: `@app.get("/healthz")` in `app_main.py` and `@router.get("/healthz")` in `health/ready.py` included via `app.include_router(health_router)`. |
| 2 | Is `/readyz` defined? | **Yes**, `health/ready.py` `@router.get("/readyz")`, mounted at app root (no prefix). |
| 3 | Is `/health/live` defined? | **Yes**, `app_main.py` `@app.get("/health/live")`. |
| 4 | Are routes under path prefixes? | **No prefix** for `/healthz`, `/readyz`, `/health/live` — all top-level. |
| 5 | Does deploy script assume `/healthz`? | **Yes** — `scripts/deploy_rag_demo.sh` and `scripts/deploy_and_verify_cloud_run.sh` (pre-fix) used `curl …/healthz`. |
| 6 | Code vs “production truth” drift? | **Yes** — code says `/healthz` exists; **public Cloud Run URL** can still return **Google HTML 404** for `/healthz` (see evidence log). |

## File / function evidence

| Endpoint | Location |
|----------|----------|
| `/healthz` (app) | `services/fiqa_api/app_main.py` — `async def healthz()` |
| `/healthz` (router) | `services/fiqa_api/health/ready.py` — `async def health_check()` |
| `/readyz` | `services/fiqa_api/health/ready.py` — `async def readiness_check()` |
| `/health/live` | `services/fiqa_api/app_main.py` — `async def health_live()` |
| `/health`, `/health/ready` | `services/fiqa_api/app_main.py` |
| SPA catch-all | `services/fiqa_api/app_main.py` — `serve_spa` on `/{full_path:path}` when `frontend/dist` exists |

## Docker / probes

| Artifact | Before sprint | Notes |
|----------|---------------|--------|
| `Dockerfile.cloudrun` `HEALTHCHECK` | `curl …/healthz` | Hits **localhost** inside container — typically reaches uvicorn (not Google edge). |
| Cloud Run external `curl` | `/healthz` | Can fail **before** container (see evidence). |

## Duplicate `/healthz`

Two handlers register the same path. Starlette keeps both entries; the **first registered** route wins for matching. This is technical debt but **not** the cause of Cloud Run’s Google 404 (response body is Google HTML, not FastAPI JSON).
