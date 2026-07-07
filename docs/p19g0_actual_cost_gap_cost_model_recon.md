# P19G-0 — Actual Cost Gap / Cost Model Recon

**Date:** 2026-07-07  
**Type:** Cost reconnaissance — **documentation only**  
**Audience:** Andy, Chen Kui pilot pricing, P19G+ agents  
**Prerequisite:** P19E-2 Progress Card ✅ CLOSED · P19F-1 Workbench Drawer UX Polish ✅ CLOSED (evidence `4ab6684`, revision `fiqa-api-00164-8c9`)  
**Related:** `p19f0_workbench_performance_scale_survey.md` · `p18_6_demo_readiness_cost_smoothness_audit.md` · `wecom_q0_cloud_run_network_decision.md` · `trial/TRACK_A_ACCEPTANCE_REPORT.md`

**This loop:** No code. No deploy. No config change. No billing change. No resource creation/deletion.

**Status:** ✅ **CLOSED** (2026-07-07) — recon complete; ready for P19G-1 Pricing / Pilot Package.

---

## 1. Executive Summary

P19G-0 answers one question: **what does this stack actually cost today, and what breaks first at 100 / 1,000 cases/month?**

| Finding | Answer |
|---------|--------|
| **Current largest fixed cost** | **Cloud SQL `caseiq-pilot-pg` (`db-f1-micro`) + WeCom networking (Cloud NAT + static IP)** — together ~**$18–24/month** |
| **Current largest variable cost** | **Cloud Run compute** at pilot volume — but still **<$5/month**; not dangerous yet |
| **Is cost dangerous at pilot scale?** | **No** — total estimated **$25–50/month** all-in |
| **Is cost dangerous at 100 cases/month?** | **No** — fixed infra still dominates; variable adds **~$5–15/month** |
| **What gets expensive at 1,000 cases/month?** | **OCR (if enabled)** and **LLM-per-message (if enabled)** become the main variable risks; preview proxy egress grows but stays secondary |
| **Minimum viable Chen Kui pilot price** | **$499/month** for one broker office (covers infra + support buffer); **$199/month** only viable as short intro promo with tight usage caps |
| **Better target price** | **$499–799/month** for single-office paid pilot |
| **True office intake system price** | **$999+/month** when OCR, multi-user Workbench, and SLA expectations are included |

**One-line recommendation:**

> **Paid pilot economics are fine today.** Fixed GCP baseline (~$25–45/month) is acceptable for a single paying broker office. Do **not** optimize infra prematurely. Guard against **OCR-on-every-upload** and **LLM-on-every-message** — those are the future cost cliffs, not Cloud SQL or GCS.

---

## 2. Current Project Environment

### 2.1 GCP project (live, inspected 2026-07-07)

| Item | Value |
|------|-------|
| **GCP project** | `optimal-disk-472305-e2` |
| **Billing account** | `015AB8-391105-7ECE90` (linked, `billingEnabled: true`) |
| **Region** | `us-west1` |
| **Backend** | Cloud Run `fiqa-api` |
| **Backend URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **Current revision** | `fiqa-api-00164-8c9` (deployed 2026-07-07 ~20:15 UTC) |
| **Cloud SQL** | `caseiq-pilot-pg` → database `caseiq` @ private IP `10.73.0.3` |
| **DB secret** | `fiqa-service-record-database-url-cloudsql-private` |
| **GCS bucket** | `gs://caseiq-wecom-media-qa` (private) |
| **Frontend** | Vercel stable alias `https://ui-smoky-beta.vercel.app` |
| **WeCom egress** | Cloud NAT `fiqa-wecom-nat-gateway` + static IP `8.235.43.132` |
| **OCR on WeCom/H5** | **Not active** — attachments stored; preview via backend proxy |
| **LLM on WeCom slice** | **Not used** — `wecom/intent.py` is rule-based |
| **LLM on Unified Intake API** | `LLM_GENERATION_ENABLED=1` on Cloud Run; selective routing in `triage.py` |

### 2.2 Inspection commands used (read-only)

```bash
gcloud config get-value project
gcloud run services describe fiqa-api --region=us-west1
gcloud sql instances describe caseiq-pilot-pg
gsutil du -s gs://caseiq-wecom-media-qa
gsutil ls -l gs://caseiq-wecom-media-qa/**
gcloud compute routers list
gcloud compute addresses list
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="fiqa-api"' ...
gcloud billing projects describe optimal-disk-472305-e2
```

### 2.3 What could not be queried from this environment

| Item | Status |
|------|--------|
| **Actual GCP invoice / month-to-date spend** | Billing Budgets API not enabled; no BigQuery billing export dataset found (`bq ls` shows only `agent_*` datasets). **Billing line-item data not accessible from CLI in this environment.** |
| **Postgres row counts / DB byte size** | Initial attempt via private IP `10.73.0.3` timed out from operator laptop. **Follow-up read-only query via authorized public IP succeeded:** 22 cases, 23 messages, DB size **8.74 MB**. |

### 2.4 Current actual environment finding (A)

