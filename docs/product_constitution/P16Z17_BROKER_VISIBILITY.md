# P16-Z17 Phase 4 — Broker Visibility Test

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Case:** `case_98f4ac099d15` (after Day 2 + Day 3 appends)  
**Surface:** Broker Workbench (`BrokerWorkbenchTab`) + `GET /api/inbox/cases/{case_id}`

---

## Test procedure

1. Customer completes formal submit + two append messages (VIN reconfirm, daughter drives).
2. Broker opens Unified Intake → Broker Workbench tab.
3. Load queue: `GET /api/inbox/cases`
4. Open case: `GET /api/inbox/cases/case_98f4ac099d15`

No customer conversation reopen required.

---

## Broker can see (live payload)

| Field | Present | Value / notes |
|-------|---------|---------------|
| **case_id** | ✅ | `case_98f4ac099d15` (copyable in dev; short ID in trial) |
| **Latest summary** | ✅ | `broker_next_step`: "Run quote for 2024 Tesla Model 3. Confirm delivery date and driver with client before binding. Confirm name and phone for follow-up." |
| **collected_fields** | ✅ | `year, make_model, vin, zip, delivery_date, primary_driver, insurance_status_add_to_existing` |
| **missing fields** | ✅ | `still_needed_fields: []` — hero checklist empty |
| **timeline (case_messages)** | ✅ | 11 messages — last 5 shown in **对话记录** card |
| **timeline (case_activity)** | ✅ | 3 entries — `case_created` + 2× `conversation_appended` |
| **source_text** | ✅ | Full bracket-tagged thread in collapsed **完整对话（备查）** |
| **formal_submitted_at** | ✅ | `2026-06-03T08:58:13Z` |
| **updated_at** | ✅ | Reflects Day 3 append |

### Last 5 messages visible to broker (对话记录)

| Role | Text (truncated) |
|------|------------------|
| customer | 【正式提交办公室】… |
| customer | VIN is 5YJ3E1EA1KF123456 |
| system | 补充已看到。补充已写入同一条服务记录… |
| customer | My daughter will drive it too. |
| system | 收到你补充的信息。已把这次补充记到当前服务记录里… |

---

## UI surfaces (code map)

| Component | File | What broker sees |
|-----------|------|------------------|
| Queue cards | `BrokerWorkbenchTab.tsx` | Preview, urgency, Add-Car status strip; trial hides full case_id on card |
| Hero glance | `OfficeWorkbenchOneGlanceSummary` in `WorkbenchSummary.tsx` | Headline, **缺少资料** checklist, next step, vehicle line |
| Thread | `formatCaseMessagesForThread()` in `intakePure.ts` | Last 5 `case_messages` |
| Activity audit | `BrokerWorkbenchTab` **操作记录** | Full `case_activity[]` — **dev mode only** (`!productOnlyUi`) |
| Follow-up banner | **整理明细** | `follow_up_added` / `conversation_appended` → "最近更新" badge |

Trial/paid-pilot mode: broker gets glance + message thread + append paste; full activity panel hidden.

---

## Can broker understand case without reopening customer conversation?

## **Yes.**

Evidence:

- Structured `collected_fields` humanized in hero and collapse panels
- `broker_next_step` gives actionable office instruction after each append
- `case_messages` preserves Day 1 thread + Day 2/3 appends in order
- `client_reply_draft` available for copy-to-client workflow
- Append updates `broker_next_step` without requiring broker to re-triage manually

Broker does **not** need to switch to Customer Entry or replay chat to understand vehicle, VIN, driver change, or next action.

---

## Gaps (non-blockers for pilot)

| Gap | Impact |
|-----|--------|
| Queue list is lightweight — full timeline only after open | Minor — one click |
| Trial hides **操作记录** full audit | Broker still sees message thread + badges |
| `office_case_title` null on this case | Headline falls back to inferred category — still usable |

---

## Verdict

**Broker Review: PASS at data + workbench layer.** Same `case_id` from customer formal submit through multi-day append; broker workbench reflects all updates.
