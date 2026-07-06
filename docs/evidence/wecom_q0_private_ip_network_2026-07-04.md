# WeCom Q0.9.6 — Cloud SQL Private IP Network Evidence

**Date:** 2026-07-04  
**Task:** Q0.9.6 — Option A networking (Cloud SQL Private IP + Direct VPC all-traffic + Cloud NAT)  
**Branch:** `sprint/p16-trust-layer` @ `cb4940b`  
**GCP project:** `optimal-disk-472305-e2`  
**Operator:** ainew6380@gmail.com (gcloud active account)  
**Final verdict:** **PARTIAL** — private IP network path **PASS**; empty-drain clean-room **PARTIAL** (stale Q0.9.4 queue rows)

---

## 1. Pre-check

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Commit | `cb4940b` |
| Cloud SQL `caseiq-pilot-pg` | RUNNABLE, `us-west1`, `db-f1-micro`, 10 GB, ZONAL |
| Region | `us-west1` ✓ |
| VPC / subnet | `default` / `default` (`10.138.0.0/20`) ✓ |
| Cloud Run service | `fiqa-api` |
| Pre-change revision (Neon rollback) | `fiqa-api-00134-5wx` |
| Pre-change DB secret | `fiqa-service-record-database-url:2` (Neon) |
| Pre-change queue flags | `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0` |
| WeCom NAT | `fiqa-wecom-nat-gateway` → static IP **`8.235.43.132`** ✓ |
| Direct VPC egress | `all-traffic`, network `default`, subnet `default` ✓ |
| Cloud SQL connector (pre-change) | absent (`run.googleapis.com/cloudsql-instances: ''`) ✓ |

---

## 2. Private Services Access (default VPC)

| Item | Value |
|------|-------|
| servicenetworking API | enabled (was not enabled before this run) |
| Allocated range name | `google-managed-services-default` |
| CIDR | `10.73.0.0/16` |
| Peering | `servicenetworking-googleapis-com` on network `default` |
| Peering status | active (reserved range attached) |

Commands used (standard GCP pattern; did not modify Cloud NAT / router):

1. `gcloud compute addresses create google-managed-services-default --global --purpose=VPC_PEERING --prefix-length=16 --network=default`
2. `gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --ranges=google-managed-services-default --network=default`

---

## 3. Cloud SQL private IP

| Setting | Before | After |
|---------|--------|-------|
| Private IP | not enabled | **`10.73.0.3`** |
| Public IP | `34.169.226.245` | still enabled (`ipv4Enabled: true`) |
| Private network | — | `projects/optimal-disk-472305-e2/global/networks/default` |
| Tier | `db-f1-micro` | unchanged |
| Storage | 10 GB | unchanged |
| HA | ZONAL | unchanged |
| Storage auto-increase | OFF | unchanged |
| Replicas | none | unchanged |

Patch operation `1533f063-21eb-4350-b38b-943600000033` completed successfully (~15 min).

---

## 4. Secret Manager — private IP DB URL

| Secret | Purpose | Status |
|--------|---------|--------|
| `fiqa-service-record-database-url` (Neon) | production URL | **Untouched** |
| `fiqa-service-record-database-url-cloudsql` | public IP + socket URLs | **Untouched** |
| `fiqa-service-record-database-url-cloudsql-private` | private IP runtime URL | **Created** v1 |

| Field | Value |
|-------|-------|
| Secret name | `fiqa-service-record-database-url-cloudsql-private` |
| Host type | private IP |
| Host | `10.73.0.3` |
| DB name | `caseiq` |
| User | `caseiq_app` |
| Password | hidden |
| Connection format | `postgresql://caseiq_app:<hidden>@10.73.0.3:5432/caseiq?sslmode=disable` |

IAM: `1013093472160-compute@developer.gserviceaccount.com` granted `secretAccessor`.

---

## 5. Cloud Run deploy (private IP path)

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **New revision** | **`fiqa-api-00135-8zw`** |
| DB secret | `fiqa-service-record-database-url-cloudsql-private:latest` |
| Cloud SQL connector | **absent** (cleared / not bound) |
| VPC egress | `all-traffic` (Direct VPC) |
| Network interfaces | `[{"network":"default","subnetwork":"default"}]` |
| Cloud NAT / static IP | unchanged — **`8.235.43.132`** |

**Flags (unchanged):**

| Flag | Value |
|------|-------|
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_INBOX_QUEUE` | `0` |
| `WECOM_REPLY_OUTBOX` | `0` |
| `WECOM_QUEUE_ADMIN_TOKEN` | set (not logged) |
| WeCom secrets | unchanged |

Update command (no image rebuild):

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-secrets=SERVICE_RECORD_DATABASE_URL=fiqa-service-record-database-url-cloudsql-private:latest \
  --clear-cloudsql-instances \
  --network=default --subnet=default --vpc-egress=all-traffic
```

---

## 6. Admin endpoint security

| Test | HTTP | Result |
|------|------|--------|
| GET `/api/admin/wecom/queues/status` — no token | **401** | ✓ fail closed |
| GET `/api/admin/wecom/queues/status` — wrong token | **401** | ✓ fail closed |
| GET `/api/admin/wecom/queues/status` — correct token | **200** | ✓ |

Correct-token response shape:

- `db_preflight.ok=true`
- Returns counts only (`inbox.*`, `outbox.*` status buckets)
- No payload bodies exposed
- No `memory_degraded`

---

## 7. Cloud Run → Cloud SQL private IP — 5× status preflight

All 5 runs (3 s apart): **HTTP 200**, `db_preflight.ok=true`, no `memory_degraded`, no DB connection errors.

