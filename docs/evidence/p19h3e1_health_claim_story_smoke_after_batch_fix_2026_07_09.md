# P19H-3e-1 — Health Check + Claim Story Smoke After Batch Fix

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Validate deployed `2dbf41f` batch-list fix on Cloud Run, confirm QA gate no longer stalls on `list_all_cases_for_read`, and run Claim Story smokes A–E plus H5/Add Vehicle regressions.

---

## 2. Deployed revision / GIT_SHA

| Field | Value |
|-------|-------|
| Initial check | `fiqa-api-00179-f6r` — GIT_SHA **`5ab6022d3`** (batch fix not yet live) |
| Action | `bash scripts/deploy_paid_pilot.sh` (required for acceptance) |
| Final revision | **`fiqa-api-00180-7hv`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`2dbf41fbd`** (`GET /version`) |

---

## 3. Health / readyz

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |

---

## 4. Frontend stable alias

| Field | Value |
|-------|-------|
| **Stable alias** | `https://ui-smoky-beta.vercel.app` |
| `/workbench/document-intake` | **HTTP 200** |
| Bundle strings | `事故摘要`, `还缺什么`, `建议问客户`, `最近记录`, `照片清单` — all present in `assets/index-*.js` |

---

## 5. QA gate timing after batch fix

```bash
time bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

| Metric | Result |
|--------|--------|
| Outcome | **PASS** |
| Elapsed | **14.44s** |
| `Argument list too long` | **No** |
| ~90s list scan | **No** |
| API `total_count` | 33 |

---

## 6. Smoke A — text story

**Suffix:** `3e1_smoke_044849`  
**Case:** `case_782f25c975d9`  
**Method:** QA Cloud SQL seed + Cloud Run API readback (`scripts/p19h3e1_deploy_claim_story_smoke.py` path)

| Check | Result |
|-------|--------|
| `claim_timeline` | **Yes** — types: `claim_started`, `customer_text` ×2, `basics_complete` (+ `customer_photo` after C) |
| `claim_case_brief` | **Yes** |
| `key_facts.accident_datetime` | 今天下午三点多 |
| `key_facts.accident_location` | Costco 停车场出口 |
| `key_facts.accident_description` | 被后车追尾，后保险杠被撞了 |
| `key_facts.injury_status` | **no** |
| `next_best_question` | 请问对方车牌或保险信息拿到了吗？ (single question) |
| Forbidden language | **None** (已报案 / 一定会赔 / 对方全责 / 保险公司已收到) |

**PASS**

---

## 7. Smoke B — injury quick replies

**Method:** Internal `ingest_claim_injury_quick_reply()` simulator (not live WeCom msgmenu)

| Check | Result |
|-------|--------|
| `[没有受伤]` → `injury_status` | **no** |
| Missing info no longer starts with `injury_status` | **Yes** |
| `[有人受伤]` → `injury_status` | **yes** |
| Manual escalation | **Yes** (`manual_handle` / `needs_broker_manual_handle`) |
| No H5/photo nag on injury-yes reply | **Yes** |
| Live msgmenu click | **HUMAN-PENDING** |

**PASS**

---

## 8. Smoke C — photo timeline

| Check | Result |
|-------|--------|
| `case_attachments` appended | **Yes** |
| `claim_timeline` `customer_photo` event | **1** |
| `claim_case_brief.evidence_received.photo_count` | **≥ 1** |
| Reply contains `收到照片` + `已记到这份事故记录里` | **Yes** |
| Reply avoids `上传事故照片` / button nag | **Yes** |
| Sample reply | `收到照片，已记到这份事故记录里 ✅` … `不用重复发同一张` |

**PASS**

---

## 9. Enrichment parity

**Case:** `case_782f25c975d9`

| Field | List `GET /api/inbox/cases?limit=50` | Single `GET /api/inbox/cases/{id}` |
|-------|--------------------------------------|-------------------------------------|
| `claim_timeline` | **Yes** | **Yes** |
| `claim_case_brief` | **Yes** | **Yes** |
| `claim_evidence_summary` | **Yes** | **Yes** |

List endpoint still returns full Claim enrichment on current page (unchanged contract). Workbench drawer also hydrates via single GET.

**PASS**

---

## 10. Workbench visual result

**HUMAN-PENDING** — no browser automation this run.

Partial validation:
- API brief + timeline on smoke case **PASS**
- Frontend bundle contains Brief hero strings **PASS**

Manual checklist for operator:
1. Open `https://ui-smoky-beta.vercel.app/workbench/document-intake`
2. Open case `case_782f25c975d9` (or newest `p19h3e1_deploy_smoke` / workbench_test Claim)
3. Confirm above fold: 事故摘要, summary, 还缺什么, 建议问客户, 最近记录, photo count
4. Evidence Checklist collapsed; Accident Basics collapsed

---

## 11. Add Vehicle result (Smoke E)

| Check | Result |
|-------|--------|
| `media_attached_to_case` | **Yes** |
| `service_lane` | **add_car** |
| No `claim_timeline` on add_car case | **Yes** |
| No `claim_case_brief` on API | **Yes** |
| Attachment present | **Yes** |

**PASS**

---

## 12. H5 result (Smoke F)

| Check | Result |
|-------|--------|
| Cloud API `GET /api/h5/tasks/{token}` after local mint | **403** — HMAC secret differs local laptop vs Cloud Run (expected for local mint against prod API) |
| Regression tests | **PASS** — `test_p19h3c3c_h5_claim_slot_persistence.py`, `test_p19h3c2_claim_c1_h5_button.py` (16 tests) |

H5 claim evidence path validated via test suite; live cloud H5 token mint requires Cloud Run-issued link or shared secret.

**PASS** (regression); cloud live token **HUMAN-PENDING**

---

## 13. Logs result

Scanned Cloud Run logs (400 recent, `fiqa-api` us-west1):

| Finding | Severity |
|---------|----------|
| Qdrant / Redis / embedding warmup | WARN/ERROR — **OK** (non-blocking for Claim Story) |
| `claim_timeline` / `claim_case_brief` / list batch errors | **None** |
| Workbench 500s | **None** |
| WeCom quick reply errors | **None** |

**PASS**

---

## 14. Performance note (smoke script)

Full smoke A–E elapsed **~38s** (down from ~92s+ when `list_all_cases_for_read` used N+1 full hydration). Injury quick-reply path benefits from batched queue loader.

---

## 15. Constraints

- No schema migration
- No OCR / ASR / damage AI
- No fault / coverage / carrier filing
- No highlights[]
- No slot assignment
- No new product feature

---

## 16. Known limitations

- Deterministic brief only (no LLM brief)
- No full timeline UI in Workbench
- Live WeCom msgmenu injury clicks **HUMAN-PENDING**
- Workbench visual **HUMAN-PENDING**
- H5 cloud token from local mint **403** against prod API (use pytest or prod-minted link)

---

## 17. Next recommended prompt

**P19H-3e-1b Claim Case Brief Highlights**

---

## 18. GO / HOLD

**GO** — `2dbf41f` deployed, health/QA/smokes PASS, batch fix validated.
