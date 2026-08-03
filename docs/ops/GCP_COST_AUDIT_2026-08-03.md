# GCP Cost Audit — 2026-08-03 (read-only)

**Project:** `optimal-disk-472305-e2`  
**Billing account:** `015AB8-391105-7ECE90` (enabled)  
**Auditor posture:** read-only — no resize, stop, delete, or scale changes executed  
**Cloud QA scale (verified):** `fiqa-api-qa` maxScale=`2`, minScale unset → **0**

---

## 1. Actual spend availability

| Window | Actual spend from billing export / Billing API |
|--------|-----------------------------------------------|
| Last 30 days | **Unavailable** |
| Last 90 days | **Unavailable** |
| Current monthly run-rate (invoice-based) | **Unavailable** |

### Limitation (do not invent numbers)

- No BigQuery billing export dataset exists in this project (`agent_main` / `agent_ops` / `agent_quarantine` are product datasets, not billing).
- Cloud Billing Budget API and Cloud Billing API are **not enabled** on the project (CLI refused without enabling APIs; this audit did not enable them).
- No SKU/service invoice line items were retrieved.

**Therefore:** sections below separate **verified inventory** from **labeled estimates** based on public list prices + observed resource shape. Prior modeled baseline: `docs/p19g0_actual_cost_gap_cost_model_recon.md` (~$25–50/mo). This audit updates inventory (notably Artifact Registry / Cloud Build storage growth).

**Founder follow-up for actuals:** enable BigQuery billing export on `015AB8-391105-7ECE90` → project dataset, or pull Console → Billing → Reports CSV for 30/90 days (do not commit sensitive exports).

---

## 2. Verified live inventory (2026-08-03)

### Cloud SQL

| Field | Value |
|-------|--------|
| Instance | `caseiq-pilot-pg` |
| Region | `us-west1` |
| Tier | `db-f1-micro` |
| Activation | `ALWAYS` |
| Availability | ZONAL |
| Disk | 10 GB PD_SSD |
| Backups | enabled, 7 retained |
| State | RUNNABLE |
| Created | 2026-07-04 |

### Cloud Run

| Service | Region | CPU | Memory | minScale | maxScale | Ready revision |
|---------|--------|-----|--------|----------|----------|----------------|
| `fiqa-api` | us-west1 | 1 | 1Gi | 0 (unset) | 2 | `fiqa-api-00233-scz` |
| `fiqa-api-qa` | us-west1 | 1 | 1Gi | 0 (unset) | 2 | `fiqa-api-qa-00040-xbf` |
| `airport-mvp-api` | us-west1 | 1 | 512Mi | 0 | 2 | yes |
| `airport-mvp-api-dev` | us-west1 | 1 | 512Mi | 0 | 2 | yes |
| `mortgage-agent-api` | us-west1 | 1 | 512Mi | 0 | 10 | yes |
| `smartsearchx-api` | us-west1 | 1 | 512Mi | 0 | 20 | **no ready URL / False** |
| `vitals-ingest` | us-central1 | 2 | 1Gi | 0 | 10 | yes |
| `vitals-ingest-lite` | us-central1 | 1 | 256Mi | 0 | 10 | yes |
| `vitals-viewer` | us-central1 | 1 | 512Mi | 0 | 20 | yes |

Revisions retained: **`fiqa-api` ≈ 233**, **`fiqa-api-qa` = 40**. Idle revisions do not bill compute while scaled to zero, but inflate Artifact/image retention pressure.

### Cloud Storage

| Bucket | Size (bytes) | Notes |
|--------|--------------|-------|
| `optimal-disk-472305-e2_cloudbuild` | **15,249,429,244** (~14.2 GiB) | Build artifacts — major storage pile |
| `caseiq-wecom-media-qa` | 83,647,320 (~80 MiB) | QA media — required for claim evidence |
| `run-sources-…-us-west1` | 8,806,297 | Cloud Run sources |
| `run-sources-…-us-central1` | 24,418 | negligible |
| `smartsearchx-bucket` | 0 | empty |

### Artifact Registry / GCR

| Repository | Location | Size (MB) |
|------------|----------|-----------|
| `gcr.io` | us | **65,325** (~63.8 GiB) |
| `ssx` | us-west1 | **5,783** |
| `cloud-run-source-deploy` | us-west1 | **2,521** |
| `cloud-run-source-deploy` | us-central1 | **143** |

