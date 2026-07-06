# Loop 3B Stable Checkpoint

**Date:** 2026-07-05  
**Purpose:** Save stable state after Coverage Risk live WeCom smoke PASS. Documentation only at tag time.

---

## Git

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| HEAD (tag) | `ccf20b0` — `feat: add WeCom coverage risk minimal lane` |
| Tag | `loop-3b-stable-2026-07-05` |
| Prior stable | `loop-2f-stable-2026-07-05` → `fd2cdbe` |

### Loop 3 checkpoint commits

| Commit | Message |
|--------|---------|
| `ccf20b0` | feat: add WeCom coverage risk minimal lane |

---

## Live environment

| Role | Value |
|------|-------|
| **Backend** | Cloud Run `fiqa-api-00147-hjc` |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **GIT_SHA** | `ccf20b07c` |
| **Frontend** | https://ui-smoky-beta.vercel.app |
| **DB** | GCP Cloud SQL `caseiq` @ `10.73.0.3` (private VPC) |
| **DB secret** | `fiqa-service-record-database-url-cloudsql-private` |
| **Neon** | Legacy only — **not** QA truth |

---

## Workbench demo state (post Loop 3B live smoke)

| Metric | Value |
|--------|-------|
| API `total_count` | 14 (includes archived rows) |
| **UI visible rows** | **8** = 5 seed + 2 Loop 2 live + 1 coverage live |
| Seed customers | 张先生, 王女士, 李先生, 陈女士, 赵先生 |
| Loop 2 live | `case_2a1e00dc3b75` (Premium), `case_16c897a66fe1` (Claim) |
| Loop 3 live | `case_079c09b5f27a` (Coverage Risk) |
| Archived smoke | 6 rows hidden via `workbench_archived` |

---

## Verified flows (Loop 3B)

| Flow | Result |
|------|-------|
| Coverage Risk live WeCom | PASS — `coverage_risk` case + conservative reply |
| Live msg_id | `AvNtWunCeqi2noBYsiC1wdSgZN` |
| Generic hello | No Draft — guided menu (Loop 2D/2F regression) |
| Premium Review | Live + simulated PASS |
| Claim Lite | Live + simulated PASS |
| Add Vehicle | Start Card only before click |
| Customer display | `WeCom · …mxcw` (pre–Loop 3D polish) |
| QA gate | PASS — `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` |
| WeCom regression tests | 82 passed |

---

## Remaining gaps (known)

1. **API `total_count` includes archived rows** — UI filters archived.
2. **WeCom customer label** — technical placeholder `WeCom · …suffix` → Loop 3D polish.
3. **WeCom image / OCR** — not implemented.
4. **Queue mode OFF** — sync callback path primary.

---

## Recovery commands

```bash
# QA gate
bash scripts/check_chen_kui_demo_environment.sh --cloud-api

# Reseed demo (QA Cloud SQL)
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa

# Checkout this checkpoint
git checkout loop-3b-stable-2026-07-05
```

---

## Authority

- Runbook: `docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md`
- Loop 2 stable: `docs/evidence/loop_0_to_2f_stable_checkpoint_2026_07_05.md`
