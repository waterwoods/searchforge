# WeCom Q0.9.5 — Cloud Run Networking Architecture Decision

**Status:** Decision doc (Q0.9.5). No network changes executed. No live smoke scheduled.

**Task:** Resolve the conflict between WeCom static NAT egress and stable Cloud SQL connectivity from a single Cloud Run service (`fiqa-api`).

**Context:** Q0.9.3 created a low-cost Cloud SQL smoke DB. Q0.9.4 switched Cloud Run to Cloud SQL and attempted Phase 2 smoke. Preflight and empty drain passed; real drain failed with a Cloud SQL connection error. Production was rolled back to Neon with queue flags OFF.

**Evidence:**
- [`docs/evidence/wecom_q0_cloud_sql_smoke_2026-07-04.md`](evidence/wecom_q0_cloud_sql_smoke_2026-07-04.md) — Q0.9.4 failure record
- [`docs/evidence/wecom_q0_cloud_sql_2026-07-04.md`](evidence/wecom_q0_cloud_sql_2026-07-04.md) — Q0.9.3 instance/secret setup
- [`docs/trial/TRACK_A_ACCEPTANCE_REPORT.md`](trial/TRACK_A_ACCEPTANCE_REPORT.md) — WeCom NAT / Direct VPC egress acceptance

---

## 1. Executive summary

| Question | Answer |
|----------|--------|
| What broke in Q0.9.4? | Real drain (`limit=1`) failed with `no route to host` to Cloud SQL Auth Proxy port **3307** while Direct VPC egress `all-traffic` was enabled. |
| Why did preflight pass? | Preflight opens one short-lived connection; drain opens many connections over ~7–60s during `sync_msg` + slice + outbox writes. |
| Root cause class | **Network path conflict** — `all-traffic` Direct VPC egress + Cloud SQL connector (public proxy dial on `:3307`), not a Postgres engine or schema issue. |
| Recommended fix | **Option A** — Cloud SQL **private IP** on the existing VPC path; keep Direct VPC `all-traffic` + Cloud NAT for WeCom. |
| Fallback | **Option C** — split callback and worker/drain into separate Cloud Run services if Option A is blocked. |
| Do not retry yet | No Phase 2 rerun until empty drain and preflight pass from Cloud Run on the new DB network path. |

---

## 2. Current network facts

### 2.1 Cloud Run service

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| Region | `us-west1` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GCP project | `optimal-disk-472305-e2` |
| VPC egress | **Direct VPC Egress**, `--network=default --subnet=default --vpc-egress=all-traffic` |
| WeCom static NAT IP | **`8.235.43.132`** (reserved: `fiqa-wecom-static-ip`) |

### 2.2 WeCom NAT path (Track A — must preserve)

```
Cloud Run fiqa-api (us-west1)
  │  Direct VPC Egress (all-traffic)
  ▼
VPC "default" — subnet "default" (us-west1, 10.138.0.0/20)
  ▼
Cloud Router "fiqa-wecom-nat-router"
  ▼
Cloud NAT "fiqa-wecom-nat-gateway" (manual IP: 8.235.43.132)
  ▼
WeCom Open API (qyapi.weixin.qq.com) — 企业可信IP allowlist
```

WeCom requires outbound `sync_msg` / `send_msg` to originate from **`8.235.43.132`**. Without `all-traffic` Direct VPC egress + Cloud NAT, Cloud Run uses dynamic Google egress IPs and WeCom returns `errcode=60020`.

### 2.3 Cloud SQL instance (Q0.9.3)

| Item | Value |
|------|-------|
| Instance | `caseiq-pilot-pg` |
| Connection name | `optimal-disk-472305-e2:us-west1:caseiq-pilot-pg` |
| Region / zone | `us-west1` / `us-west1-b` |
| Tier | `db-f1-micro`, 10 GB, zonal (non-HA) |
| Engine | PostgreSQL 15 |
| Public IP (operator schema apply) | `34.169.226.245` |
| Private IP | **Not enabled** at Q0.9.3/Q0.9.4 time |
| Secret | `fiqa-service-record-database-url-cloudsql` (v1 public IP, v2 Unix socket) |

