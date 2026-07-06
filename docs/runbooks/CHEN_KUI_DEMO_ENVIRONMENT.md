# Chen Kui Demo Environment — Loop 1B/1C Alignment

**Canonical doc:** [`docs/CHEN_KUI_DEMO_ENVIRONMENT.md`](../CHEN_KUI_DEMO_ENVIRONMENT.md) (Loop 1C QA source of truth).

**Purpose:** Single source for *which URL* to use for Chen Kui broker demo.  
**Not** a feature spec — see `docs/p18_5_chen_kui_demo_experience_plan.md`.

---

## Demo environment decision (authoritative)

| Role | URL | When |
|------|-----|------|
| **Primary demo** | https://ui-smoky-beta.vercel.app/workbench/unified-intake | Broker rehearsal, Chen Kui screen-proof |
| **Customer entry (WeCom path)** | https://ui-smoky-beta.vercel.app/add-car | Add Vehicle live / customer-facing |
| **API backend** | https://fiqa-api-g7zatxrycq-uw.a.run.app | Vercel `VITE_API_BASE_URL` (baked at build) |
| **Dev fallback only** | http://localhost:5173 + http://127.0.0.1:8001 | Engineering — **not** formal demo |

**Local is not the demo path.** `ERR_EMPTY_RESPONSE` on localhost:5173 means the Vite dev server is not running — start with `bash scripts/run_demo_local.sh` or use Vercel QA instead.

---

## Data paths

```
Loop 1 seed (local)  → data/unified_intake_cases.json     (dev only)
Loop 1C seed (QA)    → GCP Cloud SQL caseiq               (QA truth — same as Cloud Run)
Legacy Neon          → neondb via .env.cloudrun             (NOT QA truth)
Cloud Run API        → Cloud SQL via Secret Manager
Vercel Workbench     → GET Cloud Run /api/inbox/cases
WeCom live           → Cloud Run callback → inbox/outbox → case rows (Q0.11.1)
```

See full detail: `docs/CHEN_KUI_DEMO_ENVIRONMENT.md`.

---

## Cloud-safe seed / reset

**Seed (QA/GCP Cloud SQL):**

```bash
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa --dry-run
```

**Reset (demo-tagged only):**

```bash
bash scripts/reset_chen_kui_demo.sh --qa
bash scripts/reset_chen_kui_demo.sh --qa --reseed
```

**Safety guarantees:**

- Only rows with `extra.demo_name = chen_kui_p18` AND `extra.workbench_test = true`
- No `TRUNCATE`, no full-table delete
- No `sync_cursor` / WeCom queue reset
- Fail closed if `--target qa` and gcloud secret / network unavailable

**Local seed (dev):**

```bash
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py              # default --target local
bash scripts/reset_chen_kui_demo.sh --reseed
```

---

## Environment check

```bash
bash scripts/check_chen_kui_demo_environment.sh
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

---

## Demo cases (after seed)

| Customer | Type | Tags |
|----------|------|------|
| 张先生 | VIP Premium Review | VIP, Uber Black, Manual Handle |
| 王女士 | Claim Lite | Urgent, Manual Handle |
| 李先生 | Add Vehicle Draft | Draft, missing ZIP |
| 陈女士 | Add Vehicle Ready | Confirm button |
| 赵先生 | Coverage Risk | Risk flags |

Filter Workbench queue by **测试** tag or search customer name.

---

## Two demo paths

### Path A — Seed-backed Workbench (Loop 1 screen-proof)

1. `seed_chen_kui_demo.py --target qa`
2. Open https://ui-smoky-beta.vercel.app/workbench/unified-intake
3. Open each of the 5 cases → Case Workspace panel visible

### Path B — WeCom live (Q0.11.1, unchanged)

1. Customer messages via WeCom KF
2. Cloud Run `/api/wecom/kf/callback` enqueues → drain with `scripts/wecom_drain_queues.py`
3. Add Vehicle text/click path creates/updates cases
4. Workbench shows live case (may coexist with seed cases; seed rows are `workbench_test`)

**Do not** reset production `sync_cursor` for demo rehearsal.

---

## Known alignment risks

1. **Cloud Run DB vs Neon** — If API `total_count=0` but Neon shows demo rows, seed targeted wrong DB. Fix: `seed --target qa` to Cloud SQL (do NOT point Cloud Run to Neon). See Loop 1C report.
2. **Office ownership** — If `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP=1`, list may require matching `X-Org-Id`. Seed cases use `client_id=chen_kui`; legacy unstamped rows remain visible when enforcement is off.
3. **Vercel API key** — Browser calls need `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` at build time for authenticated intake routes.

---

## Fallback strategy

| Failure | Fallback |
|---------|----------|
| Vercel down | Pre-recorded Workbench clip (Loop 4) |
| Cloud Run 503 | `bash scripts/restore_8001_readiness.sh` + local dev **for engineering only** |
| Live WeCom fails | Path A seed cases on QA Workbench |
| Empty queue after seed | Run `check_chen_kui_demo_environment.sh --cloud-api`; verify DB alignment |

---

*Loop 1B — environment alignment only. Loop 2 (Premium/Claim live lanes) starts only after GO.*
