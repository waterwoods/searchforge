# SearchForge FinOps — Billing Visibility V1

**Status:** Phase 2A — **EXPORT CONFIGURED; WAITING FOR GOOGLE DATA**  
**Date:** 2026-08-10  
**Project:** `optimal-disk-472305-e2`  
**Billing account:** `015AB8-391105-7ECE90` (`My Billing Account`, open, USD)  
**Authority:** ops inventory companion to `SEARCHFORGE_ACCOUNT_AND_INFRASTRUCTURE_INVENTORY_V1.md`  
**Safety:** This document does **not** authorize Artifact Registry / Cloud Build deletion (Phase 2B).

---

## 0. Founder action completed

Founder enabled:

**Google Cloud Billing → BigQuery export → Standard usage cost**

Verified by Cursor (2026-08-10 ~04:05Z):

| Check | Result | Class |
|-------|--------|-------|
| Project | `optimal-disk-472305-e2` | **KNOWN** |
| Dataset `billing_export` | Exists | **KNOWN** |
| Dataset location | **US** | **KNOWN** |
| Dataset created | ~2026-08-10T03:51:05Z | **KNOWN** |
| Billing export writer IAM | `billing-export-bigquery@system.gserviceaccount.com` has OWNER on dataset | **KNOWN** (strong signal export is wired) |
| Table `gcp_billing_export_v1_*` | **Not present yet** (`bq ls` empty; `__TABLES__` = `[]`) | **WAITING** |
| Actual $ queries | Not run (no table) | **WAITING** |

This empty-table state shortly after enable is **normal**, not a failure. Google may take hours (sometimes ~24–48h) before the first rows appear; multi-region US backfill of current + previous month can take up to ~5 days.

---

## 1. Billing architecture (configured)

```
GCP resources (Cloud Run, SQL, AR, GCS, …)
        → usage meters
        → Cloud Billing Account 015AB8-391105-7ECE90
        → BigQuery export (Standard usage cost)   ← Founder Save completed
        → dataset optimal-disk-472305-e2:billing_export (US multi-region)
        → table gcp_billing_export_v1_015AB8_391105_7ECE90   ← WAITING
        → SQL cost queries   ← blocked until table exists
```

**Expected table FQN (when created by Google):**

`optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`

---

## 2. What is measurable now vs after first rows

| Question | Now | After table has rows |
|----------|-----|----------------------|
| Export configured? | **YES** | YES |
| Actual $ last 7/30/90 days | **WAITING** | Measurable via SQL |
| Top service by $ | **WAITING** | Measurable |
| Cloud SQL / Run / AR $ | Shape known from inventory; $ **WAITING** | Measurable |
| Cost-per-case | Not available | Approximate GCP infra only (OpenAI/STT/LangSmith/Vercel still external) |

---

## 3. Prior Phase 2A CLI facts (still true)

| Fact | Class |
|------|-------|
| Project linked; billingEnabled=true | **KNOWN** |
| Founder `roles/billing.admin` | **KNOWN** |
| BigQuery API enabled | **KNOWN** |
| Do not reuse `agent_*` for billing | **KNOWN** (isolation) |
| Budgets API not required for Standard export | **KNOWN** |

---

## 4. Export design (locked for Phase 2A)

| Export type | Status |
|-------------|--------|
| **Standard usage cost** | **Enabled by Founder** |
| Detailed usage cost | Not in this phase |
| Pricing export | Not in this phase |
| FOCUS | Not in this phase |

---

## 5. Hypothesis validation (billing $)

| ID | Hypothesis | Status |
|----|------------|--------|
| H1 | Artifact Registry / image storage is a major cost driver | **INSUFFICIENT DATA** (size ~80.6 GiB known; $ not yet) |
| H2 | Cloud Build storage is meaningful | **INSUFFICIENT DATA** (~14.5 GiB known; $ not yet) |
| H3 | Cloud SQL db-f1-micro creates always-on baseline | **INSUFFICIENT DATA** (ALWAYS tier known; $ not yet) |
| H4 | Cloud Run cheap at pilot with minScale≈0 | **INSUFFICIENT DATA** |
| H5 | OpenAI not in GCP billing; measure separately | **PARTIALLY CONFIRMED** by architecture (OpenAI is vendor invoice; GCP export cannot show it) — $ still N/A |

Re-run validation SQL after table appears to upgrade H1–H4.

---

## 6. Optimization (blocked on $)

No measured TOP drivers / TOP savings yet.

**Do not** delete Artifact Registry images, Cloud Build objects, or Cloud Run revisions until real $ confirms priority (Phase 2B, human approval).

---

## 7. Cost-per-case readiness

| Layer | In GCP Standard export? | Status |
|-------|-------------------------|--------|
| GCP infrastructure | Yes (when table fills) | **WAITING** |
| OpenAI | No | External console |
| Chirp STT | Partially (Google STT SKUs may appear in GCP) | Later |
| LangSmith | No | External |
| Vercel | No | External |

Do not build a FinOps platform; wait for table → run SQL → optional later: infra $ ÷ case count from product metrics.

---

## 8. Validation SQL (run only after table exists)

```sql
-- 0) Table present?
SELECT table_id, creation_time
FROM `optimal-disk-472305-e2.billing_export.__TABLES__`
WHERE table_id LIKE 'gcp_billing_export%';
```

```sql
-- 1) Row window
SELECT
  COUNT(*) AS row_count,
  MIN(usage_start_time) AS min_usage_start,
  MAX(usage_start_time) AS max_usage_start,
  MIN(export_time) AS min_export_time,
  MAX(export_time) AS max_export_time
FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`;
```

```sql
-- 2) Current calendar month (UTC) — gross / credits / net
SELECT
  ROUND(SUM(cost), 4) AS gross_cost_usd,
  ROUND(SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS credits_usd,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS net_cost_usd
FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`
WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH);
```

```sql
-- 3) Last 7 / 30 / 90 days net
SELECT
  days,
  ROUND(SUM(net), 4) AS net_cost_usd
FROM (
  SELECT 7 AS days,
    cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0) AS net
  FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`
  WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  UNION ALL
  SELECT 30, cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)
  FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`
  WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  UNION ALL
  SELECT 90, cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)
  FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`
  WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
)
GROUP BY days
ORDER BY days;
```

```sql
-- 4) Top services last 30 days
SELECT
  service.description AS service,
  ROUND(SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS net_cost_usd
FROM `optimal-disk-472305-e2.billing_export.gcp_billing_export_v1_015AB8_391105_7ECE90`
WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY 1
ORDER BY net_cost_usd DESC
LIMIT 10;
```

If 90-day query returns sparse history, report **PARTIAL / NOT AVAILABLE** — never extrapolate. Multi-region US typically backfills **current + previous month** only.

---

## 9. Next recommended action

1. Wait for Google to create `gcp_billing_export_v1_015AB8_391105_7ECE90`.  
2. Re-run:  
   `FinOps Phase 2A Validation — table present; run real cost SQL`  
3. Until then, optional interim: Billing Console → **Reports** (manual $ view).  
4. **Do not** start Phase 2B cleanup until measured $ confirms drivers.

---

## 10. Safety boundaries

- Billing visibility ≠ cleanup authorization.  
- No Artifact Registry / Cloud Build / Cloud Run revision deletes in this phase.  
- No secrets in this document.