### 2.4 Q0.9.4 wiring (failed configuration)

| Item | Value |
|------|-------|
| Cloud SQL binding | `--add-cloudsql-instances=optimal-disk-472305-e2:us-west1:caseiq-pilot-pg` |
| DB secret | `fiqa-service-record-database-url-cloudsql:latest` (v2 socket URL) |
| VPC egress | `all-traffic` (unchanged — WeCom NAT preserved) |
| Queue flags during test | `WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1` |

### 2.5 Q0.9.4 test results

| Step | Result |
|------|--------|
| Admin auth | PASS — correct token → 200 |
| Status preflight 3× | PASS — `db_preflight.ok=true` |
| Empty drain | PASS — HTTP 200, `claimed=0` |
| One WeCom test message enqueued | PASS — 1 inbox row `pending` |
| **Real drain `limit=1`** | **FAIL — HTTP 503** |
| Post-drain status | FAIL — `db_preflight.ok=false` (transient) |

**Failure log (root cause):**

```text
Cloud SQL connection failed: dial error: failed to dial
  (connection name = "optimal-disk-472305-e2:us-west1:caseiq-pilot-pg"):
  dial tcp 34.169.226.245:3307: connect: no route to host
```

Worker claimed inbox row 1, ran `sync_msg` (returned 13 historical messages), then multiple DB writes failed. `inbox.processed=0`, `outbox.sent=0`, no phone reply.

### 2.6 Rollback state (current production)

| Item | Value |
|------|-------|
| `SERVICE_RECORD_DATABASE_URL` | Neon — `fiqa-service-record-database-url:2` |
| Cloud SQL connector | **Removed** from Cloud Run |
| `WECOM_INBOX_QUEUE` / `WECOM_REPLY_OUTBOX` | `0` |
| Cloud SQL instance | Left running for investigation |

---

## 3. Why Q0.9.4 failed

### 3.1 Primary cause — egress policy vs connector path

Cloud Run was configured with **Direct VPC egress `all-traffic`**, which routes **all** outbound traffic through the VPC subnet and Cloud NAT.

Q0.9.4 simultaneously used the **Cloud SQL Auth Proxy connector** (`--add-cloudsql-instances` + Unix socket URL). The connector sidecar dials the instance's **public endpoint on port 3307** to establish the proxy tunnel.

With `all-traffic` egress, that dial to `34.169.226.245:3307` did not have a valid route from the Cloud Run network namespace. Result: **`connect: no route to host`**.

This is a **routing conflict**, not:
- Cloud SQL instance health (instance was `RUNNABLE`)
- Schema or credentials (preflight succeeded)
- WeCom API permission ( `sync_msg` ran before DB writes failed)
- The Neon-class cross-cloud flapping seen in Q0.8.x (same GCP region; different failure mode)

### 3.2 Why preflight is insufficient

| Check | Load profile | What it proves |
|-------|--------------|----------------|
| Admin status / preflight | 1 short `SELECT 1` + table existence probes; request < 1s | "Can I open **one** connection right now?" |
| Empty drain | Preflight + claim attempt (0 rows); no `sync_msg` batch | "Does the idle path stay up?" |
| **Real drain** | Preflight + claim + **`sync_msg`** + N × (case + dedup + outbox) + mark; 8–15+ connections over 7–60s | "Can I **sustain** many connections under worker load?" |

Q0.9.4 proved that **preflight and empty drain are necessary but not sufficient**. Real drain is the proof path for Cloud Run → DB stability.

### 3.3 Secondary amplifier — `sync_msg` history batch

During the failed drain, `sync_msg` returned **13 historical messages** (not 13 duplicate callbacks for one user send). That amplified DB write load on `db-f1-micro` and created 13 pending outbox rows. This is an operational concern for future smokes (drain scope / sync cursor) but **did not cause** the `no route to host` error.

---

## 4. Options comparison

### Option A — Cloud SQL Private IP + Direct VPC Egress `all-traffic` + Cloud NAT

**Design:**

```
Cloud Run fiqa-api
  ├─ all-traffic egress → VPC → Cloud NAT → 8.235.43.132 → WeCom API (public)
  └─ all-traffic egress → VPC private path → Cloud SQL private IP :5432 (RFC1918)
```

