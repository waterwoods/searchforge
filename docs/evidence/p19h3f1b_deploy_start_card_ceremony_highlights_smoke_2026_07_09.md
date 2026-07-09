# P19H-3f-1b — Deploy + Start Card Ceremony + Highlights Smoke

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Deploy commit `62c4b35` (Start Card ceremony contract + Claim Case Brief `highlights[]`) to Cloud Run + Vercel, and verify on QA Cloud SQL that:

1. Start Card = Claim case creation ceremony  
2. No Start Card = no formal customer-facing Claim case started  
3. `claim_case_brief.highlights[]` generated online and visible in UI bundle  
4. Random photo / random accident narrative do not create formal Claim  
5. Injury click alone does not create formal Claim  
6. Add Vehicle / H5 regressions unaffected  

---

## 2. Deployed backend revision / GIT_SHA

| Field | Value |
|-------|-------|
| Commit | **`62c4b35`** — feat: add Claim start ceremony contract and brief highlights |
| Revision | **`fiqa-api-00182-rmf`** |
| Prior revision | `fiqa-api-00181-sb4` (`5dc3075`) |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`62c4b35d8`** (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |

---

## 3. Frontend deployment / stable alias

| Field | Value |
|-------|-------|
| Command | `cd ui && vercel --prod --yes` |
| Deployment URL | `https://ui-dbal9g4jn-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Bundle | `assets/index-BKeOwpB_.js` |
| Bundle strings | `Claim · 记录中`, `待确认材料`, `重点速览`, `highlights` present |
| `/workbench/unified-intake` | **HTTP 200** |
| `/workbench/document-intake` | **HTTP 200** |
| `/add-car` | **HTTP 200** |

UI changes in `62c4b35`: `ClaimCaseBriefPanel.tsx`, `inboxTriage.ts` — **frontend redeploy required** ✅

---

## 4. Health / readyz

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"62c4b35d8",...}` |

---

## 5. QA gate

```bash
time bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

| Metric | Result |
|--------|--------|
| Outcome | **KNOWN QA SEED MISMATCH** (not a core Claim boundary failure) |
| Elapsed | **14.62s** |
| Revision | `fiqa-api-00182-rmf` |
| API `total_count` | 52 (post-smoke: 53+) |
| readyz / routes | **PASS** |

**Exact mismatches (same class as prior deploys):**

| Check | Result |
|-------|--------|
| Missing demo names in API page | **张先生**, **王女士** |
| 王女士 Claim Lite tags | Missing **Urgent** or **Manual Handle** |
| 张先生 Premium Review tags | Missing **VIP** or **Retention Risk** |

**Still passing:** Cloud API health, total_count alignment, 陈女士 Add Vehicle Ready, 李先生 Needs Info, 赵先生 Coverage Risk, QA Cloud SQL seed rows, no local JSON fallback.

**Action:** Record only — do **not** treat as Claim boundary / Start Card / highlights failure. Recommend `P19H-3f-2` or dedicated QA seed alignment patch for deploy confidence.

---

## 6. Smoke method

QA Cloud SQL write via same `ingest_*()` functions as deployed revision + Cloud Run API readback.  
Ephemeral smoke cases tagged `demo_name=p19h3f1_deploy_smoke` / `workbench_test=true`.  
Suffix: `3f1_060923`.

---

## 7. Smoke A — random photo only

**Case:** `case_60f6b4f0f1c2` · ext `wm_p19h3f1_photo_3f1_060923`

| Check | Result |
|-------|--------|
| Outcome | `media_unassigned` |
| `service_lane` (API readback) | **`wecom_media_intake`** (not `claim`) |
| Reply contains 【尚未开始事故记录】 | **Yes** |
| Reply contains 我要理赔 | **Yes** |
| Start Card (事故记录已开始) | **No** |
| Formal Claim case for ext | **No** |
| `claim_timeline` / `claim_case_brief` | **None** |
| Display | **`待确认材料 · 未分配微信资料 · 不是正式 case`** |

**Note:** Local `get_case_by_id` immediately after write returned `service_lane=null` (PG read timing); Cloud API GET confirmed `wecom_media_intake`.

**PASS**

---

## 8. Smoke B — random narrative only

**Input:** `昨晚 Costco 被追尾了，后保险杠有点坏。` · ext `wm_p19h3f1_narr_3f1_060923`

| Check | Result |
|-------|--------|
| Formal Claim case created | **No** |
| Holding ack | **Yes** — 【尚未开始事故记录】 |
| `claim_timeline` | **None** |
| `claim_case_brief` | **None** |
| Start Card | **No** |
| Guides 我要理赔 / start recording | **Yes** |

**PASS**

---

## 9. Smoke C — explicit start + Start Card ceremony

**Input:** `我要理赔` · **Case:** `case_ebd97a57af03`

| Check | Result |
|-------|--------|
| Formal Claim case created | **Yes** |
| `service_lane` | **`claim`** |
| Start Card 【事故记录已开始 ✅】 | **Yes** |
| 陈总办公室 | **Yes** |
| 有没有受伤 | **Yes** |
| 不代表已经向保险公司正式报案 | **Yes** |
| Injury quick replies (`menu_payload`) | **Yes** |
| API `claim_timeline` | **Present** (`claim_started`) |
| Forbidden language | **None** |

**PASS** — **Formal Claim creation emits Start Card** ✅

---

## 10. Smoke D — full new customer flow + highlights

**Flow:** 我要理赔 → [没有受伤] → Costco story → photo  
**Case:** `case_e2e677089929`

| Check | Result |
|-------|--------|
| `claim_timeline` types | `claim_started`, `customer_text` ×3, `basics_complete`, `customer_photo` |
| Injury recorded | `customer_text` metadata `quick_reply_key=injury_status` |
| `claim_case_brief` | **Yes** |
| `highlights[]` count | **4** (≤ 5) |
| `highlights_safe` | **Yes** |
| Workbench display | **`Claim · 记录中 · Broker Review pending`** |
| Photo ack 已记到这份事故记录里 | **Yes** |
| `next_best_question` | `请问对方车牌或保险信息拿到了吗？` |
| Forbidden language | **None** |

**Example `highlights[]`:**

```json
[
  {"level": "important", "label": "受伤情况已确认：没有受伤", "kind": "injury"},
  {"level": "received", "label": "已收到 1 张照片", "kind": "evidence"},
  {"level": "received", "label": "事故基本经过已记录", "kind": "basics"},
  {"level": "missing", "label": "还缺对方保险信息", "kind": "missing_info"}
]
```

**PASS**

---

## 11. Smoke E — injury click alone

**Input:** menu `claim_injury_no` with no active Claim · ext `wm_p19h3f1_inj_3f1_060923`

| Check | Result |
|-------|--------|
| Claim case created | **No** |
| Start Card | **No** |
| Holding gate asks 我要理赔 | **Yes** |
| Outcome | `claim_injury_holding_gate` |

**PASS**

---

## 12. Workbench UI result

| Check | Result |
|-------|--------|
| Claim row `case_e2e677089929` lane | **`claim`** |
| Claim display | **`Claim · 记录中 · Broker Review pending`** |
| API `claim_case_brief.highlights` | **4 items** (factual, broker-safe) |
| Media row `case_60f6b4f0f1c2` lane | **`wecom_media_intake`** |
| Media display | **`待确认材料 · 未分配微信资料 · 不是正式 case`** |
| Rows clearly separate | **Yes** |
| Frontend bundle | `重点速览`, `highlights`, `Claim · 记录中`, `待确认材料` |
| Browser drawer visual | **HUMAN-PENDING** — operator can open https://ui-smoky-beta.vercel.app/workbench/unified-intake |

**PASS** (API/PG + bundle strings; live drawer optional)

---

## 13. Add Vehicle result

| Check | Result |
|-------|--------|
| Add-car photo attach | **PASS** — `media_attached_to_case`, lane `add_car`, no `claim_timeline` |

**PASS**

---

## 14. H5 result

| Check | Result |
|-------|--------|
| H5 claim evidence cloud token (local mint) | **403** `invalid_or_expired_task_link` — expected (local `.env.cloudrun` secret ≠ Cloud Run Secret Manager) |
| H5 pytest regression | **PASS** — `test_h5_add_vehicle_photo_flow.py`, `test_p19h3c2_claim_c1_h5_button.py` (23 tests) |

**PASS** (Add Vehicle unaffected; H5 path validated via pytest per prior deploy evidence pattern)

---

## 15. Logs result

Scanned Cloud Run logs (`fiqa-api-00182-rmf`, post-deploy window):

| Finding | Result |
|---------|--------|
| Claim boundary / Start Card / highlights errors | **None** |
| HTTP 500 on inbox/claim paths | **None** |
| Inbox API during smoke | **200** (`/api/inbox/cases`, case detail GETs) |
| Qdrant / Redis / embedding warmup ERROR | Expected optional (intake_core readiness unaffected) |

---

## 16. Start Card ceremony acceptance

| Rule | Result |
|------|--------|
| Formal Claim creation emits Start Card | **Yes** (Smoke C) |
| No Start Card means no customer-facing formal Claim started | **Yes** (Smokes A, B, E) |

---

## 17. Highlights acceptance

| Rule | Result |
|------|--------|
| `highlights[]` exists on formal Claim brief | **Yes** |
| Max 5 items | **Yes** (4 observed) |
| Factual only — injury / photo / basics / gaps | **Yes** |
| No fault / coverage / filed language | **Yes** (`brief_highlights_are_broker_safe`) |
| UI shows 重点速览 above 还缺什么 (bundle) | **Yes** |

---

## 18. Constraints honored

| Constraint | Status |
|------------|--------|
| No new product features this prompt | ✅ deploy + smoke only |
| No schema migration / new DB table | ✅ |
| No OCR / ASR / damage AI | ✅ |
| No fault / liability / coverage judgment | ✅ |
| No carrier filing | ✅ |
| No LLM brief | ✅ |
| No True End Card | ✅ |
| No large UI refactor | ✅ |

---

## 19. Known limitations

- QA gate seed/demo mismatch: missing 张先生 / 王女士; 王女士 / 张先生 tag expectations not met on current API page
- Injury timeline stored as `customer_text` + `quick_reply_key=injury_status`, not separate `event_type=injury`
- H5 cloud token from local mint returns 403 (use pytest or prod-minted link for live H5)
- Workbench list endpoint does not inline `claim_display_status`; UI computes from lane + enrichment fields
- Browser drawer visual not automated this run (HUMAN-PENDING)

---

## 20. Next recommended prompt

1. **P19H-3f-2 True End Card on Broker Done**  
2. **QA seed/demo alignment patch** — if seed mismatch blocks future deploy confidence

---

## 21. GO / HOLD

**GO** — `62c4b35` deployed; health/readyz pass; Start Card ceremony live; highlights generated and API/bundle-visible; random photo/narrative/injury-alone held at boundary; full new-customer flow produces timeline + brief + highlights; Add Vehicle/H5 regressions pass; QA gate seed mismatch recorded as known limitation only.

**STOP**