#### Private IP vs public IP access

| Check | Result |
|-------|--------|
| **Private IP `10.73.0.3` from operator laptop** | **Connection timed out** — **expected and normal** |
| **Why** | Operator machine is **not inside GCP VPC**; Cloud Run reaches DB via VPC private networking; laptop cannot route to `10.73.0.3` directly |
| **Authorized public IP read-only retry** | **Success** via `34.169.226.245` (Cloud SQL authorized network includes operator IP) |
| **Method** | `apply_qa_postgres_env(for_write=True)` rewrites secret host to public IP; `SELECT COUNT(*)` only — no writes, no config change |

#### Actual DB data volume (2026-07-07)

| Metric | Value |
|--------|-------|
| **Cases** (`service_records`) | **22** |
| **Messages** (`record_messages`) | **23** |
| **Database size** (`caseiq`) | **8.74 MB** |
| **Provisioned storage** | 10 GB SSD (utilization **<0.1%**) |

#### Conclusions from DB measurement

| Conclusion | Detail |
|------------|--------|
| **DB data volume is tiny** | 8.74 MB vs 10 GB provisioned — years of pilot cases fit easily |
| **Postgres usage cost/scale risk currently low** | Storage and query volume are negligible; no tier upgrade pressure from data size |
| **Postgres is not a performance bottleneck today** | Confirms P19F-0 — preview proxy and cold start matter more than DB |
| **Cloud SQL fixed instance cost dominates over data usage** | You pay for **always-on `db-f1-micro` (~$12–18/mo)** regardless of 8.74 MB or 874 MB |
| **Variable cost risk is elsewhere** | Future OCR, LLM, Cloud Run preview traffic, logging — not Postgres row growth |

---

## 3. Current Cost Components

| Component | Role | Billing model | Current observed scale | Est. monthly $ |
|-----------|------|---------------|------------------------|----------------|
| **Cloud SQL `caseiq-pilot-pg`** | Postgres SoT (cases, messages, WeCom queues) | Always-on instance + SSD + backups | `db-f1-micro`, 10 GB SSD, zonal, backups on (7 retained) | **$12–18** |
| **Cloud NAT + static IP** | WeCom `sync_msg` / API egress whitelist | Fixed gateway + IP + per-GB processed | NAT router `fiqa-wecom-nat-router`, IP `8.235.43.132` | **$6–8** |
| **Cloud Run `fiqa-api`** | API, WeCom callback, H5 upload, preview proxy | Per request + vCPU-seconds + GiB-seconds | min=**0**, max=**2**, 1 vCPU, 1 GiB, concurrency=30 | **$0–5** |
| **GCS `caseiq-wecom-media-qa`** | Private attachment storage | $/GB-month + egress | **34 objects, 41.83 MiB** | **<$0.10** |
| **Secret Manager** | DB URL, OpenAI, Qdrant, H5 token, etc. | Per secret + access | 7 secrets | **~$0.50** |
| **Cloud Logging** | Request logs, PREVIEW_PERF, WeCom traces | Ingest + retention | ≥5,000 log entries / 7 days (query limit hit) | **$0–3** |
| **Artifact Registry / GCR** | Container images | Storage + egress on pull | `gcr.io/optimal-disk-472305-e2/fiqa-api` | **<$1** |
| **Cloud Build** | Deploy builds | Per build-minute | Occasional deploys | **$0–5** |
| **Vercel** | Workbench frontend | Plan-based + bandwidth | Unknown plan from CLI | **$0–20** |
| **OpenAI API** | Unified Intake LLM triage (optional path) | Per token | WeCom path = $0; API path selective | **$0–10** |
| **Qdrant Cloud** | Vector RAG (optional for intake-core) | External SaaS | Secret bound; warmup errors in logs — **not on critical path** for intake | **$0–25** (if active) |
| **OCR / Vision** | Not on WeCom/H5 path | Per image | **$0 today** | **$0** |

**Estimated current total:** **$25–50/month** (wide band reflects Vercel plan unknown and Qdrant usage uncertain).

### 3.1 Current monthly cost estimate (B)

> **Billing data not accessible from CLI; estimate based on current resource shape.**  
> No BigQuery billing export; no invoice line items retrieved. Figures below are **modeled**, not actuals.

| Component | Fixed $ | Variable $ | Total est. $ | Notes |
|-----------|---------|------------|--------------|-------|
| **Cloud SQL** | $12–18 | ~$0 | **$12–18** | `db-f1-micro` always-on; 8.74 MB data irrelevant to price |
| **Cloud NAT + static IP** | $6–8 | <$1 | **$6–9** | WeCom egress whitelist requirement |
| **Cloud Run** | $0 | $0–5 | **$0–5** | min=0; ~3.3k req/30d; likely within free tier |
| **GCS storage** | ~$0 | ~$0 | **<$0.10** | 41.83 MiB |
| **GCS bandwidth / preview proxy** | $0 | <$1 | **<$1** | 13 PREVIEW_PERF / 30d; proxy not public URL |
| **Cloud Logging** | $0 | $0–3 | **$0–3** | ≥5k entries/7d; within free tier likely |
| **Secret Manager + GCR + Build** | ~$1 | $0–5 | **$1–6** | Occasional deploys |
| **Vercel** | $0–20 | ~$0 | **$0–20** | Plan unknown from CLI |
| **OCR / Vision API** | $0 | $0 | **$0** | WeCom/H5 path: not active |
| **LLM API (OpenAI)** | $0 | $0–10 | **$0–10** | WeCom rules-only; API triage selective |
| **Qdrant (optional)** | $0–25 | $0 | **$0–25** | Not on intake-critical path |
| | | | | |
| **TOTAL** | **~$19–52** | **~$0–24** | **$25–50/month** | Fixed ~70–85% of total |

