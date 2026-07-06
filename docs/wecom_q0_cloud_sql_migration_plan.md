# WeCom Q0.9 — Cloud SQL Postgres Migration Execution Plan

**Status:** Plan only (Q0.9.1 + Q0.9.2 + **Q0.9.2.1**). **Do not execute** until operator approval and Q0.9.3 decision gate (§C₂.5 + §C₂.6).

**Cost target (Q0.9.2):** Cloud SQL pilot ideally **under $20/month** — see §C₂ and final review §C₂.6.

**Context:** Q0.8.5 concluded Neon serverless (`us-west-2`) is not stable enough for real Cloud Run queued WeCom drain. Cloud Run (`fiqa-api`, `us-west1`) opens many short-lived Postgres connections over 30–60s during drain; preflight passes but real drain fails (Q0.8.2, Q0.8.4). This doc is the concrete, copy-pasteable path to Cloud SQL Postgres in the **same GCP region** before the next live smoke.

**Related docs:**

- Root-cause analysis: [`docs/wecom_q0_db_stability_decision.md`](wecom_q0_db_stability_decision.md)
- Smoke runbook (after migration): [`docs/wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md)
- Evidence (failed Neon drains): [`docs/evidence/wecom_q0_smoke_2026-07-04.md`](evidence/wecom_q0_smoke_2026-07-04.md)

**Out of scope (Q0.9.1 / Q0.9.2 / Q0.9.2.1):** creating Cloud SQL, migrating data, deploying, running live smoke.

---

## A. Why move from Neon to Cloud SQL

| Factor | Neon (today) | Cloud SQL (target) |
|--------|--------------|---------------------|
| Role | Fast demo / dev Postgres | Cloud Run production / pilot Postgres |
| Region | `us-west-2` (external) | `us-west1` (same as Cloud Run) |
| Network | Public internet via Cloud Run NAT → AWS | Same GCP project; private IP or Auth Proxy / connector |
| Connection pattern | Many fresh TCP+TLS handshakes per drain | Colocated, lower latency, fewer cross-provider resets |
| Ops | Separate console / billing | GCP backups, IAM, monitoring alongside `fiqa-api` |

Neon was useful for quick demo and schema iteration. For the queued WeCom pipeline (inbox → worker → outbox → `send_msg`), **same-cloud / same-region Postgres** is the better fit. Q0.8.3 proved application correctness (fail-closed, preflight); Q0.8.4 proved **infrastructure** is the blocker.

**WeCom callback path is unchanged:** inbound WeCom traffic still hits Cloud Run in `us-west1` and egresses via the existing NAT static IP for `sync_msg` / `send_msg`. Only the database endpoint moves.

---

## B. Target architecture

```
WeCom callback ──► Cloud Run fiqa-api (us-west1)
                      │
                      ├─ fast enqueue ──► Cloud SQL Postgres (us-west1)
                      │                    ├─ wecom_inbox_events
                      │                    ├─ wecom_reply_outbox
                      │                    ├─ wecom_reply_dedup (app DDL)
                      │                    └─ service_records + intake_*
                      │
                      └─ admin drain / worker
                            ├─ short DB tx: claim (preflight → claim → mark)
                            ├─ WeCom sync_msg / send_msg (no DB held)
                            └─ short DB tx: outbox claim / mark

SERVICE_RECORD_DATABASE_URL ──► Secret Manager ──► Cloud SQL connection string
```

| Component | Value (discovered in repo) |
|-----------|----------------------------|
| Cloud Run service | `fiqa-api` |
| Cloud Run region | `us-west1` |
| Default GCP project | `optimal-disk-472305-e2` (`scripts/deploy_cloud_run_core.sh`) |
| DB env var | `SERVICE_RECORD_DATABASE_URL` (fallback `DATABASE_URL`) |
| Secret Manager secret | `fiqa-service-record-database-url` (override: `CLOUD_RUN_SECRET_SERVICE_RECORD_DB`) |
| Deploy binding | `scripts/deploy_cloud_run_core.sh` when `CLOUD_RUN_USE_SECRET_MANAGER=1` |
| Inbox/outbox tables | Postgres — no in-memory fallback when queue flags are on (Q0.8.3) |

**Not in deploy script today:** Cloud SQL instance annotation (`--add-cloudsql-instances`) or VPC connector. Operator must pick a connection method in §C and apply it during the first Cloud SQL cutover deploy (see §D step 8).

---

## C. Required decisions (fill before execution)

Copy this table and record choices in your ops log. Placeholders below match repo defaults; adjust if your pilot uses a different project.

| Decision | Recommended (pilot) | Notes |
|----------|---------------------|-------|
| **GCP project id** | `optimal-disk-472305-e2` | `export PROJECT_ID=...` |
| **Region** | `us-west1` | Must match Cloud Run |
| **Cloud SQL instance name** | `caseiq-pg-usw1` | Globally unique per project |
| **Postgres version** | `POSTGRES_15` or `POSTGRES_16` | Match Neon major version before cutover |
| **Instance tier** | **Smallest shared-core in `us-west1`** (discover via §C₂) | Do **not** default to `db-g1-small` or dedicated vCPU for smoke |
| **Database name** | `caseiq` | |
| **App user** | `caseiq_app` | Least privilege; not `postgres` superuser |
| **Secret Manager secret** | `fiqa-service-record-database-url` | New **version**; keep Neon versions for rollback |
| **Connection method (pilot)** | **Public IP + Cloud SQL Auth Proxy** from laptop for schema; **Unix socket / connector on Cloud Run** for runtime | Fastest path to validate drain |
| **Connection method (production)** | **Private IP + VPC connector** or **Cloud SQL connector** without public IP | Tighten after smoke passes |

### Connection method trade-offs

| Method | Pilot speed | Production fit |
|--------|-------------|----------------|
| Public IP + authorized networks + SSL | Fastest for `psql` schema apply | Restrict authorized networks; rotate password |
| Cloud SQL Auth Proxy (local `psql`) | Safe admin access without opening `0.0.0.0/0` | Use for schema + verification only |
| Cloud Run + `--add-cloudsql-instances` + Unix socket URL | **Recommended for runtime** | No public DB IP required on Cloud Run |
| Private IP + Serverless VPC Access | Best long-term | Requires VPC / connector setup |

Example Cloud Run Unix socket URL shape (placeholders):

```text
postgresql://caseiq_app:PASSWORD@/caseiq?host=/cloudsql/PROJECT_ID:us-west1:caseiq-pg-usw1
```

---

## C₂. Low-cost pilot configuration (Q0.9.2)

Use this profile for the **first smoke** and early broker pilot. Goal: prove Cloud Run → Postgres drain stability **without** Neon-level cost or production over-provisioning.

### C₂.1 Recommended settings

| Setting | Pilot value | Rationale |
|---------|-------------|-----------|
| **Region** | `us-west1` | Same region as `fiqa-api` — required for stability, not optional |
| **High availability** | **OFF** (`--availability-type=zonal`) | HA doubles instance cost (`REGIONAL` / `HA db-*` tiers) — **do not use for smoke** |
| **Instance tier** | **Smallest shared-core Postgres tier in `us-west1`** | Operator discovers via `gcloud sql tiers list` — typically `db-f1-micro` (0.2 vCPU shared, 0.6 GB RAM) |
| **Read replicas** | **None** | Not needed for smoke or single-broker pilot |
| **Storage type** | SSD | Default; HDD not required for this workload |
| **Storage size** | **10 GB** (Cloud SQL minimum) | Schema + smoke rows are ≪ 1 GB; no case history migrated |
| **Storage auto-increase** | **OFF** (`--no-storage-auto-increase`) | Safe for clean-DB pilot; prevents silent bill growth. Re-enable before real pilot if you expect large `service_records` growth |
| **Backups** | **On** (default automated daily) | Minimal but safe — small backup storage cost on empty/small DB. Do **not** enable extra PITR or long retention for smoke |
| **Data** | **Clean DB** — schema only | No Neon `pg_dump`; no stuck queue rows (see §F) |
| **Public IP** | Optional for smoke | Unix socket / connector on Cloud Run avoids exposing Postgres; public IP + Auth Proxy is OK for one-time schema apply |

### C₂.2 Cost guardrail

| Item | Guidance |
|------|----------|
| **Target** | **≤ $20/month** total for this pilot instance (compute + storage + backups + IP) |
| **Feasibility** | Google's published **test-instance** example (`db-f1-micro`, 10 GB, zonal, `us-central1`, no backup storage) is **~$9.37/month** ([pricing examples](https://cloud.google.com/sql/docs/postgres/pricing-examples)). `us-west1` may differ slightly — still likely **well under $20** at this size |
| **Repo cannot pin live price** | Exact monthly cost depends on region, tier availability, backup bytes, and billing account. **Operator must verify** in [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) **before** Q0.9.3 instance creation |
| **Watch the bill** | After creation: Billing → Reports → filter `Cloud SQL`. Delete instance promptly if smoke-only (§H₂) |

**Warnings — do not create these for smoke/pilot:**

| Anti-pattern | Why |
|--------------|-----|
| **HA / `REGIONAL` availability** | ~2× instance cost |
| **`db-g1-small` or larger** without measured need | 3–7×+ vs `db-f1-micro`; smoke does not need it |
| **Dedicated vCPU tiers** (`db-custom-*`, `db-perf-optimized-*`) | Production scale; far above $20/month |
| **Read replicas** | Extra full instance charge |
| **Large storage** (100 GB+) or **auto-increase ON** without monitoring | Unnecessary for clean-DB smoke |
| **Migrating Neon queue history** | Operational risk, not cost — but wastes debugging time |

`db-f1-micro` is **not covered by Cloud SQL SLA** and is **shared-core** — acceptable for smoke and short pilot; scale up only after measured load.

### C₂.3 Discover machine tiers (do not hardcode expensive tier)

Run **before** `gcloud sql instances create`. Pick the **cheapest tier that supports Postgres in `us-west1`**.

```bash
export PROJECT_ID="optimal-disk-472305-e2"   # ← confirm
export REGION="us-west1"

gcloud config set project "$PROJECT_ID"

# All tiers available in us-west1
gcloud sql tiers list --filter="region:${REGION}" \
  --format="table(tier,region,RAM,DISK_QUOTA)"

# Shared-core tiers only (usual pilot candidates)
gcloud sql tiers list --filter="region:${REGION} AND tier:db-f*" \
  --format="table(tier,region,RAM,DISK_QUOTA)"

gcloud sql tiers list --filter="region:${REGION} AND tier:db-g1-small" \
  --format="table(tier,region,RAM,DISK_QUOTA)"
```

Record the chosen tier:

```bash
# Operator sets after reviewing tiers list — example placeholder only:
export INSTANCE_TIER="db-f1-micro"   # ← replace with smallest valid tier from list above
echo "Selected tier: $INSTANCE_TIER"
```

**Do not proceed** if the smallest available tier estimates above $20/month in the Pricing Calculator.

### C₂.4 Low-cost `instances create` template

Uses `$INSTANCE_TIER` from §C₂.3 — **not** a hardcoded production size.

```bash
export PROJECT_ID="optimal-disk-472305-e2"   # ← confirm
export REGION="us-west1"
export INSTANCE_NAME="caseiq-pg-usw1"        # ← confirm
export INSTANCE_TIER="REPLACE_ME"            # ← from gcloud sql tiers list
export DB_NAME="caseiq"
export DB_USER="caseiq_app"
export DB_PASSWORD="$(openssl rand -base64 24)"

# Zonal, minimal storage, no auto-increase, no HA
gcloud sql instances create "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --database-version=POSTGRES_15 \
  --tier="$INSTANCE_TIER" \
  --region="$REGION" \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB \
  --no-storage-auto-increase \
  --backup-start-time=03:00
```

For **one-time schema apply** from laptop (optional public IP — tighten before production):

```bash
gcloud sql instances create "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --database-version=POSTGRES_15 \
  --tier="$INSTANCE_TIER" \
  --region="$REGION" \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB \
  --no-storage-auto-increase \
  --backup-start-time=03:00 \
  --authorized-networks=YOUR_OPERATOR_IP/32
```

After create, verify disk settings:

```bash
gcloud sql instances describe "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --format="yaml(settings.tier,settings.dataDiskSizeGb,settings.storageAutoResize,settings.availabilityType)"
```

### C₂.5 Decision gate — before Q0.9.3 (actual instance creation)

**Stop.** Complete **§C₂.6 Final cost and risk review** first. Do not run §D2 until every row in §C₂.6.5 is confirmed in your ops log.

| # | Operator must confirm | Record |
|---|----------------------|--------|
| 1 | **Estimated monthly cost** is acceptable (Pricing Calculator ≤ **$20/month** target, or explicit override) | $____ / month |
| 2 | **Instance tier** chosen from `gcloud sql tiers list` | `$INSTANCE_TIER` = ______ |
| 3 | **Storage size** | 10 GB, auto-increase OFF |
| 4 | **Region** | `us-west1` |
| 5 | **HA** | OFF (zonal only) |
| 6 | **Purpose** | ☐ Temporary smoke DB (delete after smoke) ☐ Short pilot DB (keep until broker trial) |
| 7 | **Data strategy** | Clean DB only — **no** Neon migration for first smoke |
| 8 | **Neon rollback** | Neon secret version #____ saved |
| 9 | **Queue flags** | Will stay OFF until empty drain passes |
| 10 | **Deletion/cleanup plan** | §H₂ path understood and scheduled if smoke-only |

If purpose is **temporary smoke DB**, schedule instance deletion in §H₂ immediately after smoke evidence is recorded — do not leave a running instance “just in case.”

---

### C₂.6 Final cost and risk review before Q0.9.3 (Q0.9.2.1)

**Purpose:** One last cost and risk pass **before** any `gcloud sql instances create`. This section does not create resources — it confirms the cheapest safe pilot configuration and lists what could accidentally increase cost or break the migration.

**Verified in repo session (2026-07-04):** `db-f1-micro` is listed for `us-west1` via `gcloud sql tiers list`. `gcloud sql instances create --help` states storage default is **10 GB**. Exact monthly price still requires operator verification in the [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) — do not treat placeholder estimates below as final quotes.

#### C₂.6.1 Cost review — confirmed pilot target

| Item | Confirmed value |
|------|-----------------|
| **Monthly cost target** | **≤ $20/month** if feasible (likely at `db-f1-micro` + 10 GB zonal — see §C₂.6.4) |
| **Engine** | Postgres (`POSTGRES_15` or `POSTGRES_16`) |
| **Region** | `us-west1` (same as Cloud Run `fiqa-api`) |
| **Availability** | **Zonal / non-HA** (`--availability-type=zonal`) |
| **Instance tier** | **Smallest shared-core tier** — **`db-f1-micro`** if supported (0.2 vCPU shared, ~614 MiB RAM) |
| **Storage** | **10 GB SSD** |
| **Read replicas** | **None** |
| **HA** | **Off** |
| **Storage auto-increase** | **Off** (`--no-storage-auto-increase`) |
| **Data** | **Clean DB** — schema only for first smoke; no Neon historical data |

**Explicit do-nots for Q0.9.3 create:**

- **Do not** choose `db-g1-small` or any larger tier unless `db-f1-micro` is unavailable in `us-west1` or fails smoke (connection/OOM) with measured evidence.
- **Do not** choose a **dedicated-core** instance (`db-custom-*`, `db-perf-optimized-*`, or any non-shared tier) for this smoke DB.
- **Do not** enable **HA** (`REGIONAL` availability or HA machine tiers).
- **Do not** enable **read replicas**.
- **Do not** enable **automatic storage increase** for this first smoke DB.
- **Do not migrate Neon historical data** (cases, queue rows, dedup keys) before smoke passes on a clean Cloud SQL DB.

#### C₂.6.2 Storage review — does size affect price? Is 2 GB / 5 GB worth trying?

| Question | Answer |
|----------|--------|
| **Does storage size affect price?** | **Yes.** Cloud SQL bills provisioned SSD capacity (GB-month) in addition to instance compute. Larger disk = higher storage line item even if mostly empty. |
| **Can smaller storage reduce cost?** | **In theory, yes** — but only if Cloud SQL allows provisioning below 10 GB for Postgres in your project/region. |
| **What does gcloud say?** | `gcloud sql instances create --help`: `--storage-size` must be an integer number of GB; **default is 10 GB**. The repo does not document a supported 2 GB or 5 GB minimum for Postgres Cloud SQL. |
| **Is 2 GB / 5 GB worth trying?** | **No — not for this smoke.** Do not force 2 GB or 5 GB if `gcloud` rejects the value or docs imply 10 GB minimum. The savings vs 10 GB on an empty pilot DB are negligible compared to instance compute; chasing sub-10 GB risks a failed create or rework. |
| **Recommendation** | **Use 10 GB** for the first smoke unless operator explicitly confirms a smaller size is supported at create time (unlikely). Schema + smoke rows are ≪ 1 GB; 10 GB is the practical minimum. |

**Irreversible storage growth warning:** Storage on an existing Cloud SQL instance is **easy to increase** but **hard or impossible to shrink in place**. If you over-provision (e.g. 100 GB “to be safe”), you pay for that capacity until you **delete and recreate** the instance. For a smoke-only DB, **delete/recreate** is safer than living with wrong-sized disk.

#### C₂.6.3 Hidden cost risks

| Risk | How cost spikes | Mitigation |
|------|-----------------|------------|
| **HA / regional availability** | ~**doubles** instance compute (standby + replication) | `--availability-type=zonal` only |
| **Bigger machine tier** | `db-g1-small` and up are **multiples** of `db-f1-micro` hourly rate | Stay on smallest shared-core until measured need |
| **Dedicated-core tiers** | Far above $20/month pilot budget | Shared-core only for smoke |
| **Storage auto-increase** | Disk grows silently; bill grows with provisioned GB | `--no-storage-auto-increase` |
| **Backups / PITR retention** | Daily backups are default (small on empty DB); **extended PITR or long backup retention** adds storage charges | Default daily backup OK; do **not** enable extra PITR or long retention for smoke |
| **Network egress (cross-region)** | Cloud Run `us-west1` → DB in another region adds latency **and** egress charges | **Must** use `us-west1` |
| **Leaving test instance running** | Full monthly instance + storage charge continues after smoke | Delete per §H₂ if smoke-only; set calendar reminder |
| **Neon + Cloud SQL both active** | **Two** Postgres bills if Neon paid plan stays up during pilot | Expect dual DB cost during overlap; downgrade/cancel Neon only after Cloud SQL proven |
| **Logging / monitoring** | Minor — Cloud Logging and metrics usually small vs instance | Acceptable; avoid verbose debug logging at high volume |

#### C₂.6.4 Estimated monthly cost (placeholders — verify in Pricing Calculator)

**Operator action:** Open [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) → Cloud SQL for PostgreSQL → region **`us-west1`**, tier **`db-f1-micro`**, 10 GB SSD, zonal, backups on. Record your quote in the ops log.

| Line item | Estimate (placeholder) | Notes |
|-----------|------------------------|-------|
| **Instance compute** (`db-f1-micro`, zonal, 730 h/month) | **$___ / month** | Google’s published test-instance example (`db-f1-micro`, 10 GB, zonal, `us-central1`) is **~$9.37/month** compute+storage ([pricing examples](https://cloud.google.com/sql/docs/postgres/pricing-examples)). `us-west1` may differ — **verify, do not assume**. |
| **Storage (10 GB SSD provisioned)** | **$___ / month** | Often bundled in calculator with instance; ~$0.17/GB-month list price varies — use calculator |
| **Backup storage** | **$___ / month** | Small on clean DB; grows if you retain many backups or enable PITR |
| **Public IP (if assigned)** | **$___ / month** | Optional; Unix socket on Cloud Run avoids needing public IP for runtime |
| **Total estimated range** | **~$8–$18 / month** (indicative only) | Target ≤ **$20/month**; if calculator exceeds $20 at `db-f1-micro` + 10 GB zonal, **stop** and re-check tier/region before Q0.9.3 |

Repo cannot pin live billing-account pricing. **Placeholders above are not a quote.**

#### C₂.6.5 Required operator decision gate (Q0.9.2.1 sign-off)

Before Q0.9.3, operator must **explicitly confirm** each row (copy to ops log):

| # | Decision | Confirmed? | Record |
|---|----------|------------|--------|
| 1 | **Estimated monthly cost** accepted (from Pricing Calculator or explicit override) | ☐ | $____ / month |
| 2 | **Region `us-west1`** accepted | ☐ | |
| 3 | **Instance tier** accepted (`db-f1-micro` or documented fallback) | ☐ | `$INSTANCE_TIER` = ______ |
| 4 | **Storage size 10 GB** accepted (auto-increase OFF) | ☐ | |
| 5 | **Non-HA (zonal)** accepted | ☐ | |
| 6 | **Clean DB first** accepted — no Neon migration before smoke | ☐ | |
| 7 | **Deletion/cleanup plan** accepted (§H₂ if smoke-only; Neon rollback §H₁ if cutover fails) | ☐ | |

**No Q0.9.3 create** until all seven rows are checked and recorded.

#### C₂.6.6 Safe create parameters (copy to ops log)

Use these values in §C₂.4 / §D2 unless operator documents a justified exception:

```text
INSTANCE_TIER=db-f1-micro          # smallest shared-core; confirm via gcloud sql tiers list
STORAGE_SIZE=10GB
REGION=us-west1
AVAILABILITY_TYPE=ZONAL
HA=OFF
REPLICAS=OFF
AUTO_STORAGE_INCREASE=OFF
DATA_MODE=CLEAN_DB_FOR_SMOKE
```

#### C₂.6.7 Technical risks (migration / smoke breakers)

| Risk | Symptom | Mitigation |
|------|---------|------------|
| **Cloud Run not authorized for Cloud SQL** | 403 / connection refused from runtime | Grant runtime SA `roles/cloudsql.client` (§D8) |
| **Missing `--add-cloudsql-instances` or connector config** | Unix socket URL fails on Cloud Run | Add `SQL_CONNECTION_NAME` annotation on deploy (§D8 Path 3) |
| **Wrong Secret Manager version** | Cloud Run points at Neon URL, old password, or disabled version | Add **new** version for Cloud SQL URL; pin revision; keep Neon version for rollback (§D4, §H₁) |
| **Schema incomplete** | Preflight or drain fails on missing table | Apply §D5 / §E files in order; bootstrap `wecom_reply_dedup` if needed |
| **Clean DB has no historical `service_records`** | Workbench empty; no old cases | Expected for smoke — smoke creates **new** Draft rows only |
| **WeCom still generates multiple callbacks** | Duplicate inbox rows / dedup noise | One test message only in Phase 2; monitor `wecom_inbox_events` |
| **Queue rows from Neon copied to Cloud SQL** | Empty-drain never reaches `claimed=0`; false failure | **Do not** `pg_dump` Neon `wecom_*` tables (§F) |
| **Old Neon stuck rows (ids 8–11) migrated** | Inbox stuck in `processing` / poisoned drain | **Do not migrate** — repair Neon separately; Cloud SQL starts empty |

---

## D. Step-by-step commands

**Prerequisites:** `gcloud` authenticated; `psql` installed; repo cloned. Run from repo root unless noted.

### D0. Set operator variables

```bash
export PROJECT_ID="optimal-disk-472305-e2"   # ← confirm
export REGION="us-west1"
export INSTANCE_NAME="caseiq-pg-usw1"        # ← confirm
export DB_NAME="caseiq"
export DB_USER="caseiq_app"
export DB_PASSWORD="$(openssl rand -base64 24)"   # save in password manager
export SM_SECRET="fiqa-service-record-database-url"

gcloud config set project "$PROJECT_ID"
```

### D1. Enable APIs (once per project)

```bash
gcloud services enable sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  --project "$PROJECT_ID"
```

### D2. Create Cloud SQL Postgres instance

**Prerequisite:** Q0.9.3 decision gate passed (§C₂.5). Use §C₂.4 low-cost template — not the legacy examples below.

```bash
# Tier must come from §C₂.3 — do not guess
export INSTANCE_TIER="${INSTANCE_TIER:?Set INSTANCE_TIER from gcloud sql tiers list}"

gcloud sql instances create "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --database-version=POSTGRES_15 \
  --tier="$INSTANCE_TIER" \
  --region="$REGION" \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB \
  --no-storage-auto-increase \
  --backup-start-time=03:00 \
  --no-assign-ip
```

For **schema apply from laptop** with temporary public IP (remove authorized networks after smoke):

```bash
gcloud sql instances create "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --database-version=POSTGRES_15 \
  --tier="$INSTANCE_TIER" \
  --region="$REGION" \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB \
  --no-storage-auto-increase \
  --backup-start-time=03:00 \
  --authorized-networks=YOUR_OPERATOR_IP/32
```

**Do not use** `--availability-type=regional`, HA tiers, read replicas, or tiers larger than `$INSTANCE_TIER` without a new cost sign-off.

Record instance connection name:

```bash
export SQL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
echo "$SQL_CONNECTION_NAME"
```

### D3. Create database and user

```bash
gcloud sql databases create "$DB_NAME" \
  --instance="$INSTANCE_NAME" \
  --project="$PROJECT_ID"

gcloud sql users create "$DB_USER" \
  --instance="$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --password="$DB_PASSWORD"
```

### D4. Build connection URL and store in Secret Manager

Pick one URL form.

**Option A — Public IP (pilot / local `psql` only):**

```bash
export SQL_PUBLIC_IP="$(gcloud sql instances describe "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --format='value(ipAddresses[0].ipAddress)')"

