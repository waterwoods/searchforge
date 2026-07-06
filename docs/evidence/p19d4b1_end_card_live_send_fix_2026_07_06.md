# P19D-4B.1 End Card Live Send Fix — Log Investigation

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **ROOT CAUSE FOUND** · **FIX DEPLOYED** · **Phone End Card retest PENDING**

---

## Deploy (End Card fix)

| Field | Value |
|-------|-------|
| Commit | `32cfdbc` — fix: persist WeCom open_kf_id for H5 End Card send |
| Prior revision | `fiqa-api-00158-qnr` (`99a1531`) |
| **New revision** | **`fiqa-api-00159-6kz`** |
| QA gate | **PASS** |
| Frontend | Skipped (backend-only) |

---

## Andy reported issue

Scenario B partial PASS:
- `重新加车` → new Start Card ✅
- H5 Step 1 VIN → uploads complete ✅

Scenario B FAIL:
- After H5「返回微信」→ **no End Card** in WeChat ❌

---

## Log window (16:33–16:36 PT ≈ 23:33–23:36 UTC)

| Time (UTC) | Event |
|------------|--------|
| 23:33:04 | Customer text `重新加车` normalized |
| 23:33:05 | `wecom_draft_case_start_click_v1` **created** `case_36cc65a3f650` with `external_userid` bound at create |
| 23:33:05 | Start Card sent (`start_card_triggered_v1`) |
| 23:33:39 | H5 upload `vin_photo` OK |
| 23:33:47 | H5 upload `registration_photo` OK |
| 23:33:52–55 | H5 skip/upload insurance → **flow_complete** |
| 23:33:52–34:03 | **`h5_flow_complete_notify_skipped_v1`** ×4 — reason **`no_wecom_channel_binding`** |

**Not observed:**
- `h5_flow_complete_notify_sent_v1` ❌
- `h5_flow_complete_notify_failed_v1` ❌
- `outbox_dedup` ❌
- Send to old case ❌

**Conclusion:** Flow reached `flow_complete=true` on **new case** `case_36cc65a3f650`, but End Card send was skipped because case read path lacked **`wecom_open_kf_id`**.

---

## Root cause

Postgres `extra` JSONB round-trip was incomplete:

| Field | `_build_extra` (write) | `_hydrate_extra_pilot_fields` (read) |
|-------|------------------------|--------------------------------------|
| `wecom_external_userid` | ✅ | ✅ |
| `wecom_open_kf_id` | ❌ missing | ❌ missing |
| `h5_photo_flow_state` | ❌ missing | ❌ missing |

`bind_case_channel_identity()` set both fields on the in-memory case and persisted via `persist_case_append`, but **`wecom_open_kf_id` was dropped** on Postgres write. H5 upload completion calls `get_case_for_read()` → End Card checks:

```python
if not external_userid or not open_kf_id:
    reason = "no_wecom_channel_binding"
```

Local JSON tests passed because full case document retains all fields; **Cloud SQL production path did not**.

---

## Fix

**File:** `services/fiqa_api/db/service_record_repository.py`

1. Add `wecom_open_kf_id` and `h5_photo_flow_state` to `_build_extra` keys
2. Hydrate both in `_hydrate_extra_pilot_fields`
3. `persist_case_append`: merge new extra patch with existing DB `extra` (avoid wiping pilot fields on partial updates)

**Tests:**
- `tests/test_service_record_wecom_extra.py` — build/hydrate round-trip
- `tests/test_wecom_h5_photo_end_card.py` — missing `open_kf_id` guard

---

## Guardrails

| Item | Status |
|------|--------|
| OCR / LLM | ❌ |
| Schema migration | ❌ |
| Cloud callback/VPC/NAT/Secret change | ❌ |
| Public URL | ❌ |
| Full external_userid in doc | ❌ |
| Neon | ❌ |

---

## Phone retest after deploy

1. Send `重新加车` → new Start Card
2. Complete H5 photo flow
3. Tap「返回微信」
4. Expect End Card within ~10s: `【加车资料】照片已收到 ✅` + text field checklist

Reply: **`4B.1-B endcard done`**

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Fix + tests | **GO** |
| Deploy + phone End Card smoke | **PENDING** — revision `fiqa-api-00159-6kz` live |

**STOP**