**Combined container image storage ≈ 72 GiB** — dominant storage cost driver vs July model (<$1 assumed).

### Networking

| Resource | Detail |
|----------|--------|
| Cloud NAT | `fiqa-wecom-nat-gateway` on `fiqa-wecom-nat-router` (us-west1), MANUAL_ONLY |
| Static IP | `fiqa-wecom-static-ip` = `8.235.43.132` IN_USE by NAT |
| Forwarding rules / LB | none listed |
| VPC | `default` |

### Other

| Service | Observation |
|---------|-------------|
| Secret Manager | 8 secrets (small fixed cost) |
| Logging | `_Default` retention 30d; `_Required` 400d |
| BigQuery | agent datasets present; no billing export |
| Load balancing | none observed |

---

## 3. Estimates (labeled — not invoices)

Public list-price modeling, us-west1 / multi-region storage where applicable. Ranges are conservative.

| Component | Est. monthly $ | Why it exists | Required? | Notes |
|-----------|----------------|---------------|-----------|-------|
| Cloud SQL `caseiq-pilot-pg` | **$12–18** | Postgres SoT for cases / WeCom | **Yes** for QA+pilot | Always-on fixed cost |
| Cloud NAT + static IP | **$6–9** | WeCom whitelist egress | **Yes** while WeCom live callback needed | Charges while provisioned |
| Artifact Registry / GCR storage | **$7–12** | ~72 GiB images @ ~$0.10/GB-mo | Partially — keep recent only | **Grew sharply vs July** |
| Cloud Build bucket GCS | **$0.30–0.50** | ~14 GiB build junk | No long-term | Lifecycle cleanup |
| Cloud Run `fiqa-api` + `fiqa-api-qa` | **$0–5** | API traffic; min=0 | Yes | Idle ≈ $0 compute |
| Other Cloud Run (airport/mortgage/vitals/ssx) | **$0–8** | Legacy / side products | Mostly **no** for claim pilot | Scale-to-zero helps; images still stored |
| GCS media QA | **<$0.05** | Attachments | Yes (QA) | Small |
| Logging / Monitoring | **$0–5** | Ops | Yes light | 30d default |
| Secret Manager | **~$0.50** | Config | Yes | |
| **Modeled subtotal (GCP)** | **~$26–58** | | | Excludes Vercel / OpenAI / Qdrant SaaS |

### Answers to required questions

1. **Is Cloud SQL the largest fixed cost?**  
   **Likely yes among always-on compute/DB (~$12–18).** Closely challenged by **Artifact Registry storage (~$7–12)** and **NAT+IP (~$6–9)**. Without invoices, SQL remains the largest *fixed runtime* cost; image storage may now rival it.

2. **Cloud Run cost with QA min=0 / max=2?**  
   **Estimate $0–3/mo for `fiqa-api-qa` alone** when idle most hours (scale-to-zero). Bursts during Founder QA / deploys add CPU-time only. Not the bill driver.

3. **What charges while unused?**  
   Cloud SQL ALWAYS, Cloud NAT gateway + static IP, Artifact Registry / GCS stored bytes, Secret Manager, logging retention, idle image layers.

4. **Abandoned / obsolete?**  
   - Cloud Run: `smartsearchx-api` unhealthy; `airport-*`, `mortgage-agent-api`, `vitals-*` not on claim Stage 1 path  
   - 233 prod + 40 QA revisions retained  
   - `gcr.io` 63+ GiB + `ssx` ~5.7 GiB + Cloud Build bucket ~14 GiB  
   - Empty `smartsearchx-bucket`

5. **Safe schedule / downsize / archive / delete?**  
   See §5. Prefer image/build lifecycle and non-claim service retirement **later** with owner sign-off. Do **not** stop Cloud SQL or NAT without WeCom/claim impact review.

6. **Smallest stable infra**

