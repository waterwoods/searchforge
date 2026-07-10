# P19H-3h — Claim Supplement Routing Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Feature commit:** `fdba4b7` — fix: route Claim supplements away from Add Car Phase 2  
**Predeploy tag:** `p19h-claim-supplement-routing-predeploy-20260710` → `fdba4b7`

---

## 1. Safety

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Starting commit | `fdba4b7` |
| Tracked working tree at deploy | **Clean** (patch committed before deploy) |
| Schema migration | **No** |
| Frontend deploy | **No** — backend-only patch; no `ui/` changes |

---

## 2. Pre-deploy tests

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19h3h_append_first_split_later.py -q
# 17 passed

PYTHONPATH=. python3 -m pytest \
  tests/test_p19h3h_append_first_split_later.py \
  tests/test_p19h2_simplified_claim_wecom_basics.py \
  tests/test_p19h2_claim_wecom_basics.py \
  tests/test_p19h3f5_single_active_task_per_lane.py \
  tests/test_p19e1_phase2_routing_fix.py \
  tests/test_h5_claim_intake_form.py \
  -q
# 89 passed
```

**Result:** All **PASS**

---

## 3. Backend deploy (Cloud Run)

| Item | Before | After |
|------|--------|-------|
| **GIT_SHA** | `4211cb28c` | `fdba4b7fc` |
| **Revision** | `fiqa-api-00197-2sg` | `fiqa-api-00198-5sj` |
| **URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app | (unchanged) |
| **Deploy command** | `bash scripts/deploy_paid_pilot.sh` | |

### Pre-deploy probes

```text
GET /version     → {"commit":"4211cb28c", ...}
GET /health/live → {"ok":true}
GET /readyz      → intake_core_readiness: true
```

### Post-deploy probes

```text
GET /version     → {"commit":"fdba4b7fc", ...}
GET /health/live → {"ok":true}
GET /readyz      → intake_core_readiness: true, intake_path_ready: true
```

### Live env confirmed

| Variable | Value |
|----------|-------|
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `WECOM_INBOX_QUEUE` | `0` (unchanged) |

---

## 4. Post-deploy smoke

### H5 intake live smoke (HTTP + QA DB)

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_h5_intake_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS**  
**Evidence:** `docs/evidence/p19h3h_claim_h5_intake_smoke_3h_smoke_194248.json`

### Claim supplement routing smoke (QA DB, simulated WeCom)

```bash
PYTHONPATH=. python3 scripts/p19h3h_claim_supplement_routing_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Result:** **PASS**  
**Evidence:** `docs/evidence/p19h3h_claim_supplement_routing_smoke_csr_smoke_194840.json`

Verified scenarios:

| # | Scenario | Result |
|---|----------|--------|
| 1 | Submitted Claim + open Add Car Phase 2 +「补充一下，对方车牌是 ABC123」 | `claim_supplement_appended`; no Phase 2 fields; `other_party_plate=ABC123`; timeline event |
| 2 |「对方保险是 State Farm」on same Claim | `claim_supplement_appended`; `other_party_info=State Farm`; workbench shows plate |
| 3 |「我要加车」with active Claim | Explicit Add Car path not blocked by supplement policy |

### Append-first WeCom smoke (existing script)

```bash
PYTHONPATH=. python3 scripts/p19h3h_append_first_wecom_smoke.py
```

**Result:** **FAIL** (checks 1, 2, 6) on repeated runs — QA DB **message dedup** collision from fixed `msg_id` values (`af1`…`af6`) reused across same-day runs. Not a regression signal for this patch; focused supplement routing smoke above covers the deployed fix.

**Evidence (failed run):** `docs/evidence/p19h3h_append_first_wecom_smoke_3h_af_smoke_194919.json`

---

## 5. Frontend

| Item | Value |
|------|-------|
| Deployed? | **No** |
| Reason | No frontend files in `fdba4b7`; backend routing patch only |

---

## 6. Behavior after deploy (expected live)

| User message | Expected routing |
|--------------|------------------|
| `补充一下，对方车牌是 ABC123` (active/submitted Claim) | Append to Claim; supplement ack; **not** Add Car Phase 2 |
| `对方保险是 State Farm` | Append to Claim; update `other_party_info` |
| `我要加车` | Explicit Add Car / lane switch unchanged |
| Workbench | Timeline + known_facts show supplements; no duplicate Add Car from supplements |

---

## 7. Manual checklist

**Path:** `docs/evidence/p19h3h_claim_supplement_routing_manual_checklist_2026_07_10.md`

Human steps: submitted Claim → plate supplement → insurance supplement → 进度 → 我要加车 → Workbench readback.

---

## 8. Remaining gaps

| Gap | Notes |
|-----|-------|
| Real WeCom manual retest | **Required** — run manual checklist §7 |
| H5 Dashboard / Always-return H5 entry | Not in scope |
| Add Car append-first broader policy | Partial — only Claim supplement vs Phase 2 fix shipped |
| Workbench polish | Not done |
| `p19h3h_append_first_wecom_smoke.py` dedup hygiene | Fixed msg_ids collide on repeated QA runs; consider suffixing msg_ids in a follow-up |

---

## 9. Rollback plan

### Backend rollback

```bash
gcloud run services update-traffic fiqa-api \
  --project=optimal-disk-472305-e2 --region=us-west1 \
  --to-revisions=fiqa-api-00197-2sg=100
```

### Git rollback

```bash
git checkout p19h-claim-supplement-routing-predeploy-20260710
```

Older safe tags:

- `p19h-wecom-card-h5-submit-clarity-predeploy-20260710`
- `p19h-h5-completion-polish-predeploy-20260710`
- `p19h-append-first-predeploy-20260710`

### Frontend rollback

Not applicable (no frontend deploy).

---

## 10. Recommendation

| Gate | Verdict |
|------|---------|
| Manual WeCom retest | **GO** — backend live @ `fdba4b7`; run manual checklist |
| Next group task (Claim Task Dashboard / Always-return H5 Entry) | **HOLD** until manual WeCom pass |
| Next exact task | Human WeCom retest per checklist → then Claim Task Dashboard / Always-return H5 Entry |
