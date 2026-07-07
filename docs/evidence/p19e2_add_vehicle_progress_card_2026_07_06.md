# P19E-2 — Add Vehicle Progress Card Evidence

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Type:** Local dev + deploy + live smoke prep  
**Verdict:** **DEPLOY PASS** · **QA gate PASS** · **Andy live phone smoke PENDING**

---

## Commits (pushed)

| Commit | Message |
|--------|---------|
| `48761e7` | docs: add P19E Add Vehicle progress card recon |
| `67a57cc` | feat: add Add Vehicle progress card |

Pushed: `git push origin sprint/p16-trust-layer` (`c66305a..67a57cc`)

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/add_vehicle_progress.py` | **NEW** — case selection, phase derive, routing gate, H5 resume link |
| `services/fiqa_api/wecom/intent.py` | Status/progress inquiry markers + vague greeting helpers |
| `services/fiqa_api/wecom/reply.py` | `build_add_vehicle_progress_card()` — 5 customer states |
| `services/fiqa_api/wecom/slice.py` | Progress Card route before draft merge / duplicate H5 Start |
| `services/fiqa_api/wecom/add_vehicle_phase2.py` | Vague/status-only messages defer to Progress Card |
| `tests/test_p19e2_add_vehicle_progress_card.py` | **NEW** — 26 tests |
| `tests/test_p19e1_add_vehicle_text_field_collection.py` | Expect Progress Card after Phase 1 for「我要加车」 |
| `tests/test_wecom_active_case.py` |「你好」with open add_car → Progress Card |

---

## Progress Card

| Item | Value |
|------|-------|
| External title | **【加车资料进度】** |
| Internal name | `AddVehicleProgressCard` |
| Channel | WeCom text / msgmenu (Phase 1 resume button) |

---

## Status intent phrases

**Chinese:** 你好, 继续, 进度, 查进度, 还差什么, 我现在到哪了, 我提交了吗, 现在怎么样, 资料齐了吗, 还有什么要补, 下一步是什么, 已提交, 完成了吗, 好了吗, 交了吗, 还没完, 继续办, 继续上传, 缺什么, 到哪了, 哪一步

**English:** status, progress, continue, what is next, what else do you need, did i submit, where am i

**Vague greeting (with active case):** 你好, 您好, 在吗, hello, hi there, etc.

**Exclusions:** Phase 2 field text wins; 重新加车 wins; claim/premium/coverage lanes win.

---

## State-to-card mapping

| State | Card |
|-------|------|
| A — No active case | Guided menu (unchanged) |
| B — Phase 1 photos in progress | ▶️ 第 1 步 + missing slots +「继续上传照片」button |
| C — Phase 1 done, Phase 2 empty | ▶️ 第 2 步 + missing text fields |
| D — Phase 2 partial | ▶️ 第 2 步 + collected values + missing fields |
| E — Phase 2 complete / broker review | ▶️ 第 3 步 — no action needed |
| F — Broker done / confirmed | ✅ 第 3 步 陈总已处理 |

Derived from: `h5_photo_flow_state`, attachments/slots, `collected_fields`, `guided_workflow_state`, `add_vehicle_phase`, `broker_confirmed_at` — **no schema migration**.

---

## Routing priority (inserted)

1. Start Card clicks  
2. Premium / Claim / Coverage minimal lanes  
3. Phase 2 text collection (extractable fields)  
4. **NEW:** Status inquiry OR vague greeting OR「我要加车」with open case → Progress Card  
5. Draft merge / add_car H5 Start (restart only when photos complete)  
6. Generic greeting menu (no active add_car)

---

## H5 resume link (Phase 1)

- Reuses `mint_h5_add_vehicle_photo_flow_link()` for same case — no new case  
- msgmenu view button「继续上传照片」+「联系经纪人」  
- Long URL not shown in main copy; tail:「如果按钮打不开，请回复：链接」  
- If token mint fails: fallback text「请回复：重新加车…」

---

## Read path

- `list_all_cases_for_read` + `get_case_for_read` only  
- Newest `updated_at` when multiple open add_car cases  
- Multi-car tail:「如果您同时办理多台车，请联系陈总。」

---

## Tests / build

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19e1_*.py tests/test_p19e2_*.py -q
PYTHONPATH=. python3 -m pytest tests/test_wecom_*.py tests/test_h5_*.py tests/test_workbench_attachment_api.py -q
cd ui && npm run build
```

**Result:** PASS (246 tests in combined WeCom/H5/P19E run)

---

## QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result:** PASS — Cloud SQL `caseiq @ 10.73.0.3`, Neon not QA truth

---

## Constraints verified

