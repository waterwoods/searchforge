# P19H-3h — WeCom Card + H5 Submit Clarity Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Feature commit:** `4211cb2` — feat: polish WeCom cards and H5 submit clarity  
**Predeploy tag:** `p19h-wecom-card-h5-submit-clarity-predeploy-20260710` → `4211cb2`

---

## 1. Safety

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Tracked working tree | Clean at deploy start |
| Schema migration | **No** |
| `WECOM_INBOX_QUEUE` | Preserved `0` |
| `WECOM_SLICE_SEND_REPLY` | Confirmed `1` on live service |
| `H5_TASK_TOKEN_SECRET` | Bound from Secret Manager |

---

## 2. Pre-deploy tests

| Command | Result |
|---------|--------|
| `pytest tests/test_p19h3f4_unified_status_card.py -q` | **17 passed** |
| `pytest tests/test_h5_claim_intake_form.py -q` | **18 passed** |
| `pytest tests/test_p19h3h_append_first_split_later.py -q` | **11 passed** |
| `pytest tests/test_p19h3f3_claim_collision_resolver.py -q` | **11 passed** |
| `cd ui && npm run build` | **PASS** |

---

## 3. Backend deploy (Cloud Run)

| Item | Before | After |
|------|--------|-------|
| **GIT_SHA** | `883039b45` | `4211cb28c` |
| **Revision** | `fiqa-api-00196-k4l` | `fiqa-api-00197-2sg` |
| **URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app | (unchanged) |
| **Deploy method** | `bash scripts/deploy_paid_pilot.sh` | |

### Pre-deploy probes

```text
GET /version  → {"commit":"883039b45", ...}
GET /health/live → {"ok":true}
GET /readyz → intake_core ready, intake_path_ready=true
```

### Post-deploy probes

```text
GET /version  → {"commit":"4211cb28c", ...}
GET /health/live → {"ok":true}
GET /readyz → intake_core ready, intake_path_ready=true
```

### Live env confirmed

- `GIT_SHA=4211cb28c`
- `WECOM_SLICE_SEND_REPLY=1`
- `WECOM_INBOX_QUEUE=0`
- `H5_TASK_TOKEN_SECRET` from Secret Manager

---

## 4. Backend live smoke

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS**  
**Evidence:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_183331.json`

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
| Status open has H5 continue link | true |
| Status submitted no continue link | true |

### Card copy verification (in-process, same commit)

**Evidence:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_183353.json`

| Check | Result |
|-------|--------|
| `card_start_has_submit_instruction` | true |
| `card_start_has_h5_button` (`打开资料填写页面`) | true |
| `card_start_disclaimer_once` | true |
| `card_submit_confirmation_not_broker_done` | true |
| `card_submit_confirmation_has_title` (`【资料已提交 ✅】`) | true |
| `status_submitted_not_continuable` | true |
| `status_submitted_no_continue_when_url_omitted` | true |

**Note:** `single_submitted_timeline_event: false` in live HTTP smoke read path — known PG/JSON read lag; workbench API confirms `workflow_phase=intake_ready_for_broker`.

---

## 5. Frontend deploy (Vercel)

| Item | Value |
|------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | https://ui-rlpeabuxb-andys-projects-1f411b73.vercel.app |
| **Stable alias** | **https://ui-smoky-beta.vercel.app** |

### Route probes

| URL | Status |
|-----|--------|
| `https://ui-smoky-beta.vercel.app` | HTTP 200 |
| `https://ui-smoky-beta.vercel.app/task/claim/test-token-placeholder` | HTTP 200 (SPA shell) |
| `https://ui-smoky-beta.vercel.app/task/upload/test-token-placeholder` | HTTP 200 (SPA shell) |

### Bundle verification

Production JS bundle (`index-CyLcLZK3.js`) contains:

- `提交给陈总审核`
- `提交后，陈总会在工作台看到资料`
- `还没有提交，返回微信不会把资料交给陈总`
- `已提交给陈总`

---

## 6. Card behavior (deployed backend copy)

