# P19H-3h — H5 Task Page as Primary Intake Surface Recon

**Date:** 2026-07-10  
**Sprint:** P19H-3h Recon  
**Status:** Recon complete — **GO (Claim H5 Task Page MVP)** recommended  
**Scope:** Product / architecture recon — **documentation only**  
**Audience:** Andy, Chen Kui pilot team, P19H+ implementation agents  
**Prerequisite:** P19E-3 (channel strategy) ✅ · P19H-3c (Claim H5 photo) ✅ · P19H-3f-4 (Status Card) ✅ · P19H-3f-5 (Single Active Task) ✅ · P19H-3g-5 (WeCom smooth UX) ✅

**This loop:** No code. No deploy. No schema migration.

---

## Executive summary

WeCom + AI/workflow/Workbench is operational for Chen Kui Claim pilot, but **formal资料补全 in chat** hits structural UX limits: slow replies, no button disable, repeat taps, and low task-app trust. The codebase already has H5 infrastructure (signed tokens, photo flow, GCS attachments) — but H5 today is **photo-only**; Claim text basics still live in WeCom chat (`claim_basics.py`).

**Core hypothesis validated:** WeCom is the right **entry + notify + trust** channel; H5 is the right **primary formal intake surface** for structured Claim data collection.

| Question | Answer |
|----------|--------|
| H5 recommended as primary Claim intake? | **YES** — for structured fields + photos + submit UX |
| Mini program needed now? | **NO** — H5 WebView from WeCom link is sufficient |
| Existing code reusable? | **YES** — tokens, `known_facts`, photo upload, `claim_case_brief`, broker_done |
| Estimated Claim MVP effort | **5–7 days** (backend + frontend + WeCom copy + smoke) |
| Schema change required? | **NO** — reuse `known_facts`, `claim_timeline`, existing slots |

**One-line recommendation:**

> Shift Claim **formal资料补全** from WeCom chat Q&A to an **H5 multi-step Task Page**; keep WeCom for Start/Status/End Cards, reminders, and optional chat supplements. Do **not** rewrite the AI brain — wire H5 submits into existing `patch_case_known_facts` + phase transitions.

---

## 1. Current problem

### 1.1 Customer pain (WeCom chat as primary intake)

| Symptom | Root cause | H5 fix |
|---------|------------|--------|
| 回复慢 | Synchronous inline callback (`WECOM_INBOX_QUEUE=0`); 2–5s before any reply | H5 form is local; submit is one API round-trip |
| 用户重复点击 | No disable on msgmenu buttons; duplicate guards partial (P19H-3g-5) | Single primary CTA with `disabled` + loading state |
| 无法 disable button | WeCom msgmenu is fire-and-forget | Standard web form controls |
| 信息来回提交不丝滑 | Free-text extraction loop; customer must parse「还需要」lists | Step-by-step wizard with done/not-done progress |
| 客户信任感不足 | Chat feels like a bot Q&A, not a task app | Spark-like task page: header, progress, confirmation |
| 体验不如 Spark Driver | No in-session step machine on customer side for text fields | Binary step model on H5 (P19E-0 pattern) |

### 1.2 What works today (keep)

| Layer | Status | Role |
|-------|--------|------|
| WeCom Start Card + injury menu | ✅ Shipped | Entry, trust anchor, lane start |
| Claim Status Card (`进度`) | ✅ P19H-3f-4 | Status / missing summary in chat |
| H5 photo flow (`claim_evidence_pack`) | ✅ P19H-3c | 3-slot photo chain |
| Workbench Claim brief | ✅ P19H-3e | Broker review hero |
| `broker_done` → End Card | ✅ P19H-3f-2 | Terminal ceremony |
| Single Active Task per lane | ✅ P19H-3f-5 | Append vs collision routing |

### 1.3 What is missing

| Gap | Impact |
|-----|--------|
| **No H5 text-field intake page** | Accident basics collected via chat extract only |
| **No customer-facing Claim progress UI on web** | `CustomerIntakeProgressSummary` exists but unused |
| **H5 = photo shell only** (P19E-3 decision) | Correct for Jul 6 Add Vehicle; **insufficient for Claim pilot UX bar** |
| **No H5 submit → broker_review ceremony** | Phase transition only via chat completeness heuristics |

