# Loop 0–2F Stable Checkpoint

**Date:** 2026-07-05  
**Purpose:** Save stable state before Loop 3. No feature work in this checkpoint — documentation only.

---

## Git

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| HEAD | `c33e46d` — `docs: add Chen Kui P18/Q0 demo evidence and runbooks` |
| Tag (recommended) | `loop-2f-stable-2026-07-05` |

### Loop 2E/2F checkpoint commits

| Commit | Message |
|--------|---------|
| `020cdbd` | chore: lock QA demo environment to Cloud SQL |
| `4d72b9d` | feat: add WeCom premium and claim minimal lanes |
| `c9e6cd1` | feat: Chen Kui workbench demo hygiene and screen-proof |
| `c33e46d` | docs: add Chen Kui P18/Q0 demo evidence and runbooks |

---

## Live environment

| Role | Value |
|------|-------|
| **Backend** | Cloud Run `fiqa-api-00146-sgl` |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Frontend** | https://ui-smoky-beta.vercel.app |
| **DB** | GCP Cloud SQL `caseiq` @ `10.73.0.3` (private VPC) |
| **DB secret** | `fiqa-service-record-database-url-cloudsql-private` |
| **Neon** | Legacy only — **not** QA truth |

---

## Workbench demo state

| Metric | Value |
|--------|-------|
| API `total_count` | 13 (includes archived rows) |
| **UI visible rows** | **7** = 5 seed + 2 live WeCom smoke |
| Seed customers | 张先生, 王女士, 李先生, 陈女士, 赵先生 |
| Live smoke (visible) | `case_2a1e00dc3b75` (Premium), `case_16c897a66fe1` (Claim) |
| Archived smoke | 4 Loop 2B/2C simulated rows hidden via `workbench_archived` |

---

## Verified flows (Loop 2D / 2F)

| Flow | Result |
|------|--------|
| Generic hello | No Draft — guided menu only |
| Premium Review | Live WeCom path PASS — `policy_review` case, customer label + tags |
| Claim Lite | Live WeCom path PASS — `claim_lite` case, customer label + tags |
| Add Vehicle | Start Card only before click — no Draft regression |
| Customer display | Live cases show `WeCom · …mxcw` (not "—") |
| QA gate | PASS — `bash scripts/check_chen_kui_demo_environment.sh --cloud-api` |
| WeCom regression tests | 65 passed |

---

## Remaining gaps (known — not blockers for Loop 3 start)

1. **API `total_count` includes archived rows** — UI filters archived; API list does not yet exclude them.
2. **Coverage Risk / Suspended Coverage** — seed case (赵先生) exists; **WeCom minimal lane not implemented**.
3. **WeCom image / OCR** — not implemented; images stored as evidence only.
4. **Queue mode OFF / sync callback path** — Q0 queue infrastructure shipped; production uses sync callback path; queue mode not primary.

---

## Recommended next loop

**Loop 3: Coverage Risk / Suspended Coverage minimal lane**

- Mirror Premium/Claim minimal-lane pattern for coverage-risk intent.
- No schema migration unless explicitly approved.
- Preserve Add Vehicle Start Card and existing live paths.

---

## Recovery commands

```bash
# QA gate
bash scripts/check_chen_kui_demo_environment.sh --cloud-api

# Reseed demo (QA Cloud SQL)
PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa

# Hide smoke duplicates (dry-run default)
PYTHONPATH=. python3 scripts/cleanup_chen_kui_smoke_cases.py --target qa --dry-run

# Checkout this checkpoint
git checkout loop-2f-stable-2026-07-05
```

---

## Authority

- Runbook: `docs/runbooks/CHEN_KUI_DEMO_ENVIRONMENT.md`
- Environment: `docs/CHEN_KUI_DEMO_ENVIRONMENT.md`
- Loop evidence: `docs/evidence/wecom_q0_*.md`