| Card | Deployed behavior |
|------|-------------------|
| **Start Card** | `【事故记录已开始 ✅】`; H5-first copy with「提交给陈总审核」instruction; CTA「打开资料填写页面」; disclaimer once |
| **Status Card** | Phase labels: 资料收集中 / 已提交给陈总审核 / 等待陈总查看 / 陈总已确认; H5 continue link only when continuable |
| **Confirm Card** | `【请确认】` for rare exceptions; unified disclaimer footer |
| **Submit Confirmation** | `【资料已提交 ✅】` — distinct from broker_done |
| **End Card** | `【陈总已确认 ✅】` — broker_done only (unchanged) |
| **Disclaimer dedup** | msgmenu tail = link hint only; disclaimer in card frame once |

---

## 7. H5 Review UX (deployed frontend)

| Item | Deployed |
|------|----------|
| Submit block at top of Review | Yes — highlighted box, larger button |
| Primary button | `提交给陈总审核` |
| Subtext | `提交后，陈总会在工作台看到资料，你也会在微信收到「资料已提交」确认。` |
| Warning | `还没有提交，返回微信不会把资料交给陈总。` |
| beforeunload guard | Yes on Review step |
| Done page | Unchanged — `已提交给陈总 ✅`;「返回微信」secondary |

---

## 8. Manual live test checklist (human WeCom retest)

### A. Fresh Start Card

微信发：`我要理赔`

Expected:

- Card title: `【事故记录已开始 ✅】`
- Tells user to open H5 and fill资料
- Explicitly says after finishing, click「提交给陈总审核」
- Primary action: `打开资料填写页面`
- Disclaimer appears once

### B. H5 Review submit clarity

Open H5, fill steps, reach Review.

Expected:

- Submit block is obvious at top
- Button: `提交给陈总审核`
- Subtext about 陈总工作台 + WeCom「资料已提交」确认
- Warning: `还没有提交，返回微信不会把资料交给陈总。`

### C. Submit confirmation

Click submit.

Expected:

- H5 Done page shows `已提交给陈总 ✅`
- WeCom receives `【资料已提交 ✅】`
- This is **not** broker_done

### D. Status Card

微信发：`进度`

Expected:

- Submitted case shows `已提交给陈总审核` / `等待陈总查看`
- Does not incorrectly ask user to restart H5
- Does not say 陈总已确认 unless broker_done happened

### E. Append-first

微信发：`补充一下，对方车牌是 ABC123`

Expected:

- Append to current Claim
- No「继续当前事故 / 开始新事故」card

### F. Explicit new accident

微信发：`这是另一个事故，不是刚才那个。`

Expected:

- Confirm Card can appear (rare exception)

### G. Workbench

Open Broker Workbench.

Expected:

- Case visible
- known_facts visible
- timeline has H5 and WeCom supplement events
- broker_done remains manual

---

## 9. Remaining gaps

| Gap | Notes |
|-----|-------|
| Real WeCom manual retest | **Required** — Cursor cannot verify WeChat msgmenu rendering |
| Card visual limits | WeCom text-frame only; no native template card backgrounds |
| Future native template cards | Possible later if WeCom API adopted |
| Workbench polish | Next group task candidate |

---

## 10. Rollback plan

### Backend rollback

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 --region=us-west1 \
  --to-revisions=fiqa-api-00196-k4l=100
```

Prior known-good: `fiqa-api-00196-k4l` @ `883039b45` (H5 completion polish)

### Frontend rollback

```bash
cd ui && vercel rollback
# or redeploy previous frontend commit (883039b era)
```

### Git rollback

```bash
git checkout p19h-wecom-card-h5-submit-clarity-predeploy-20260710
```

Older safe tags:

- `p19h-h5-completion-polish-predeploy-20260710`
- `p19h-append-first-predeploy-20260710`
- `p19h-claim-h5-mvp-predeploy-20260710`

---

## 11. Recommendation

| Item | Verdict |
|------|---------|
| Manual WeCom retest | **GO** — backend + frontend deployed; run checklist §8 |
| Group Task 3 | **GO** after manual WeCom pass |
| Next task | Human WeCom retest → Workbench polish or next H5/WeCom group |