export SERVICE_RECORD_DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${SQL_PUBLIC_IP}:5432/${DB_NAME}?sslmode=require"
```

**Option B — Cloud Run Unix socket (runtime — recommended after instance exists):**

```bash
export SERVICE_RECORD_DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}"
```

Store as a **new secret version** (do not delete Neon versions):

```bash
printf '%s' "$SERVICE_RECORD_DATABASE_URL" | gcloud secrets versions add "$SM_SECRET" \
  --project="$PROJECT_ID" \
  --data-file=-

# List versions (record Neon version number for rollback)
gcloud secrets versions list "$SM_SECRET" --project="$PROJECT_ID"
```

Local operator copy (git-ignored):

```bash
# Append or update .env.cloudrun — NEVER commit
echo "SERVICE_RECORD_DATABASE_URL=${SERVICE_RECORD_DATABASE_URL}" >> .env.cloudrun
```

### D5. Apply schema files (in order)

From repo root. Use Auth Proxy if instance has no public IP:

```bash
# Optional: Cloud SQL Auth Proxy in another terminal
# cloud-sql-proxy "$SQL_CONNECTION_NAME"

set -a && source .env.cloudrun && set +a

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/stage1_service_record.sql

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/intake_sessions.sql

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/intake_entities.sql

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_inbox_events.sql

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/wecom_reply_outbox.sql

