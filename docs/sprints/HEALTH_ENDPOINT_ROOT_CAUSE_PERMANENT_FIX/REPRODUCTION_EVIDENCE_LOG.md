# Reproduction / Evidence Log

**Date:** 2026-03-22  
**Environment:** WSL2; public HTTPS requests to Cloud Run service `fiqa-api-g7zatxrycq-uw.a.run.app` (example URL from repo scripts).

## Directly reproduced (HTTPS, public Cloud Run)

| Request | HTTP status | Response body (characterization) |
|---------|-------------|--------------------------------|
| `GET /healthz` | **404** | **Google** HTML error page (“Error 404 (Not Found)!!1”, `www.google.com` styling) — **not** `{"detail":"Not Found"}` |
| `GET /healthz/` | **307** | Redirect to `http://…/healthz` (strip SSL) → still broken chain for external checks |
| `GET /readyz` | **200** | JSON from app (readiness payload) |
| `GET /health/live` | **200** | JSON `{"ok":true}` from app |
| `GET /api/healthz` (before code deploy) | **404** | FastAPI JSON `{"detail":"Not Found"}` — proves request **reached** the app (no route yet) |
| `GET /livez` | **404** | Google HTML 404 (same family as `/healthz`; not used as contract) |

## Inferred from code (not HTTP-reproduced in this log)

| Item | Inference |
|------|-----------|
| Local `/healthz` | Expected **200** when uvicorn serves `app_main:app` — routes are registered (verified by introspecting `app.routes`). |
| SPA mount | If `frontend/dist` exists, catch-all `/{full_path:path}` is registered; previous skip used `startswith("health")` which matches **`healthz`** — corrected in sprint to explicit `healthz` / `readyz` + `health/` (defensive ordering / clarity). |

## Classification

| Observation | Type |
|---------------|------|
| Google HTML on `/healthz` | **Direct** |
| `/readyz` 200 JSON | **Direct** |
| `/health/live` 200 JSON | **Direct** |
| App defines `/healthz` in Python | **Code** |
| Duplicate `/healthz` registration | **Code** |

## Mismatch summary

**Symptom:** “`/healthz` 404 in production.”  
**Reality:** For Cloud Run **public** URL, `/healthz` often fails at **Google’s HTTP frontend**, so the container never sees the request. Deploy scripts that treat that 404 as “app unhealthy” are **misleading**.
