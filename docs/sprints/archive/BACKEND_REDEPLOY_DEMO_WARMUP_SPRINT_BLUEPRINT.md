# Backend Redeploy + Demo Warmup Sprint — Blueprint

**Sprint:** Backend Redeploy + Demo Warmup  
**Theme:** Ship backend changes, validate warmup, improve demo-day reliability  
**Budget:** 20–40 min

---

## Why Backend Redeploy Matters Now

- Latest high-value backend changes are implemented but not yet live:
  - **Turn 1 lightweight first-pass** — rule-based path for high-confidence Turn 1 messages (avoids LLM latency on cold start)
  - **Mixed-intent fallback** — when 2+ flow markers present, routes to LLM (avoids rule-path misclassification)
  - **Improved warmup script** — realistic triage payload, warms both fast and LLM paths
- Deploying now ensures founder demo uses the improved Turn 1 behavior and warmup flow.

---

## Why Warmup Matters Now

- Cloud Run uses `min_instances=0` (cost-safe) → first request after idle = cold start (5–15 s)
- Demo-day first impression: slow Turn 1 = bad impression
- `warmup_for_demo.sh` touches `/healthz`, `/readyz`, `/api/inbox/triage` 2–3 min before demo
- Validating warmup flow ensures founder has a practical, documented step to reduce risk.

---

## What "Good Enough for Demo Day" Means

- Backend is live at Cloud Run URL
- `/healthz` and `/readyz` return OK
- Triage API returns valid triage output for a realistic Turn 1 payload
- Warmup script runs successfully against live backend
- Founder has clear pre-demo steps in `ANDY_2MIN_BEFORE_DEMO.md` and `COLD_START_DEMO_DAY_RUNBOOK.md`

---

## In Scope

- Create Sprint Blueprint, Execution Outline, Acceptance Criteria
- Pre-deploy validation (inbox triage scenarios, guardrail, smoke check)
- Backend redeploy via `deploy_rag_demo.sh`
- Post-deploy verification (health, triage, Turn 1 path observation)
- Demo warmup execution and evaluation
- Optional second loop for one small, high-value fix
- Final operational judgment and report

---

## Out of Scope

- New feature development
- Broad polish or unrelated changes
- Changing min_instances or Cloud Run config
- Frontend changes
