# Acceptance Criteria

**Sprint passes only if all are true.**

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | Root cause **explicitly identified** | Google frontend HTML 404 on public `/healthz`; app routes still registered |
| 2 | **One clear canonical contract** for Cloud Run liveness + readiness | Liveness: `/health/live` (+ `/api/healthz` alias); Readiness: `/readyz` |
| 3 | Deploy script **aligned** with production truth | `deploy_rag_demo.sh` checks `/health/live` first |
| 4 | Health checks **no longer fail for wrong reason** | No “app broken” conclusion solely from public `/healthz` 404 |
| 5 | Founder-readable explanation exists | `FINAL_REPORT.md` + `FOUNDER_INSPECTION_NOTES.md` |

## Post-deploy verification (operator)

After next Cloud Run deploy:

```bash
curl -sf "https://<YOUR_SERVICE_URL>/health/live" && echo OK
curl -sf "https://<YOUR_SERVICE_URL>/api/healthz" && echo OK
curl -sS "https://<YOUR_SERVICE_URL>/readyz" | head -c 200; echo
```

Optional: `GET /healthz` may still show Google 404 — **do not** treat as app regression if above pass.
