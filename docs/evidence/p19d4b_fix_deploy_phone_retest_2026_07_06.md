# P19D-4B Fix Deploy — Phone Retest Ready

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Fix commit:** `54933ca` — fix: polish WeCom H5 photo flow completion UX  
**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Phone retest READY**

---

## Deployed commits (pushed)

| Commit | Message |
|--------|---------|
| `54933ca` | fix: polish WeCom H5 photo flow completion UX |
| (prior) `c57afbd` | feat: add WeCom completion card for H5 photo flow |

Pushed: `git push origin sprint/p16-trust-layer` (`3b72115..54933ca`)

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00157-zvt`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `54933ca42` |
| `/health/live` | 200 |
| `/readyz` | 200 |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` — unchanged |

---

## Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` |
| Deployment | `https://ui-cvt732mww-andys-projects-1f411b73.vercel.app` |
| **Alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/workbench/document-intake` | HTTP 200 |
| H5 completed-state copy | Deployed (「此照片上传流程已完成」) |

---

## Post-deploy QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00157-zvt`)

---

## What changed in this deploy

1. **Start Card** — no long URL in tail; `如果按钮打不开，请回复：链接`
2. **Completed photo flow** — tapping「加车」on completed case → follow-up text (End Card copy), not new H5 link
3. **End Card backfill** — follow-up path calls `try_send_h5_photo_flow_end_card()` if never sent
4. **Restart** — reply `重新加车` to start fresh draft + new H5 flow
5. **H5** — completed page says flow already done + restart hint

Prior investigation: `docs/evidence/p19d4b_fix_start_card_end_card_live_debug_2026_07_06.md`

---

## Andy phone retest — Scenario A (completed case follow-up)

**Precondition:** Your WeCom user already has an add_car case with photo flow complete (e.g. prior `case_5e2da3c42e43`).

| Step | Action | Expected |
|------|--------|----------|
| A1 | Send `你好` | Short Chinese greeting menu |
| A2 | Tap `【加车资料补充】` or send `我要加车` | **Follow-up text message** (not H5 Start Card with button) |
| A3 | Read message | `【加车资料】照片已收到 ✅` + checklist + 提车日期/ZIP/电话 + 陈总人工确认 |
| A4 | Start Card tail | **No long URL** visible |
| A5 | Do NOT expect new H5 upload steps | You should not land on「开始上传照片」for same completed flow |

Reply: `4B-A done` if pass.

---

## Andy phone retest — Scenario B (重新加车 new flow + End Card)

| Step | Action | Expected |
|------|--------|----------|
| B1 | Send `重新加车` | New Start Card with **开始上传照片** button (no URL in tail) |
| B2 | Tap button → H5 | Step 1/3 VIN (not 3/3 complete) |
| B3 | Upload VIN + registration + insurance (or skip insurance) | Progress advances each step |
| B4 | H5 final page | 「此照片上传流程已完成」+ 返回微信 + 确认消息提示 + 已提交 fallback |
| B5 | Tap **返回微信** | Within ~10s: End Card in chat |
| B6 | End Card content | Checklist + 还差 3 项文字字段 + 不会自动修改保单 |
| B7 | Refresh H5 final page | **No duplicate** End Card |

Use non-sensitive test images only.

Reply: `4B-B done` with path (3 uploads vs skip insurance).

---

## Guardrails

| Item | Status |
|------|--------|
| OCR | ❌ |
| Schema migration | ❌ |
| Cloud callback/VPC/NAT change | ❌ |
| Neon QA truth | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Deploy + QA | **GO** |
| Andy phone A + B | **PENDING** |

**STOP** — awaiting Andy phone retest results.
