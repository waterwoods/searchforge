# P19H-3h — Master Design Summary

**Date:** 2026-07-10  
**Sprint:** P19H-3h Design  
**Purpose:** Handoff document for implementation agents (read this first tomorrow)  
**Verdict:** **GO** — Claim H5 Task Page MVP

---

## 1. Final decision

**WeCom + H5 Task Page + Broker Workbench**

| Channel | Role |
|---------|------|
| WeCom | Entry · notify · simple confirm · exceptions (Confirm / Collision) |
| H5 Task Page | Primary structured intake (Claim MVP first) |
| Broker Workbench | Review · Done · risk visibility |

State machine (`claim_state.py`) controls flow. AI extracts and summarizes — it does not control steps.

---

## 1b. Core product principle — Structured Task First, AI Assist Second

**结构化任务优先，AI 理解辅助。**

| Rule | Meaning |
|------|---------|
| **State machine is the controller** | `derive_claim_phase`, step completion, and phase transitions are authoritative. AI does **not** decide「what step are we on」or advance the workflow. |
| **H5 Task Page is the execution surface** | Customers complete tasks via explicit buttons, fields, uploads, and submit — not by guessing free text. |
| **WeCom is entry / notify / light confirm** | Start Card, Status Card, End Card, Collision Confirm — not the primary structured intake UI. |
| **AI is backend assist only** | Extraction, normalization, summary, missing-info hints, risk flags, and **broker draft** — never the customer-facing main path. |

**Customer input priority (highest → lowest trust):**

1. Explicit H5 buttons / fields / upload / submit
2. H5 confirmed facts (PATCH persisted, timeline `source: h5_task`)
3. WeCom free text / photos as **supplemental / provisional**
4. AI extraction as **draft only** — never auto-promoted to confirmed without structured or broker confirmation

**Broker Workbench:** Shows AI-assisted draft and structured facts; **Chen confirms** before handoff is treated as final.

**Product rationale (Spark Driver analogy):** Smoothness comes from a clear task state machine, not free chat. Less user guessing and waiting; fewer system misroutes and duplicate asks; broker trusts structured data.

**Claim H5 MVP (tomorrow):** Implementation **must** obey this principle. Do not build chat-driven step prompts, LLM phase control, or WeCom-as-primary-form flows.

---

## 2. Why this is better than pure WeCom chat

| Pure chat | WeCom + H5 |
|-----------|------------|
| 2–5s per field | Local form, one API per step |
| No button disable | `disabled` + spinner |
| Bulk narrative re-parse | Explicit fields per step |
| Pull-based progress (`进度`) | Push progress on each step |
| ~50–60% Spark-like | ~85–88% Spark-like |
| Broker scrolls WeChat | Structured brief in 10 seconds |

WeCom stays for **trust and ceremony**. H5 owns **formal资料补全**.

---

## 3. Why not mini program now

- H5 deep link + `h5t1` token already shipped
- 5–7 days vs 2–4× eng + audit weeks
- ~85–88% Spark target sufficient for Chen pilot
- Mini program → Phase 4+ after task model validated

---

## 4. Why not independent app now

- Chen customers are WeChat-native
- Zero install friction
- Wrong distribution for single-broker pilot
- Revisit for multi-tenant SaaS brand

---

## 5. Spark Driver principles → our product

| Spark Driver | Our translation |
|--------------|-----------------|
| One task at a time | Single Active Task per lane |
| One primary action per screen | H5 wizard: one「下一步」/「提交」|
| Clear progress | Step counter + 已收到/还缺 |
| Complete trip → clear payout status | Submit →「已提交给陈总」→ End Card |
| Exceptions off main path | Collision / lane-switch Confirm Cards in WeCom |
| Tap once, know it worked | Idempotent submit + disabled button |

---

## 6. Claim MVP scope

**Route:** `/task/claim/:taskToken`

**Trip steps:**
1. Start (H5 landing)
2. Injury (`anyone_injured`)
3. Time + Location
4. Story
5. Vehicle / Other Party
6. Evidence (3 photo slots — reuse upload API)
7. Review
8. Submit to Broker
9. Done

**WeCom change:** Start Card primary CTA = H5 link (deprecate injury menu for new cases).

**New backend:**
- `FLOW_CLAIM_INTAKE_FORM` token flow
- `GET /api/h5/tasks/{token}/intake`
- `PATCH /api/h5/tasks/{token}/fields`
- `POST /api/h5/tasks/{token}/submit`

**No schema migration.** Reuse `known_facts`, `claim_timeline`, `derive_claim_phase`, `build_claim_case_brief`.

**Estimate:** 5–7 days.

---

## 7. Add Car follow-up scope

**Phase 3** after Claim MVP stable (2–3 days).

- Same framework, lane-specific steps (vehicle, driver, date, coverage, docs)
- `FLOW_ADD_CAR_INTAKE_FORM`
- Add Car Start Card → H5 link
- Confirm Card for「再加一辆车」(deferred from P19H-3f-5)
- Reuse `H5StepWizard` extracted from Claim page

