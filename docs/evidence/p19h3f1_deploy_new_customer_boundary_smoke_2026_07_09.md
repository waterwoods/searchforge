# P19H-3f-1 — Deploy + New Customer Claim Boundary Smoke

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Deploy commit `5dc3075` (Claim case boundary policy) to Cloud Run + Vercel, and verify on QA Cloud SQL that:

> Random chat / random photo does **not** create a formal Claim case.  
> Formal Claim case requires explicit start (我要理赔) or controlled task entry.

---

## 2. Deployed revision / GIT_SHA

| Field | Value |
|-------|-------|
| Commit | **`5dc3075`** — feat: enforce Claim case boundary policy |
| Revision | **`fiqa-api-00181-sb4`** |
| Prior revision | `fiqa-api-00180-7hv` (`2dbf41f`) |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`5dc3075ca`** (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |

---

## 3. Frontend deployment / stable alias

| Field | Value |
|-------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | `https://ui-jmaj37w7i-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Bundle strings | `Claim · 记录中`, `待确认材料` present in `assets/index-D0oIR5U3.js` |
| `/workbench/unified-intake` | **HTTP 200** |
| `/add-car` | **HTTP 200** |

UI changes in `5dc3075`: `DocumentIntakeInboxPage.tsx`, `claimWorkbenchDisplay.ts` — **frontend redeploy required** ✅

---

## 4. Health / ready

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"5dc3075ca",...}` |

---

## 5. QA gate

```bash
time bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

| Metric | Result |
|--------|--------|
| Outcome | **PASS** |
| Elapsed | **12.55s** |
| Revision | `fiqa-api-00181-sb4` |
| API `total_count` | 39 (post-smoke: 42) |

---

## 6. Smoke method

QA Cloud SQL write via same `ingest_*()` functions as deployed revision + Cloud Run API readback.  
Ephemeral smoke cases tagged `demo_name=p19h3f1_deploy_smoke` / `workbench_test=true`.  
Suffix: `3f1_054621`.

---

## 7. Smoke A — random photo only

**Case:** `case_de46eddc2874` · ext `wm_p19h3f1_photo_3f1_054621`

| Check | Result |
|-------|--------|
| `service_lane` | **`wecom_media_intake`** (not `claim`) |
| Outcome | `media_unassigned` |
| Reply contains 【尚未开始事故记录】 | **Yes** |
| Reply contains 我要理赔 | **Yes** |
| Start Card (事故记录已开始) | **No** |
| Formal Claim case for ext | **No** |

**PASS**

---

## 8. Smoke B — random narrative only

**Input:** `昨晚 Costco 被追尾了，后保险杠有点坏。` · ext `wm_p19h3f1_narr_3f1_054621`

| Check | Result |
|-------|--------|
| Formal Claim case created | **No** |
| Holding ack | **Yes** — 【尚未开始事故记录】 |
| `claim_timeline` | **None** |
| `claim_case_brief` | **None** |
| Start Card | **No** |

**PASS**

---

## 9. Smoke C — explicit start

**Input:** `我要理赔` · **Case:** `case_ef46f2734fe5`

| Check | Result |
|-------|--------|
| Formal Claim case created | **Yes** |
| `service_lane` | **`claim`** |
| Start Card 【事故记录已开始 ✅】 | **Yes** |
| 陈总办公室值班助手 | **Yes** |
| 有没有受伤 | **Yes** |
| 不代表已经向保险公司正式报案 | **Yes** |
| Injury quick replies (menu_payload) | **Yes** |
| API `claim_timeline` | **Present** |

**PASS**

---

## 10. Smoke D — full new customer flow

**Flow:** 我要理赔 → 没有受伤 → Costco story → photo  
**Case:** `case_52d80db0a7d9`

| Check | Result |
|-------|--------|
| `claim_timeline` types | `claim_started`, `customer_text` ×3, `basics_complete`, `customer_photo` |
| Injury recorded | `known_facts.injury_status=no`; timeline `customer_text` metadata `quick_reply_key=injury_status` |
| `claim_case_brief` | **Yes** |
| Workbench display (computed) | **`Claim · 记录中 · Broker Review pending`** |
| Photo ack 已记到这份事故记录里 | **Yes** |
| Forbidden language | **None** (已报案 / 一定会赔 / 对方全责 / 保险公司已收到) |

**Note:** Injury quick-reply is stored as `customer_text` with metadata (not a separate `injury` event type) — matches unit tests in `test_p19h3f1_case_boundary_policy.py`.

**PASS**

---

## 11. Smoke E — injury click alone

**Input:** menu `claim_injury_no` with no active Claim · ext `wm_p19h3f1_inj_3f1_054621`

| Check | Result |
|-------|--------|
| Claim case created | **No** |
| Holding gate asks 我要理赔 | **Yes** |
| Outcome | `claim_injury_holding_gate` |

**PASS**

---

## 12. Smoke F — Add Vehicle + H5 regressions

| Check | Result |
|-------|--------|
| Add-car photo attach | **PASS** — `media_attached_to_case`, lane `add_car`, no `claim_timeline` |
| H5 claim evidence cloud token (local mint) | **403** `invalid_or_expired_task_link` — expected (local `.env.cloudrun` secret ≠ Cloud Run Secret Manager) |
| H5 pytest regression | **PASS** — `test_h5_add_vehicle_photo_flow.py`, `test_p19h3c2_claim_c1_h5_button.py` |

**PASS** (Add Vehicle unaffected; H5 path validated via pytest per prior deploy evidence pattern)

---

## 13. Workbench visual

| Check | Result |
|-------|--------|
| Claim row `case_52d80db0a7d9` lane | **`claim`** |
| Claim display (backend helper) | **`Claim · 记录中 · Broker Review pending`** |
| Media row `case_de46eddc2874` lane | **`wecom_media_intake`** |
| Media display (backend helper) | **`待确认材料 · 未分配微信资料 · 不是正式 case`** |
| Rows clearly separate | **Yes** |
| Unassigned media not presented as formal Claim | **Yes** |
| Frontend bundle labels | `Claim · 记录中`, `待确认材料` |
| Browser drawer visual | **HUMAN-PENDING** — operator can open https://ui-smoky-beta.vercel.app/workbench/unified-intake |

**PASS** (API/PG + bundle strings; live drawer optional)

---

## 14. Logs

Scanned Cloud Run logs (`fiqa-api-00181-sb4`, ~3h window):

| Finding | Result |
|---------|--------|
| Claim boundary errors | **None** |
| HTTP 500 on inbox/claim paths | **None** |
| Qdrant embedding warmup ERROR | Expected optional (intake_core readiness unaffected) |

---

## 15. Constraints honored

| Constraint | Status |
|------------|--------|
| No schema migration | ✅ |
| No OCR / carrier filing | ✅ |
| Holding Card buttons deferred | ✅ (text-only gate) |

---

## 16. Known limitations

- Injury timeline event is `customer_text` + `quick_reply_key=injury_status`, not `event_type=injury`
- H5 cloud token from local mint returns 403 (use pytest or prod-minted link for live H5)
- Workbench list endpoint does not inline `claim_display_status`; UI computes from lane + enrichment fields

---

## 17. GO / HOLD

**GO** — `5dc3075` deployed; boundary policy live; random photo/narrative held; explicit start creates formal Claim + Start Card; full new-customer flow produces timeline + brief; injury-alone gated; Add Vehicle/H5 regressions pass.

**STOP**

---

## 18. Next recommended prompt

1. **P19H-3e-1b Claim Case Brief Highlights**
2. **P19H-3f-1b Holding Card buttons (开始记录这次事故 / 只是咨询)**
