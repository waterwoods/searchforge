# P19M-0 — H5 to Mini Program Mapping

**Date:** 2026-07-10  
**Parent SSOT:** `p19m0_unified_claim_mini_program_architecture_v1_2026_07_10.md`  
**Status:** DRAFT — architecture freeze only

---

## 1. Feature-by-Feature Mapping

| # | Existing H5 capability | Current implementation | Mini Program equivalent | Reuse? | Adapt? | Replace? | Retire? | Prototype priority |
|---|------------------------|------------------------|-------------------------|--------|--------|----------|---------|-------------------|
| 1 | Task token auth | `h5_task_token.py` — `h5t1.*`, `verify_h5_task_token()`, `FLOW_CLAIM_INTAKE_FORM`, 72h TTL | MP launch query param + optional wx session | ✓ | ✓ bind openid later | | | P0 |
| 2 | Task deep link | `mint_h5_claim_intake_form_link()` → `/task/claim/{token}` | WeCom mini program card `path?task_token=` | | ✓ | ✓ card vs URL | H5 primary CTA | P0 |
| 3 | Dashboard / Task Home | `H5ClaimIntakePage.tsx` `dashboard_summary`; `_build_dashboard_summary()` in `h5_task_intake.py` | MP Task Home page | ✓ API | ✓ UI | ✓ React → WXML | | P0 |
| 4 | Wizard stepper | `CLAIM_INTAKE_STEPS` + `H5ClaimIntakePage` steps | MP Guided Step pages (one screen per step) | ✓ semantics | ✓ UI | ✓ | | P0 |
| 5 | Received / missing | `get_claim_missing_items()`, `_dashboard_received_items()` | Task Home + Missing Items screen | ✓ | ✓ layout | | | P0 |
| 6 | Injury step | PATCH step=`injury`, fields `anyone_injured` | MP radio step | ✓ | | | | P0 |
| 7 | Time/location | PATCH step=`time_location` | MP form step | ✓ | | | | P1 |
| 8 | Story | PATCH step=`story`, `accident_description` | MP textarea / voice | ✓ | ✓ voice new | | | P0 |
| 9 | Vehicle/other party | PATCH step=`vehicle_other_party` | MP form step | ✓ | | | | P1 |
| 10 | Photo upload | `POST /api/h5/tasks/{token}/upload`, `ingest_h5_slot_upload()` | `wx.chooseMedia` → same endpoint | ✓ | ✓ client | | | P0 |
| 11 | Photo skip | `POST .../skip`, `skip_h5_flow_slot()` | MP skip button | ✓ | | | | P2 |
| 12 | Review | `H5ClaimIntakePage` step=`review` | MP Final Review | ✓ logic | ✓ UI | ✓ | | P0 |
| 13 | Submit | `submit_intake_form()`, `X-Submit-Intent-Id` | MP submit + idempotency | ✓ | | | | P0 |
| 14 | Done / receipt | step=`done`, `completion_summary` | MP Submit Receipt | ✓ payload | ✓ UI | ✓ | | P0 |
| 15 | Resume | Token TTL 72h; WeCom「进度」re-mint | MP history + WeCom Resume card | ✓ | ✓ session | | | P0 |
| 16 | Completion summary | `_build_completion_summary()` | Receipt screen | ✓ | ✓ UI | | | P1 |
| 17 | WeCom submit confirmation | `h5_submit_confirmation.try_send_h5_submit_confirmation` | Same backend trigger on MP submit | ✓ | | | | P1 |
| 18 | Provenance | `patch_case_known_facts`, `known_fact_provenance` | Same; MP writes `source_channel: customer_task` or keep `h5_task` | ✓ | ✓ tag name | | | P1 |
| 19 | Idempotency | field dedup keys, submit_intent_ids, photo hash | Same server keys | ✓ | | | | P0 |
| 20 | Safety disclaimer | `CLAIM_INTAKE_SAFETY_COPY` | Tenant config footer on every MP page | ✓ copy | ✓ config | | | P0 |
| 21 | Injury alert | `injury_alert` in intake response | MP inline alert | ✓ | ✓ UI | | | P1 |
| 22 | Upload URL (evidence pack) | `mint_h5_claim_evidence_pack_link()` | Inline in MP Media page — no separate route | ✓ backend | ✓ UX | separate H5 upload route | | P2 |
| 23 | Progress label | `completed_count` / `step_total` | MP progress bar | ✓ | ✓ UI | | | P0 |
| 24 | Error: expired token | 403 `invalid_or_expired_task_link` | MP Help + WeCom recovery | ✓ | ✓ UI | | | P0 |
| 25 | beforeunload guard | `H5ClaimIntakePage` review guard | MP `onUnload` warn | | ✓ | ✓ | | P2 |
| 26 | WeCom H5 link in cards | `build_claim_start_h5_intake_card_payload` | Mini program card payload | | ✓ | ✓ | H5 as primary | P0 |
| 27 | WeCom text supplement | `claim_basics` append + `channel_ux_policy` | Keep; ack → MP card not H5 URL | ✓ | ✓ policy | | parallel wizard | P1 |
| 28 | WeCom photo supplement | `media_intake.ingest_wecom_media_message` | Keep; save + MP nudge | ✓ | ✓ | | | P1 |
| 29 | Status commands | `is_claim_h5_link_request()` etc. | Return MP card not H5 URL | ✓ routing | ✓ reply | | | P1 |
| 30 | Add Car H5 | `/task/upload` Add Car flow | **Out of Prototype** | | | | defer | — |

