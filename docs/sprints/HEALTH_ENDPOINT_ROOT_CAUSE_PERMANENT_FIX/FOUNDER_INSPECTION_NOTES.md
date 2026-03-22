# Founder Inspection Notes

**Plain language — what happened**

## What you were seeing

After deploy, scripts said **`/healthz` failed** (404). That felt like the backend was broken or routes were wrong.

## What was actually wrong

The backend **does** define `/healthz`. On **Cloud Run’s public URL**, Google’s front door often answers `/healthz` itself with a **Google 404 web page** — the request **never hits your container**.  

That is why **`/readyz` and `/health/live` worked**: those paths are not blocked the same way, so they reach FastAPI and return JSON.

## How to think about it

- **Liveness (“is the service up?”)** → use **`/health/live`** (or **`/api/healthz`** after this deploy).  
- **Readiness (“are dependencies OK for RAG?”)** → still **`/readyz`**, with the usual DEMO_MODE nuance for triage-only.

## What we changed (high level)

- Deploy checks and Docker healthcheck now follow that contract.  
- Added **`/api/healthz`** so anything that still wants the word “healthz” hits a path that **reaches the app** on Cloud Run.  
- Runbooks now warn: **don’t trust public `/healthz` on Cloud Run.**

## Trust model going forward

| Check | Trust on Cloud Run? |
|-------|---------------------|
| `/health/live` | **Yes** (liveness) |
| `/api/healthz` | **Yes** (after redeploy; liveness alias) |
| `/readyz` | **Yes** (readiness signal; interpret per DEMO_MODE) |
| `/healthz` | **No** as sole signal (may be Google 404) |