**Largest fixed cost:** Cloud SQL + NAT/IP (**~$18–26/month**).  
**Largest variable cost today:** Cloud Run (**<$5/month**) — trivial at current traffic.

---

## 4. Actual Cost Check Method

### 4.1 GCP billing / cost

| Check | Result |
|-------|--------|
| `gcloud billing accounts list` | Account `015AB8-391105-7ECE90` exists, open |
| `gcloud billing projects describe optimal-disk-472305-e2` | `billingEnabled: true` |
| BigQuery billing export | **Not configured** (no `billing_export` / `gcp_billing` dataset) |
| `gcloud billing budgets list` | **Blocked** — `billingbudgets.googleapis.com` not enabled on project |
| Cloud Console Cost Table | **Not queried** (would require console UI or billing export setup) |

**Conclusion:** **Billing line-item data not accessible from CLI in this environment.** All dollar figures below are **modeled from resource config + published GCP pricing + observed traffic**, not from an actual invoice.

**Recommended follow-up (operator, not this sprint):** Enable [Billing export to BigQuery](https://cloud.google.com/billing/docs/how-to/export-data-bigquery) or create a $50/month budget alert in Console.

### 4.2 Cloud Run (`fiqa-api`)

| Setting | Value | Cost implication |
|---------|-------|------------------|
| **min instances** | **0** (no `autoscaling.knative.dev/minScale` annotation) | No idle instance burn; cold starts possible (+2–5s) |
| **max instances** | **2** | Caps burst spend |
| **CPU / memory** | 1 vCPU, 1 GiB | Standard pilot sizing |
| **concurrency** | 30 | One instance serves many light requests |
| **timeout** | 60s | Preview of large images can hold instance longer |
| **VPC egress** | `all-traffic` via Direct VPC (WeCom NAT path) | Required for WeCom; adds NAT processing cost (small at pilot volume) |
| **startup CPU boost** | enabled | Faster cold start; minor cost on scale-to-zero wake |

**Request volume (30 days, from Cloud Logging HTTP entries):** **~3,279 requests** (~110/day).

**Status distribution (sample):** 1,877× 200, 29× 401, 25× 404, 20× 504, others minor.

**Cold start cost implication:** At min=0 and ~110 req/day, cold starts are **infrequent enough that cost is negligible**; the bigger issue is **latency** (P19F-0), not money. Setting min=1 would add roughly **$15–25/month** (1 vCPU × 730 hr) — a deliberate tradeoff, not required for cost control at pilot scale.

### 4.3 Cloud SQL (`caseiq-pilot-pg`)

| Setting | Value |
|---------|-------|
| **Tier** | `db-f1-micro` (shared 0.2 vCPU, 0.6 GB RAM) |
| **Edition** | Enterprise |
| **Availability** | Zonal (non-HA) |
| **Storage** | 10 GB PD-SSD (`dataDiskSizeGb: 10`, auto-resize off) |
| **Backups** | Enabled, 7 retained, daily ~03:00 UTC |
| **Network** | Private IP `10.73.0.3` on `default` VPC; public IP still present |
| **Database** | `caseiq` (plus default `postgres`) |

**Rough monthly baseline (published pricing, us-west1 ≈ us-central1):**

- Instance (`db-f1-micro`): **~$7.50–$10** ([Google pricing example](https://cloud.google.com/sql/docs/postgres/pricing-examples): $9.37/mo for similar test instance)
- 10 GB SSD: **~$1.70**
- Backup storage: **~$0.50–2** (small DB expected)
- **Total: ~$10–18/month**

**Is Cloud SQL likely the largest fixed cost?** **Yes** — together with Cloud NAT, it forms the **non-negotiable monthly floor**.

### 4.4 GCS (`caseiq-wecom-media-qa`)

| Metric | Value |
|--------|-------|
| **Object count** | 34 |
| **Total size** | 41.83 MiB (43,862,003 bytes) |
| **Average object size** | ~1.29 MB |
| **Median object size** | ~393 KB |
| **Max object size** | ~4.7 MB |
| **Min object size** | 22 bytes (likely placeholder/test) |
| **Paths** | `wecom/…` and `h5/case_…/…` |

**Monthly storage cost:** 42 MiB × $0.020/GB ≈ **$0.001/month** — effectively free.

**Egress pattern:** Workbench preview uses **backend proxy** (`download_as_bytes` → inline response), so GCS egress is **Cloud Run ↔ GCS internal** (no public URL); browser egress is **Cloud Run → Vercel user**. At pilot scale this is **pennies**; at 1,000 cases/month with heavy preview it becomes **tens of dollars**, still below OCR/LLM.

### 4.5 Logging

| Signal | Observed |
|--------|----------|
| Log entries (7d sample) | ≥5,000 (query limit reached) |
| PREVIEW_PERF entries (30d) | 13 |
| Sample PREVIEW_PERF | `total_ms=136–249`, `gcs_ms=52–145`, `bytes=22–4,054,403` |
| Error logs (7d) | Qdrant warmup failures (non-fatal for intake-core) |

**Current logging cost:** Likely **within free tier** (50 GiB ingest/month) → **$0–3/month**.

**Future risk:** If every preview, WeCom callback, and case mutation logs at INFO with full payloads, **1,000 cases/month could push ingest to 20–100+ GiB** → **$10–50/month**. PREVIEW_PERF is valuable but should stay **one line per preview**, not per chunk.

### 4.6 Vercel

| Item | Status |
|------|--------|
| Production alias | `https://ui-smoky-beta.vercel.app` |
| Deploy evidence | `vercel deploy --prod` (P19F-1) |
| Actual plan / invoice | **Unknown from CLI** |

**Model:**

| Plan | Monthly | Pilot fit |
|------|---------|-----------|
| Hobby | $0 | Possible for founder demo; not ideal for paid broker |
| Pro | ~$20/seat | Reasonable for pilot |
| Bandwidth | Low at 1–5 broker users | **Low risk** for pilot |

---

## 5. Scenario Cost Model (C)

Assumptions align with P19F-0 load model. All figures are **rough ranges**, not quotes.  
**Billing data not accessible from CLI; estimates based on current resource shape.**

### Scenario 1 — Current / Pilot

| Dimension | Assumption |
|-----------|------------|
| Offices | 1 broker office |
| Cases | 10–50/month |
| Images | 2–4 per case → 20–200 images/month |
| OCR | **Off** |
| Traffic | Low — ~100 req/day observed |

| | Estimate |
|---|----------|
| **Fixed cost** | **$20–28/mo** (SQL + NAT + secrets + Vercel floor) |
| **Variable cost** | **$5–22/mo** (Run, GCS, logs, LLM buffer) |
| **Total** | **$25–50/mo** |
| **Major driver** | Cloud SQL instance hours (not data volume) |
| **Dangerous?** | **No — acceptable** |

### Scenario 2 — Small Paid Pilot (100 cases/month)

| Dimension | Assumption |
|-----------|------------|
| Cases | 100/month |
| Images | ~300/month |
| Users | 1–3 brokers |
| OCR | Off or limited manual trigger |

| | Estimate |
|---|----------|
| **Fixed cost** | **$20–38/mo** (same SQL/NAT; Vercel Pro likely) |
| **Variable cost** | **$15–42/mo** (Run previews, logging, optional LLM) |
| **Total** | **$35–80/mo** |
| **Major driver** | Still **fixed infra ~60–70%**; variable creeping from Run + logging |
| **Dangerous?** | **No — acceptable** if priced ≥$499/mo |

### Scenario 3 — Growth (500–1,000 cases/month)

| Dimension | Assumption |
|-----------|------------|
| Cases | 500–1,000/month |
| Images | 2,000–4,000/month |
| Users | ~5 brokers |
| OCR | Maybe **async** on upload |

| | Estimate (rules-only) | Estimate (OCR + selective LLM) | Estimate (OCR + LLM every message) |
|---|----------------------|-------------------------------|----------------------------------|
| **Fixed cost** | $25–55/mo | $25–55/mo | $25–55/mo |
| **Variable cost** | $45–95/mo | $75–195/mo | $175–645/mo |
| **Total** | **$70–150/mo** | **$100–250/mo** | **$200–700+/mo** |
| **Major driver** | Cloud Run + logging | **OCR** + Run | **LLM** >> OCR |
| **Dangerous?** | **Acceptable** at $799+/mo | **Watch OCR caps** | **Yes — not viable** without usage limits |

#### Component detail — 1,000 cases/month (rules-only path)

| Component | Est. monthly $ | Notes |
|-----------|----------------|-------|
| Cloud SQL | $12–35 | May need `db-g1-small` under write burst — not because of 8.74 MB → GB data |
| Cloud NAT + IP | $6–10 | Flat |
| Cloud Run | $15–60 | Preview + webhook volume |
| GCS storage + proxy | $6–30 | Still secondary |
| Vercel + Logging | $30–90 | Logging verbosity matters |
| OCR | $0 | Off |
| LLM | $0–20 | Selective only |
| **Total** | **$70–150** | |

---

## 6. Cloud Run Cost

| Question | Answer |
|----------|--------|
| Is Cloud Run currently cheap? | **Yes** — min=0, ~3.3k req/month, likely **$0–5** |
| What drives Cloud Run cost up? | Preview proxy (CPU + duration), WeCom webhook bursts, cold-start churn if min=0 with spiky traffic |
| When to set min=1? | **UX reason** (eliminate cold start), not cost — adds ~$15–25/month |
| When does max=2 hurt? | Peak: 5 brokers × 4 previews × concurrent cases could queue; scale **latency** issue before **cost** issue |
| Direct VPC `all-traffic` cost | NAT processing on WeCom egress; **<$1/month** at pilot volume per TRACK_A |

**Per-request rough math (warm):**

- Case GET: ~100–400 ms × 1 vCPU → negligible
- Preview proxy: ~150–3,000 ms × 1 vCPU, 1–5 MB memory spike → **~$0.0001–0.001 per preview**
- 1,000 previews/month ≈ **$0.10–1.00** compute + similar egress

---

## 7. Cloud SQL Cost

| Question | Answer |
|----------|--------|
| Is Cloud SQL overkill but acceptable? | **Yes** — `db-f1-micro` is the **smallest production-viable** Postgres on GCP; ~$12–18/month is correct for SoT |
| Is it the largest fixed cost? | **Yes** (single component); NAT+IP close second |
| When to upgrade tier? | Sustained CPU >60%, connection exhaustion, or `sync_msg` batch writes causing latency — not at 100 cases/month |
| HA / read replica? | **Not now** — doubles cost; defer until revenue |
| Replacing Cloud SQL to save $10/month? | **Not worth it** — migration risk >> savings |

**Backup note:** 7 daily backups on a small DB — expect **<$2/month** backup storage. Acceptable.

---

## 8. GCS Storage / Egress Cost

| Question | Answer |
|----------|--------|
| Is GCS storage cheap? | **Yes** — 42 MiB today costs **fractions of a cent** |
| At 1,000 cases/month? | ~2–5 GB/month new data → **$0.04–0.10/month** storage |
| Egress via preview proxy? | **Moderate variable** — money secondary to **latency** (P19F-0) |
| Public URL vs proxy? | Proxy is correct for security; signed URL + CDN is V2 cost optimization |
| Workbench preview: latency vs money? | **Primarily latency** at pilot/growth scale; money becomes visible only at **10k+ previews/month** |

**Image size observation:** Average ~1.3 MB, max ~4.7 MB. H5 uploads dominate large files. Thumbnails (P19F V1.1) save **broker time** more than **dollars** at current scale.

---

## 9. Vercel Cost

| Item | Assessment |
|------|------------|
| Plan unknown | Model **$0 (Hobby)** or **$20 (Pro)** |
| Bandwidth risk at pilot | **Low** — static SPA + API calls to Cloud Run |
| Bandwidth risk at 1,000 users | Still **low** — assets cached; API traffic hits GCP not Vercel |
| When Vercel matters | Team seats, Pro features, or commercial terms — not compute |

**Recommendation:** Budget **$20/month** for Vercel Pro in paid pilot COGS; confirm actual plan in Vercel dashboard.

---

## 10. Logging Cost

| Log source | Volume risk | Mitigation (future, not now) |
|------------|-------------|------------------------------|
| Cloud Run request logs | Medium at scale | Sample / exclude health checks |
| PREVIEW_PERF | Low today (13/30d) | Keep one-line structured; don't log bodies |
| WeCom callback logs | Medium if full payload logged | Log msg_id + outcome only |
| Error stack traces | Low | Acceptable |

**Verdict:** Logging is **not a cost issue today**. At 1,000 cases/month with current verbosity, could reach **$10–50/month** — still less than OCR/LLM mistakes.

---

## 11. Future OCR / Vision Cost (D — OCR)

### Current: OCR is not a cost today

| Fact | Detail |
|------|--------|
| WeCom/H5 main path | Images stored in GCS; **`ocr_status: not_started`** |
| Customer-facing copy | Never mentions OCR (P19D-1 guardrail) |
| Code exists | `v6_attachment_sidecar`, `image_input_pipeline.py` — **not invoked** on production WeCom/H5 upload |
| **Current OCR cost** | **$0/month** |

### Future: OCR must be async

| Rule | Why |
|------|-----|
| **Async only** | Must not block customer upload or WeCom chat flow |
| **Queue / batch after save** | Image saved → metadata in Postgres → OCR worker later |
| **Never sync on upload path** | Sync OCR adds latency + cost spike on every photo |
| **Broker-trigger or gated** | OCR on confirm, or capped images/month per plan |

### Future: OCR can become a top variable cost

**Current state:** WeCom/H5 path stores images in GCS with **`ocr_status: not_started`**. `v6_attachment_sidecar` + `image_input_pipeline.py` support Google Vision (REST or SDK) but are **not invoked** on the production WeCom/H5 upload path.

**If async OCR enabled on all uploads:**

| Volume | Vision API (~$1.50/1k images) | GPT-4o vision (~$0.005/image) | Gemini Flash (~$0.0005/image) |
|--------|-------------------------------|-------------------------------|-------------------------------|
| 300 images/mo (100 cases) | ~$0.45 | ~$1.50 | ~$0.15 |
| 3,000 images/mo (1,000 cases) | ~$4.50 | ~$15 | ~$1.50 |
| 30,000 images/mo (10k cases) | ~$45 | ~$150 | ~$15 |

**Will OCR become the main variable cost?** **Yes, if enabled at scale** — but only **after** fixed infra; at 1,000 cases/month with Vision, OCR (~$5–15) still **less than LLM-per-message** (~$50–500).

**Design guardrails (from P18.6):**

- Images saved first; OCR async / broker-triggered
- Never block customer upload on OCR
- WeCom customer copy never mentions OCR

---

## 12. Future LLM Cost (D — LLM)

### Judgment

| Question | Answer |
|----------|--------|
| Is LLM used on WeCom main path? | **No** — `wecom/intent.py` is rule-based; state machine + templates |
| Is LLM a current cost? | **Minimal** — `LLM_GENERATION_ENABLED=1` on Cloud Run but selective in `triage.py` |
| If every message calls LLM? | **Becomes major variable cost risk** — can exceed all GCP infra |
| Correct posture | **Rule-based / state-machine-first**; LLM only for gated, high-value moments |

**Current state:**

| Path | LLM? |
|------|------|
| WeCom `intent.py` / `slice.py` | **No** — rule-based |
| WeCom replies / cards | **No** — templates |
| Unified Intake `triage.py` | **Selective** — `LLM_GENERATION_ENABLED=1`; fast-path uses rules when `_is_fast_path_candidate` |
| Default model (when called) | `gpt-4o-mini` per `triage.py` |

**If every message uses LLM (dangerous):**

| Assumption | Cost |
|------------|------|
| 5,000 customer messages/month | |
| ~1,500 input + 300 output tokens each | |
| gpt-4o-mini ~$0.15/1M in, $0.60/1M out | **~$1.50–5/month** at this token estimate |
| With conversation history (8k input) | **~$10–50/month** |
| Full-history summarize per message | **~$50–500+/month** |

**Will LLM become costly if every message uses LLM?** **Yes** — especially with **full history context**. At 1,000 cases/month with rich context, LLM can **exceed all GCP infra combined**.

**Safe posture (maintain):**

- WeCom: rules-first (already true)
- API triage: selective LLM + fast path (already partially true)
- Case summary: rule template or **one LLM call per case state change**, not per message

---

## 13. Biggest Cost Risks

| Rank | Risk | Severity | When it bites |
|:----:|------|:--------:|---------------|
| 1 | **LLM on every message / full-history summarize** | 🔴 High | Any growth with `LLM_GENERATION_ENABLED=1` and loose routing |
| 2 | **Sync OCR on all uploads without async batching** | 🟠 Medium–High | 500+ cases/month |
| 3 | **Cloud SQL tier creep** (HA, `db-g1-small` without revenue) | 🟡 Medium | Premature "production hardening" |
| 4 | **Cloud Run min instances = 1 "for peace of mind"** without UX need | 🟡 Medium | +$15–25/month fixed |
| 5 | **Verbose logging at scale** | 🟡 Medium | 1,000+ cases/month |
| 6 | **Scope creep infra** (K8s, microservices, second Cloud Run service) | 🟠 Medium | Engineering choice, not customer-driven |
| 7 | **Preview proxy full-object fetch** | 🟢 Low (money) / 🟠 High (latency) | Broker UX, not COGS |
| 8 | **GCS storage accumulation** | 🟢 Low | Years of retention without lifecycle policy |
| 9 | **Qdrant Cloud subscription** | 🟢 Low | Only if RAG flows become mandatory — intake-core marks vectors optional |

**Hidden cost risks:**

- **Founder/engineering time** fixing cost problems that don't exist yet
- **Under-pricing pilot** below $400/month when support + infra + iteration is included
- **sync_msg historical batch** amplifying DB writes on `db-f1-micro` (operational, not dollar — but causes upgrade pressure)

---

## 14. Paid Pilot Pricing Implications (E)

### 14.0 Practical pricing judgment

| Price | Verdict | When to use |
|-------|---------|-------------|
| **$199/month** | **Too low for sustainable paid pilot** | Fixed Cloud SQL (~$18) + NAT (~$7) + Vercel (~$20) + founder support time → margin too thin. OK only as **short intro promo** with hard usage caps (≤50 cases, no OCR, no SLA) |
| **$499/month** | **Reasonable paid pilot starting point** | Covers COGS (~$50–80) + iteration buffer; aligns with Chen Kui value if tool saves **10+ hr/month** broker time |
| **$599–799/month** | **Recommended target** | Room for onboarding, OCR pilot, min instances for UX |
| **$999+/month** | **Mature office intake system** | Multi-seat, async OCR, retention policy, priority support, SLA |
| **Free / friend trial** | **OK to prove value once** | Cannot be long-term business model — fixed infra still burns ~$25–45/mo |

**Charge for business value, not cloud COGS alone.**

| Value lever | How pricing justifies it |
|-------------|--------------------------|
| **Broker time saved** | 50 add-car cases/mo × 6 min saved ≈ **22 hr/mo** (~$1,320 at $60/hr) — P16 model |
| **Fewer missed fields /漏单** | Structured intake + Workbench checklist reduces rework |
| **Staff handoff** | Case memory in Postgres — 吴小姐 can pick up without oral transfer |
| **VIP / urgency visibility** | Priority tags — not possible in raw WeChat FIFO |

### 14.1 COGS floor (single office)

| Line item | Monthly |
|-----------|---------|
| GCP fixed (SQL + NAT + secrets) | $20–28 |
| GCP variable (Run, GCS, logs) | $5–15 |
| Vercel Pro (assumed) | $20 |
| OpenAI buffer | $5–15 |
| **COGS subtotal** | **$50–80** |
| Support / iteration buffer (1.5–3× COGS) | $75–160 |
| **Minimum viable economics** | **~$125–240** internal floor |

This is **COGS + minimal sustain**, not fair market price for broker time saved.

### 14.2 Pricing recommendation

| Tier | Price | Rationale |
|------|-------|-----------|
| **Too low** | $199/month | Covers infra but **not** support, iteration, or OCR/LLM headroom; OK only as **3-month intro** with hard caps |
| **Minimum viable pilot** | **$499/month** | Covers COGS (~$80) + engineering/support buffer; defensible for one office saving 10–20 hr/month broker time |
| **Better target** | **$599–799/month** | Room for OCR pilot, min instances, onboarding |
| **True office intake system** | **$999+/month** | Multi-user, OCR async, SLA, retention policy, priority support |

### 14.3 Suggested usage limits (pilot contract)

| Limit | Starter ($499) | Growth ($799) |
|-------|----------------|---------------|
| Cases/month | 150 included | 500 included |
| Images/month | 500 included | 2,000 included |
| Broker seats | 3 | 10 |
| OCR | Off or 50 images/mo manual | 500 images/mo async |
| LLM | Rules-only WeCom; API triage selective | + case summary on confirm |
| Retention | 90 days attachments | 1 year |
| Overages | $2/case or pause | Negotiated |

### 14.4 Business value anchor (not COGS-only)

From `trial/P16_TIME_SAVINGS_MODEL.md`: at 50 add-car cases/month and 6.2 min saved/case → **~22 hr/month** recovered. At $60/hr broker time equivalent → **~$1,320/month value**. **$499/month is <40% of conservative value capture** — reasonable for paid pilot.

---

## 15. What Not To Optimize Yet

Explicit **do not do now** list:

| Do not | Why |
|--------|-----|
| Kubernetes / GKE | No scale problem; massive ops cost |
| Microservices split | Premature; Cloud Run monolith is fine |
| CDN for attachments | Private bucket + auth; needs signed URL design first |
| Aggressive caching layer | Pilot traffic too low |
| DB sharding | ~1,000 cases is trivial for Postgres |
| Event table **only for cost** | V2 architecture; JSONB + `state_history` sufficient |
| Replace Cloud SQL with Neon/SQLite to save ~$10 | Risk >> savings; Cloud SQL justified |
| Premature OCR on WeCom/H5 | Cost + latency cliff before product need |
| LLM on every message | Biggest future cost risk |
| WeChat mini program **for cost** | Channel decision is product, not COGS |
| Cloud SQL HA / read replica | Doubles DB cost without revenue |
| Second Cloud Run service | TRACK_A already rejected Option C for cost |
| Rip out preview proxy for public URLs | Security regression |

**Do optimize first if cost rises (ordered):**

1. **LLM routing** — tighten fast path; never full-history per message
2. **OCR gating** — async, broker-triggered, or post-confirm only
3. **Logging sampling** — exclude health checks; cap payload logging
4. **Preview thumbnails** — UX win with modest egress savings
5. **Cloud SQL tier** — only when metrics show sustained CPU/connection pressure
6. **GCS lifecycle policy** — archive attachments >1 year (when retention policy defined)

---

## 16. Final Recommendation

### 16.1 Answers to the 12 cost questions

| # | Question | Answer |
|---|----------|--------|
| 1 | Current largest fixed cost? | **Cloud SQL `db-f1-micro` (~$12–18/mo)**; NAT+IP (~$6–8/mo) close second |
| 2 | Current largest variable cost? | **Cloud Run** — but **<$5/mo** at observed volume |
| 3 | Cost dangerous at pilot scale? | **No** |
| 4 | Cost dangerous at 100 cases/month? | **No** — est. **$35–80/month** total |
| 5 | What gets expensive at 1,000 cases/month? | **LLM (if loose)** > **OCR (if enabled)** > logging > Cloud Run egress |
| 6 | Cloud SQL overkill but acceptable? | **Yes** |
| 7 | Cloud Run currently cheap? | **Yes** |
| 8 | GCS storage cheap? | **Yes** |
| 9 | OCR future main variable cost? | **Yes, if enabled at scale** — still below runaway LLM |
| 10 | LLM costly if every message? | **Yes** — can exceed all infra |
| 11 | Preview cost more latency than money? | **Yes** at pilot/growth scale |
| 12 | Minimum Chen Kui monthly price for viability? | **$499/month** (sustainable); **$599–799** better |

### 16.2 Strategic recommendation

1. **Current cost is not dangerous** — ~$25–50/month modeled; safe to continue pilot.
2. **Postgres data is tiny (8.74 MB)** — not a performance or variable-cost risk; `db-f1-micro` is correct.
3. **Cloud SQL fixed cost is the main floor** — instance hours, not row count.
4. **OCR / LLM are future variable cliffs** — gate them; keep WeCom rule-based.
5. **Do not architect for cost savings now** — no K8s, no SQL replacement, no microservices.
6. **Price on value** — $499+ for paid pilot; $199 only as capped intro.
7. **Close P19G-0** → next: **P19G-1 Pricing / Pilot Package** or product polish.

### 16.3 Direction supported by this recon

| Direction | Supported? |
|-----------|:----------:|
| Current cost not dangerous | ✅ |
| Postgres data tiny — not a risk | ✅ |
| Cloud SQL = main fixed cost | ✅ |
| OCR / LLM = future variable risk | ✅ |
| No big architecture changes for small savings | ✅ |
| Price on business value, not COGS alone | ✅ |
| Ready to close P19G-0 | ✅ |

---

## STOP Report (Final)

| # | Item | Result |
|---|------|--------|
| 1 | **Document path** | `docs/p19g0_actual_cost_gap_cost_model_recon.md` |
| 2 | **Current DB stats** | **22 cases** · **23 messages** · **8.74 MB** |
| 3 | **Private IP connection finding** | Laptop → `10.73.0.3` **timed out (expected)** — not in VPC. Authorized public IP read-only query **succeeded** |
| 4 | **Billing data accessible?** | **No** — Billing data not accessible from CLI; estimate based on current resource shape |
| 5 | **Current largest fixed cost** | **Cloud SQL `db-f1-micro` (~$12–18/mo)** + **NAT/IP (~$6–8/mo)** |
| 6 | **Current largest variable cost** | **Cloud Run (~$0–5/mo)** |
| 7 | **Estimated current monthly cost** | **$25–50/month** |
| 8 | **Estimated 100 cases/month** | **$35–80/month** |
| 9 | **Estimated 1,000 cases/month** | **$70–150** (rules-only) · **$100–250** (OCR selective) · **$200–700+** (LLM loose) |
| 10 | **Cost dangerous now?** | **No** |
| 11 | **Cloud SQL acceptable?** | **Yes** — `db-f1-micro` appropriate |
| 12 | **Postgres data size a concern?** | **No** — 8.74 MB; not performance or variable-cost risk |
| 13 | **OCR future main cost risk?** | **Yes, if enabled at scale** — async only; **$0 today** |
| 14 | **LLM future cost risk?** | **Yes** — if every message; worse than OCR |
| 15 | **Pricing recommendation** | Min **$499/mo** · Target **$599–799/mo** · Mature **$999+/mo** |
| 16 | **Optimize first if cost rises** | LLM routing → OCR gating → logging → thumbnails → SQL tier |
| 17 | **What not to optimize yet** | K8s, microservices, CDN, DB sharding, SQL replacement, sync OCR, LLM-every-message |
| 18 | **Code changed?** | **No** |
| 19 | **Deploy happened?** | **No** |
| 20 | **STOP** | **✅ P19G-0 CLOSED** → next: **P19G-1 Pricing / Pilot Package** or product polish |

---

## Appendix A — Evidence snapshot (2026-07-07)

```
Cloud Run: min=0 max=2 concurrency=30 cpu=1 memory=1Gi
Cloud SQL: caseiq-pilot-pg db-f1-micro 10GB zonal backups=7
Cloud SQL data (read-only, public IP): 22 cases, 23 messages, 8.74 MB DB size
GCS: 34 objects 41.83 MiB avg=1.29MB
HTTP requests 30d: ~3279
PREVIEW_PERF 30d: 13
Billing export: not configured
```

## Appendix B — References

| Doc | Relevance |
|-----|-----------|
| `docs/p19f0_workbench_performance_scale_survey.md` | Load model, preview bottleneck |
| `docs/p18_6_demo_readiness_cost_smoothness_audit.md` | LLM/OCR guardrails |
| `docs/wecom_q0_cloud_run_network_decision.md` | NAT cost, db-f1-micro target |
| `docs/trial/TRACK_A_ACCEPTANCE_REPORT.md` | NAT ~$6–8/month |
| `docs/trial/P16_TIME_SAVINGS_MODEL.md` | Value-based pricing anchor |
| [Cloud SQL pricing examples](https://cloud.google.com/sql/docs/postgres/pricing-examples) | db-f1-micro ~$9.37/mo reference |
| [Cloud Run pricing](https://cloud.google.com/run/pricing) | Per vCPU-second model |

---

*P19G-0 CLOSED 2026-07-07. No code. No deploy. No config change. Recon only.*
