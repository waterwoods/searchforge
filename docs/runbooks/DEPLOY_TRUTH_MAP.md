# Deploy Truth Map — Unified Intake

One screen. **Authority:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)

---

## Operator entries (only these)

| Goal | Script | Sets |
|------|--------|------|
| **Paid broker pilot** | `bash scripts/deploy_paid_pilot.sh` | `PRODUCT_ONLY=1`, `INTAKE_CORE_READINESS=1`, PG-primary, no DEMO_MODE |
| Local founder demo | `bash scripts/run_demo_local.sh` | Port 8001; may use JSON / platform_full |
| Demo cloud smoke | `bash scripts/deploy_demo_cloud_smoke.sh` | DEMO_MODE; not for paid pilot |
| Pre-trial gate | `bash scripts/trial_launch_check.sh` | Docs + guardrail + env posture |

---

## Not operator entries

| Script | Why |
|--------|-----|
| `deploy_cloud_run_core.sh` | Shared impl — wrappers call it |
| `deploy_rag_demo.sh` | Deprecated alias → core; prints warning |
| `deploy_cloud_run.sh` | Legacy SearchForge path |
| `deploy_and_verify_cloud_run.sh` | Internal verify wrapper |
| `start_all.sh`, `dev_local.sh`, … | Lab / old stack |

---

## Pre-deploy checklist

1. `PYTHONPATH=. python3 scripts/validate_pilot_deploy_env.py --env-file .env.cloudrun`
2. Postgres URL + both API keys in `.env.cloudrun`
3. `bash scripts/check_ui_node_version.sh` (Node 22 for UI)
4. `bash scripts/guardrail_inbox_triage.sh`

---

## Post-deploy checks

```bash
URL=<Cloud Run URL>
curl -sf "$URL/health/live"
curl -sf "$URL/readyz" | python3 -m json.tool
bash scripts/unified_intake_release_gate.sh "$URL" "https://<vercel-host>"
```

**Success:** liveness 200; `/readyz` shows `intake_path_ready: true` for paid pilot (even if `ok: false` without Qdrant).

---

## Frontend (Vercel)

| Env | Value |
|-----|-------|
| `VITE_API_BASE_URL` | Cloud Run URL, no trailing slash |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `1` for broker-facing UI |

```bash
source scripts/with_node22_path.sh
cd ui && npm run build && vercel --prod
```

---

## Topology

```
Browser (Vercel) → Cloud Run (fiqa-api) → Postgres (required)
                                      ↘ Qdrant (optional)
```

---

## Rollback

- Cloud Run: redeploy previous image / `gcloud run services update-traffic`
- Env mistake: fix `.env.cloudrun`, re-run `deploy_paid_pilot.sh`
- Full doc rollback: see `docs/SIMPLIFICATION_EXECUTION_PLAN.md` checkpoint tag
