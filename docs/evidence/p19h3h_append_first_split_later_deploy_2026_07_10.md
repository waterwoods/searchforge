# P19H-3h-1G — Append-first Split-later Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Predeploy tag:** `p19h-append-first-predeploy-20260710` (pushed @ `a119bb2`)  
**Deploy commit:** `a119bb2` (`a119bb247`)

---

## 1. Safety

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Starting commit | `a119bb2` |
| Tracked working tree | **Clean** (untracked smoke JSON/scripts only) |
| Schema migration | **No** |
| Frontend deploy | **No** |

---

## 2. Backend

| Item | Before | After |
|------|--------|-------|
| GIT_SHA | `73e13673a` | `a119bb247` |
| Cloud Run revision | `fiqa-api-00194-85v` | `fiqa-api-00195-9lz` |
| Service URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | same |
| `/health/live` | 200 `{"ok":true}` | 200 `{"ok":true}` |
| `/readyz` | 200 `intake_core_readiness: true` | 200 `intake_core_readiness: true` |

**Deploy command:** `bash scripts/deploy_paid_pilot.sh`

---

## 3. Pre-deploy tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3h_append_first_split_later.py -q   # 11 passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3f3_claim_collision_resolver.py -q  # 14 passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3f5_single_active_task_per_lane.py -q  # 20 passed
PYTHONPATH=. python3 -m pytest tests/test_h5_claim_intake_form.py -q              # 11 passed
PYTHONPATH=. python3 -m pytest tests/test_p19h3f4_unified_status_card.py -q       # 14 passed
```

**Result:** All **PASS**

---

## 4. Post-deploy smoke

### H5 intake live smoke (HTTP + QA DB)

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS**  
**Evidence JSON:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_065139.json`  
**Smoke case:** `case_d2b236cb495a` (test-tagged via `wm_p19h3h_smoke_*` prefix)

### Append-first simulated WeCom smoke (QA DB, no real callbacks)

```bash
PYTHONPATH=. python3 scripts/p19h3h_append_first_wecom_smoke.py
```

**Result:** **PASS**  
**Evidence JSON:** `docs/evidence/p19h3h_append_first_wecom_smoke_3h_af_smoke_065241.json`

Verified scenarios:
- Active open Claim + ordinary narrative → append, no collision
- Active open Claim +「补充一下，对方保险是 State Farm」→ append
- Active open Claim +「这是另一个事故」→ explicit confirm card
- Repeat「我要理赔」on open/incomplete Claim → continue, not collision
- Status Card with H5 continue link when intake not submitted
- Fresh「我要理赔」→ H5 Start Card

---

## 5. Frontend

| Item | Value |
|------|-------|
| Deployed? | **No** |
| Reason | Patch is backend-only (`claim_basics.py`, `claim_identity.py`); no `ui/` changes in `a119bb2` |

---

## 6. Manual WeCom checklist

**Path:** `docs/evidence/p19h3h_append_first_split_later_manual_checklist_2026_07_10.md`

Real WeCom manual retest **not yet done** — pending human tester on Chen pilot KF.

---

## 7. Remaining gaps

- Real WeCom manual retest not yet done
- Add Car append-first not implemented
- Broker split/merge UI not implemented
- Identity/nickname audit separate
- Performance hardening separate

---

## 8. Rollback plan

### Backend rollback

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 --region=us-west1 \
  --to-revisions=fiqa-api-00194-85v=100
```

Prior known-good: `fiqa-api-00194-85v` @ `73e13673a` (Claim H5 MVP)

### Git rollback

```bash
git checkout p19h-append-first-predeploy-20260710
```

Or older H5 checkpoint:

```bash
git checkout p19h-claim-h5-mvp-predeploy-20260710
```

### Frontend rollback

Not applicable — frontend was not deployed.

---

## 9. Recommendation

| Gate | Verdict |
|------|---------|
| Manual WeCom retest | **GO** — backend deployed, smokes pass; proceed with human checklist |
| Chen demo after manual test | **HOLD** — wait for manual WeCom sign-off |

**Next recommended task:** Execute manual WeCom checklist on Chen pilot KF; then broker Workbench timeline verification.
