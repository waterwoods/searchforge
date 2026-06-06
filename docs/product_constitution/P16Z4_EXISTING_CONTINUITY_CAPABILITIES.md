# P16-Z4 Phase 1 — Existing Continuity Capabilities Audit

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Constraint:** Audit only — no new services, no P17  
**Sources:** `services/fiqa_api/inbox_triage/`, `ui/src/features/intake/`, `scripts/`, P16-Z0/Z2/Z3/X/Y archaeology

---

## Executive summary

Unified Intake is **not** a Turn-1-only backend. The repo contains a **production-grade multi-turn stack** that is **under-exposed in broker trial UX**. Continuity failure is primarily **discoverability + summary merge + post-copy exit**, not missing APIs.

| Layer | Backend | Broker UI | Customer UI |
|-------|---------|-----------|-------------|
| Case persist | ✅ Strong | ✅ Strong | ✅ Partial (hidden on trial) |
| Append | ✅ Strong | ⚠️ Gated on reopen | ⚠️ Collapsed post-handoff |
| Timeline (`case_messages`, `case_activity`) | ✅ Strong | ⚠️ Activity in collapse | ⚠️ Progress panel only |
| Next action fields | ✅ Strong | ✅ Glance | ⚠️ Demoted on customer card |
| Follow-up (`waiting_on`) | ✅ PATCH API | ⚠️ Collapsed / kebab | ❌ Not customer-facing |

---

## Capability inventory by keyword

### `case_store`

| Capability | Location | Status |
|------------|----------|--------|
| `save_case()` — formal persist, `case_messages`, activity seed | `case_store.py` | Implemented |
| `append_follow_up_message()` — message thread + triage refresh | `case_store.py` | Implemented |
| `update_case_follow_up()` — `waiting_on`, `next_contact_by` | `case_store.py` | Implemented |
| `add_case_note()` — broker notes + activity | `case_store.py` | Implemented |
| `add_attachment_to_case()` — photos/docs on case | `case_store.py` | Implemented |
| DB + JSON dual-write | `service_record_repository.py` | Implemented |
| `MAX_CASE_ACTIVITY`, normalized activity list | `case_store.py` | Implemented |
| `formal_submitted_at` preserved on append | `case_store.py` | Implemented |
| `lifecycle_status` → `office_followup` on append | `case_store.py` | Implemented |

### `append` / `triage_for_append`

| Capability | Location | Status |
|------------|----------|--------|
| `triage_for_append()` — full re-triage for follow-up | `triage.py` | Implemented |
| `triage_mode: append` | `triage.py` | Implemented |
| `_classify_append_case_boundary()` — same vs new issue | `triage.py` | Implemented |
| `_apply_append_case_boundary()` — broker copy prefixes | `triage.py` | Implemented |
| `append_allowed` / `requires_new_case` enforcement | `triage.py`, routes | Implemented |
| `POST /cases/{id}/append-message` | `routes/inbox_triage.py` | Implemented |
| `append_case_boundary_copy` config externalization | `append_case_boundary_copy.py` | Implemented |
| Append blocked analytics | `funnel_events.py` | Implemented |
| Tests: `test_new_issue_append_enforcement.py`, `test_append_truth_alignment.py` | `tests/` | Implemented |
| Scripts: `run_follow_up_append_simulations.py`, boundary AB | `scripts/` | Implemented |

### `timeline` (thread + activity)

| Capability | Location | Status |
|------------|----------|--------|
| `case_messages[]` — sequenced customer/system messages | `case_store.py` | Implemented |
| `case_activity[]` — typed audit (created, follow_up_added, note_added, follow_up_updated) | `case_store.py` | Implemented |
| `conversation_summary` on save/append | `case_store.py`, `triage.py` | Implemented |
| `_build_conversation_summary()` — multi-turn intent line | `triage.py` | Implemented (merge gaps Y44) |
| `source_text` rebuilt from messages | `case_store.py` | Implemented |
| Activity UI in workbench (collapse panel) | `BrokerWorkbenchTab.tsx` | Partial — not hero |
| `getLatestUpdateForDisplay()` / tracking summary | `intakePure.ts` | Implemented |
| Add-car timeline intent (`add_car_timeline`) | `add_car_intent.py`, `conversion_layer.py` | Implemented (lane-specific) |

### `follow-up` / `waiting_on`