---

## 8. Smooth UX principles (non-negotiable)

0. **Structured Task First, AI Assist Second** — see §1b; state machine controls flow; H5 owns structured intake; AI draft only
1. **幂等** — double-click safe everywhere
2. **短确认** — WeCom acks are one line, not full cards
3. **状态卡同步** — Status Card and H5 read same phase/missing
4. **Loading/disabled** — never wonder if click worked
5. **Reply dedup** — no duplicate Start/Confirm/End Cards
6. **Submit intent UUID** — client retry safe after timeout
7. **Photo content-hash** — no duplicate attachments

See: `p19h3h_smooth_ux_idempotency_async_design_2026_07_10.md`

---

## 9. Implementation order

| # | Workstream | Est. | Depends on |
|---|------------|------|------------|
| 1 | **Claim H5 Task Page MVP** — token flow + 3 APIs + `H5ClaimIntakePage` | 5–7d | — |
| 2 | **Smooth UX idempotency** — submit keys, disabled states, photo dedup | 1d | #1 |
| 3 | **H5/WeCom Status sync** — Status Card H5 link footer; phase alignment | 0.5d | #1 |
| 4 | **WeCom Start Card copy** — H5 link primary CTA | 0.5d | #1 |
| 5 | **Add Car H5 reuse** — shared wizard + Add Car steps | 2–3d | #1 stable |
| 6 | **Broker correction tools** — needs-more-info, mark duplicate (future) | defer | post-pilot |

### Suggested file map (Claim MVP)

| Layer | Files |
|-------|-------|
| Token | `h5_task_token.py`, `h5_task_link.py` |
| API | `h5_task_intake.py` (new), `routes/h5_task_upload.py` |
| State | `claim_state.py` (minimal wire) |
| WeCom | `reply.py`, `claim_basics.py` (Start copy) |
| Frontend | `H5ClaimIntakePage.tsx`, `h5ClaimIntake.ts`, `App.tsx` |
| Tests | `test_h5_claim_intake_form.py`, deploy smoke script |

### Deploy

- Frontend: Vercel (`ui-smoky-beta.vercel.app`)
- Backend: Cloud Run
- Smoke: `scripts/p19h3h_deploy_claim_h5_intake_smoke.py` (new)

---

## 10. What NOT to build now

| Out of scope | Reason |
|--------------|--------|
| Mini program | H5 sufficient |
| Independent app | Wrong pilot distribution |
| Multi-tenant admin | Single broker pilot |
| OCR / ASR | Raw text + photos |
| Complex CRM | Workbench brief enough |
| Multi-open customer picker | Single Active Task policy |
| LLM-generated brief | Deterministic brief shipped |
| Schema / new DB tables | JSON on case document |
| Auto broker_done | Manual Chen trust anchor |
| Enterprise WeCom template card | Text-frame cards sufficient |

---

## Document index

| # | Document | Contents |
|---|----------|----------|
| 1 | `p19h3h_product_architecture_wecom_h5_workbench_2026_07_10.md` | Thesis, architecture, platform direction |
| 2 | `p19h3h_claim_h5_task_state_machine_2026_07_10.md` | Claim 9-step trip spec |
| 3 | `p19h3h_add_car_h5_task_state_machine_2026_07_10.md` | Add Car trip + reuse |
| 4 | `p19h3h_smooth_ux_idempotency_async_design_2026_07_10.md` | Idempotency, async phases, risk matrix |
| 5 | `p19h3h_evidence_chain_broker_review_design_2026_07_10.md` | Timeline, Workbench, visibility rules |
| 6 | `p19h3h_master_design_summary_2026_07_10.md` | This document |

**Recon source:** `docs/policy/p19h3h_h5_task_page_primary_intake_recon_2026_07_10.md`

---

## Open questions (resolve during implementation)

| # | Question | Default if unresolved |
|---|----------|----------------------|
| 1 | Token TTL: 24h or 72h for Claim form? | **72h** (multi-day accident) |
| 2 | Injury in WeCom Start vs H5 only? | **H5 only** (Option A) |
| 3 | Photo step inline vs separate `/task/upload` route? | **Inline** for Spark continuity |
| 4 | Post-H5-submit WeCom notify — P0 or P1? | **P1** (H5 Done screen sufficient for MVP) |
| 5 | `own_vehicle_info` — single field or split year/make/model? | **Single text** for MVP; split later |
| 6 | Enable `WECOM_SLICE_SEND_REPLY` on Cloud Run before pilot? | **Yes** for live End Card |

---

## GO / HOLD

| Item | Verdict |
|------|---------|
| Design complete | ✅ |
| Core principle recorded (Structured Task First) | ✅ |
| Implementation tomorrow | **GO** (must obey §1b) |
| Claim H5 MVP | **GO** |
| Add Car H5 | **GO** after Claim stable |
| Mini program / app | **HOLD** |

**Next prompt:** `P19H-3h-1 Implement: Claim H5 Task Page MVP`

---

*STOP — design phase complete*
