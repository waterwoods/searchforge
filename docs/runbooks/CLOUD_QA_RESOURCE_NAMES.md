# Cloud QA Resource Names (P36 T1) — Canonical SSOT

**Status:** frozen naming SSOT + P36 T4 provisioned foundation  
**Authority:** single obvious place for Cloud QA vs Production resource names  
**P36 T4 (2026-07-21):** `caseiq-qa`, secret `fiqa-service-record-database-url-qa`, and Cloud Run `fiqa-api-qa` exist.  
**P36 T5 (2026-07-21):** Founder QA clients (Vercel Preview + Mini Program `apiProfile=qa`) retarget to `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`.  
**P36 T6 (2026-07-21):** Founder PAT on isolated Cloud QA — **PASS WITH FOLLOW-UP DEFECTS**. Evidence: `docs/evidence/p36_t6_founder_pat_2026_07_21.md`.  
**Still does not:** Add Vehicle / Add Driver; Production mutation from QA work.

Copy templates:

| Environment | Template (committed) | Local file (gitignored) |
|-------------|----------------------|-------------------------|
| **Cloud QA** | `configs/cloud_qa.env.example` | `.env.cloudrun.qa` |
| **Production / paid pilot** | `configs/demo.env.example` | `.env.cloudrun` |

---

## Canonical naming table

| Resource | Cloud QA | Production |
|----------|----------|------------|
| **Cloud Run service** | `fiqa-api-qa` | `fiqa-api` |
| **Postgres database** | `caseiq-qa` | `caseiq` |
| **Cloud SQL instance** | `caseiq-pilot-pg` | `caseiq-pilot-pg` |
| **DB Secret Manager secret** | `fiqa-service-record-database-url-qa` | `fiqa-service-record-database-url-cloudsql-private` |
| **Operator env file** | `.env.cloudrun.qa` | `.env.cloudrun` |
| **Env template** | `configs/cloud_qa.env.example` | `configs/demo.env.example` |
| **GCP project** | `optimal-disk-472305-e2` | `optimal-disk-472305-e2` |
| **Region** | `us-west1` | `us-west1` |

Same Cloud SQL **instance** is allowed; Cloud QA and Production must use **different database names** and **different DB secrets**. They must never share a mutable case store.

---

## Secret Manager names

### Database URL (must differ)

| Role | Secret name |
|------|-------------|
| Cloud QA | `fiqa-service-record-database-url-qa` |
| Production | `fiqa-service-record-database-url-cloudsql-private` |

### Other secrets (Production names — do not rename)

These Production secret names stay as-is. Cloud QA may reuse them until a later task requires separation. The DB secret above is the isolation boundary.

| Binding | Production secret name |
|---------|------------------------|
| `OPENAI_API_KEY` | `fiqa-openai-api-key` |
| `QDRANT_API_KEY` | `fiqa-qdrant-api-key` |
| `H5_TASK_TOKEN_SECRET` | `fiqa-h5-task-token-secret` |

Legacy Neon secret `fiqa-service-record-database-url` is **not** used for Cloud QA or Production.

---

## Deploy variable defaults (for later wrappers — not deployed by this doc)

| Variable | Cloud QA | Production |
|----------|----------|------------|
| `SERVICE_NAME` | `fiqa-api-qa` | `fiqa-api` |
| `CLOUD_RUN_SECRET_SERVICE_RECORD_DB` | `fiqa-service-record-database-url-qa` | `fiqa-service-record-database-url-cloudsql-private` |
| Env file loaded by deploy | `.env.cloudrun.qa` | `.env.cloudrun` |

---

## Hard rules (operator mistakes to prevent)

1. **Never** deploy Cloud QA with `SERVICE_NAME=fiqa-api`.
2. **Never** point Cloud QA at database `caseiq` or secret `fiqa-service-record-database-url-cloudsql-private`.
3. **Never** use `.env.cloudrun` as the Cloud QA deploy env file.
4. **Never** rename or retarget Production resources to “make QA.” Create the sibling names above instead.
5. Docs or scripts that still say “QA” while meaning the shared pilot (`fiqa-api` + `caseiq`) are **transitional**; the target Cloud QA names in this file win for P36+.

---

## Why these names (mistake minimization)

| Choice | Why |
|--------|-----|
| `fiqa-api-qa` vs `fiqa-api` | `-qa` suffix is visible in every `gcloud` command and URL; hard to confuse with Production. |
| `caseiq-qa` vs `caseiq` | Same product family, different database name — isolation is obvious in `psql` / Cloud SQL console. |
| Same instance `caseiq-pilot-pg` | Avoids inventing a second instance name before cost/ops justify it; isolation is the **database**, not the host. |
| `…-database-url-qa` vs `…-cloudsql-private` | Distinct Secret Manager ids so a QA deploy cannot silently bind the Production URL. |
| `.env.cloudrun.qa` vs `.env.cloudrun` | File-level separation; Production deploy scripts keep loading `.env.cloudrun` unchanged. |

---

## Isolation verifier (P36 T2) — run before every Cloud QA deploy

Fail-closed guard. Proves Cloud QA cannot use Production mutable case data.
If anything cannot be proven safe → **exit 1**. Do not deploy on FAIL.

