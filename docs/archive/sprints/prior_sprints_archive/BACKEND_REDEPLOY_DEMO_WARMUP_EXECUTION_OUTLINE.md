# Backend Redeploy + Demo Warmup — Execution Outline

---

## Workstreams

| # | Workstream | Owner | Deliverable |
|---|------------|-------|-------------|
| 1 | Control docs | Planner | Blueprint, Outline, Acceptance |
| 2 | Pre-deploy check | Backend | Files confirmed, validations pass |
| 3 | Backend deploy | Deploy worker | Cloud Run live, URL captured |
| 4 | Post-deploy verify | Runtime worker | healthz, readyz, triage, Turn 1 |
| 5 | Warmup execution | Runtime worker | Warmup run, runbook clarity |
| 6 | Optional second loop | QA | One small fix if worthwhile |
| 7 | Final judgment | Product reviewer | Report, risk summary, next steps |

---

## Deployment Sequence

1. Load `.env.cloudrun` (required)
2. Validate gcloud, Qdrant, Dockerfile
3. Build image via Cloud Build
4. Deploy to Cloud Run
5. Capture service URL and revision
6. Run health checks (healthz, readyz)

---

## Warmup Sequence

1. Call `warmup_for_demo.sh` with `--url <Cloud Run URL>`
2. Verify: healthz OK, readyz OK, triage OK
3. Confirm runbook references warmup for Cloud Run

---

## Verification Sequence

1. **Pre-deploy:** run_inbox_triage_scenarios, guardrail_inbox_triage, unified_intake_smoke_check
2. **Post-deploy:** curl healthz, readyz, POST /api/inbox/triage
3. **Turn 1 path:** Send high-confidence payload → expect `triage_path: "fast"` when LLM enabled
4. **Mixed-intent:** Send payload with 2+ flow markers → expect `triage_path: "llm"`

---

## Likely Loop Count

- **Loop 1:** Deploy + verify + warmup (primary)
- **Loop 2:** Optional — one small fix (runbook wording, warmup payload, verification step)