# Optional explicit migration (also auto-applied on first PG write via repository):
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql
```

`wecom_reply_dedup` has **no** standalone `.sql` file — created on first use by `services/fiqa_api/wecom/reply_dedup.py`.

### D6. Verify `SELECT 1`

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT 1 AS ok;"
```

Python preflight (same check Cloud Run admin uses):

```bash
PYTHONPATH=. python3 -c "
from services.fiqa_api.wecom.queue_db import preflight_wecom_queue_db
print(preflight_wecom_queue_db())
"
```

Expect `ok: True` and both queue tables reachable.

### D7. Verify required tables

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -c "\dt"

psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'wecom_inbox_events',
    'wecom_reply_outbox',
    'service_records',
    'record_messages',
    'structured_record_data',
    'state_history',
    'office_actions',
    'intake_sessions',
    'intake_entities'
  )
ORDER BY table_name;
"
```

Optional — trigger `wecom_reply_dedup` DDL without sending traffic:

```bash
PYTHONPATH=. python3 -c "
from services.fiqa_api.wecom.reply_dedup import claim_reply_send, release_reply_claim
assert claim_reply_send('__schema_bootstrap__') is True
release_reply_claim('__schema_bootstrap__')
print('wecom_reply_dedup OK')
"
```

### D8. Wire Cloud Run to new DB secret

**IAM** (runtime service account needs secret access + Cloud SQL client if using connector):

```bash
export SERVICE_NAME="fiqa-api"
export RUN_SA="$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format='value(spec.template.spec.serviceAccountName)')"

