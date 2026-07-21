# Cloud QA Resource Names (P36 T1) — Canonical SSOT

**Status:** frozen naming — documentation and configuration only  
**Authority:** single obvious place for Cloud QA vs Production resource names  
**Does not:** deploy, create infrastructure, create databases, rename Production, or change runtime behavior

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

## Related

- Deploy entry map: [`DEPLOY_TRUTH_MAP.md`](./DEPLOY_TRUTH_MAP.md)
- Production deploy playbook: [`DEPLOYMENT_PLAYBOOK.md`](./DEPLOYMENT_PLAYBOOK.md)
- Environment strategy (local vs cloud boundaries): [`docs/p18_11_environment_strategy_and_dev_rules.md`](../p18_11_environment_strategy_and_dev_rules.md)
