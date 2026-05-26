# Permanent Fix Decision Spec

**Date:** 2026-03-22  

## Root-cause judgment (single choice)

**Category D + platform constraint:** The **intended app-standard** liveness checks live in FastAPI, but **top-level `/healthz` is not a reliable public URL on Google Cloud Run** because Google’s HTTP frontend returns its own **HTML 404** for that path — the request **does not reach uvicorn**.  

This is **not** “FastAPI forgot to register `/healthz`” and **not** primarily cold start.

## Allowed outcomes (sprint decision)

| Option | Decision |
|--------|----------|
| A. Restore public `/healthz` on Cloud Run | **Not feasible** from application code alone — the failure is **before** the container. |
| B. Retire `/healthz` as **Cloud Run canonical** | **Chosen** — canonical **liveness** for ops: `GET /health/live` (and alias `GET /api/healthz`). |
| C. Readiness | **Unchanged canonical:** `GET /readyz` (with existing DEMO_MODE semantics documented elsewhere). |

## Contract going forward

| Concern | Canonical URL | Notes |
|---------|---------------|--------|
| **Liveness** (process up, no deps) | `/health/live` | Stable on public Cloud Run URL. |
| **Liveness alias** (name `healthz`, reaches container) | `/api/healthz` | Same body semantics as `/health/live` (`{"ok": true}`). |
| **Readiness / dependency signal** | `/readyz` | May be `ok: false` for RAG deps; intake semantics per DEMO_MODE docs. |
| **Legacy local / docs** | `/healthz` | Still registered in app for local and non-CR; **do not** use as sole Cloud Run probe. |

## Alignment checklist (implemented in repo)

- [x] Deploy script uses `/health/live` first, then `/api/healthz`, then optional `/healthz`.  
- [x] Docker `HEALTHCHECK` uses `/health/live` (container-local; already bypasses Google edge).  
- [x] `KNOWN_DEPLOYMENT_GOTCHAS.md` + `DEPLOYMENT_PLAYBOOK.md` updated.  
- [x] SPA skip-list hardened so `health` prefix does not accidentally match `healthz`.  

## Explicit non-decisions

- Removing duplicate `/healthz` registrations — **deferred** (behavioral change risk; not required to fix Cloud Run false alarms).
