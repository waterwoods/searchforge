# P19H-3h — Claim H5 MVP Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Predeploy tag:** `p19h-claim-h5-mvp-predeploy-20260710` (pushed)  
**Deploy commit:** `73e1367` (`73e13673a`)

---

## 1. Backend

| Item | Before | After |
|------|--------|-------|
| GIT_SHA | `a96d8eef6` | `73e13673a` |
| Cloud Run revision | `fiqa-api-00193-b5q` | `fiqa-api-00194-85v` |
| Service URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | same |
| `/health/live` | 200 `{"ok":true}` | 200 `{"ok":true}` |
| `/readyz` | 200 `intake_core_readiness: true` | 200 `intake_core_readiness: true` |
| Schema migration | **No** | **No** |

**Deploy command:** `bash scripts/deploy_paid_pilot.sh`

---

## 2. Frontend

| Item | Value |
|------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | `https://ui-2052n6k1d-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| `/task/claim/:taskToken` | 200 SPA shell |
| `/task/upload/:taskToken` | unchanged (200 SPA shell) |
| Bundle contains `task/claim` | **Yes** |

---

## 3. Pre-deploy tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py -q          # 11 passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3f4_unified_status_card.py -q  # 14 passed
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py                # pass (in_process)
cd ui && npm run build                                                      # pass
```

---

## 4. Backend live smoke

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS** (after smoke script loads `H5_TASK_TOKEN_SECRET` from Secret Manager `fiqa-h5-task-token-secret`)

**Evidence JSON:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_054225.json`

**Smoke case:** `case_7f11d0046a78` (test-tagged via smoke external_userid prefix)

Verified live:
- GET `/api/h5/tasks/{token}/intake` → `flow=claim_intake_form`, `upload_url` present
- PATCH all required fields → persisted
- POST submit + idempotent resubmit
- Workbench API: `workflow_phase=intake_ready_for_broker`, `workbench_visible=true`
- Timeline: `h5_step_complete`, `customer_submitted_intake`
- Status Card: H5 continue link before submit; omitted after submit; no duplicate case

---

## 5. H5 live URL sample

Minted intake link (submitted case — opens Done state):

```
https://ui-smoky-beta.vercel.app/task/claim/h5t1.{token}
```

Live GET for smoke-submitted case returns `submitted: true`, `phase: intake_ready_for_broker`.

**Manual browser check:** Open minted link from new Claim Start Card in WeCom (see checklist below).

---

## 6. Workbench verification (API)

`GET /api/inbox/cases/case_7f11d0046a78`:

| Field | Value |
|-------|-------|
| `workflow_phase` | `intake_ready_for_broker` |
| `workbench_visible` | `true` |
| `key_facts.accident_location` | `Irvine Blvd` |
| `key_facts.own_vehicle_info` | `2020 Toyota Camry` |
| Timeline events | `h5_step_complete` (×4), `customer_submitted_intake` |
| `broker_done` | Unaffected — still manual |

---

## 7. WeCom verification

| Check | Result |
|-------|--------|
| Start Card H5 intake link (`/task/claim/`) | **Simulated PASS** — `build_claim_start_h5_intake_card_payload` + `mint_h5_claim_intake_form_link` → `ui-smoky-beta.vercel.app/task/claim/...` |
| Status Card H5 continue link (open case) | **Live smoke PASS** |
| Status Card after H5 submit | **Live smoke PASS** — no continue link |
| End Card semantics | **Unchanged** (unit tests; no code change this deploy) |
| Real WeCom customer message | **NOT verified** — IP blocked for `kf/customer/batchget` from deploy runner |

### Manual WeCom checklist (operator)

1. From test WeCom account, send「我要理赔」
2. Confirm Start Card button「打开资料填写页面」opens `https://ui-smoky-beta.vercel.app/task/claim/...`
3. Complete H5 wizard → submit
4. Send「进度」→ Status Card should **not** show「继续补充资料」after submit
5. Broker opens Workbench → case shows H5 facts + timeline
6. Broker Done → End Card unchanged semantics

---

## 8. Rollback plan

### Backend

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 \
  --region=us-west1 \
  --to-revisions=fiqa-api-00193-b5q=100
```

Prior known-good: `fiqa-api-00193-b5q` @ `a96d8eef6`

### Frontend

```bash
cd ui && vercel rollback   # or redeploy prior deployment from Vercel dashboard
```

Prior stable deployment served `ui-smoky-beta` before this deploy (2026-07-10 ~02:22 UTC `last-modified`).

### Git

```bash
git checkout p19h-claim-h5-mvp-predeploy-20260710
# or older design checkpoint:
git checkout p19h-pre-h5-task-mvp-20260710
```

---

## 9. Remaining gaps

- Inline photo upload in Claim wizard
- Photo hash dedup
- Real WeCom end-to-end click-through (manual)
- Add Car H5
- Workbench polish (H5 source badge)
- Smoke script requires GCP Secret Manager access for `--use-qa-db` deploy mode

---

## 10. Recommendation

**GO for Chen demo** — backend + frontend deployed; live API smoke PASS; Workbench readback PASS. Complete manual WeCom checklist on test account before customer-facing demo.
