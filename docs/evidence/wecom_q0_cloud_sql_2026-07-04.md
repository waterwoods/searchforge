# WeCom Q0.9.3 — Cloud SQL Smoke DB Evidence

**Date:** 2026-07-04  
**Task:** Q0.9.3 — create low-cost Cloud SQL Postgres smoke DB, apply schema, verify preflight  
**Branch:** `sprint/p16-trust-layer` @ `cb4940b`  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com (gcloud active account)

**Scope completed:** instance create, DB/user, new Secret Manager secret, schema apply, local preflight.  
**Not done (by design):** Cloud Run cutover, WeCom live smoke, queue/outbox feature flags, scheduler/cron/jobs.

---

## 1. Pre-check

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Commit | `cb4940b` |
| Project ID | `optimal-disk-472305-e2` ✓ |
| Region | `us-west1` ✓ |
| Tier availability | `db-f1-micro` listed for `us-west1` ✓ |
| Instance name collision | No existing `caseiq-pilot-pg` before create ✓ |
| Neon secret untouched | `fiqa-service-record-database-url` versions 1–2 unchanged ✓ |

---

## 2. Cloud SQL instance

| Setting | Value |
|---------|-------|
| **Instance name** | `caseiq-pilot-pg` |
| **Connection name** | `optimal-disk-472305-e2:us-west1:caseiq-pilot-pg` |
| **Region / zone** | `us-west1` / `us-west1-b` |
| **Engine** | PostgreSQL 15 (`POSTGRES_15`) |
| **Tier** | `db-f1-micro` |
| **Storage** | 10 GB SSD |
| **Availability** | ZONAL (non-HA) |
| **HA** | OFF |
| **Read replicas** | OFF (none configured) |
| **Storage auto-increase** | OFF (`storageAutoResize: false`) |
| **Data mode** | CLEAN_DB_FOR_SMOKE (schema only; no Neon migration) |
| **Public IP** | `34.169.226.245` (for operator schema apply) |
| **Authorized network** | Operator IP `/32` only (temporary, for laptop apply) |
| **State** | `RUNNABLE` |