gcloud secrets add-iam-policy-binding "$SM_SECRET" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${RUN_SA}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUN_SA}" \
  --role="roles/cloudsql.client"
```

**New revision** — pick one path:

*Path 1 — Secret-only update (no image rebuild) if `CLOUD_RUN_USE_SECRET_MANAGER=1` already and connector already configured:*

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --update-secrets="SERVICE_RECORD_DATABASE_URL=${SM_SECRET}:latest"
```

*Path 2 — Full deploy (sets env bundle + secrets):*

```bash
# Ensure .env.cloudrun has CLOUD_RUN_USE_SECRET_MANAGER=1
bash scripts/deploy_paid_pilot.sh
```

*Path 3 — First-time Cloud SQL connector on Cloud Run (add before or with update):*

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --add-cloudsql-instances="$SQL_CONNECTION_NAME" \
  --update-secrets="SERVICE_RECORD_DATABASE_URL=${SM_SECRET}:latest"
```

Confirm revision picked up new secret version:

```bash
gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format='yaml(spec.template.spec.containers[0].env,spec.template.metadata.annotations)'
```

**Queue flags for first validation revision:** keep `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0` until empty-drain checks pass (§G).

### D9. Rollback to Neon secret (if needed)

```bash
# List versions; pick last known-good Neon version (e.g. 2)
gcloud secrets versions list "$SM_SECRET" --project="$PROJECT_ID"

