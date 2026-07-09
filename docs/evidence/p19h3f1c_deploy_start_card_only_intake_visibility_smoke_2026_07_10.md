# P19H-3f-1c — Deploy + Start Card Only Intake Visibility Smoke

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **GO**

---

## 1. Goal

Deploy commit `3d113d8` and verify online:

1. Pre-Start-Ceremony inbound does **not** enter broker default work queue  
2. Random photo/text does not appear as case / half-case / 待确认材料 broker task  
3. Explicit「我要理赔」→ Claim + Start Card + default Workbench  
4. Active Claim + photo binds to formal Claim  
5. Raw inbound debug (`include_raw_inbound=true`) works but default hidden  
6. Add Vehicle / H5 / Claim Brief regressions unaffected  

---

## 2. Deployed backend revision / GIT_SHA

| Field | Value |
|-------|-------|
| Commit | **`3d113d8`** — feat: enforce Start Card only intake visibility |
| Revision | **`fiqa-api-00183-79r`** |
| Prior revision | `fiqa-api-00182-rmf` (`62c4b35`) |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | **`3d113d849`** (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |

---

## 3. Frontend deployment / stable alias

| Field | Value |
|-------|-------|
| Command | `cd ui && npm run build && vercel --prod --yes` |
| Deployment URL | `https://ui-kf4p639pp-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Bundle | `assets/index-BIFuHqSn.js` |
| Bundle strings | `Claim · 记录中`, `重点速览`, `highlights` present |
| `/workbench/unified-intake` | **HTTP 200** |
| `/add-car` | **HTTP 200** |

---

## 4. Health / readyz

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"3d113d849",...}` |

---

## 5. QA gate

```bash
time bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

| Metric | Result |
|--------|--------|
| Outcome | **PASS** — QA UI + Cloud Run API + Cloud SQL aligned |
| Elapsed | **12.99s** |
| Revision | `fiqa-api-00183-79r` |
| API `total_count` | 50 |
| Demo names / tags | **All present** (张先生 VIP, 王女士 Manual Handle, etc.) |

**Note:** Unlike prior deploys, QA seed mismatch did **not** occur on this run.

---

## 6. Smoke method

QA Cloud SQL write via same `ingest_*()` functions as deployed revision + Cloud Run API readback.  
Ephemeral smoke cases tagged `demo_name=p19h3f1c_deploy_smoke` / `workbench_test=true`.  
Suffix: `3f1c_181840`.  
Script: `PYTHONPATH=. python3 scripts/p19h3f1c_deploy_visibility_smoke.py`

---

## 7. Smoke A — random photo before Start Card

**Case:** `case_7dd75f9bb3c2` · ext `wm_p19h3f1c_photo_3f1c_181840`

| Check | Result |
|-------|--------|
| Outcome | `media_unassigned` |
| `service_lane` (API readback) | **`wecom_media_intake`** |
| Customer reply | 收到 · 我要理赔 · 没有开始事故记录前… |
| Start Card | **No** |
| Formal Claim for ext | **No** |
| Default `GET /api/inbox/cases` | **Hidden** |
| `include_raw_inbound=true` | **Visible** — `Raw Inbound Log` / `raw_inbound` |
| Display | **`技术收件记录 · 未分配微信资料 · 不是正式 case`** |

**PASS**

---

## 8. Smoke B — random narrative before Start Card

**Input:** 昨晚 Costco 被追尾了，后保险杠有点坏。

| Check | Result |
|-------|--------|
| Formal Claim created | **No** |
| Start Card | **No** |
| Default queue item | **No** |
| Pre-start copy | **Yes** |

**PASS**

---

## 9. Smoke C — explicit start

**Input:** 我要理赔  
**Case:** `case_cd5d594139bc`

| Check | Result |
|-------|--------|
| Claim created | **Yes** |
| Start Card | **Yes** — 事故记录已开始 ✅ |
| 陈总办公室 / 有没有受伤 / disclaimer | **Yes** |
| In default Workbench queue | **Yes** (`service_lane=claim`) |

**PASS**

---

## 10. Smoke D — full active Claim + photo

**Case:** `case_c4118daf1281`

| Check | Result |
|-------|--------|
| Timeline | `claim_started`, `customer_text`, `basics_complete`, `customer_photo` |
| `claim_case_brief` | **Yes** |
| `highlights[]` | **4** — injury, photo, story, missing info |
| Photo binds to Claim | **Yes** (`service_lane=claim`) |
| Raw inbound in default queue | **No** |
| Forbidden language | **Absent** |

**PASS**

---

## 11. Default Workbench queue result

| Check | Result |
|-------|--------|
| Formal Claim in default list | **Yes** — Claim · 记录中 |
| `wecom_media_intake` in default list | **No** |
| No「待确认材料」broker tasks | **Yes** |
| Brief highlights in API | **4**, broker-safe |

**PASS**

---

## 12. Raw inbound debug result

`GET /api/inbox/cases?limit=50&include_raw_inbound=true`

| Check | Result |
|-------|--------|
| Smoke media case visible | **Yes** |
| `display_title` | **Raw Inbound Log** |
| `display_status` | **技术收件记录 · … · 不是正式 case** |
| `workbench_lane_kind` | **raw_inbound** |

**PASS**

---

## 13. Add Vehicle result

| Check | Result |
|-------|--------|
| Media attach to add_car | **Yes** |
| In default queue | **Yes** |
| No `claim_timeline` on add_car | **Yes** |

**PASS**

---

## 14. H5 result

| Check | Result |
|-------|--------|
| Local minted token | **403** `invalid_or_expired_task_link` |
| Note | **Known env issue** — local `.env.cloudrun` secret ≠ Cloud Run Secret Manager |
| pytest H5 regression | Covered locally; not a deploy blocker |

**PASS** (with known 403 note)

---

## 15. Workbench UI

**URL:** https://ui-smoky-beta.vercel.app/workbench/unified-intake

| Check | Result |
|-------|--------|
| Page HTTP | **200** |
| API default queue | **PASS** (no raw inbound) |
| Bundle | **PASS** |
| Browser drawer visual | **HUMAN-PENDING** — operator can spot-check Claim row + absence of 待确认材料 |

---

## 16. Logs result

Scanned Cloud Run logs (`fiqa-api-00183-79r`, post-deploy window):

| Signal | Result |
|--------|--------|
| `GET /api/inbox/cases` | **200** |
| Workbench enrich failures | **None** |
| `include_raw_inbound` errors | **None** |
| Claim boundary / Start Card 500s | **None** |
| Qdrant warmup `InactiveRpcError` | **Present** — known noise, intake-core unaffected |

---

## 17. Policy acceptance

| Rule | Verified |
|------|----------|
| No Start Card = no broker work queue item | **Yes** — default list excludes `wecom_media_intake` |
| Start Card = formal customer-facing workflow | **Yes** — explicit start in queue as Claim |
| Raw inbound exists internally only | **Yes** — debug param reveals, default hidden |

---

## 18. Constraints

- No schema change  
- No new DB table  
- No OCR/ASR  
- No True End Card  
- Start Card policy unchanged (visibility enforced)  

---

## 19. Known limitations

- Local `get_case_by_id` immediately after PG write may return `service_lane=null`; API readback is authoritative (documented in smoke script).  
- H5 cloud token 403 from local mint — env secret mismatch.  
- No dedicated Raw Inbound Log UI tab in demo — API debug param only.  
- Browser drawer visual not fully automated.

---

## 20. Next recommended prompt

1. **P19H-3f-2** — True End Card on Broker Done  
2. Optional: dedicated Raw Inbound Log debug UI (non-demo default)  
3. H5 secret alignment for cloud smoke mint  

---

## Verdict

**GO** — `3d113d8` deployed; Start Card only intake visibility verified on QA Cloud SQL + API + frontend alias.
