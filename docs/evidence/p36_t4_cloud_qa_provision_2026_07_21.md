# P36 T4 — Isolated Cloud QA Foundation Provision Evidence

**Date:** 2026-07-21  
**Task:** Provision isolated Cloud QA resources (database, secret, Cloud Run, Direct VPC, runtime config)  
**GCP project:** `optimal-disk-472305-e2`  
**Region:** `us-west1`  
**Operator account:** `ainew6380@gmail.com`  
**Stop after T4:** yes (no Mini Program / Vercel retarget; no Founder PAT)

Secret values, passwords, and API keys are **redacted** below. `.env.cloudrun.qa` is gitignored and was not committed.

---

## 1. One objective / out of scope

**Objective:** Stand up an isolated Cloud QA foundation (`fiqa-api-qa` + `caseiq-qa`) that cannot mutate Production case data.

**Out of scope:** Add Vehicle, Add Driver, Vercel retarget, Mini Program retarget, Founder PAT, Production mutations.

---

## 2. Production read-only baseline (before)

| Field | Value |
|-------|-------|
| Service | `fiqa-api` |
| Ready revision | `fiqa-api-00233-scz` |
| Observed generation | `233` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Service account | `1013093472160-compute@developer.gserviceaccount.com` |
| Memory / CPU | `1Gi` / `1` |
| Concurrency | `30` |
| Max instances | `2` |
| Direct VPC | `network=default`, `subnet=default`, `vpc-egress=all-traffic` |
| DB secret binding | `fiqa-service-record-database-url-cloudsql-private` |
| Production DB | `caseiq` on `caseiq-pilot-pg` (private host `10.73.0.3`) |
| `service_records` count | `64` |

---

## 3. Repository changes (committed)

| Path | Change |
|------|--------|
| `scripts/deploy_cloud_run_core.sh` | Direct VPC flags on deploy (`network`/`subnet`/`vpc-egress`); JSON-based post-deploy VPC parity check |
| `scripts/deploy_cloud_qa.sh` | Fix isolation verifier CLI (`--qa-env` / `--prod-env`); notes |
| `configs/cloud_qa.env.example` | Runtime posture + Direct VPC guidance |
| `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` | T4 provisioned status + deploy notes |
| `docs/evidence/p36_t4_cloud_qa_provision_2026_07_21.md` | This evidence |

**Not committed:** `.env.cloudrun.qa`, Secret Manager payloads, DB passwords, generated API keys.

---

## 4. Commands executed (redacted)

Preflight printed before each mutation: project, target resource, intended action, why safe.

### 4.1 Create database `caseiq-qa`

```bash
gcloud sql databases create caseiq-qa \
  --instance=caseiq-pilot-pg \
  --project=optimal-disk-472305-e2 \
  --charset=UTF8 \
  --collation=en_US.UTF8
```

**Result:** created. Databases on instance: `postgres`, `caseiq`, `caseiq-qa`.

### 4.2 Apply schemas/migrations (operator public IP only)

Connected as `caseiq_app` via public IP `34.169.226.245` for DDL. Before every DDL: `SELECT current_database()` must equal `caseiq-qa` (refused if `caseiq`).

Applied in order:

1. `stage1_service_record.sql`
2. `intake_sessions.sql`
3. `intake_entities.sql`
4. `wecom_inbox_events.sql`
5. `wecom_reply_outbox.sql`
6. `wecom_message_processed.sql`
7. `wecom_sync_cursors.sql`
8. migrations `001` … `005`
9. `wecom_reply_dedup` DDL (from `reply_dedup.py` pattern)

**Result:** `ACTIVE_DB_CONFIRMED=caseiq-qa`, 23 public tables. Production check afterward: `('caseiq', 22)` tables / `service_records=64` unchanged.

### 4.3 Create QA DB secret

```bash
gcloud secrets create fiqa-service-record-database-url-qa \
  --project=optimal-disk-472305-e2 \
  --replication-policy=automatic

gcloud secrets versions add fiqa-service-record-database-url-qa \
  --project=optimal-disk-472305-e2 \
  --data-file=<local-qa-private-url-file>

gcloud secrets add-iam-policy-binding fiqa-service-record-database-url-qa \
  --member=serviceAccount:1013093472160-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

**Resolved QA secret fingerprint:** `host=10.73.0.3 db=caseiq-qa user=caseiq_app`  
**Resolved Production secret fingerprint (unchanged):** `host=10.73.0.3 db=caseiq`  
**URL form (redacted):** `postgresql://caseiq_app:***@10.73.0.3:5432/caseiq-qa?sslmode=require`

### 4.4 Create `.env.cloudrun.qa` (gitignored)

- Copied frozen names from `configs/cloud_qa.env.example`
- Generated new `UNIFIED_INTAKE_INTAKE_API_KEY` / `UNIFIED_INTAKE_SUPPORT_API_KEY` (not Production keys; values not recorded)
- Bound `CLOUD_RUN_SECRET_SERVICE_RECORD_DB=fiqa-service-record-database-url-qa`
- Set Direct VPC + product intake posture; Founder QA flags left off for first deploy