export NEON_SECRET_VERSION="2"   # ← operator sets

gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --update-secrets="SERVICE_RECORD_DATABASE_URL=${SM_SECRET}:${NEON_SECRET_VERSION}"

gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1

# Record rollback revision
gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format='value(status.latestReadyRevisionName)'
```

Neon database remains intact. For cost cleanup, delete the Cloud SQL instance per §H₂.

---

## E. Schema list (discovered in repo)

### E.1 SQL files — apply for smoke test

| Order | File path | Tables / purpose |
|-------|-----------|------------------|
| 1 | `services/fiqa_api/db/schema/stage1_service_record.sql` | `service_records`, `record_messages`, `structured_record_data`, `state_history`, `office_actions` |
| 2 | `services/fiqa_api/db/schema/intake_sessions.sql` | `intake_sessions` |
| 3 | `services/fiqa_api/db/schema/intake_entities.sql` | `intake_entities` |
| 4 | `services/fiqa_api/db/schema/wecom_inbox_events.sql` | `wecom_inbox_events` |
| 5 | `services/fiqa_api/db/schema/wecom_reply_outbox.sql` | `wecom_reply_outbox` |
| 6 (optional) | `services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql` | `office_owner_org_id` column + index on `service_records` |

### E.2 App-managed DDL (no standalone `.sql`)

| Table | Module | Notes |
|-------|--------|-------|
| `wecom_reply_dedup` | `services/fiqa_api/wecom/reply_dedup.py` | `CREATE TABLE IF NOT EXISTS` on first `claim_reply_send()` |

### E.3 Tables used by current WeCom + draft flow (no separate “active case” table)

| Table | Used by | Smoke relevance |
|-------|---------|-----------------|
| `wecom_inbox_events` | `inbox_queue.py`, `inbox_worker.py`, `queue_admin.py` | Callback enqueue; drain claim/mark |
| `wecom_reply_outbox` | `reply_outbox.py`, `queue_admin.py` | Outbound queue; Phase 2 `sent=1` |
| `wecom_reply_dedup` | `reply_dedup.py`, `slice.py` | Exactly-one phone reply guard |
| `service_records` (+ children) | `service_record_repository.py`, `case_truth_repository.py`, `active_case_bridge.py` | Draft case create/read during slice |
| `intake_sessions` | `session_repository.py`, `session_store.py` | Session payload if slice touches intake session |
| `intake_entities` | entity memory path | Optional for smoke; apply for schema parity |

**No `wecom_active_case` table** — active workspace state is carried in `service_records` / intake session JSON via `active_case_bridge.py` and `case_truth_repository.py`.

### E.4 DB helpers (discovered in repo)

| Helper | File | Role |
|--------|------|------|
| `service_record_database_url()` | `services/fiqa_api/db/service_record_settings.py` | Resolves `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL` |
| `service_record_connection()` | `services/fiqa_api/db/service_record_repository.py` | Primary Postgres context manager (`connect_timeout=3`) |
| `intake_session_connection()` | `services/fiqa_api/inbox_triage/session_repository.py` | Intake sessions (`connect_timeout=10`) |
| `preflight_wecom_queue_db()` | `services/fiqa_api/wecom/queue_db.py` | Admin preflight: `SELECT 1` + queue table probe |
| `require_service_record_database_url()` | `services/fiqa_api/wecom/queue_admin.py` | Operator drain/status guard |
| `claim_reply_send()` / `release_reply_claim()` | `services/fiqa_api/wecom/reply_dedup.py` | Outbound idempotency |
| `_ensure_office_owner_org_schema()` | `services/fiqa_api/db/service_record_repository.py` | Runtime DDL for `office_owner_org_id` |

### E.5 Operator scripts (post-migration, not Q0.9.1)

| Script | Purpose |
|--------|---------|
| `scripts/wecom_drain_queues.py` | Local/manual drain (`--status`, `--limit 1`) |
| `scripts/deploy_paid_pilot.sh` | Paid pilot deploy wrapper → `deploy_cloud_run_core.sh` |
| `scripts/validate_pilot_deploy_env.py` | Pre-deploy env validation |

---

## F. Clean DB vs migrate data

**Q0.9.2 policy:** First smoke uses a **clean Cloud SQL database**. Do **not** migrate Neon data yet.

| Scenario | Recommendation | Why |
|----------|----------------|-----|
| **First smoke after Cloud SQL cutover** | **Clean Cloud SQL DB** (schema only) | Isolates infra validation from Neon baggage |
| **Neon stuck queue rows (ids 8–11)** | **Do not copy** to Cloud SQL | Q0.8.4 left inbox rows in `processing` / `pending`; copying them would poison empty-drain and Phase 2 signals |
| **Neon `wecom_*` tables** | **Do not migrate** for smoke | Start with empty inbox/outbox/dedup on Cloud SQL |
| **Neon `service_records` / cases** | **Do not migrate** for first smoke | Smoke creates fresh Draft rows; avoids conflating old case state with new infra |
| **After smoke passes** | Decide later whether to migrate selected tables | Candidate tables: `service_records`, `record_messages`, `structured_record_data`, `state_history`, `intake_sessions` — **not** `wecom_inbox_events` / `wecom_reply_outbox` unless you have a deliberate ops reason |
| **Real pilot with existing cases** | Selective `pg_dump` / `pg_restore` in a **future** step (post-Q0.9.3) | Only after Cloud SQL drain stability is proven |

Clean DB reduces risk and cost: failed Neon drains left rows in `processing` and multiplied callback dedup keys. A 10 GB zonal instance with schema-only data stays within the §C₂ cost guardrail. Neon can be repaired separately (`repair-stale`) while Cloud SQL proves empty-drain stability.

---

## G. Smoke test after migration (do not run during Q0.9.1 / Q0.9.2)

Follow [`docs/wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md). Minimum bar **before** any WeCom test message:

### G1. Admin status 3× (from Cloud Run)

```bash
export SERVICE_URL="$(gcloud run services describe fiqa-api \
  --region us-west1 --project "$PROJECT_ID" --format='value(status.url)')"
export WECOM_QUEUE_ADMIN_TOKEN="<from Secret Manager or env — do not log>"

for i in 1 2 3; do
  curl -sS -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN" \
    "$SERVICE_URL/api/admin/wecom/queues/status" | jq '.db_preflight'
done
```

Expect `ok: true` all three times.

### G2. Empty drain

```bash
curl -sS -X POST "$SERVICE_URL/api/admin/wecom/queues/drain?limit=1" \
  -H "Authorization: Bearer $WECOM_QUEUE_ADMIN_TOKEN" | jq .
```

Expect HTTP 200, `inbox.claimed=0`, `outbox.claimed=0`, no 503/504.

### G3. Phase 2 one-message test

Only after G1–G2 pass:

1. Set `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`, `WECOM_SLICE_SEND_REPLY=1` on Cloud Run.
2. Send **one** test message from a test WeCom customer account.
3. Drain via Cloud Run admin (`limit=1`) — not local laptop unless WeCom IP whitelist includes it.
4. Verify:
   - `wecom_reply_outbox` has **one** row with `status=sent` (or equivalent success)
   - Phone receives **exactly one** reply
   - Workbench shows **exactly one** Draft (no duplicate Draft from replay)
   - No `memory_degraded` in logs (fail-closed Q0.8.3)