| Constraint | Status |
|------------|--------|
| No OCR / LLM / vision | ✅ |
| No schema migration | ✅ |
| No Cloud config / callback change | ✅ |
| No public URL / GCS expose | ✅ |
| No Neon as QA truth | ✅ |
| No 小程序 / H5 Task Home / H5 form | ✅ |
| No deploy (local loop) | ✅ (superseded by deploy below) |
| P19E-1 Phase 2 preserved | ✅ |
| P19E-1.5 Postgres read facade preserved | ✅ |
| P19D H5 / restart preserved | ✅ |

---

## Known limitations

- MVP shows **newest** open add_car case only (no case picker UI)  
- Repeated「进度」within minutes returns same card (no dedup short version yet — V1.1)  
- Broker-requested re-upload (Recovery Card) not in scope  
- Progress Card does not emit timeline event `progress_card_sent` (optional V1.1)

---

## GO / HOLD (local)

| Gate | Verdict |
|------|---------|
| Local tests + build | **GO** |
| QA gate (pre-deploy) | **GO** |

---

## Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Project | `optimal-disk-472305-e2` |
| Service | `fiqa-api` |
| Region | `us-west1` |
| **Revision (prior)** | `fiqa-api-00162-qhp` |
| **Revision (this deploy)** | **`fiqa-api-00163-w4k`** |
| URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| GIT_SHA | `67a57ccfd` |
| Deploy time (UTC) | 2026-07-07 ~03:17 UTC |
| `/health/live` | 200 |
| `/readyz` | 200 (`intake_core_readiness: true`) |
| `/healthz` | 404 at edge (expected — use `/health/live`) |
| `WECOM_SLICE_SEND_REPLY` | `1` |
| `H5_TASK_TOKEN_SECRET` | Secret Manager `fiqa-h5-task-token-secret` — unchanged |
| DB secret | `fiqa-service-record-database-url-cloudsql-private` — unchanged |
| Cloud SQL | `caseiq` @ `10.73.0.3` — unchanged |
| VPC / NAT / WeCom callback | unchanged |

---

## Frontend deploy

| Field | Value |
|-------|-------|
| **Action** | **Skipped** — P19E-2 is backend WeCom routing only |
| **Alias** | `https://ui-smoky-beta.vercel.app` (unchanged) |
| Rationale | No `ui/` changes in `67a57cc` |

---

## Post-deploy QA gate

`bash scripts/check_chen_kui_demo_environment.sh --cloud-api` → **PASS** (revision `fiqa-api-00163-w4k`)

---

## Pre-smoke log check

Revision `fiqa-api-00163-w4k` startup logs reviewed (80 lines):

- **No** import/syntax errors
- **No** Postgres read facade errors
- **No** WeCom route exceptions
- **No** H5 token generation errors at startup
- Expected optional warnings only: embedding warmup deferred, Qdrant/Redis optional, bm25 optional

---

## Andy live phone smoke checklist

**Revision under test:** `fiqa-api-00163-w4k` · **GIT_SHA:** `67a57cc`

### Smoke A — Existing active add_car case

If Andy already has an active add_car case in WeCom:

| # | Send | Expected |
|---|------|----------|
| A1 | `你好` | Reply contains **【加车资料进度】** — not generic main menu. State matches case: Phase 1 → 第 1 步; Phase 2 → 第 2 步; broker review → 第 3 步 |
| A2 | `进度` | Same Progress Card as A1 |
| A3 | `还差什么` | Progress Card lists missing items OR says no action needed (Phase 3) |
| A4 | `7月10号提车，zip 92705，电话2031234567` | Phase 2 extractor wins — **not** Progress Card. If complete: **【第 2 阶段完成 ✅ · 文字信息】** + 第 3 步 broker confirm |
| A5 | `我要理赔` | Claim lane — **not** Add Vehicle Progress Card |
| A6 | `重新加车` | New H5 Start Card / new flow — **not** Progress Card |

### Smoke B — No active add_car case

| # | Send | Expected |
|---|------|----------|
| B1 | `你好` | Normal greeting / guided menu |
| B2 | `进度` | Normal menu or no-active-case behavior — **not** fake progress |

### Smoke C — Phase 1 incomplete (new flow)

| # | Step | Expected |
|---|------|----------|
| C1 | Send `重新加车` | New Start Card |
| C2 | Start flow but leave a photo missing | — |
| C3 | Return to WeCom, send `继续` | **【加车资料进度】** · 第 1 步 · button **继续上传照片** · same case (not new) |

### Live smoke result

| Item | Status |
|------|--------|
| Andy phone smoke executed | **PENDING** |
| Screenshots / exact messages | _(fill after Andy retest)_ |

---

## GO / HOLD (deploy + live)

| Gate | Verdict |
|------|---------|
| Deploy | **GO** |
| Post-deploy QA | **GO** |
| Logs pre-smoke | **GO** |
| Andy live phone smoke | **PENDING** |

**Recommendation:** Andy run Smoke A–C on WeCom; report exact messages + PASS/HOLD per row.