```bash
# Default: load .env.cloudrun.qa (+ .env.cloudrun if present); may call gcloud for secrets
PYTHONPATH=. python3 scripts/p36_verify_cloud_qa_isolation.py

# Offline / CI with plaintext URLs already in env files (no gcloud):
PYTHONPATH=. python3 scripts/p36_verify_cloud_qa_isolation.py --no-secret-access
```

| Exit | Meaning |
|------|---------|
| `0` | **PASS** — service name, DB secret name, and resolved DB target are isolated |
| `1` | **FAIL** — do not deploy Cloud QA; fix the reported WHY lines |

Unit tests: `PYTHONPATH=. python3 -m pytest tests/test_p36_verify_cloud_qa_isolation.py -q`

---

## Deploy wiring (P36 T3) — safety before gcloud

| Entry | Env file | Service |
|-------|----------|---------|
| `bash scripts/deploy_paid_pilot.sh` | `.env.cloudrun` | `fiqa-api` |
| `bash scripts/deploy_cloud_qa.sh` | `.env.cloudrun.qa` | `fiqa-api-qa` |

Fail-closed checks (`scripts/p36_deploy_safety_check.py`, invoked by `deploy_cloud_run_core.sh`):

- Cloud QA cannot load `.env.cloudrun` or target `fiqa-api` / Production DB secret.
- Production cannot load `.env.cloudrun.qa`, bind QA DB secret, or enable QA Harness flags.
- QA Harness flags (`ENABLE_P35_MP_QA_HARNESS`, `ENABLE_P26H_FIXTURE_RUNNER`, `UNIFIED_INTAKE_QA_FIXTURE_SURFACE`, `P20_SLICE1_REQUEST_MORE`) never default ON.

```bash
# Safety-only (no deploy):
DEPLOY_SAFETY_CHECK_ONLY=1 bash scripts/deploy_paid_pilot.sh
DEPLOY_SAFETY_CHECK_ONLY=1 SKIP_P36_ISOLATION_VERIFIER=1 bash scripts/deploy_cloud_qa.sh
```

T3 does **not** create Cloud Run services, databases, or secrets — that is P36 T4 (see evidence doc in the status line above).

Deploy Cloud QA (after `.env.cloudrun.qa` exists):

```bash
bash scripts/deploy_cloud_qa.sh
```

First revision includes Direct VPC parity with Production: `network=default`, `subnet=default`, `vpc-egress=all-traffic`.

---

## Founder QA client routing (P36 T5)

Frozen Cloud QA API URL:

```text
https://fiqa-api-qa-g7zatxrycq-uw.a.run.app
```

| Client | QA / Preview | Production (unchanged) |
|--------|--------------|------------------------|
| **Vercel UI / Founder Console** | Preview env `VITE_API_BASE_URL` = Cloud QA URL | Production env `VITE_API_BASE_URL` = `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **WeChat Mini Program** | `apiProfile=qa` → `miniapp/config.qa.ts` Cloud QA URL | Do not use `apiProfile=qa` for a Production customer release |

### Vercel operator steps (Preview only — never change Production)

```bash
cd ui
vercel env add VITE_API_BASE_URL preview
# paste: https://fiqa-api-qa-g7zatxrycq-uw.a.run.app

vercel env add VITE_UNIFIED_INTAKE_INTAKE_API_KEY preview
# paste QA intake key from local .env.cloudrun.qa (not Production)

vercel env add VITE_ENABLE_QA_TOOLS preview
# paste: 1

vercel --yes   # redeploy Preview only — do NOT pass --prod
```

Template: `ui/env.preview.example`  
Build guard: `ui/src/api/cloudBackendUrls.ts` (Preview≠Production, Production≠QA, missing Preview URL fails).

### WeChat request合法域名 (operator)

Add Cloud QA host to the Mini Program admin allowlist (QA / Experience builds):

```text
fiqa-api-qa-g7zatxrycq-uw.a.run.app
```

Keep Production host on the Production Mini Program allowlist if a Production release exists. Do **not** upload/publish a Mini Program release as part of T5.

### CORS note (Cloud QA backend)

If Vercel Preview origins call `fiqa-api-qa`, ensure `ALLOWED_ORIGINS` on **fiqa-api-qa** includes those Preview origins (QA service only — never patch Production `fiqa-api` for this).

---

## Related

- Deploy entry map: [`DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md)
- Production deploy playbook: [`DEPLOYMENT_PLAYBOOK.md`](./DEPLOYMENT_PLAYBOOK.md)
- Environment strategy (local vs cloud boundaries): [`docs/p18_11_environment_strategy_and_dev_rules.md`](../p18_11_environment_strategy_and_dev_rules.md)
- P36 T4 provision evidence: [`docs/evidence/p36_t4_cloud_qa_provision_2026_07_21.md`](../evidence/p36_t4_cloud_qa_provision_2026_07_21.md)
- P36 T5 client retarget evidence: [`docs/evidence/p36_t5_founder_qa_client_retarget_2026_07_21.md`](../evidence/p36_t5_founder_qa_client_retarget_2026_07_21.md)