---

## 2. Why pure WeCom chat is not enough

Prior recon (`docs/p19d16_pure_wecom_chat_vs_h5_guided_flow_recon.md`) established:

| Dimension | Pure WeCom Chat | WeCom + H5 |
|-----------|-----------------|------------|
| Spark-like (photo) | ~15–25% | ~75% |
| Spark-like (text steps) | ~80% | ~80% if chat owns text |
| Spark-like (overall) | ~35–45% | ~75–85% |

**P19H-3h update:** For Claim, text steps in chat drop effective score to **~50–60%** because:

1. **Extraction latency** — each field requires send → sync_msg → LLM/rules → reply.
2. **No step lock** — customer can skip ahead or send bulk narrative; backend must re-parse.
3. **No visual progress** — Status Card helps but is pull-based (`进度`), not push-on-complete.
4. **Trust** — Chen Kui customers expect「填表」not「跟机器人聊天」for accident records.

WeCom chat remains essential for: **entry, 人工感, 状态通知, 紧急受伤提醒, 补充说明**. It should **not** be the primary surface for the 6-step accident record.

---

## 3. Why H5 before mini program

| Factor | H5 | Mini Program |
|--------|-----|--------------|
| Time to ship Claim form MVP | **5–7 days** | 2–4× eng; audit weeks |
| WeCom deep link | ✅ Already works (`H5_TASK_FRONTEND_BASE_URL`) | Requires open-data / binding |
| Token auth (no login) | ✅ `h5t1.*` shipped | Identity binding complexity |
| Photo upload | ✅ GCS path exists | Native picker better but not blocking |
| Pilot iteration speed | Fast deploy (Vercel) | Slow review cycle |
| Spark-like target for pilot | **~85–88%** with form + photos | ~92–95% |

**P19E-3 verdict still holds for mini program: NO now.**  
**P19E-3 H5 scope guardrail evolves:** H5 moves from「photo shell only」→「**Claim primary intake form + photos**」; WeCom retains notify/trust, not field collection.

---

## 4. Current asset inventory

### 4.1 H5 / customer pages (answers to recon Q1)

| Asset | Route | Exists? | Scope |
|-------|-------|---------|-------|
| H5 photo task page | `/task/upload/:taskToken` | ✅ | Photo-only; Add Car + Claim evidence |
| H5 Claim intake form page | — | ❌ | **To build** |
| H5 Task Home (read-only) | — | ❌ | V1.1 per P19E-3 |
| Customer portal | `/workbench/unified-intake` | ✅ | Add-Car-strong; Claim = generic text triage |
| Add Car wizard | `/add-car` | ✅ | 6-screen standalone (not WeCom-primary) |

**Q1 answer:** Partial H5 task page exists (photo only). **No** full Claim customer task page.

### 4.2 Token mechanism (Q2)

| Mechanism | Format | Reusable? |
|-----------|--------|-----------|
| H5 task token | `h5t1.<payload>.<sig>` | **YES** — extend v2 flow model |
| Case binding | `case_id` + `lane` + `flow` + `slots` | **YES** |
| TTL | 24h default | **YES** — may extend for multi-day resume |
| `case_token` | N/A | Does not exist; use `taskToken` |

**Files:**
- `services/fiqa_api/inbox_triage/h5_task_token.py`
- `services/fiqa_api/inbox_triage/h5_task_link.py`
- `ui/src/api/h5TaskUpload.ts`

**Q2 answer:** Token mechanism is **fully reusable**. Add new flow constant e.g. `FLOW_CLAIM_INTAKE_FORM` with step keys instead of photo slots.

### 4.3 Claim field mapping (Q3)

