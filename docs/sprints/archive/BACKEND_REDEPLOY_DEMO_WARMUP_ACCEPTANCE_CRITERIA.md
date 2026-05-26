# Backend Redeploy + Demo Warmup — Acceptance / SLA Criteria

---

## Successful Backend Deploy

- `bash scripts/deploy_rag_demo.sh` completes without error
- Service URL returned and reachable
- `/healthz` returns 200
- `/readyz` returns 200 (or acceptable skip if Qdrant still warming)

---

## Successful Warmup

- `bash scripts/warmup_for_demo.sh --url <Cloud Run URL>` completes
- All three steps report OK (or SKIP with clear reason)
- Triage response contains `issue_category` and valid structure

---

## Acceptable Demo Readiness

- Founder can run warmup 2–3 min before demo
- Runbook (`COLD_START_DEMO_DAY_RUNBOOK.md`) and `ANDY_2MIN_BEFORE_DEMO.md` reference warmup for Cloud Run
- First Turn 1 after warmup should feel fast (no cold-start surprise)

---

## Acceptable vs Unacceptable Risk

| Acceptable | Unacceptable |
|------------|--------------|
| readyz may take a few seconds after deploy | healthz fails |
| Warmup SKIP if backend not running | Warmup fails when backend is up |
| One validation script flaky (document, retry) | All validations fail |
| Turn 1 path not directly observable in prod (inferred from code) | Triage API returns 500 |