### 4.5 Isolation verifier (before deploy)

```bash
PYTHONPATH=. python3 scripts/p36_verify_cloud_qa_isolation.py \
  --qa-env .env.cloudrun.qa \
  --prod-env .env.cloudrun
```

**Result:** `RESULT: PASS` / exit `0`

### 4.6 Deploy Cloud QA only

```bash
bash scripts/deploy_cloud_qa.sh
```

**Created/updated:** `fiqa-api-qa` only (never `fiqa-api`).

| Field | Value |
|-------|-------|
| Service URL | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| First revision | `fiqa-api-qa-00001-vgr` |
| Image | `gcr.io/optimal-disk-472305-e2/fiqa-api-qa:latest` |
| Image digest | `sha256:e6b8eeea3fd58a67ab20fde8af2d66edfee745b3fcd722d0a2635c3e97ceb856` |
| Cloud Build ID | `f91d2b15-a1f8-4915-9333-4564ad18f2de` |
| DB secret on service | `fiqa-service-record-database-url-qa:latest` |
| Direct VPC | `network=default`, `subnet=default`, `vpc-egress=all-traffic` |
| Memory / concurrency | `1Gi` / `30` |

### 4.7 Enable Founder QA flags (after identity proven)

```bash
gcloud run services update fiqa-api-qa \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-env-vars='ENABLE_P35_MP_QA_HARNESS=1,UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1,ENABLE_P26H_FIXTURE_RUNNER=1,P20_SLICE1_REQUEST_MORE=1,ENABLE_GOLDEN_QA_LAUNCH=1'
```

**Result:** revision `fiqa-api-qa-00002-rx9`; Direct VPC preserved; Production untouched.

---

## 5. Verification results

| Check | Result |
|-------|--------|
| `fiqa-api-qa` exists | PASS — revision `fiqa-api-qa-00002-rx9` |
| Direct VPC matches Production baseline | PASS — `default` / `default` / `all-traffic` |
| `GET /health/live` | PASS — HTTP 200 `{"ok":true}` |
| `GET /readyz` | PASS — HTTP 200, `status=ready`, `intake_core_readiness=true`, `intake_path_ready=true`, `readiness_mode=intake_core` |
| Support manifest `k_service` | PASS — `fiqa-api-qa` |
| Case persistence mode | PASS — `STRICT_PG_ONLY`, DB URL present via secret |
| QA secret → `caseiq-qa` | PASS |
| Isolation verifier | PASS — exit 0 (before and after) |
| Production revision/generation | PASS — still `fiqa-api-00233-scz` / gen `233` |
| Production DB `caseiq` | PASS — still `caseiq`, `service_records=64` |
| DB identities differ | PASS — QA `service_records=0` vs Prod `64` |

### Tests

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p36_verify_cloud_qa_isolation.py \
  tests/test_p36_deploy_safety_check.py -q
```

**Before provision:** PASS  
**After provision / script fixes:** PASS (25 tests)

---

## 6. Deviations from plan

1. **Post-deploy VPC check false negative on first deploy.** Direct VPC was correctly applied on revision `00001`, but `deploy_cloud_run_core.sh` used a broken `gcloud --format` path for annotation keys containing `/`, so the script exited `1` after a successful create. Fixed to JSON-based verification; no second image rebuild required for VPC.
2. **Schema apply used public IP** (`34.169.226.245`) from the authorized operator laptop. Runtime secret uses **private** host `10.73.0.3` (required).
3. **QA schema includes `wecom_sync_cursors` + migrations `002`–`005`** in addition to the older WeCom Q0.9.3 set, for Founder QA readiness parity.
4. **gcloud CLI sometimes prints** `https://fiqa-api-qa-1013093472160.us-west1.run.app`; canonical `status.url` is `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` (both resolve to the same service).

No Production resources were mutated. No stop-condition triggered.

---

## 7. Created resources summary

| Resource | Name / identity |
|----------|-----------------|
| Cloud SQL database | `caseiq-qa` on `caseiq-pilot-pg` |
| Secret Manager secret | `fiqa-service-record-database-url-qa` (v1) |
| Cloud Run service | `fiqa-api-qa` |
| QA URL | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| Deployed image digest | `sha256:e6b8eeea3fd58a67ab20fde8af2d66edfee745b3fcd722d0a2635c3e97ceb856` |
| Operator env file | `.env.cloudrun.qa` (local only) |

---

## 8. Explicit non-actions

- Did **not** retarget Mini Program or Vercel
- Did **not** begin Founder PAT
- Did **not** deploy or update `fiqa-api`
- Did **not** modify database `caseiq` or Production DB secret
- Did **not** change Cloud SQL instance configuration
