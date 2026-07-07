# P19E-1 Deploy — Add Vehicle Text Field Collection Live Smoke

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Phone happy-path PENDING**

---

## Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `262bcbd` | docs: add P19E binary step model recon |
| `c252369` | feat: add Add Vehicle text field collection loop |

Pushed: `git push origin sprint/p16-trust-layer` (`361fc5e..c252369`)

---

## Pre-deploy checks

| Check | Result |
|-------|--------|
| Working tree clean | ✅ |
| pytest (236 tests incl. P19E-1) | **PASS** |
| `npm run build` | **PASS** |
| Pre-deploy QA gate | **PASS** |

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00159-6kz` |
| **Revision (this deploy)** | **`fiqa-api-00160-44g`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `c252369d9` |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `H5_TASK_TOKEN_SECRET` | Secret Manager `fiqa-h5-task-token-secret` — unchanged |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` — unchanged |
| VPC/NAT/callback | unchanged |

---

## Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` |
| Deployment | `https://ui-p3t5z3lmx-andys-projects-1f411b73.vercel.app` |
| **Alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/workbench/document-intake` | HTTP 200 |
| `/task/upload/:token` | HTTP 200 (route serves SPA) |
| H5 Phase 1 copy deployed | Bundle contains **「第 1 阶段完成」** |

---

## Post-deploy QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00160-44g`)

---

## Live phone smoke — Andy checklist (PENDING)

**Precondition:** Use non-sensitive test images only. Deploy revision `fiqa-api-00160-44g` + alias `ui-smoky-beta`.

### Step A — Restart new flow

Send WeCom: **`重新加车`**

| Expect | |
|--------|--|
| New Start Card | head includes **「好的，我们重新开始一组加车资料收集」** |
| Button | **开始上传照片** |
| Tail | no long URL |
| H5 | Step 1/3 VIN — **not** 3/3 complete |

### Step B — H5 Phase 1

Upload VIN + registration + insurance (or skip insurance).

| H5 final page expect | |
|---------------------|--|
| Headline | **第 1 阶段完成 ✅** |
| Sub | 照片上传已完成 |
| Progress | ① 上传照片 ✓ → ② 补充文字 → ③ 陈总确认 |
| CTA | 返回微信 |

### Step C — Stage Complete S1

After returning to WeChat (~10s):

```text
【第 1 阶段完成 ✅ · 照片资料】
…
【下一步 · 第 2 步：补充文字信息】
```

Must **not** say: 加车完成 / 全部资料已收齐 / OCR language.

### Step D — Phase 2 combined text

Reply:

```text
7月10号提车，ZIP 92705，电话 949-123-4567
```

| Expect | |
|--------|--|
| Extract | delivery_date + zip + phone |
| Reply | **Stage Complete S2** |
| S2 contains | **第 2 阶段完成 ✅ · 文字信息** |
| S2 contains | **第 3 步：陈总人工确认** |
| Safe copy | 资料已基本收齐 — not 全部资料已收齐 |

### Step E — Workbench verify

Open: https://ui-smoky-beta.vercel.app/workbench/document-intake

| Field | Expect |
|-------|--------|
| Attachments | VIN / registration / insurance visible |
| `collected_fields` | includes `delivery_date`, `zip`, `phone` |
| `known_facts` | values present if populated |
| `guided_workflow_state` | `ready_for_broker_review` |
| `add_vehicle_phase` | `phase_3_broker_review` |
| Phase 2 `still_needed` | empty for the trio |
| OCR | not_started |
| Public GCS URL | none in UI |

**Reply when done:** `P19E-1 smoke done` + insurance path (3 uploads vs skip).

---

## Optional partial-field smoke

1. Reply only: `ZIP 92705` → Current Step Card with ✓ ZIP, ○ date, ○ phone  
2. Reply: `7月10号提车，电话 949-123-4567` → S2 (no duplicate on repeat)

---

## Server-side status at deploy time

| Signal | Result |
|--------|--------|
| Cloud Run logs (post-deploy) | No `wecom_phase2_text_ingest_v1` yet — phone smoke not run |
| API add_car cases with `guided_workflow_state` | 0 (pre-smoke) |

---

## Regression checks (post-smoke)

| Check | Expected |
|-------|----------|
| `我要加车` after Phase 1 | S1 / Phase 2 prompt — not new H5 |
| `重新加车` | new H5 flow |
| Premium / Claim / Coverage | unchanged |
| Duplicate S2 on repeat message | deduped |

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM / vision | ❌ |
| Schema migration | ❌ |
| Cloud callback / VPC / NAT / Secret change | ❌ |
| Public GCS / public URL in chat | ❌ |
| Neon as QA truth | ❌ |
| Full external_userid in this doc | ❌ |
| Token / access token / image binary in this doc | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Push + backend deploy | **GO** |
| Frontend deploy (H5 copy) | **GO** |
| Post-deploy QA gate | **GO** |
| Andy phone happy-path smoke | **PENDING** |
| Next loop (broker confirm / OCR) | **HOLD** until phone smoke PASS |

**STOP** — awaiting Andy phone smoke on `fiqa-api-00160-44g` + `ui-smoky-beta`.