| Aspect | Assessment |
|--------|------------|
| WeCom NAT | **Preserved** — all public egress still exits via Cloud NAT static IP |
| Cloud SQL path | **Private IP** inside VPC — direct TCP to Postgres; **no connector / no :3307** |
| Services | **Single** Cloud Run service — pilot-simple |
| Security | DB not exposed on public internet for runtime |
| Complexity | Moderate one-time VPC setup (private services access + private IP on instance) |
| Q0.9.4 evidence | Not yet tested; addresses the specific route conflict |

**Requirements:**
- Enable **private services access** (VPC peering to Google managed services) on VPC `default`
- Enable **private IP** on `caseiq-pilot-pg` (or recreate with private IP if enable-in-place is blocked)
- Update Secret Manager URL to use **private IP host** (not `/cloudsql/...` socket)
- Deploy Cloud Run **without** `--add-cloudsql-instances` when using direct private IP
- Keep `--network=default --subnet=default --vpc-egress=all-traffic` unchanged

**Verdict:** **Preferred** — production-like, cost-controlled, single service.

---

### Option B — Cloud SQL Public IP + Cloud SQL connector, preserving WeCom NAT

**Design:** Keep `all-traffic` egress + `--add-cloudsql-instances` + Unix socket URL (Q0.9.4 configuration).

| Aspect | Assessment |
|--------|------------|
| WeCom NAT | Intended to preserve — but DB path broke |
| Cloud SQL path | Connector dials public IP `:3307` — **conflicts with `all-traffic` routing** |
| Q0.9.4 result | **Failed** under real drain |
| Possible mitigations | Switch to `vpc-egress=private-ranges-only` — but then **WeCom public API egress loses NAT** unless split further; or add complex routing rules |
| Risk | High trial-and-error; same connector mechanism that already failed |

**Verdict:** **Not preferred.** Q0.9.4 is direct evidence that this combination does not work reliably under drain load. Only reconsider if Option A is blocked and a carefully validated connector + egress split is proven in a throwaway revision.

---

### Option C — Split services

**Design:**

| Service | Role | Network posture |
|---------|------|-----------------|
| `fiqa-api` (or `fiqa-api-callback`) | WeCom callback, fast enqueue | Direct VPC `all-traffic` + Cloud NAT → static IP |
| `fiqa-api-worker` (or admin-drain service) | Admin drain, inbox/outbox worker | Optimized for Cloud SQL — e.g. connector without `all-traffic`, or private IP with `private-ranges-only` |

| Aspect | Assessment |
|--------|------------|
| WeCom NAT | **Preserved** on callback service |
| Cloud SQL | **Can work** — worker service does not need `all-traffic` |
| Complexity | **High** — two deploy surfaces, two secret/env sets, routing between services, operational runbooks |
| Cost | Potential second always-on Cloud Run service |
| When to use | Fallback if single-service Option A cannot be configured in acceptable time |

**Verdict:** **Fallback** if Option A is blocked (e.g. private IP cannot be enabled on existing instance/VPC without recreation or org policy block).

---

### Option D — Go back to Neon

**Design:** Keep Neon serverless Postgres (`us-west-2`) with current Direct VPC `all-traffic` egress.

| Aspect | Assessment |
|--------|------------|
| WeCom NAT | Works — `sync_msg` passed from Cloud Run NAT in Q0.8.x |
| Cloud SQL | N/A |
| Drain stability | **Failed** under real drain in Q0.8.2 and Q0.8.4 (connection reset, IPv6 unreachable, pooled endpoint flaps) |
| Region | Cross-region `us-west1` → `us-west-2` adds latency and egress risk |
| Q0.9.4 rollback | Already reverted here — Neon is current state |

**Verdict:** **Not recommended** for pilot/production. Lowest infra change, but the same failure mode that motivated Q0.9.x Cloud SQL migration. See [`docs/wecom_q0_db_stability_decision.md`](wecom_q0_db_stability_decision.md).

---

## 5. Recommendation

### Preferred: Option A

**Cloud SQL Private IP with existing Direct VPC egress `all-traffic` + Cloud NAT.**