| Capability | Location | Status |
|------------|----------|--------|
| `waiting_on`: none \| client \| carrier \| broker | `case_store.py`, API | Implemented |
| `next_contact_by` free-text date | `case_store.py` | Implemented |
| `PATCH /cases/{id}/follow-up` | `routes/inbox_triage.py` | Implemented |
| `updateSavedCaseFollowUp()` client | `inboxTriage.ts` | Implemented |
| Queue filter: waiting on client count | `BrokerWorkbenchTab.tsx` | Implemented |
| `humanizeWaitingOn()` Chinese labels | `intakePure.ts` | Implemented |
| `getFollowUpSummary()` / `getCaseTrackingSummary()` | `intakePure.ts` | Implemented |
| Follow-up editor in workbench | `BrokerWorkbenchTab.tsx` | Partial — collapsed |

### `broker_next_step` / `collected_fields` / `still_needed_fields`

| Capability | Location | Status |
|------------|----------|--------|
| Category templates → `broker_next_step`, `client_prep` | `triage.py`, configs | Implemented |
| `claim_intake`, `cancellation_warning`, add-car lanes | `triage.py` | Implemented |
| P16-Y missing info library (20 patterns) | `triage.py`, configs | Implemented |
| `merge_still_needed_for_intent()` | `triage.py` | Implemented |
| Glance chips 已收集 / 还缺 | `BrokerWorkbenchTab.tsx` | Implemented |
| `humanizeStructuredField()` | `intakePure.ts` | Implemented |
| Office Actionability 25/25 on battery | P16-Y | Implemented (wording EN mix) |
| Multi-turn field merge on correction | `triage.py` | **Partial** (Y44/Y45) |

### Session / lifecycle

| Capability | Location | Status |
|------------|----------|--------|
| `session_store` — mid-flow restore | `session_store.py` | Implemented |
| `conversation_turns` on triage API | `routes/inbox_triage.py` | Implemented |
| `lifecycle_status`: handed_off → office_followup | `case_store.py` | Implemented |
| `case_lifecycle.py` helpers | `case_lifecycle.py` | Implemented |
| Customer multi-turn `submitMessage()` | `CustomerEntryTab.tsx` | Implemented (dev/trial gated) |
| `MyRequestsTab` / `UserCaseListProgressPanel` | UI | Implemented (product_only hidden) |

---

## TOP 20 existing continuity capabilities

| # | Capability | Why it matters for Case → Timeline → Next Action |
|---|------------|--------------------------------------------------|
| 1 | **`append_follow_up_message()`** | Core Turn-2+ — same `case_id`, updated draft |
| 2 | **`triage_for_append()`** | Re-classifies follow-up without new case |
| 3 | **`case_messages` thread** | Durable timeline per case |
| 4 | **`case_activity` audit log** | Office-visible “what happened” |
| 5 | **`conversation_summary` merge** | Case headline across turns (needs UX + Y44 tune) |
| 6 | **`collected_fields` / `still_needed_fields`** | Missing-info layer without re-reading paste |
| 7 | **`broker_next_step` + `client_reply_draft`** | Next Action for office + client |
| 8 | **Append boundary (`requires_new_case`)** | Prevents polluting wrong case |
| 9 | **`update_case_follow_up()`** | Explicit waiting state |
| 10 | **`PATCH follow-up` API** | Broker sets 在等客户/保司 |
| 11 | **`triage_conversation()` + turns** | Greenfield multi-bubble before persist |
| 12 | **`session_store` restore** | Resume in-progress intake |
| 13 | **Guardrail append simulations** | Regression safety for continuity |
| 14 | **P16-Y 50-case battery** | Proves L1–L4 single-turn engine |
| 15 | **`getCaseTrackingSummary()`** | Queue glance for follow-up state |
| 16 | **Broker reopen + append UI** | `handleAppendMessage` in workbench |
| 17 | **Customer `appendFollowUpMessage`** | Portal-style 提交补充 |
| 18 | **`lifecycle_status: office_followup`** | State machine for post-handoff |
| 19 | **Attachment on case** | Photo/doc continuity (claims, add-car) |
| 20 | **Category templates in config** | Tune next action without new service |

---

## Gaps (not missing capabilities — missing wiring)

| Gap | Type |
|-----|------|
| Post-copy CTA to append | UX copy |
| Append visible on first persist | UX layout |
| Summary merge on correction (Y44) | Engine tune |
| `case_messages` rendered as chat timeline | UX |
| `waiting_on` prominent after copy | UX |
| Customer tab on trial URL | Deploy/config |
| FP-004 SSO | Access |

---

*End of P16-Z4 Phase 1*
