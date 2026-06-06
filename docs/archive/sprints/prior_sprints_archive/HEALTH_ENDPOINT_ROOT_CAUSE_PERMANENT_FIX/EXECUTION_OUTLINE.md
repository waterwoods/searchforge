# Execution Outline

**Target budget:** 20–45 minutes  
**Mode:** inspect → reproduce → isolate → fix → verify → summarize (looped)

## Loop 1 — Audit

1. Grep repo for `healthz`, `readyz`, `health/live`, deploy scripts, Dockerfile.  
2. Read `app_main.py` mount order, `health/ready.py`, `Dockerfile.cloudrun` CMD.  
3. Answer audit spec table with **file:symbol** citations.

## Loop 2 — Reproduce

1. `curl -i` production Cloud Run URL for `/healthz`, `/readyz`, `/health/live`.  
2. Classify response: Google HTML vs FastAPI JSON.  
3. Record in evidence log.

## Loop 3 — Root cause

1. Eliminate app-route-missing hypothesis using code + `/api/...` probe behavior.  
2. Select single judgment (platform edge vs app).

## Loop 4 — Fix

1. Add **`GET /api/healthz`** liveness alias in `app_main.py` (delegates to `health_live`).  
2. Update `deploy_rag_demo.sh`, `deploy_and_verify_cloud_run.sh`, `smoke_cloud_run.sh`, `warmup_for_demo.sh`.  
3. Update `Dockerfile.cloudrun` `HEALTHCHECK` to `/health/live`.  
4. Update runbooks + gotchas; fix SPA exclusion logic for clarity.

## Loop 5 — Verify

1. Introspect `app.routes` for `/api/healthz`, `/health/live`.  
2. Re-run `curl` against production **after deploy** for `/api/healthz` (expected 200 once new revision is live).  
3. Confirm deploy script prints liveness OK without false “healthz FAILED” alarm.

## Loop 6 — Document

1. Write sprint folder artifacts + `FINAL_REPORT.md` with founder copy-paste block.