**Reasons:**
1. **Preserves WeCom static IP** (`8.235.43.132`) — no change to Track A NAT topology.
2. **Puts DB on private/internal network** — aligns with production posture; avoids public `:3307` proxy dial.
3. **Avoids the Q0.9.4 route conflict** — direct private IP `:5432` does not use the Cloud SQL connector sidecar path that failed.
4. **Keeps one Cloud Run service** — simplest ops for paid pilot.
5. **Same-region, cost-controlled** — `db-f1-micro`, zonal, no HA required for smoke/pilot.

### Fallback: Option C

Split worker/drain into a separate Cloud Run service if Option A cannot be configured quickly (VPC peering blocked, private IP enable fails, or org policy constraints).

### Explicitly not recommended

- **Option B** — already failed in Q0.9.4 under real drain.
- **Option D** — already failed under real drain in Q0.8.x; rolled back to temporarily, not a target state.

---

## 6. Implementation plan for Option A (do not execute yet)

Operator executes these steps only after explicit approval. **No steps below are run as part of Q0.9.5.**

### Phase 0 — Preconditions

- [ ] Confirm current Cloud Run revision uses Neon secret and flags OFF (rollback complete).
- [ ] Record current `gcloud run services describe fiqa-api --region=us-west1` network block for rollback reference.
- [ ] Confirm Cloud SQL instance `caseiq-pilot-pg` is `RUNNABLE`.

### Step A — Check VPC / subnet used by Direct VPC egress

```bash
gcloud run services describe fiqa-api \
  --region=us-west1 \
  --format='yaml(spec.template.metadata.annotations)' \
  | grep -E 'vpc|network|subnet|egress'
```

**Expected:** `network=default`, `subnet=default`, `vpc-egress=all-traffic`.

Document subnet CIDR: `10.138.0.0/20` (`us-west1`).

### Step B — Configure private services access for VPC `default`

If not already configured:

```bash
# Check existing allocated range
gcloud compute addresses list --global --filter='purpose=VPC_PEERING'

# Allocate range and create private connection (example — adjust prefix if conflict)
gcloud compute addresses create google-managed-services-default \
  --global \
  --purpose=VPC_PEERING \
  --prefix-length=16 \
  --network=default

gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=google-managed-services-default \
  --network=default \
  --project=optimal-disk-472305-e2
```

**Verify:** VPC peering to `servicenetworking.googleapis.com` exists in Cloud Console → VPC network → VPC network peering.

### Step C — Enable private IP on `caseiq-pilot-pg`

Preferred: enable private IP on existing instance (no data loss if instance supports it).

```bash
gcloud sql instances patch caseiq-pilot-pg \
  --network=projects/optimal-disk-472305-e2/global/networks/default \
  --no-assign-ip   # optional later: remove public IP after validation
```

If patch is blocked (instance created public-only without peering), options:
- Enable private IP while retaining public IP temporarily, **or**
- Recreate instance with private IP from scratch (schema re-apply; smoke DB is clean-test data only).

**Do not** enable HA or upgrade tier for this step.

### Step D — Confirm Cloud SQL private IP address

```bash
gcloud sql instances describe caseiq-pilot-pg \
  --format='value(ipAddresses)'
```

Record the **PRIVATE** type IP (e.g. `10.x.x.x`). This becomes the runtime DB host.

### Step E — Create/update Secret Manager DB URL (private IP)

Create a **new secret version** on `fiqa-service-record-database-url-cloudsql` (do not overwrite Neon secret):

```text
postgresql://caseiq_app:<PASSWORD>@<PRIVATE_IP>:5432/caseiq?sslmode=require
```

**Not** the Unix socket form:

```text
# Do NOT use for Option A runtime
postgresql://...@/caseiq?host=/cloudsql/optimal-disk-472305-e2:us-west1:caseiq-pilot-pg
```

Test from Cloud Shell or a VM in VPC `default` before Cloud Run cutover.

### Step F — Deploy Cloud Run (flags OFF)

Deploy with:

