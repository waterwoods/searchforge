# P19D-4B Fix — Start Card / End Card Live Debug

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Verdict:** **FIX PASS (local)** · **Deploy HOLD** — await approval

---

## Andy reported issues

| # | Issue | Severity |
|---|--------|----------|
| 1 | Start Card shows button **and** long H5 URL — feels like two entrances | P1 UX |
| 2 | H5 opens on already-completed 3/3 state — user confused old vs new flow | P0 UX |
| 3 | No End Card after「返回微信」| P0 acceptance |

Greeting menu improvement: **confirmed good** by Andy.

---

## Log investigation (12:24–12:26 PT ≈ 19:24–19:26 UTC)

| Time (UTC) | Event |
|------------|--------|
| 19:24:36 | Andy sends `你好` → greeting menu |
| 19:24:46 | Andy taps `【加车资料补充】` (menu_id `add_vehicle`) |
| 19:24:47 | `attached_existing` → **`case_5e2da3c42e43`** |
| 19:24:47 | Start Card sent (`h5_task_link_masked`) |
| 19:24:48 | `wecom_slice_reply_sent_v1` |

**No H5 upload POST** in Andy's session after 19:24.  
**No `h5_flow_complete_notify_sent_v1`** for `case_5e2da3c42e43`.

Earlier same day (18:49): Andy also got Start Card for same `case_5e2da3c42e43`.

`case_5e2da3c42e43` already had **4 H5 attachments** (completed photo flow from prior sessions).

---

## Root cause summary

### Issue 1 — Start Card long URL

**Cause:** `build_h5_vin_start_card_payload()` put full H5 URL in `tail_content` by design (P19D-3 fallback). In WeCom msgmenu with view button, this reads as a **second main entrance**.

**Not a bug** — intentional fallback over-exposed in card UI.

### Issue 2 — H5 shows 3/3 completed

**Cause:** `find_open_add_car_case_by_external_userid()` reuses open add_car case without checking photo-flow completion. Start Card minted **new token for same completed case** → H5 GET returns `flow_complete=true` immediately.

**Contributing factors:**
- (a) Reused completed case — **yes**
- (b) Old token — possible if user re-tapped same chat link
- (c) Case already complete — **yes**
- (d) H5 cache — not primary
- (e) No exclusion of completed photo flow — **yes, root bug**

### Issue 3 — End Card missing

**Cause:** **Not a send API failure during Andy's test.**

Andy opened **already-completed** flow → no `not complete → complete` transition → **End Card never triggered**.

Additional factors for historical completions:
- End Card feature deployed in `c57afbd`; flows completed **before** deploy may lack `end_card_sent_at`
- `create_or_attach_draft_case_for_start_click` on `attached_existing` did **not** refresh `wecom_open_kf_id` (fixed in this patch)

**Dedup:** Not the issue in Andy's session (no new completion).  
**Channel binding:** Andy's case has WeCom binding (Start Card path uses `wmtLevSg…` + `wktLevSg…`).

---

## Fixes made

### A. Start Card entry convergence

- msgmenu `tail_content` no longer shows full URL
- New tail: `如果按钮打不开，请回复：链接`
- View button URL unchanged (single technical entry)
- Plain-text fallback (`build_h5_vin_start_text_fallback`) still includes URL when msgmenu unavailable

### B. Completed flow handling

- `h5_photo_flow_is_complete(case)` helper
- `_build_add_car_h5_start_menu()`: if photo flow complete → send **follow-up text** (End Card copy) instead of new H5 Start Card
- Best-effort `try_send_h5_photo_flow_end_card()` on follow-up (sends if never sent; dedup if already sent)
- `wants_restart_add_car_photo_flow()` — explicit `重新加车` etc. creates **new** draft case
- `create_or_attach_draft_case_for_start_click()`: refresh `wecom_open_kf_id` on attach
- H5 success page: **「此照片上传流程已完成。」** + restart hint **「重新加车」**

### C. End Card

- No change to send-on-transition logic (correct)
- Follow-up path now **re-attempts** End Card for completed cases where it was never sent (e.g. pre-4B completions)

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/reply.py` | Hide URL in Start Card tail |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | `h5_photo_flow_is_complete`, restart markers |
| `services/fiqa_api/wecom/slice.py` | Follow-up vs Start Card routing |
| `services/fiqa_api/wecom/active_case_bridge.py` | Channel bind on attach; restart new case |
| `ui/src/pages/H5SingleSlotUploadPage.tsx` | Completed-state copy |
| `ui/src/pages/h5SingleSlotUpload.static.test.mjs` | Static assertions |
| `tests/test_p19d4b_completion_ux_fix.py` | **New** |
| `tests/test_wecom_reply.py` | Start Card tail assertions |
| `tests/test_wecom_h5_vin_start_card.py` | URL not in tail |
| `tests/test_wecom_active_case.py` | Outcome expectation |

---

## Start Card copy — before / after

**Before tail:**
```
…陈总会人工审核…

如果按钮打不开，请复制链接在微信中打开：
https://ui-smoky-beta.vercel.app/task/upload/h5t1.…（长 URL）
```

**After tail:**
```
…陈总会人工审核…

如果按钮打不开，请回复：链接
```

---

## Tests / build / QA

| Suite | Result |
|-------|--------|
| H5 + end card + P19D-4B fix | PASS |
| WeCom regression | PASS |
| P19A/B guardrail | PASS |
| `npm run build` + static | PASS |
| QA gate (pre-deploy, current revision) | PASS |

---

## Deploy

**Not deployed** — awaiting explicit approval.

After deploy, Andy should retest:
1. `你好` → `【加车资料补充】` on **completed** case → expect **follow-up text**, not H5 Start Card
2. Fresh `我要加车` on **incomplete** case → Start Card with button only (no URL in tail)
3. Complete 3 photos → End Card within ~10s
4. Re-open H5 link → completed page with「此照片上传流程已完成」

---

## Guardrails

| Item | Status |
|------|--------|
| OCR | ❌ |
| Schema migration | ❌ |
| Cloud callback/VPC/NAT | ❌ |
| Public URL in customer copy | ❌ (URL removed from card tail) |
| Full external_userid in evidence | ❌ |

---

## GO / HOLD

| Gate | Verdict |
|------|---------|
| Local fix + tests | **GO** |
| Deploy + Andy re-smoke | **HOLD** |