| H5 Step | `known_facts` key | `claim_case_brief.key_facts` | `missing_info` key |
|---------|-------------------|------------------------------|-------------------|
| 1 受伤情况 | `injury_status` (`yes`/`no`/`unknown`) | `injury_status` | `injury_status` |
| 2 事故时间 | `accident_datetime` | `accident_datetime` | `accident_datetime` |
| 3 事故地点 | `accident_location` | `accident_location` | `accident_location` |
| 4 事故经过 | `accident_description` | `accident_description` | `accident_description` |
| 5 车辆/对方 | `other_party_info`, `own_vehicle_info` | `other_party_info` | `other_party_info` |
| 6 照片 | attachment slots | `evidence_received` | photo keys |
| Submit | phase → `intake_ready_for_broker` | `summary` | remaining `missing_info` |

**Phase source:** `services/fiqa_api/wecom/claim_state.py` — `derive_claim_phase()`, `CLAIM_ACCIDENT_BASICS_FIELDS`.

**Timeline events on H5 submit:** append `claim_timeline` with `source_channel: "h5_task"`, `event_type: "customer_text"` or new `h5_step_complete`.

### 4.4 Add Car same model? (Q4)

**YES, with lane-specific steps.**

| Lane | H5 today | H5 target |
|------|----------|-----------|
| Add Car | Photo flow ✅; Phase 2 text in chat | Phase 2 text could move to H5 form (Phase 3) |
| Claim | Photo flow ✅; basics in chat | **Form MVP first** (higher pilot pain) |

Add Car already has `/add-car` wizard + `CustomerEntryTab` — richer than Claim. **Reuse:** same token infra, step progress component, submit/disable pattern. Add Car H5 form is **Phase 3** after Claim pilot validates model.

### 4.5 APIs available (Q5)

