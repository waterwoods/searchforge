# P19H-3i — Claim Task Dashboard / Always-return H5 Entry Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Feature commit:** `7ac5362` — feat: add Claim task dashboard and always-return H5 entry  
**Deploy commit:** `e61e12e` — docs: evaluate Claim workflow readiness and next group tasks  
**Predeploy tag:** `p19h-claim-task-dashboard-predeploy-20260710` → `e61e12e`

---

## 1. Safety

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Starting commit | `e61e12e` (contains `7ac5362`) |
| Tracked working tree at deploy | **Clean** |
| Schema migration | **No** |
| Auth/login changed | **No** |

---

## 2. Pre-deploy tests

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p19h3f4_unified_status_card.py \
  tests/test_h5_claim_intake_form.py \
  tests/test_p19h3h_append_first_split_later.py \
  tests/test_p19h3f3_claim_collision_resolver.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19e1_phase2_routing_fix.py \
  tests/test_p19h3f5_single_active_task_per_lane.py \
  -q
# 103 passed

cd ui && npm run build
# ✓ built
```

**Result:** All **PASS**

---

## 3. Pre-deploy live state

| Probe | Before |
|-------|--------|
| `GET /version` | `fdba4b7fc` |
| Cloud Run revision | `fiqa-api-00198-5sj` |
| `GET /health/live` | `{"ok":true}` |
| `GET /readyz` | `intake_core_readiness: true`, `intake_path_ready: true` |
| `https://ui-smoky-beta.vercel.app` | HTTP 200 |

---

## 4. Backend deploy (Cloud Run)

| Item | Before | After |
|------|--------|-------|
| **GIT_SHA** | `fdba4b7fc` | `e61e12e28` |
| **Revision** | `fiqa-api-00198-5sj` | `fiqa-api-00199-5c9` |
| **URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app | (unchanged) |
| **Deploy command** | `bash scripts/deploy_paid_pilot.sh` | |

### Post-deploy probes

```text
GET /version     → {"commit":"e61e12e28", ...}
GET /health/live → {"ok":true}
GET /readyz      → intake_core_readiness: true, intake_path_ready: true
```

### Env vars (unchanged)

| Variable | Value |
|----------|-------|
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_INBOX_QUEUE` | `0` |
| `H5_TASK_TOKEN_SECRET` | via Secret Manager (smoke mint OK) |

---

## 5. Backend live smoke

### H5 intake smoke

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app --use-qa-db
```

**Result:** **PASS**  
Evidence: `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_223843.json`

### Dashboard / always-return smoke

```bash
PYTHONPATH=. python3 scripts/p19h3i_claim_task_dashboard_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app --use-qa-db
```

**Result:** **PASS**  
Evidence: `docs/evidence/p19h3i_claim_task_dashboard_smoke_3i_smoke_224257.json`

Verified live:

- `dashboard_summary` on GET `/api/h5/tasks/{token}/intake`
- Pre/post submit dashboard states
- WeCom status commands (进度/补资料/链接/事故资料/继续填写/上传照片) → **继续补充事故资料** + H5 link
- Supplement ack with H5 link + customer text note
- Explicit Add Car intent preserved
- Workbench timeline shows supplement text

---

## 6. Frontend deploy (Vercel)

| Item | Value |
|------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | https://ui-2vartsx2r-andys-projects-1f411b73.vercel.app |
| **Stable alias** | **https://ui-smoky-beta.vercel.app** |

### Route checks

| URL | Status |
|-----|--------|
| `https://ui-smoky-beta.vercel.app` | HTTP 200 |
| `https://ui-smoky-beta.vercel.app/task/claim/test-token-placeholder` | HTTP 200 |
| `https://ui-smoky-beta.vercel.app/task/upload/test-token-placeholder` | HTTP 200 |

### Bundle verification (`assets/index-CMCFIgyh.js`)

Found in production bundle:

- 我的事故资料
- 已收到
- 还缺
- 下一步
- 这只是资料收集，不代表已经正式向保险公司报案

Submitted-state copy (资料已提交给陈总审核 / 继续补充…) is **API-driven** via `dashboard_summary` — verified in live smoke, not hardcoded in bundle.

---

## 7. Manual checklist

Path: `docs/evidence/p19h3i_claim_task_dashboard_manual_checklist_2026_07_10.md`

Requires real WeCom account for photo ack and end-to-end UX confirmation.

---

## 8. Remaining gaps

- Photo ack inline H5 URL (today: reply directs to 进度/链接)
- Workbench `known_fact_provenance` label suffix on QA read path (timeline raw text verified in smoke)
- Full Workbench provenance UI later
- Add Car dashboard later
- Mini-program not needed now

---

## 9. Rollback plan

### Backend

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 --region=us-west1 \
  --to-revisions=fiqa-api-00198-5sj=100
```

### Frontend

```bash
cd ui && vercel rollback
```

### Git

```bash
git checkout p19h-claim-task-dashboard-predeploy-20260710
```

Older safe tags: `p19h-claim-supplement-routing-predeploy-20260710`, `p19h-wecom-card-h5-submit-clarity-predeploy-20260710`

---

## 10. Recommendation

**GO** for manual WeCom retest using checklist §7.  
**GO** for next group task after manual A–H pass (Pilot Readiness / Demo cleanup / Workbench polish).