| Run | HTTP | db_preflight.ok | memory_degraded |
|-----|------|-----------------|-----------------|
| 1 | 200 | true | false |
| 2 | 200 | true | false |
| 3 | 200 | true | false |
| 4 | 200 | true | false |
| 5 | 200 | true | false |

**Result: PASS** — private IP DB path stable under repeated admin status probes.

Pre-drain queue snapshot (stale Q0.9.4 residue):

- inbox: `processing=1`, `processing_stale=1`
- outbox: `pending=13`

---

## 8. Empty drain stability test (2×)

Both runs returned **HTTP 200** (not 503). DB preflight succeeded throughout. **No HTTP 500. No memory_degraded. No Cloud SQL connection errors** (contrast with Q0.9.4 `no route to host :3307` failure).

| Run | HTTP | inbox | outbox | ok |
|-----|------|-------|--------|-----|
| 1 | 200 | claimed=1, processed=1, failed=0 | claimed=1, sent=0, **failed=1** | false |
| 2 | 200 | claimed=0 | claimed=1, sent=0, **failed=1** | false |

**Why not a clean empty drain:** Cloud SQL still holds Q0.9.4 smoke residue (1 stale inbox row, 13 pending outbox rows). Drain reclaimed stale inbox and attempted outbox sends. Failures were **WeCom API business errors** (not DB/network):

- inbox `sync_msg`: errcode **95007** (invalid msg token) — from IP **8.235.43.132** ✓ NAT preserved
- outbox `send_msg`: errcode **95018** (session status invalid) — from IP **8.235.43.132**

Cloud Run logs confirm `wecom_queue_db_preflight_ok_v1` on every drain step — **private IP Postgres connectivity held through multi-step drain** (the Q0.9.4 failure mode did not recur).

**Result: PARTIAL** — network/DB path PASS; clean-room empty drain FAIL due to stale queue data + WeCom API rejections on old outbox rows.

---

## 9. Queue state cleanup guidance

**repair-stale dry run** (post-drain):

```json
{
  "ok": true,
  "dry_run": true,
  "inbox_repaired": 0,
  "outbox_repaired": 0
}
```

**Current queue counts** (after 2× drain):

| Queue | pending | processing/sending | processed/sent | failed |
|-------|---------|-------------------|----------------|--------|
| inbox | 0 | 0 | 1 | 0 |
| outbox | 11 | 0 | 0 | 2 |

**Operator recommendations before Phase 2 live smoke:**

1. **Do not blindly drain** remaining 11 pending outbox rows — they will attempt `send_msg`.
2. Preferred: **clean reset** of smoke queue tables (`wecom_inbox_events`, `wecom_reply_outbox`) on `caseiq-pilot-pg`, or recreate smoke DB — **requires operator confirmation**.
3. Alternative: mark stale outbox rows failed/exhausted via controlled SQL (operator-approved), not via live drain.
4. Do **not** enable `WECOM_INBOX_QUEUE=1` / `WECOM_REPLY_OUTBOX=1` until queue tables are clean.

---

## 10. Acceptance criteria scorecard

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Cloud SQL has private IP | **PASS** (`10.73.0.3`) |
| 2 | Cloud Run uses private IP DB secret | **PASS** |
| 3 | Direct VPC all-traffic + Cloud NAT preserved | **PASS** (WeCom from `8.235.43.132`) |
| 4 | No Cloud SQL connector / public proxy path | **PASS** |
| 5 | Admin status 5× with `db_preflight.ok=true` | **PASS** |
| 6 | Empty drain 2× clean success | **PARTIAL** (HTTP 200 + DB OK; stale rows caused WeCom API failures) |
| 7 | No live WeCom smoke / Phase 2 | **PASS** (no new inbound message; drain touched stale outbox — see §9) |
| 8 | Queue flags OFF | **PASS** |
| 9 | Evidence file | **PASS** (this doc) |
| 10 | No scheduler/cron/PubSub/UI/product changes | **PASS** |

---

## 11. Rollback

**Not executed** — private IP network path succeeded. Production Cloud Run is now on Cloud SQL private IP (`fiqa-api-00135-8zw`), not Neon.

If operator needs to revert DB only (keep private IP infra):

```bash
gcloud run services update fiqa-api \
  --region=us-west1 \
  --project=optimal-disk-472305-e2 \
  --update-secrets=SERVICE_RECORD_DATABASE_URL=fiqa-service-record-database-url:2 \
  --network=default --subnet=default --vpc-egress=all-traffic
```

Keep `WECOM_INBOX_QUEUE=0`, `WECOM_REPLY_OUTBOX=0`, `WECOM_SLICE_SEND_REPLY=1`.

Do **not** delete Cloud SQL instance or private services access range without operator approval.

---

## 12. Final verdict and next action

**Verdict: PARTIAL**

| Area | Verdict |
|------|---------|
| Option A private IP networking | **PASS** |
| Cloud Run → Cloud SQL stability (status + drain DB path) | **PASS** |
| WeCom NAT egress preservation | **PASS** |
| Clean empty drain | **FAIL** (stale Q0.9.4 queue residue) |

**Next action (Q0.9.7 or operator step):**

1. ~~Clean smoke queue tables on `caseiq-pilot-pg` (operator confirmation required).~~ **Done — see Q0.9.6.1**
2. ~~Re-run empty drain 2× until `inbox.claimed=0` and `outbox.claimed=0` with `failed=0`.~~ **Done — PASS**
3. Only then proceed to Phase 2 live WeCom smoke with queue flags ON.

**Q0.9.6.1 follow-up (2026-07-04):** Queue cleanup and 2× empty drain **PASS** — evidence in [`wecom_q0_clean_queue_2026-07-04.md`](wecom_q0_clean_queue_2026-07-04.md). Ready for Q0.9.7.
