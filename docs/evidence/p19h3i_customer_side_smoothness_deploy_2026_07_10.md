# P19H-3i — Customer-side Smoothness Live Deploy Evidence

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Feature commits:**  
- `d9b3a9d` — fix: route Claim H5 requests away from legacy fallback  
- `31ada1c` — fix: include H5 link in Claim photo acknowledgements  

---

## 1. Safety

| Item | Value |
|------|-------|
| Branch | `sprint/p16-trust-layer` |
| Deployed HEAD | `31ada1c` |
| Schema migration | **No** |
| Frontend deploy | **No** — backend-only |

---

## 2. Pre-deploy tests (local)

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p19h3i_claim_legacy_fallback_regression.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3h_append_first_split_later.py \
  tests/test_p19h3f4_unified_status_card.py \
  tests/test_p19e1_phase2_routing_fix.py \
  tests/test_p19h3i_claim_photo_ack_h5_link.py \
  -q
# 68 passed
```

**Result:** All **PASS**

---

## 3. Backend deploy (Cloud Run)

| Item | Value |
|------|-------|
| **Revision** | `fiqa-api-00200-jxs` |
| **URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Deploy command** | `bash scripts/deploy_paid_pilot.sh` |
| **Memory / concurrency** | 1Gi / 30 |

### Post-deploy probes

```text
GET /health/live → {"ok":true}
GET /readyz      → intake_core_readiness: true, intake_path_ready: true
POST /api/inbox/triage (with intake API key) → 200 cancellation_warning
```

---

## 4. Post-deploy smoke

### P19H-3i claim task dashboard + photo ack (HTTP + QA DB)

```bash
PYTHONPATH=. python3 scripts/p19h3i_claim_task_dashboard_smoke.py \
  --base-url https://fiqa-api-g7zatxrycq-uw.a.run.app \
  --use-qa-db
```

**Evidence:** `docs/evidence/p19h3i_claim_task_dashboard_smoke_3i_smoke_232838.json`  
**Result:** **PASS**

Key live checks:

| Check | Result |
|-------|--------|
| Status commands (`进度`, `补资料`, `链接`, …) → H5 link | ✅ |
| Text supplement ack → H5 link | ✅ |
| **Photo ack → H5 link** (`photo_ack_has_h5_link`) | ✅ |
| **Photo ack CTA** (`继续补充事故资料`) | ✅ |
| Add Car intent not misrouted as supplement | ✅ |
| `broker_done_false` | ✅ |

---

## 5. What shipped

1. Claim H5 / status / supplement commands no longer fall through to legacy bilingual fallback (`d9b3a9d`).
2. WeCom photo ack on active Claim includes direct H5 task link (`31ada1c`).
3. Customer copy: `照片已收到` + `继续补充事故资料` + disclaimer (no primary `进度/链接` path when link mints).

---

## 6. Manual follow-up

Use `docs/evidence/p19h3i_customer_side_smoothness_manual_checklist_2026_07_10.md` — especially **step 7 (send photo)** on a real WeCom customer with an active Claim.

---

## 7. Notes

- `scripts/test_inbox_triage_api.py` against prod returns 401 without `X-Unified-Intake-Api-Key`; triage verified manually with intake key from `.env.cloudrun`.
- WeCom profile lookup warning (`errcode 60020` IP allowlist) during in-process smoke is expected from WSL IP; does not block Claim routing smoke.