---

## 2. Reuse / Adapt / Replace / Retire Summary

### Direct reuse (backend — no changes required for Prototype)

- `intake_info_for_token()` — `services/fiqa_api/inbox_triage/h5_task_intake.py`
- `patch_intake_fields()`
- `submit_intake_form()`
- `ingest_h5_slot_upload()` — `services/fiqa_api/inbox_triage/h5_task_upload.py`
- `verify_h5_task_token()` — `h5_task_token.py`
- `derive_claim_phase()`, `get_claim_missing_items()` — `wecom/claim_state.py`
- `build_claim_case_brief()` — `claim_workbench_display.py`
- `append_claim_timeline_event()`, `patch_case_known_facts()` — `case_store.py`
- `mark_claim_broker_done()` — `case_store.py`
- WeCom supplement ingest — `claim_basics.py`, `media_intake.py`

### Adapt

| Item | Change |
|------|--------|
| API path prefix | `/api/h5/tasks/*` → facade `/api/customer/tasks/*` (optional) |
| `source_channel` | Add `customer_task` alias; keep `h5_task` for backward compat |
| WeCom cards | Primary CTA: mini program `appId` + `path` instead of H5 view URL |
| Token delivery | Card query `task_token` instead of browser URL |
| Dashboard CTA | `primary_cta` strings unchanged; action opens MP pages |
| Identity | Add wx session layer atop token |

### Replace (customer frontend only)

| Item | Replacement |
|------|-------------|
| `ui/src/pages/H5ClaimIntakePage.tsx` | Native mini program pages |
| `ui/src/api/h5ClaimIntake.ts` | `mp/api/task.js` client (same JSON contracts) |
| H5 as WeCom primary CTA | Mini program card |
| React inline styles wizard | WXML + WXSS task UI |

### Retire (as primary path — keep as fallback)

| Item | Notes |
|------|-------|
| H5 `/task/claim/:token` as main entry | Keep deployed for QA/emergency |
| WeCom structured field prompts | `build_claim_missing_basics_reply` chat form — notify only |
| Injury quick-reply menu in WeCom | Legacy only per `p19h3h_claim_h5_task_state_machine` |
| H5 URL in every supplement ack | `channel_ux_policy` — MP card on demand only |

---

## 3. API Mapping Table

