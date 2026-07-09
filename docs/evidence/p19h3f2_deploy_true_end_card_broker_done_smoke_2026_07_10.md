# P19H-3f-2 — Deploy Smoke: True End Card on Broker Done

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Source commit:** `824232c`  
**Smoke suffix:** `3f2_smoke_184327`  
**Smoke case:** `case_6bf131e387c8`

---

## 1. Goal

Deploy and verify production True End Card loop:

| Step | Ceremony |
|------|----------|
| Start | `【事故记录已开始 ✅】` — formal Claim begins |
| Broker Done | Chen/office manual confirm |
| End Card | `【陈总已确认 ✅】` — collection phase ends (not carrier filing) |

---

## 2. Deployed revision

| Item | Value |
|------|-------|
| Backend service | `fiqa-api` (us-west1) |
| Revision | `fiqa-api-00184-jp2` |
| **GIT_SHA** | **`824232c5e`** |
| Deploy command | `bash scripts/deploy_paid_pilot.sh` |

---

## 3. Frontend

| Item | Value |
|------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | `https://ui-obf5opaz2-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |

---

## 4. Health / readyz

| Check | Result |
|-------|--------|
| `/version` | `824232c5e` |
| `/health/live` | 200 |
| `/readyz` | 200, `intake_path_ready: true` |
| `/workbench/unified-intake` | 200 |
| `/add-car` | 200 |

---

## 5. QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result:** FAIL (known seed/demo mismatch — not deploy blocker)

| Area | Result |
|------|--------|
| Vercel routes | PASS |
| Cloud Run readyz | PASS |
| Workbench list core | PASS |
| Missing demo names (张先生, 王女士 tags) | FAIL — re-seed optional |
| Cloud SQL alignment | PASS |

**Continued** focused broker_done smoke per operator guidance.

---

## 6. Smoke A — Formal Claim before broker_done

**Flow:** 我要理赔 → [没有受伤] → Costco story → photo

| Check | Result |
|-------|--------|
| Start Card | ✅ `事故记录已开始` |
| Timeline | `claim_started`, injury, `customer_text`, `basics_complete`, `customer_photo` |
| Brief + highlights | ✅ 4 highlights |
| Default queue | ✅ visible |
| Display | `Claim · 记录中 · Broker Review pending` |

**PASS**

---

## 7. Smoke B — broker_done action

`POST /api/inbox/cases/case_6bf131e387c8/broker-done`

| Check | Result |
|-------|--------|
| HTTP | 200 |
| `claim_phase` | `broker_done` |
| Timeline `broker_done` | ✅ actor=broker, source=workbench |
| `display_status` | `Claim · 已确认 / 已交接` |
| End Card | **preview** returned (`end_card_sent: false` — no WeCom channel on smoke case) |
| Copy markers | ✅ 陈总已确认 / 收集阶段已结束 / 不代表结案/赔付 |
| Forbidden language | ✅ absent |

**PASS** (preview; live WeCom send requires customer channel binding)

**Note:** `claim_end_card_state.broker_done_at` stored in DB but not exposed in sanitized API response.

---

## 8. Smoke C — Idempotency

Second `POST broker-done` on same case:

| Check | Result |
|-------|--------|
| HTTP | 200 |
| `already_done` | `true` |
| Timeline `broker_done` events | 1 (no duplicate) |

**PASS**

---

## 9. Smoke D — Queue after done

| Check | Result |
|-------|--------|
| Default `GET /api/inbox/cases` | case **not** in active queue |
| `GET /api/inbox/cases/{id}` | 200, still exists |
| Display | `Claim · 已确认 / 已交接` |
| Brief/highlights | visible |
| Timeline | includes `broker_done` |

**PASS**

---

## 10. Smoke E — Raw inbound rejected

Raw photo case: `case_ddc405065c5c` (`wecom_media_intake`)

`POST broker-done` → **400** `broker_done_blocked_raw_inbound`

| Check | Result |
|-------|--------|
| No broker_done timeline | ✅ |
| Lane unchanged | `wecom_media_intake` / Raw Inbound Log |

**PASS**

---

## 11. Smoke F — Workbench UI

| Check | Result |
|-------|--------|
| Page HTTP | 200 |
| JS bundle (`index-BwABC0DH.js`) | contains `陈总已确认 / 结束收集`, `broker-done` |
| Browser click test | **HUMAN-PENDING** |

**PASS** (API + bundle strings)

---

## 12. Add Vehicle regression

| Check | Result |
|-------|--------|
| Media attach to add_car | `media_attached_to_case` |
| `POST broker-done` on add_car | 400 `broker_done_blocked_not_claim_lane:add_car` |

**PASS**

---

## 13. H5 regression

| Check | Result |
|-------|--------|
| `pytest -k h5` | PASS |
| H5 task token mint | lane=claim, flow=claim_evidence_pack |
| Live GET `/api/h5/tasks/{token}` | 403 (expected without browser session) |

**PASS**

---

## 14. Start Card only policy regression

| Check | Result |
|-------|--------|
| Random photo hidden from default queue | ✅ |
| Explicit 我要理赔 → Start Card + queue | ✅ |

**PASS**

---

## 15. Logs

Cloud Run `fiqa-api-00184-jp2` after smoke:

- `POST .../broker-done` → 200 (Claim) and 400 (raw/add_car) — expected
- No broker_done 500s
- No duplicate send errors
- Qdrant/Redis warmup noise only

**PASS**

---

## 16. Constraints

| Constraint | Held |
|------------|------|
| No schema | ✅ |
| No auto close | ✅ |
| No OCR/ASR | ✅ |
| No fault/coverage/carrier filing | ✅ |
| No LLM brief | ✅ |

---

## 17. Known limitations

1. Smoke cases lack `wecom_external_userid` + `open_kf_id` → End Card **preview only**, not live WeCom send
2. `claim_end_card_state` not in sanitized workbench API payload (internal dedup field)
3. QA gate seed names/tags stale — unrelated to broker_done
4. Browser drawer click not automated this run

---

## 18. Next recommended prompt

1. **Pilot Demo Script / Chen readiness** — full Start → Record → Broker Done → End Card walkthrough with real WeCom customer
2. **QA seed refresh** — `PYTHONPATH=. python3 scripts/seed_chen_kui_demo.py --target qa` (optional)

---

## Verdict: **GO**

True End Card broker_done deployed and verified on QA Cloud SQL + Cloud Run `824232c`.

---

## Smoke artifact

Local run JSON: `docs/evidence/p19h3f2_smoke_run_3f2_smoke_184327.json` (not committed)