```bash
psql "$SERVICE_RECORD_DATABASE_URL" -c "
SELECT id, status, sent_at, dedup_key
FROM wecom_reply_outbox
ORDER BY id DESC LIMIT 5;
"

psql "$SERVICE_RECORD_DATABASE_URL" -c "
SELECT msg_id, claimed_at FROM wecom_reply_dedup ORDER BY claimed_at DESC LIMIT 5;
"
```

---

## H. Rollback and cleanup

### H₁. Rollback Cloud Run to Neon (keep Cloud SQL instance)

If Cloud SQL cutover fails validation, revert runtime to Neon **without** deleting Cloud SQL (unless cost is a concern — see H₂).

| Step | Action |
|------|--------|
| 1 | Pin Secret Manager to last known-good **Neon** version (§D9) |
| 2 | Deploy or `gcloud run services update` so new revision mounts that version |
| 3 | Set `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0` |
| 4 | Keep `WECOM_SLICE_SEND_REPLY=1` (direct reply path if needed) |
| 5 | Record rollback revision id in [`docs/wecom_q0_smoke_execution_record.md`](wecom_q0_smoke_execution_record.md) |
| 6 | On Neon: `repair-stale` if stuck inbox rows remain (ids 8–11 era) |

```bash
export NEON_SECRET_VERSION="2"   # ← operator sets from versions list

gcloud run services update fiqa-api \
  --region us-west1 \
  --project "$PROJECT_ID" \
  --update-secrets="SERVICE_RECORD_DATABASE_URL=fiqa-service-record-database-url:${NEON_SECRET_VERSION}" \
  --update-env-vars WECOM_INBOX_QUEUE=0,WECOM_REPLY_OUTBOX=0,WECOM_SLICE_SEND_REPLY=1
```

