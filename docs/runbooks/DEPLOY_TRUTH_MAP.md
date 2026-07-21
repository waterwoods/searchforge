# Deploy Truth Map — Unified Intake

One screen. **Authority:** [`docs/CURRENT_PRODUCT_SHAPE.md`](../CURRENT_PRODUCT_SHAPE.md)

**Cloud QA vs Production resource names (P36):** [`CLOUD_QA_RESOURCE_NAMES.md`](./CLOUD_QA_RESOURCE_NAMES.md) — single SSOT. Production stays `fiqa-api` / `caseiq` / `.env.cloudrun`. Cloud QA is `fiqa-api-qa` / `caseiq-qa` / `.env.cloudrun.qa` (T4 provisioned; T5 Founder QA clients retarget to `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`).

---

## Operator entries (only these)

| Goal | Script | Sets |
|------|--------|------|
| **Paid broker pilot** | `bash scripts/deploy_paid_pilot.sh` | `PRODUCT_ONLY=1`, `INTAKE_CORE_READINESS=1`, PG-primary, no DEMO_MODE; loads `.env.cloudrun` → `fiqa-api` |
| **Cloud QA (P36)** | `bash scripts/deploy_cloud_qa.sh` | loads `.env.cloudrun.qa` → `fiqa-api-qa`; isolation + deploy safety fail-closed; QA Harness opt-in only |
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

**Before any Cloud QA deploy (P36):** isolation must PASS (fail-closed):

```bash
PYTHONPATH=. python3 scripts/p36_verify_cloud_qa_isolation.py
```

Deploy entry (also runs isolation + deploy safety inside the wrapper):

```bash
bash scripts/deploy_cloud_qa.sh
# Wiring-only (no gcloud): DEPLOY_SAFETY_CHECK_ONLY=1 bash scripts/deploy_cloud_qa.sh
```

See [`CLOUD_QA_RESOURCE_NAMES.md`](./CLOUD_QA_RESOURCE_NAMES.md). Do not deploy Cloud QA on FAIL.

Production paid-pilot refuses QA Harness flags and `.env.cloudrun.qa` (P36 T3 safety check).

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

**Production / paid pilot (live today):**

```
Browser (Vercel) → Cloud Run (fiqa-api) → Postgres caseiq (required)
                                      ↘ Qdrant (optional)
```

**Cloud QA (P36 target names — see CLOUD_QA_RESOURCE_NAMES.md):**

```
QA clients → Cloud Run (fiqa-api-qa) → Postgres caseiq-qa (required)
                                    ↘ Qdrant (optional)
```

Production and Cloud QA must never share a mutable case database.

---

## Rollback

- Cloud Run: redeploy previous image / `gcloud run services update-traffic`
- Env mistake: fix `.env.cloudrun`, re-run `deploy_paid_pilot.sh`
- Full doc rollback: see `docs/SIMPLIFICATION_EXECUTION_PLAN.md` checkpoint tag
