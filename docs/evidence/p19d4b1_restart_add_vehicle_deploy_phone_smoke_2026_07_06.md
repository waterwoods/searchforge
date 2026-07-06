# P19D-4B.1 Deploy — Restart Add Vehicle Phone Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Fix commit:** `99a1531` — fix: start new add vehicle flow on restart intent  
**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Phone Scenario B PENDING**

---

## Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `99a1531` | fix: start new add vehicle flow on restart intent |

Pushed: `git push origin sprint/p16-trust-layer` (`c0f396c..99a1531`)

Prior fix context: `docs/evidence/p19d4b1_restart_add_vehicle_new_flow_fix_2026_07_06.md`

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00157-zvt` (`54933ca`) |
| **Revision (this deploy)** | **`fiqa-api-00158-qnr`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `99a1531be` |
| `/health/live` | 200 |
| `/readyz` | 200 |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` — unchanged |

---

## Frontend deploy

| Field | Value |
|-------|-------|
| **Action** | **Skipped** — `99a1531` is backend-only (WeCom slice / case routing / Start Card copy) |
| **Alias still serving H5** | `https://ui-smoky-beta.vercel.app` (prior P19D-4B H5 completed-state copy) |
| Rationale | No `ui/` files in this commit; H5 Step 1 VIN page unchanged |

---

## Post-deploy QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00158-qnr`)

---

## What this deploy fixes

Scenario B from Andy phone retest after `54933ca`:

- **Before:** `重新加车` → old case「照片已收到」follow-up (no new flow)
- **After:** `重新加车` → new add_car draft + new H5 v2 token + Start Card from Step 1 VIN

Mechanism: bypass add-car draft merge for explicit restart; `create_or_attach_draft_case_for_start_click()` forces new case on restart phrases.

---

## Andy phone retest — Scenario B (重新加车 new flow)

**Precondition:** WeCom user already has a completed add_car photo flow on a prior case (same as prior Scenario A/B tests).

| Step | Action | Expected |
|------|--------|----------|
| B1 | Send `重新加车` | New Start Card — head includes **「好的，我们重新开始一组加车资料收集」** |
| B2 | Start Card button | **开始上传照片** (view button); tail **no long URL** — only「如果按钮打不开，请回复：链接」 |
| B3 | Tap button → H5 | **Step 1/3 VIN** (`vin_photo`) — **not** 3/3 complete |
| B4 | Upload VIN + registration + insurance (or skip insurance) | Progress advances each step |
| B5 | H5 final page | 「此照片上传流程已完成」+ 返回微信 |
| B6 | Return to WeChat | Within ~10s: **End Card** in chat |
| B7 | End Card content | Checklist + 还差 3 项文字字段 + 不会自动修改保单 |
| B8 | Refresh H5 final page | No duplicate End Card |

Use non-sensitive test images only.

Reply: **`4B.1-B done`** with path (3 uploads vs skip insurance).

---

## Regression sanity (optional)

| Check | Expected |
|-------|----------|
| Scenario A — `我要加车` on completed case | Follow-up text, **not** new Start Card |
| `你好` | Greeting menu unchanged |
| Premium / Claim lanes | Unaffected |

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM / vision extraction | ❌ |
| Schema migration | ❌ |
| Cloud callback / VPC / NAT / Secret change | ❌ |
| Public GCS / public URL in Start Card tail | ❌ |
| Neon as QA truth | ❌ |
| Full external_userid in this doc | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Push + backend deploy + QA | **GO** |
| Andy phone Scenario B | **PENDING** |

**STOP** — awaiting Andy phone retest on `fiqa-api-00158-qnr`.