| Setting | Value |
|---------|-------|
| `--network` | `default` (unchanged) |
| `--subnet` | `default` (unchanged) |
| `--vpc-egress` | `all-traffic` (unchanged) |
| Cloud NAT | unchanged (`fiqa-wecom-nat-gateway`) |
| `--add-cloudsql-instances` | **omit / clear** — direct private IP, no connector |
| `SERVICE_RECORD_DATABASE_URL` | `fiqa-service-record-database-url-cloudsql:<new_version>` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |

Example connector removal if previously set:

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --clear-cloudsql-instances
```

Pin secret version in deploy; confirm revision picked up new URL via `gcloud run services describe`.

### Step G — Verify (before any WeCom message)

| # | Check | Pass criteria |
|---|-------|---------------|
| 1 | Admin status 3× | HTTP 200, `db_preflight.ok=true` each time |
| 2 | Empty drain | `POST /api/admin/wecom/queues/drain?limit=1` → HTTP 200, `inbox.claimed=0`, `outbox.claimed=0` |
| 3 | Cloud Run logs | Connections target **private IP** `:5432`, not `/cloudsql/...` or `:3307` |
| 4 | Queue state | `pending=0`, `processing=0`, or stale rows repaired/understood |
| 5 | WeCom egress spot-check | Optional: confirm NAT IP still `8.235.43.132` via throwaway Job sharing same network config (see Track A report §4) |

**Only after G passes:** proceed to Phase 2 one-message smoke (separate approved step — not Q0.9.5).

### Step H — Rollback

If verification fails:

1. Set `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0`.
2. Point `SERVICE_RECORD_DATABASE_URL` back to Neon `fiqa-service-record-database-url:2`.
3. Remove Cloud SQL connector annotation if re-added: `--clear-cloudsql-instances`.
4. **Do not** change Direct VPC / NAT settings unless abandoning WeCom NAT entirely.
5. Deploy new revision; confirm admin status returns `db_preflight.ok=true` on Neon.
6. Leave Cloud SQL instance running for retry; document stuck rows if any.

---

## 7. Risk checklist

Complete before executing Option A:

| Risk | Mitigation |
|------|------------|
| **Private services access IP range conflict** | List existing global internal ranges; choose non-overlapping `/16` before peering |
| **Cloud SQL instance may need private IP enabled or recreation** | Try `patch` first; smoke DB is disposable — recreate if needed |
| **Cloud Run must use same VPC/subnet path** | Keep `network=default`, `subnet=default`; do not clear network annotations |
| **Firewall / routes must allow private IP connectivity** | Default VPC + private services access typically sufficient; verify from VPC-attached test host |
| **WeCom NAT must still show static IP `8.235.43.132`** | Validate egress after any deploy; do not switch to `private-ranges-only` on the callback path |
| **Do not break Direct VPC `all-traffic`** | Required for WeCom 企业可信IP; changing egress policy breaks `sync_msg` |
| **Do not expose Cloud SQL publicly if private IP works** | Remove public IP / authorized networks after private path validated |
| **Clean Cloud SQL DB may need reset before retest** | Q0.9.4 left 1 stuck inbox (`processing`), 13 pending outbox rows — repair-stale or truncate before next smoke |
| **Secret version drift** | Pin version in deploy; verify `describe` shows intended secret, not stale socket URL |
| **Removing connector while keeping socket URL** | Socket URL requires connector — must switch to private IP host in secret |
| **db-f1-micro load under `sync_msg` batch** | Operational note: one user message can still pull many historical msgs; consider drain scope in smoke runbook |

---

## 8. Cost note

| Resource | Target |
|----------|--------|
| Cloud SQL `caseiq-pilot-pg` | Keep `db-f1-micro`, 10 GB, **zonal** (no HA) — ~$8–$18/month |
| Private IP / VPC peering | No additional always-on compute; peering is standard Cloud SQL private access |
| Cloud NAT + static IP | **Existing** Track A resources (~$6/month incremental per acceptance report) |
| Second Cloud Run service (Option C) | **Avoid** unless Option A blocked — adds always-on or min-instance cost |
| **Total DB target** | **≤ $20/month** for pilot smoke DB |

Do not upgrade to HA, `db-g1-small`, or read replicas for this networking fix.

---

## 9. Test plan

### 9.1 Before live message (mandatory)

| Step | Action | Pass |
|------|--------|------|
| 1 | `GET /api/admin/wecom/queues/status` with valid admin token **3 times** | `db_preflight.ok=true`, HTTP 200 |
| 2 | `POST /api/admin/wecom/queues/drain?limit=1` (empty queue) | HTTP 200, `inbox.claimed=0`, `outbox.claimed=0` |
| 3 | Cloud Run logs | DB connects via **private IP** path; no `:3307` / `no route to host` |
| 4 | Queue inspection | Clean or stale rows repaired/documented |
| 5 | Optional NAT check | Egress IP = `8.235.43.132` |

**Stop if any step fails.** Do not send WeCom test message.

### 9.2 Live Phase 2 (only after §9.1 passes — separate approval)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Enable flags (`WECOM_INBOX_QUEUE=1`, `WECOM_REPLY_OUTBOX=1`) on validated revision | Deploy recorded |
| 2 | Send **exactly one** test WeCom message | 1 inbox row `pending` |
| 3 | `POST .../drain?limit=1` via Cloud Run admin | HTTP 200 |
| 4 | Outcomes | `inbox.processed=1`, `outbox.sent=1` |
| 5 | Operator | **Exactly one** phone reply; no duplicate Draft Case |
| 6 | Logs | No `memory_degraded`, no 503 |

**Stop conditions:** `db_preflight.ok=false`, drain HTTP 500/503, `outbox.sent != 1`, stuck `processing`, unexplained duplicate replies.

### 9.3 Post-smoke rollback readiness

- Command to set flags OFF and revision ID recorded before message send.
- Neon secret version noted for emergency revert.

---

## 10. Out of scope (Q0.9.5)

- No live smoke or WeCom messages
- No network / Cloud SQL / Cloud Run deploy changes
- No scheduler / cron / PubSub / Cloud Tasks
- No UI or product behavior changes
- No Neon data migration
- No `sync_msg` cursor / batch-limit product fix (noted as follow-up)

---

## 11. References

| Doc / resource | Purpose |
|----------------|---------|
| [`docs/evidence/wecom_q0_cloud_sql_smoke_2026-07-04.md`](evidence/wecom_q0_cloud_sql_smoke_2026-07-04.md) | Q0.9.4 failure evidence |
| [`docs/evidence/wecom_q0_cloud_sql_2026-07-04.md`](evidence/wecom_q0_cloud_sql_2026-07-04.md) | Q0.9.3 instance + secrets |
| [`docs/wecom_q0_db_stability_decision.md`](wecom_q0_db_stability_decision.md) | Neon vs Cloud SQL decision (Q0.8.5) |
| [`docs/wecom_q0_cloud_sql_migration_plan.md`](wecom_q0_cloud_sql_migration_plan.md) | Cloud SQL migration runbook |
| [`docs/trial/TRACK_A_ACCEPTANCE_REPORT.md`](trial/TRACK_A_ACCEPTANCE_REPORT.md) | WeCom NAT / Direct VPC acceptance |
| [`docs/wecom_q0_smoke_test.md`](wecom_q0_smoke_test.md) | Phase 2 smoke runbook (for future rerun) |
| [Cloud SQL private IP](https://cloud.google.com/sql/docs/postgres/configure-private-ip) | GCP private IP setup |
| [Cloud Run VPC egress](https://cloud.google.com/run/docs/configuring/vpc-direct-vpc) | Direct VPC egress docs |

---

## 12. Acceptance criteria (Q0.9.5)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `docs/wecom_q0_cloud_run_network_decision.md` exists | ✅ |
| 2 | Clearly explains why Q0.9.4 failed | ✅ §3 |
| 3 | Compares Option A / B / C / D | ✅ §4 |
| 4 | Recommends Option A; fallback Option C | ✅ §5 |
| 5 | Implementation plan for Option A (not executed) | ✅ §6 |
| 6 | Risks, rollback, cost note, test plan | ✅ §7–§9 |
| 7 | No live smoke or deployment run | ✅ |

---

*Q0.9.5 — Cloud Run networking decision — 2026-07-04. No passwords, tokens, or secret values recorded.*
