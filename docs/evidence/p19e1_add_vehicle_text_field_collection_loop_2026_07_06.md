# P19E-1 — Add Vehicle Text Field Collection Loop

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Prerequisite:** P19E-0 recon (`262bcbd`), P19D-4B.1 (`99a1531`, `32cfdbc`)

---

## Summary

Implemented Spark-style Phase 2 text collection loop for Add Vehicle:

1. Photo completion WeCom message reframed as **Stage Complete S1** (not End Card)
2. H5 success page uses Phase 1 complete + total progress framing
3. WeCom text messages after H5 photo complete extract `delivery_date`, `zip`, `phone`
4. Partial Phase 2 replies send **Current Step Card** with progress
5. All 3 fields complete sends **Stage Complete S2** + broker handoff copy
6. Case JSON updated: `collected_fields`, `still_needed_fields`, `guided_workflow_state`, `add_vehicle_phase`, `known_facts`

**No deploy.** **No OCR.** **No schema migration.** **No Cloud config/callback changes.**

---

## Commits

| Commit | Message |
|--------|---------|
| `262bcbd` | docs: add P19E binary step model recon |
| _(this sprint)_ | feat: add Add Vehicle text field collection loop |

---

## Changed Files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/reply.py` | S1/S2/Current Step Card copy |
| `services/fiqa_api/wecom/add_vehicle_phase2.py` | **NEW** — Phase 2 ingest + routing helpers |
| `services/fiqa_api/wecom/slice.py` | Phase 2 routing before draft merge |
| `services/fiqa_api/wecom/identity.py` | Enhanced date/ZIP extractors (Chinese + relative) |
| `services/fiqa_api/inbox_triage/case_store.py` | `update_add_vehicle_workflow_state`, `known_facts` merge on append |
| `services/fiqa_api/db/service_record_repository.py` | Hydrate `guided_workflow_state`, `add_vehicle_phase` |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | Phase 1 complete H5 copy |
| `tests/test_p19e1_add_vehicle_text_field_collection.py` | **NEW** — P19E-1 acceptance tests |
| `tests/test_p19d4b*.py`, `tests/test_wecom_reply.py` | S1 copy assertion updates |

---

## Phase 1 — Stage Complete S1 (WeCom)

Replaces ambiguous「照片已收到 ✅」with:

```text
【第 1 阶段完成 ✅ · 照片资料】

已收到：
✓ VIN 照片
✓ 行驶证照片
✓ 保险卡照片（或 ○ 保险卡 — 可稍后补）

──────────
【下一步 · 第 2 步：补充文字信息】

请直接在本聊天打字发送：
1. 提车日期（例：7月10日）
2. 停放 ZIP（例：92705）
3. 联系电话

陈总会人工查看并确认，不会自动修改您的保单。
```

Internal function name `build_h5_photo_phase_complete_reply` retained; comments/evidence use Stage Complete S1.

---

## H5 Final Page Copy

```text
第 1 阶段完成 ✅
照片上传已完成

已收到：✓ VIN / ✓ 行驶证 / ✓ or ○ 保险卡

总进度：① 上传照片 ✓  →  ② 补充文字  →  ③ 陈总确认

请点「返回微信」。回到聊天后，您会收到第 2 步指引。
```

Forbidden phrases not used: 加车已完成, VIN 已识别, OCR, policy updated.

---

## Field Extraction Rules (rule-based, no LLM)

| Field | Rules |
|-------|-------|
| `delivery_date` | `YYYY-MM-DD`, `M/D`, `7月10日`, relative pickup (`明天`, `下周一提车`) via `date_normalization` |
| `zip` | 5-digit US ZIP with marker (`ZIP 92705`) or standalone (`停在92705`) |
| `phone` | US 10-digit formats; conservative — ambiguous text not stored |

Examples supported:

- `7月10号提车，ZIP 92705，电话 949-123-4567`
- `提车日期是7/10，停在92705，电话9491234567`
- `ZIP 92705` / `电话是949-555-1212` / `提车明天` / `下周一提车`

Values stored in `known_facts` + `collected_fields` list entries.

---

## Phase 2 State Model

| Field | Values |
|-------|--------|
| `add_vehicle_phase` | `phase_2_text_in_progress` → `phase_3_broker_review` |
| `guided_workflow_state` | `collecting_text_fields` → `ready_for_broker_review` |
| `still_needed_fields` | Subset of `{delivery_date, zip, phone}` only during Phase 2 |
| `h5_photo_flow_state.s2_stage_complete_sent_at` | S2 dedup timestamp |

---

## Phase 2 Partial Reply (Current Step Card)

```text
【加车资料 · 第 2 步进行中】

已收到：
✓ 提车日期 — 7月10日
✓ 停放 ZIP — 92705

还差 1 项：
○ 联系电话 — 请直接打字回复
```

---

## Stage Complete S2 + Broker Handoff

```text
【第 2 阶段完成 ✅ · 文字信息】
…
【下一步 · 第 3 步：陈总人工确认】
资料已基本收齐，已转陈总审核。
```

Uses「资料已基本收齐」not「全部资料已收齐». S2 deduped via `s2_stage_complete_sent_at`.

---

## Routing

1. Explicit restart → new H5 flow (P19D-4B.1 unchanged)
2. Active add_car + photo complete + phase2 incomplete + field text → Phase 2 handler
3. High-confidence `我要加车` after Phase 1 → S1 follow-up (not new H5)
4. Premium / Claim / Coverage lanes unchanged

---

## Workbench Visibility

- `collected_fields` / `still_needed_fields` / `known_facts` exposed via existing case API
- `guided_workflow_state` and `add_vehicle_phase` hydrated from JSON extra
- **Limitation:** No new Workbench phase progress UI panel in this sprint — broker sees fields via existing Customer / Missing Items views

---

## Tests / Build

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19e1_add_vehicle_text_field_collection.py -q
# + full regression suites (H5, WeCom, workbench attachment) — all PASS

cd ui && npm run build  # PASS
bash scripts/check_chen_kui_demo_environment.sh --cloud-api  # PASS
```

---

## Constraints Verified

| Constraint | Status |
|------------|--------|
| No OCR / LLM / vision | ✅ |
| No schema migration | ✅ |
| No Cloud SQL / VPC / NAT / callback change | ✅ |
| No Neon | ✅ |
| No public GCS URL | ✅ |
| No full external_userid in logs/docs | ✅ |
| No token/access token in evidence | ✅ |
| P19D-4A H5 photo flow preserved | ✅ |
| P19D-4B.1 restart preserved | ✅ |
| No deploy | ✅ STOP |

---

## Known Limitations

- `primary_driver` / `year` / `make_model` not collected in H5 Phase 2 path (by design — 3 fields only)
- Relative dates stored as ISO when safely resolved; otherwise raw phrase
- Workbench phase label UI deferred
- Live phone smoke requires deploy — not run this sprint

---

## GO / HOLD

| Gate | Result |
|------|--------|
| Local tests + build | **PASS** |
| QA gate (cloud-api) | **PASS** |
| Deploy | **HOLD** — code not pushed/deployed |
| Live phone smoke | **HOLD** — deploy first |

**Recommendation:** Deploy to Cloud Run + Vercel, then run 15-min phone smoke: H5 三步 → S1 → 打字 3 项 → S2 → Workbench verify.