| H5 endpoint (today) | Customer Task API (target) | Handler function | Prototype action |
|---------------------|----------------------------|------------------|------------------|
| `GET /api/h5/tasks/{token}/intake` | `GET /api/customer/tasks/{id}` | `intake_info_for_token` | **Call as-is** |
| `PATCH /api/h5/tasks/{token}/fields` | `PATCH /api/customer/tasks/{id}/fields` | `patch_intake_fields` | **Call as-is** |
| `POST /api/h5/tasks/{token}/submit` | `POST /api/customer/tasks/{id}/submit` | `submit_intake_form` | **Call as-is** |
| `POST /api/h5/tasks/{token}/upload` | `POST /api/customer/tasks/{id}/media` | `ingest_h5_slot_upload` | **Call as-is** |
| `POST /api/h5/tasks/{token}/skip` | `POST /api/customer/tasks/{id}/media/skip` | `skip_h5_flow_slot` | Optional |
| `GET /api/h5/tasks/{token}` | — (upload flow metadata) | `task_info_for_token` | Use intake GET instead |
| — | `GET /api/customer/tasks/current` | **New facade** | Defer |
| — | `POST /api/customer/tasks/{id}/voice` | **New** | Mock / defer |
| — | `POST /api/customer/auth/session` | **New** wx code2session | Gate 3 |

**Routes files:** `services/fiqa_api/routes/h5_task_intake.py`, `h5_task_upload.py`  
**Link minting:** `services/fiqa_api/inbox_triage/h5_task_link.py` — `mint_h5_claim_intake_form_link()`

---

## 4. Test Mapping

| Existing test | Covers | MP Prototype needs |
|---------------|--------|-------------------|
| `tests/test_h5_claim_intake_form.py` | intake PATCH/submit/idempotency | **Re-run unchanged** — backend same |
| `tests/test_p19h3i_claim_task_dashboard_always_return_h5.py` | dashboard_summary | **Re-run** — API shape |
| `tests/test_p19h3h_append_first_split_later.py` | supplement routing | **Re-run** — WeCom unchanged |
| `tests/test_p19h3f5_single_active_task_per_lane.py` | one active claim | **Re-run** |
| `tests/test_p19h3f4_unified_status_card.py` | status card | **Adapt** when MP card added |
| `scripts/p19h3h_claim_h5_intake_smoke.py` | E2E H5 | **New** `p19m1_mp_claim_prototype_smoke.py` |
| `scripts/p19h3i_claim_task_dashboard_smoke.py` | dashboard + WeCom | **Extend** for MP card CTA |

**Prototype acceptance:** existing pytest green + new MP smoke script (HTTP level, no WeChat cloud in CI).

---

## 5. UI Concept Migration

### Worth migrating (semantics, not pixels)

| H5 concept | MP translation |
|------------|------------------|
| Dashboard panel (`dashboard_summary`) | Task Home header |
| One primary button per step | MP fixed bottom CTA |
| `submitting` / `saving` disabled states | `wx.showLoading` + button disabled |
| `submit_intent_id` UUID | Same client pattern |
| Review before submit | Final Review page |
| Post-submit supplement allowed | Task Home subtitle + CTA |
| Expired link recovery copy | Help page → WeCom「进度」 |

### Do NOT mechanically copy

| H5 pattern | Why |
|------------|-----|
| React inline `styles` object | Not portable; design for MP component model |
| Fixed web footer disclaimer | Use MP safe-area + `page` footer |
| Browser `beforeunload` | Use MP lifecycle |
| Vercel-hosted SPA routing | MP page stack |
| Web textarea for story | Consider voice-first on MP |
| 480px max-width card layout | Use full device width |
| Deep link `/task/claim/:token` URL shape | Use `pages/task/home?token=` |

---

## 6. Risks Specific to Migration

| Risk | Mitigation |
|------|------------|
| H5 and MP both live — customer confusion | WeCom policy: one primary CTA; H5 only in Help/fallback |
| `source_channel: h5_task` mislabels MP writes | Add `customer_task` tag in facade or document as alias |
| Tests assume H5 frontend | Backend tests unaffected; add MP client smoke |
| Undeployed `d413434` channel policy | Deploy before pilot; MP prompt separate from P19M-0 |
| Photo upload Content-Type differences | Test `wx.uploadFile` with same multipart contract |

---

## 7. Prototype Priority Queue

| Priority | Items |
|----------|-------|
| **P0** | Token entry, Task Home, story, 2 photos, review, submit, resume, error states, backend reuse |
| **P1** | Time/location, vehicle steps, WeCom MP card, submit confirmation, supplement policy update |
| **P2** | Skip slot, voice, facade rename, `GET /current`, evidence pack separate flow |
| **Out** | Add Car, video, multi-tenant admin, Workbench UI, OCR |

---

*Companion to P19M-0 SSOT — no implementation in this document.*