| API | Status | Use for H5 |
|-----|--------|------------|
| `GET /api/h5/tasks/{token}` | ✅ | Task metadata, slot progress |
| `POST /api/h5/tasks/{token}/upload` | ✅ | Step 6 photos |
| `POST /api/h5/tasks/{token}/skip` | ✅ | Optional photo skip |
| `patch_case_known_facts()` | ✅ internal | Field persistence |
| `build_claim_case_brief()` | ✅ read-time | Progress + confirmation page |
| `get_claim_progress_snapshot()` | ✅ | Step done/not-done |
| `POST /api/inbox/triage` | ✅ | Fallback text (don't use for H5 primary) |
| `POST /api/inbox/cases/{id}/broker-done` | ✅ broker only | Not customer-facing |

### 4.6 APIs to build (Q6)

| New endpoint | Purpose | Priority |
|--------------|---------|----------|
| `GET /api/h5/tasks/{token}/intake` | Token-scoped read: phase, `key_facts`, `missing_info`, current step, safety copy | P0 |
| `PATCH /api/h5/tasks/{token}/fields` | Submit one step's fields → `patch_case_known_facts` + timeline | P0 |
| `POST /api/h5/tasks/{token}/submit` | Final customer submit → `intake_ready_for_broker` / `broker_review` phase | P0 |
| `issue_h5_claim_intake_form_token()` | New flow token mint | P0 |
| `mint_h5_claim_intake_form_link()` | WeCom Start Card link | P0 |
| Optional: `POST /api/h5/tasks/mint` | Admin/broker re-link mint | P2 |

**No schema migration** — all fields already in `known_facts` JSON on case document.

### 4.7 Pilot timeline estimate (Q7)

| Phase | Scope | Estimate |
|-------|-------|----------|
| **Phase 1** (this recon) | Doc + route map | ✅ Done |
| **Phase 2** Claim H5 MVP | New page + 3 APIs + WeCom Start copy + smoke | **5–7 days** |
| **Phase 3** Add Car reuse | Port step model to Add Car Phase 2 text | **2–3 days** |

Breakdown Phase 2:
- Backend (token flow + 3 endpoints + wire claim_state): **2 days**
- Frontend (`H5ClaimIntakePage` 6 steps + photos + confirm): **2–3 days**
- WeCom Start Card copy + link mint: **0.5 day**
- Tests + deploy smoke: **1 day**

---

## 5. Target architecture

```text
Customer
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  WeCom (entry · trust · notify · optional supplement)        │
│  • Start Card → H5 task link (primary CTA)                   │
│  • Status Card (进度) — summary + link to resume H5          │
│  • End Card — broker_done ceremony                           │
│  • Simple confirm buttons (injury quick-reply OR defer to H5)│
│  • Chat photos/text → append to active case (safety net)     │
└───────────────────────┬─────────────────────────────────────┘
                        │ signed H5 deep link (h5t1 token)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  H5 Claim Task Page (PRIMARY formal intake)                  │
│  • Step wizard: injury → time → location → story → other   │
│  • Photo upload (reuse claim_evidence_pack or inline)        │
│  • Progress: done / missing                                  │
│  • Single CTA: disable + loading + anti double-submit      │
│  • Save/resume via token (24h+ TTL)                          │
│  • Confirmation: received + what's still missing + next      │
└───────────────────────┬─────────────────────────────────────┘
                        │ known_facts + attachments + timeline
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Postgres (source of truth — unchanged)                      │
│  • case JSON · claim_phase · claim_timeline                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Workbench (broker)                                          │
│  • ClaimCaseBriefPanel · evidence checklist                  │
│  • broker_done → WeCom End Card                              │
│  • 修正 / 关闭 / 重复标记 (future)                           │
└─────────────────────────────────────────────────────────────┘
```

### Channel responsibilities (steady state)

| Channel | Owns | Does NOT own |
|---------|------|--------------|
| **WeCom** | Start, Status, End Cards; trust copy; urgent injury alert; optional supplement | Primary structured field collection |
| **H5** | Formal step form, photos, submit, resume, loading UX | Login, carrier filing, OCR |
| **Workbench** | Broker review, done, corrections | Customer-facing intake |

---

## 6. H5 Claim Task Page MVP design

### 6.1 Route

```
/task/claim/:taskToken     → H5ClaimIntakePage (new)
/task/upload/:taskToken    → H5SingleSlotUploadPage (existing, photo-only)
```

Alternative (lower route churn): single `/task/:taskToken` with flow-type dispatch. **Recommend separate route** for clarity and independent deploy.

### 6.2 Page structure

| # | Section | Fields | Validation |
|---|---------|--------|------------|
| Header | 事故资料收集 | — | — |
| Progress | N/6 已完成 · 还缺 X 项 | from `missing_info` | — |
| Step 1 | 受伤情况 | Radio: 没有受伤 / 有人受伤 / 不确定 | Required |
| Step 2 | 事故时间 | Date + time picker or text | Required |
| Step 3 | 事故地点 | Text (city/street/intersection) | Required |
| Step 4 | 事故经过 | Textarea (what happened) | Required |
| Step 5 | 车辆/对方信息 | Text (plate, insurer, vehicle) | Required (partial ok) |
| Step 6 | 照片上传 | 3 slots (reuse upload API) | Soft-required + skip |
| Submit | 提交给陈总确认 | Single primary button | All required steps |
| Confirmation | 已收到 | Summary + missing +「陈总会人工确认」| — |

### 6.3 Interaction requirements

| Requirement | Implementation |
|-------------|----------------|
| 一个主按钮 | One「下一步」/「提交」per step; final step =「提交给陈总确认」 |
| 点击后 disable | `disabled={submitting}` on button |
| loading | Spinner +「提交中…」 |
| 防重复提交 | Client guard + server idempotency key on `submit` |
| 可返回继续补 | Back nav between steps; token resume |
| 错误提示清楚 | Map API errors to Chinese copy (pattern: `h5TaskUpload.ts`) |
| 不做复杂登录 | Token-only |
| 不做微信小程序 | H5 WebView |
| 不做 OCR/ASR | Raw text + photos |
| 不做 carrier filing | Disclaimer on every page footer |

### 6.4 Injury step note

Today injury is WeCom quick-reply (`claim_injury_no/yes/unknown`). **MVP options:**

| Option | Pros | Cons |
|--------|------|------|
| **A — H5 only** | Single surface | Start Card must link straight to H5 |
| **B — Hybrid** | Injury in Start Card; rest in H5 | Two surfaces |
| **C — H5 mirrors menu** | Consistent | Slight delay before H5 opens |

**Recommend A:** Start Card links to H5; Step 1 = injury. Deprecate injury msgmenu for new Claims (keep handler for legacy).

---

## 7. Workflow mapping (no AI rewrite)

```text
H5 Step submit
    → PATCH /api/h5/tasks/{token}/fields
    → patch_case_known_facts(case_id, {field: value})
    → append_claim_timeline_event(source_channel="h5_task")
    → derive_claim_phase(case)  [existing claim_state.py]

H5 photo upload (Step 6)
    → POST /api/h5/tasks/{token}/upload  [existing]
    → GCS h5/{case_id}/{slot}/...
    → attachment metadata source="h5_task"

H5 final submit
    → POST /api/h5/tasks/{token}/submit
    → guided_workflow_state = ready_for_broker_review
    → claim_phase → intake_ready_for_broker / broker_review
    → optional WeCom notify:「已收到您的资料，陈总会人工确认」

Broker opens Workbench
    → GET /api/inbox/cases/{id}
    → build_claim_case_brief() → hero panel

Broker Done
    → POST /api/inbox/cases/{id}/broker-done  [existing]
    → WeCom End Card  [existing claim_end_card.py]
```

**Do NOT:** new LLM extraction path, new case schema, duplicate phase machine.

---

## 8. WeCom copy

### 8.1 Start Card (updated)

```text
【事故记录已开始】

我是陈总办公室的值班助手。我会先帮您整理这次事故资料，陈总会人工确认后联系您。

为了避免信息漏掉，请点击下面页面补充资料（推荐）：
{H5_CLAIM_INTAKE_LINK}

您也可以继续在微信里发文字或照片，我会一并记录；但正式资料建议在页面里填写，不容易漏项。

⚠️ 说明：此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。
```

**Button:** `打开资料填写页面` → H5 link (not injury menu as primary).

### 8.2 Status Card addition

Append to existing Status Card (`build_claim_status_card_reply`):

```text
继续补充资料：{H5_CLAIM_INTAKE_LINK}
```

### 8.3 Post-H5-submit WeCom notify (optional P1)

```text
已收到您提交的事故资料。陈总会人工确认，如需补充可点击：{H5_LINK} 或直接在微信留言。
```

---

## 9. H5 Task Page route / API map (Phase 1 deliverable)

```text
FRONTEND
  /task/claim/:taskToken
    ├─ GET  /api/h5/tasks/{token}/intake     → load steps + progress
    ├─ PATCH /api/h5/tasks/{token}/fields    → save step
    ├─ POST  /api/h5/tasks/{token}/upload    → photo (reuse)
    ├─ POST  /api/h5/tasks/{token}/skip      → skip photo (reuse)
    └─ POST  /api/h5/tasks/{token}/submit    → final handoff

BACKEND (new/changed)
  h5_task_token.py
    └─ FLOW_CLAIM_INTAKE_FORM + step keys
  h5_task_link.py
    └─ mint_h5_claim_intake_form_link()
  h5_task_intake.py (new module)
    └─ intake_info_for_token(), save_intake_fields(), submit_intake()
  routes/h5_task_upload.py
    └─ mount new intake routes (or h5_task_intake.py router)
  wecom/reply.py + claim_basics.py
    └─ Start Card → H5 link primary CTA

WECOM (unchanged handlers, new copy)
  slice.py → process Start → mint link → send card
  claim_basics.py → ingest chat append (safety net, not primary)

WORKBENCH (unchanged)
  claim_workbench_display.py → brief auto-enriches from known_facts
```

---

## 10. Implementation phases

### Phase 1 — Recon (this doc) ✅

- Asset inventory
- Route/API map
- MVP design
- GO/HOLD decision

### Phase 2 — Claim H5 Task Page MVP

| Workstream | Files (estimated) |
|------------|---------------------|
| Token + mint | `h5_task_token.py`, `h5_task_link.py` |
| Intake API | `h5_task_intake.py` (new), `routes/h5_task_upload.py` |
| Wire submit | `claim_state.py`, `case_store.py` (minimal) |
| Frontend page | `ui/src/pages/H5ClaimIntakePage.tsx` (new) |
| API client | `ui/src/api/h5ClaimIntake.ts` (new) |
| Route | `ui/src/App.tsx` |
| WeCom copy | `wecom/reply.py`, `claim_basics.py` |
| Tests | `tests/.../test_h5_claim_intake_form.py`, static UI test |

**Deploy:**
- **Frontend deploy: YES** — new route on Vercel (`ui-smoky-beta.vercel.app`)
- **Backend deploy: YES** — new API routes on Cloud Run

**Risks:**

| Risk | Mitigation |
|------|------------|
| Token TTL too short for multi-day accident | Extend TTL to 72h for intake form flow |
| Customer ignores H5, uses chat only | Keep chat append path; Status Card re-links H5 |
| Duplicate submit | Server idempotency on `submit`; phase guard |
| WeCom link distrust | Chen Kui branded copy + same domain as existing H5 photos |
| Phase drift (H5 vs chat both writing) | H5 primary; chat append merges into same `known_facts` |

**Tests:**
- Unit: token mint/verify for new flow
- API: field patch → known_facts → phase transition
- Integration: full 6-step → submit → workbench brief
- Deploy smoke: `scripts/p19h3h_deploy_claim_h5_intake_smoke.py` (new)
- WeCom: Start Card contains link; optional live send if `WECOM_SLICE_SEND_REPLY=1`

### Phase 3 — Add Car H5 reuse

- Extract shared `H5StepWizard` component from Claim page
- Add Car Phase 2 fields (delivery_date, zip, phone) as H5 steps
- Mint from Add Car Start Card
- **2–3 days** after Claim MVP stable

---

## 11. Comparison to prior channel decisions

| Doc | Prior decision | P19H-3h evolution |
|-----|----------------|-------------------|
| P19E-3 | H5 = photo only | H5 = **Claim primary form** + photos |
| P19E-3 | Progress Card before H5 home | Status Card shipped; H5 form is next |
| P19D-16 | H5 for photo lanes | Extend to text lanes for Claim |
| P19H-3g-5 | Fix WeCom duplicate guards | Still valuable; **complements** H5, not substitute |

WeCom UX hardening (P19H-3g-6) and H5 intake form are **parallel, not exclusive**.

---

## 12. Recommendation

### GO / HOLD

| Decision | Verdict |
|----------|---------|
| **H5 as Claim primary intake** | **GO** |
| **Mini program** | **HOLD** |
| **Rewrite claim AI** | **NO** |
| **Schema change** | **NO** |
| **Before Chen pilot** | Ship Phase 2 MVP OR run pilot with explicit「H5 link is primary」script |

**Rationale:** Customer pain is structural to chat UX, not fixable by copy alone. Infrastructure (token, photos, brief, broker_done) is 70% built; gap is one form page + thin API layer.

---

## STOP report

| Item | Value |
|------|-------|
| **Is H5 recommended?** | **yes** |
| **Is mini program needed now?** | **no** |
| **Can existing code be reused?** | **yes** |
| **Estimated effort** | **5–7 days** (Claim MVP); **2–3 days** (Add Car reuse) |
| **Main files** | `h5_task_token.py`, `h5_task_link.py`, `h5_task_intake.py` (new), `routes/h5_task_upload.py`, `H5ClaimIntakePage.tsx` (new), `claim_basics.py`, `wecom/reply.py`, `claim_workbench_display.py` |
| **Risks** | Link adoption; token TTL; chat/H5 dual-write; frontend+backend deploy coordination |
| **Next implementation prompt** | **P19H-3h-1 Implement:** Claim H5 Task Page MVP — backend `FLOW_CLAIM_INTAKE_FORM` + 3 endpoints + `H5ClaimIntakePage` 6-step wizard + WeCom Start Card link + deploy smoke |
| **STOP** | — |

---

*Related: `docs/p19e3_channel_strategy_wecom_h5_miniprogram_recon.md`, `docs/p19d16_pure_wecom_chat_vs_h5_guided_flow_recon.md`, `docs/policy/p19h3g5_wecom_smooth_ux_recon_2026_07_10.md`, `docs/policy/p19h3f5_single_active_task_per_lane_recon_2026_07_10.md`*
