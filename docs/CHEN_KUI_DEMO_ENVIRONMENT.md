# Chen Kui Demo Environment — QA Source of Truth (Loop 1C)

**Purpose:** Canonical map of URLs, databases, and commands for Chen Kui broker demo.  
**Authority:** P18.11 Cloud-first QA. This doc supersedes stale Neon references in older runbooks.

---

## One-line truth

> **QA demo = Vercel QA UI + Cloud Run `fiqa-api` + GCP Cloud SQL `caseiq` on `caseiq-pilot-pg`.**  
> **Seed with `--target qa`. Neon is legacy — not QA truth.**

---

## Primary URLs

| Role | URL |
|------|-----|
| **Demo Workbench (primary)** | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| **Customer add-car entry** | https://ui-smoky-beta.vercel.app/add-car |
| **API backend** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **API health** | https://fiqa-api-g7zatxrycq-uw.a.run.app/readyz |
| **WeCom callback** | https://fiqa-api-g7zatxrycq-uw.a.run.app/api/wecom/kf/callback |

Vercel QA UI uses build-time `VITE_API_BASE_URL` → Cloud Run. No local JSON or mock data in QA builds.

---

## QA source of truth database

| Attribute | Value |
|-----------|-------|
| **Primary QA DB** | **GCP Cloud SQL** — database `caseiq`, instance `caseiq-pilot-pg` |
| **Cloud Run secret** | `fiqa-service-record-database-url-cloudsql-private` (VPC private host `10.73.0.3`) |
| **Laptop seed path** | Same secret, host rewritten to instance public IP (`34.169.226.245`) when authorized network allows |
| **Legacy (NOT QA)** | Neon `neondb` via `.env.cloudrun` / secret `fiqa-service-record-database-url` |

**Why Cloud SQL:** P18.11 Cloud-first QA. Cloud Run already reads Cloud SQL. Seeding Neon caused Loop 1B mismatch (`total_count=0` on API while Neon had 5 demo rows).

---

## Environment chain (actual)

```
Operator laptop
  seed_chen_kui_demo.py --target qa
       ↓ (public IP, authorized network)
GCP Cloud SQL caseiq  ←── Cloud Run fiqa-api (private VPC)
       ↑
Vercel QA UI ──HTTP──→ Cloud Run /api/inbox/cases
WeCom KF callback ──→ same Cloud Run fiqa-api
```

---

## Commands

### Seed (QA — required for demo)

```bash
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa --dry-run
```

`--target cloud` is a deprecated alias that now maps to `qa` (GCP Cloud SQL), **not** Neon.

### Reset (demo-tagged only)

```bash
bash scripts/reset_chen_kui_demo.sh --qa
bash scripts/reset_chen_kui_demo.sh --qa --reseed
```

Safety: only `demo_name=chen_kui_p18` + `workbench_test=true`. No truncate, no `sync_cursor` reset.

### Environment gate (run before demo / Loop 2)

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

### Local dev (NOT acceptance)

```bash
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target local
bash scripts/run_demo_local.sh
```

---

## Demo cases (after QA seed)

| Customer | Type |
|----------|------|
| 张先生 | VIP Premium Review |
| 王女士 | Claim Lite |
| 李先生 | Add Vehicle Draft |
| 陈女士 | Add Vehicle Ready |
| 赵先生 | Coverage Risk |

Filter Workbench by **测试** tag or search customer name.

---

## What is NOT source of truth

| Layer | Status |
|-------|--------|
| `data/unified_intake_cases.json` | Dev-only |
| Neon founder DB (`.env.cloudrun`) | Legacy; may have stale demo rows |
| `localhost:5173` / `:8001` | Engineering recovery only |
| Vercel env without Cloud Run API | N/A — QA UI always calls Cloud Run |

---

## WeCom live path (unchanged — Q0.11.1)

1. WeCom KF → Cloud Run `/api/wecom/kf/callback` (`fiqa-api`, `us-west1`)
2. Same Cloud SQL as Workbench QA
3. Drain: `PYTHONPATH=. python3 scripts/wecom_drain_queues.py` (with QA DB env)
4. **Do not** reset `sync_cursor` for demo rehearsal

---

## Avoiding local / Neon / GCP confusion

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Seed to Neon (`legacy-neon` or old `.env.cloudrun` only) | API `total_count=0`, Neon has 5 rows | `seed --target qa` |
| Accept local JSON seed as demo-ready | Vercel queue empty | Seed QA + run check script |
| Change Cloud Run to Neon | Violates P18.11; risks prod/QA drift | Keep Cloud Run on Cloud SQL |
| Edit local `.env` expecting Cloud Run change | No effect on QA | Change Secret Manager + redeploy (operator) |

### Proposed Cloud Run change (NOT executed in Loop 1C)

Pointing Cloud Run back to Neon is **not recommended**. If ever needed for emergency:

```bash
# RISK: violates P18.11; splits WeCom/QA from Cloud SQL truth
# gcloud run services update fiqa-api --region=us-west1 \
#   --update-secrets=SERVICE_RECORD_DATABASE_URL=fiqa-service-record-database-url:latest
```

Prefer seeding Cloud SQL instead.

---

## Required env / secrets (masked)

| Surface | Secret / var | Provider |
|---------|--------------|----------|
| Cloud Run | `fiqa-service-record-database-url-cloudsql-private` | host=10.73.0.3 db=caseiq |
| Legacy laptop | `.env.cloudrun` `SERVICE_RECORD_DATABASE_URL` | host=*.neon.tech db=neondb |
| Vercel build | `VITE_API_BASE_URL` | Cloud Run URL |
| API auth | `UNIFIED_INTAKE_INTAKE_API_KEY` | Vercel + operator laptop |

---

## Fallback strategy

| Failure | Action |
|---------|--------|
| Check script FAIL | Re-seed `--target qa`; verify gcloud auth + SQL authorized network |
| Vercel down | Pre-recorded clip (Loop 4) |
| Cloud Run 503 | `bash scripts/restore_8001_readiness.sh` for coding only |
| WeCom live fails | Path A seed cases on QA Workbench |

---

*Loop 1C — QA alignment. Loop 2 blocked until `check_chen_kui_demo_environment.sh --cloud-api` PASS.*
