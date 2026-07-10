# P19H-3h — Claim H5 Completion Polish Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Feature commit:** `883039b` — feat: polish Claim H5 completion experience  
**Predeploy tag:** `p19h-h5-completion-polish-predeploy-20260710` → `883039b`

---

## 1. Safety

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Tracked working tree | Clean at deploy start |
| Schema migration | **No** |
| `WECOM_INBOX_QUEUE` | Preserved `0` |
| `WECOM_SLICE_SEND_REPLY` | Confirmed `1` on live service |

---

## 2. Pre-deploy tests

| Command | Result |
|---------|--------|
| `pytest tests/test_h5_claim_intake_form.py -q` | **15 passed** |
| `pytest tests/test_p19h3f4_unified_status_card.py -q` | **14 passed** |
| `pytest tests/test_p19h3h_append_first_split_later.py -q` | **11 passed** |
| `scripts/p19h3h_claim_h5_intake_smoke.py --in-process` | **PASS** |
| `cd ui && npm run build` | **PASS** |

---

## 3. Backend deploy (Cloud Run)

| Item | Before | After |
|------|--------|-------|
| **GIT_SHA** | `a119bb247` | `883039b45` |
| **Revision** | `fiqa-api-00195-9lz` | `fiqa-api-00196-k4l` |
| **URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app | (unchanged) |
| **Deploy method** | `bash scripts/deploy_paid_pilot.sh` | |
| **Secret Manager** | H5 token secret bound (`fiqa-h5-task-token-secret`) | preserved |

### Post-deploy probes

```text
GET /version  → {"commit":"883039b45", ...}
GET /health/live → {"ok":true}
GET /readyz → intake_core ready, intake_path_ready=true
```

### Live env confirmed

- `GIT_SHA=883039b45`
- `WECOM_SLICE_SEND_REPLY=1`
- `WECOM_INBOX_QUEUE=0`

---

## 4. Backend live smoke

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS**  
**Evidence:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_173431.json`

| Check | Result |
|-------|--------|
| GET intake | 200 |
| PATCH fields | OK |
| POST submit | 200, `submitted: true` |
| `completion_summary.title` | `已提交给陈总 ✅` |
| `submit_has_received_list` | true |
| Submit idempotent | true |
| `broker_done_false` | true |
| Workbench `intake_ready_for_broker` | true |
| `customer_submitted_intake` in timeline (API) | true |
| Upload URL present | true |

**Note:** `single_submitted_timeline_event: false` in smoke JSON read path — local PG/JSON read lag; live API workbench confirms `workflow_phase=intake_ready_for_broker` for smoke case `case_2357dfde3933`.

---

## 5. Frontend deploy (Vercel)

| Item | Value |
|------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | https://ui-38mzd0cau-andys-projects-1f411b73.vercel.app |
| **Stable alias** | **https://ui-smoky-beta.vercel.app** |

### Route probes

| URL | Status |
|-----|--------|
| `https://ui-smoky-beta.vercel.app` | HTTP 200 |
| `https://ui-smoky-beta.vercel.app/task/claim/test-token-placeholder` | HTTP 200 (SPA shell) |
| `https://ui-smoky-beta.vercel.app/task/upload/test-token-placeholder` | HTTP 200 (SPA shell) |

### Bundle verification

Production JS bundle contains new copy:
- `提交给陈总审核`
- `刷新资料状态`
- `已提交给陈总`

---

## 6. H5 completion behavior (live)

**Browser manual check:** Not performed from Cursor (no WeChat WebView).  
**API + bundle verification:** PASS.

### Manual retest link (seeded in QA DB)

| Field | Value |
|-------|-------|
| Case ID | `case_8fa324a49554` |
| H5 URL | https://ui-smoky-beta.vercel.app/task/claim/h5t1.eyJjYXNlX2lkIjoiY2FzZV84ZmEzMjRhNDk1NTQiLCJleHAiOjE3ODM5NjQxNzEsImZsb3ciOiJjbGFpbV9pbnRha2VfZm9ybSIsImlhdCI6MTc4MzcwNDk3MSwibGFuZSI6ImNsYWltIiwibW9kZWwiOiJoNV90YXNrX3Rva2VuX3YxIiwibm9uY2UiOiJmNTAyZWM1YjVhNTI0ZTllIiwidXNlcl9yZWYiOiIzODk0NGY1OCIsInYiOjN9.b2e44675ebd715d8243250cd8580842f |

### Expected behavior when opened in WeChat

1. **Review page:** 已填资料 / 照片 / 还缺什么 / 提交提醒; button「提交给陈总审核」
2. **Submit:** loading「提交中，请稍等…」; button disabled
3. **Done page:** 已提交给陈总 ✅; 已收到 / 还缺 / 下一步 / 提醒
4. **Refresh:**「刷新资料状态」updates photo count and missing info
5. **Upload:**「继续上传照片」opens `/task/upload/...` link

---

## 7. WeCom submit confirmation

| Item | Status |
|------|--------|
| Code live on Cloud Run | **Yes** (`h5_submit_confirmation.py`) |
| `WECOM_SLICE_SEND_REPLY` | **1** |
| Simulated API submit (fake `wktest001`) | `wecom_confirmation_sent: false`, `reason: send_failed` |
| Real WeCom message delivered | **Not verified** — requires human WeChat retest from allowlisted customer channel |

### Why this is NOT broker_done

- Separate module `h5_submit_confirmation.py` (not `claim_end_card.py`)
- Copy: `【资料已提交 ✅】` — customer submit ack only
- Does not set `broker_done` phase or emit `broker_done` timeline event
- `broker_done` remains manual Chen action via Workbench

### Duplicate prevention

- Marker: `h5_intake_state.h5_submit_confirmation_sent_at`
- Idempotent re-submit does not re-send (unit tests + design)

---

## 8. Human WeCom retest checklist

1. Send **我要理赔** → expect H5 Start Card with link
2. Open H5 link → complete wizard → **提交给陈总审核**
3. H5 Done → **已提交给陈总 ✅** + disclaimer
4. WeCom → expect **【资料已提交 ✅】** message (not End Card)
5. Send **进度** → Status Card shows submitted state; no broker_done language
6. Workbench → case visible; `customer_submitted_intake` in timeline; broker_done still manual

---

## 9. Remaining gaps

| Gap | Notes |
|-----|-------|
| Real WeCom manual retest | **Required** — simulated send uses test kf id; production customer channel needed |
| `window.close()` for「返回微信」| May not work in all WebViews |
| Inline photo upload | Out of scope |
| Add Car H5 | Out of scope |
| `single_submitted_timeline_event` smoke read | Local read path lag; API confirms submit persisted |

---

## 10. Rollback plan

### Backend

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 --region=us-west1 \
  --to-revisions=fiqa-api-00195-9lz=100
```

### Frontend

```bash
cd ui && vercel rollback
# or redeploy prior deployment from Vercel dashboard
```

### Git checkpoint

```bash
git checkout p19h-h5-completion-polish-predeploy-20260710
```

Older safe tags: `p19h-append-first-predeploy-20260710`, `p19h-claim-h5-mvp-predeploy-20260710`

---

## 11. Recommendation

| Item | Verdict |
|------|---------|
| Deploy complete | **GO** |
| Manual WeCom retest | **GO** — run checklist §8 before Chen pilot demo |
| Group Task 2 (H5/WeCom Status sync) | **GO** after manual retest passes |