**Estimated monthly cost:** ~$8–$18/month (indicative; verify in [GCP Pricing Calculator](https://cloud.google.com/products/calculator) for `db-f1-micro`, 10 GB, zonal, `us-west1`). Target ≤ **$20/month**.

---

## 3. Database and user

| Item | Value |
|------|-------|
| Database | `caseiq` |
| App user | `caseiq_app` |
| Password | Generated at create time; **not recorded here** |

---

## 4. Secret Manager

| Secret | Purpose | Status |
|--------|---------|--------|
| `fiqa-service-record-database-url-cloudsql` | Cloud SQL smoke DB URL | **Created** — version `1` (enabled) |
| `fiqa-service-record-database-url` | Neon production URL | **Unchanged** — versions `1`, `2` still enabled |

**Connection URL format (public IP, for local/schema apply):**

```text
postgresql://caseiq_app:<REDACTED>@34.169.226.245:5432/caseiq?sslmode=require
```

**Q0.9.4 Cloud Run runtime URL (Unix socket — recommended after cutover):**

```text
postgresql://caseiq_app:<REDACTED>@/caseiq?host=/cloudsql/optimal-disk-472305-e2:us-west1:caseiq-pilot-pg
```

**Q0.9.4 Cloud Run settings needed (not applied yet):**

1. Add Cloud SQL connector: `--add-cloudsql-instances=optimal-disk-472305-e2:us-west1:caseiq-pilot-pg`
2. Point `SERVICE_RECORD_DATABASE_URL` at secret `fiqa-service-record-database-url-cloudsql` (new deploy env / secret binding — do **not** overwrite Neon secret)
3. Optionally remove public IP / authorized networks after cutover (runtime uses connector)

---

## 5. Schema applied

Applied in order via `psycopg` (local; `psql` not installed on operator machine):

| # | File | Result |
|---|------|--------|
| 1 | `services/fiqa_api/db/schema/stage1_service_record.sql` | OK |
| 2 | `services/fiqa_api/db/schema/intake_sessions.sql` | OK |
| 3 | `services/fiqa_api/db/schema/intake_entities.sql` | OK |
| 4 | `services/fiqa_api/db/schema/wecom_inbox_events.sql` | OK |
| 5 | `services/fiqa_api/db/schema/wecom_reply_outbox.sql` | OK |
| 6 | `services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql` | OK |
| 7 | `wecom_reply_dedup` (explicit DDL from `reply_dedup.py`) | OK |

`wecom_reply_dedup` has no standalone `.sql` file; table created explicitly with `CREATE TABLE IF NOT EXISTS` matching `services/fiqa_api/wecom/reply_dedup.py`.

---

## 6. Schema verification

```text
SELECT 1 => 1

service_records: OK
record_messages: OK
structured_record_data: OK
state_history: OK
office_actions: OK
intake_sessions: OK
intake_entities: OK
wecom_inbox_events: OK
wecom_reply_outbox: OK
wecom_reply_dedup: OK
```

---

## 7. Local DB preflight (Cloud SQL secret)

Commands used (safe against empty Cloud SQL — no Neon rows touched):

```bash
export PROJECT_ID=optimal-disk-472305-e2
export SERVICE_RECORD_DATABASE_URL="$(gcloud secrets versions access latest \
  --secret=fiqa-service-record-database-url-cloudsql --project="$PROJECT_ID")"

PYTHONPATH=. python3 -c "
from services.fiqa_api.wecom.queue_db import preflight_wecom_queue_db
print(preflight_wecom_queue_db())
"

PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status --json
```

**Results:**

```json
{"ok": true, "database_url_configured": true, "select_1": true, "tables_verified": ["wecom_inbox_events", "wecom_reply_outbox"]}
```

```json
{
  "mode": "status",
  "db_preflight": {"ok": true, "database_url_configured": true, "select_1": true},
  "inbox": {"pending": 0, "processing": 0, "processed": 0, "failed": 0},
  "outbox": {"pending": 0, "sending": 0, "sent": 0, "failed": 0}
}
```

---

## 8. Production unchanged (stop conditions respected)

| Item | Current production state |
|------|--------------------------|
| Cloud Run `fiqa-api` DB secret | `fiqa-service-record-database-url:latest` (Neon) — **not switched** |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| WeCom live smoke | **Not run** |
| Scheduler / cron / jobs / Pub/Sub / UI | **No changes** |

---

## 9. Cleanup (if smoke-only or cost too high)

**Delete Cloud SQL instance (irreversible — backups included):**

```bash
export PROJECT_ID=optimal-disk-472305-e2
export INSTANCE_NAME=caseiq-pilot-pg

gcloud sql instances delete "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --quiet

gcloud sql instances list --project="$PROJECT_ID" --filter="name:${INSTANCE_NAME}"
```

**Optional — disable Cloud SQL secret version (keep Neon rollback path):**

```bash
gcloud secrets versions disable 1 \
  --secret=fiqa-service-record-database-url-cloudsql \
  --project=optimal-disk-472305-e2
```

**Do not delete** `fiqa-service-record-database-url` (Neon versions 1–2).

---

## 10. Rollback note

If Q0.9.4 cutover fails or is deferred:

1. Leave Cloud Run on `fiqa-service-record-database-url` (Neon) — already the case.
2. Delete `caseiq-pilot-pg` when done testing (§9) to stop instance billing.
3. Disable or destroy `fiqa-service-record-database-url-cloudsql` version only after confirming Cloud Run never referenced it.

Neon stuck rows ids 8–11 were **not** copied (clean DB policy).

---

*Q0.9.3 complete — Cloud SQL smoke DB ready for Q0.9.4 cutover planning. No password or full secret value recorded.*