| Mode | Keep |
|------|------|
| Normal development | Local `run_demo_local.sh`; optional Cloud QA wake-on-use |
| Founder QA | `fiqa-api-qa` min=0 max=2, Cloud SQL, secrets, media bucket, Vercel preview → QA API |
| Chen demo | Same as Founder QA; optionally min=1 max=1 **only during demo window** then restore 0/2 |
| Future pilot | `fiqa-api` + SQL + NAT/IP (if WeCom) + media bucket + secrets; prune images; defer side services |

---

## 4. Top five cost drivers (estimated)

1. Cloud SQL `caseiq-pilot-pg` (always-on) — **$12–18/mo**
2. Artifact Registry / GCR image retention (~72 GiB) — **$7–12/mo**
3. Cloud NAT + static IP — **$6–9/mo**
4. Non-claim Cloud Run services + their images (indirect) — **$0–8/mo compute + storage share**
5. Cloud Logging / Build minutes / Build bucket — **$0–6/mo**

---

## 5. Top five safe savings opportunities (DO NOT EXECUTE in this audit)

| # | Action | Est. savings / mo | Risk | When | Commands (reference only) |
|---|--------|-------------------|------|------|---------------------------|
| 1 | Lifecycle-delete old `gcr.io` / Artifact images; keep last N digests per service | **$4–9** | Break rollback to ancient revisions | **Later** (after tag freeze) | `gcloud artifacts docker images list …` then delete untagged/old digests; set cleanup policies on repos |
| 2 | GCS lifecycle on `optimal-disk-472305-e2_cloudbuild` (delete objects >30d) | **$0.20–0.40** + clutter | Lose old build caches | **Later** | `gcloud storage buckets update gs://optimal-disk-472305-e2_cloudbuild --lifecycle-file=…` |
| 3 | Delete unused Cloud Run services after owner confirm (`smartsearchx-api`, idle vitals/airport/mortgage if abandoned) | **$0–5** compute + image GC | Break unrelated demos | **Later** | `gcloud run services delete SERVICE --region=…` (never fiqa-api / fiqa-api-qa without plan) |
| 4 | Prune old Cloud Run revisions (keep last 5–10) | Indirect (helps image GC) | Shorter rollback window | **Later** | `gcloud run revisions delete REV --region=us-west1` |
| 5 | Keep QA at min=0 max=2 (already); only raise min=1 during live Chen demo | Avoid **+$5–15** if min left at 1 | Cold start / invite process-local risk | **Now** (policy) | Demo window only: `gcloud run services update fiqa-api-qa --min-instances=1 --max-instances=1 …` then restore `--min-instances=0 --max-instances=2` |

**Expected monthly savings if #1–#4 done carefully:** about **$5–15/mo** (estimate).  
**Do not** stop Cloud SQL or delete NAT/IP for “savings” while WeCom claim path is active — high operational risk, low Founder value.

### Per-item decision table (major items)

| Item | Actual/Est $/mo | Required | Safe savings | Est. save | Risk | Act |
|------|-----------------|----------|--------------|-----------|------|-----|
| Cloud SQL | Est. $12–18 | Yes | None now (already smallest tier) | $0 | Pilot breakage | **Never** casually |
| Cloud Run QA 0/2 | Est. $0–3 | Yes | Keep 0/2 | Avoid uplift | Invite cold-start | **Now** keep |
| Cloud Run Prod 0/2 | Est. $0–5 | Yes for pilot | Keep 0/2 | — | — | **Later** tune |
| NAT+IP | Est. $6–9 | Yes if WeCom | Remove only if WeCom retired | $6–9 | WeCom fail | **Later/never** |
| GCR/AR images | Est. $7–12 | Partial | Lifecycle cleanup | $4–9 | Rollback depth | **Later** |
| Build bucket | Est. <$0.50 | No | Lifecycle | <$0.50 | Cache miss | **Later** |
| Side Run services | Est. $0–8 | No for Stage 1 | Delete/archive | $0–5 | Other demos | **Later** |

---

## 6. Cloud QA final scale (unchanged this audit)

```text
service: fiqa-api-qa
region: us-west1
minScale: 0 (unset)
maxScale: 2
```

No scaling commands were executed.

---

## 7. Recommended next step for *actual* spend

1. Console → Billing → Reports: export 30d and 90d by service/SKU (keep offline; do not commit).  
2. Enable detailed billing export to a dedicated BQ dataset (read-only analytics).  
3. Re-run this audit with actuals filling §1.