Neon database remains intact. Cloud SQL instance can stay provisioned for a later retry **or** be deleted to stop billing (H₂).

### H₂. Delete Cloud SQL instance (cost cleanup)

Use when smoke is done (temporary DB) or pilot validation failed and monthly cost is unacceptable.

**Order matters:** point Cloud Run back to Neon **first** (H₁), confirm traffic is healthy, then delete.

```bash
export INSTANCE_NAME="caseiq-pg-usw1"   # ← confirm

# 1. Confirm Cloud Run is NOT using Cloud SQL URL
gcloud run services describe fiqa-api \
  --region us-west1 --project "$PROJECT_ID" \
  --format='yaml(spec.template.spec.containers[0].env)'

# 2. Delete instance (irreversible — backups go with it)
gcloud sql instances delete "$INSTANCE_NAME" \
  --project="$PROJECT_ID" \
  --quiet

# 3. Confirm deletion
gcloud sql instances list --project="$PROJECT_ID" --filter="name:${INSTANCE_NAME}"
```

If using Cloud Run connector annotation, remove it after rollback:

```bash
gcloud run services update fiqa-api \
  --region us-west1 \
  --project "$PROJECT_ID" \
  --clear-cloudsql-instances
```

### H₃. Secret Manager cleanup (optional)

**Do not delete** the secret `fiqa-service-record-database-url` — Neon versions are your rollback path.

| Action | When | Command |
|--------|------|---------|
| **Disable Cloud SQL secret version** | Cloud SQL URL was added as `:latest` but you rolled back to Neon | Pin Cloud Run to Neon version (`:2`) — §H₁; optionally disable the Cloud SQL version |
| **Disable one secret version** | Cloud SQL version should not be picked up accidentally | `gcloud secrets versions disable VERSION_ID --secret=fiqa-service-record-database-url --project="$PROJECT_ID"` |
| **Destroy Cloud SQL version** | Cloud SQL password must be revoked | `gcloud secrets versions destroy VERSION_ID --secret=fiqa-service-record-database-url --project="$PROJECT_ID"` (only after rollback confirmed) |

List versions before any disable/destroy:

```bash
gcloud secrets versions list fiqa-service-record-database-url --project="$PROJECT_ID"
```

**Never destroy** the only remaining Neon version.

---

## I. Pre-execution checklist

- [ ] **§C₂.6 final cost and risk review (Q0.9.2.1)** complete — hidden costs + technical risks read
- [ ] §C₂.5 / §C₂.6.5 decision gate complete (cost, tier, storage, region, non-HA, clean DB, cleanup plan)
- [ ] [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) estimate ≤ **$20/month** (or explicit override recorded)
- [ ] `gcloud sql tiers list` run; `$INSTANCE_TIER` recorded — **`db-f1-micro`** preferred; **not** HA or dedicated-core
- [ ] Storage **10 GB** confirmed; 2 GB / 5 GB **not** forced; auto-increase **OFF**
- [ ] §C₂.6.6 safe create parameters copied to ops log
- [ ] Decisions in §C recorded (instance name, connection method, secret version plan)
- [ ] Neon secret version number saved for rollback
- [ ] Clean DB plan confirmed — **no** Neon migration; queue rows **not** copied; ids 8–11 **not** migrated
- [ ] Cloud SQL instance **not** created yet — Q0.9.3 is next step after this checklist
- [ ] Operator understands: schema apply ≠ data migration ≠ deploy ≠ smoke
- [ ] Cleanup path understood: §H₁ rollback + §H₂ delete if temporary smoke DB
- [ ] [`docs/wecom_q0_db_stability_decision.md`](wecom_q0_db_stability_decision.md) §10 safety checklist reviewed for post-migration smoke

---

## J. References

| Item | Location |
|------|----------|
| Q0.8.5 decision | `docs/wecom_q0_db_stability_decision.md` |
| Smoke runbook | `docs/wecom_q0_smoke_test.md` |
| Deploy / Secret binding | `scripts/deploy_cloud_run_core.sh` |
| Queue preflight | `services/fiqa_api/wecom/queue_db.py` |
| Admin drain | `services/fiqa_api/routes/wecom_queue_admin.py`, `services/fiqa_api/wecom/queue_admin.py` |
| Connect Cloud Run to Cloud SQL | [cloud.google.com/sql/docs/postgres/connect-run](https://cloud.google.com/sql/docs/postgres/connect-run) |
| Google Pricing Calculator | [cloud.google.com/products/calculator](https://cloud.google.com/products/calculator) |
| Cloud SQL Postgres pricing examples | [cloud.google.com/sql/docs/postgres/pricing-examples](https://cloud.google.com/sql/docs/postgres/pricing-examples) |

---

*Q0.9.1 + Q0.9.2 + Q0.9.2.1 — Cloud SQL migration execution plan — docs and command planning only. No Cloud SQL created, no data migrated, no deploy, no live smoke.*
