# P16 — Phone Return Rehydration Root Cause

**Sprint:** P16-CUSTOMER-FIRST-CASE-REHYDRATION-ROOT-CAUSE-SPRINT  
**Issue:** Same-phone return finds active case but conversation / intake messages are gone  
**Date:** 2026-06-07

---

## Symptom

1. Customer completes several intake turns in tab A (phone claimed, add-car draft).
2. Opens new Chrome tab (or incognito).
3. Enters same phone → **active case card appears** (vehicle summary, Still Needed, contact state).
4. **Chat history empty** after Continue — only draft starter or blank collecting UI.

---

## Investigation answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Is conversation history persisted in Postgres? | **Only the Customer First draft starter** — not subsequent `/api/inbox/triage` turns. |
| 2 | If persisted, does active-case return it? | **No.** Endpoint returns summary card only (by design). |
| 3 | If returned, is frontend ignoring it? | **N/A** — not returned. |
| 4 | Where is conversation stored today? | **Browser React state** during session; optionally `in_progress_sessions` when **no** `case_id`; **not** on service record during collecting. |
| 5 | Is UI relying on browser local state for chat memory? | **Yes** — `turns[]` in `CustomerEntryTab`; `localStorage` for phone/name and `session_id`, not full thread when `case_id` bound. |
| 6 | Does phone return only restore summary? | **Before Continue:** yes (active-case). **After Continue:** `getSavedCase` should restore thread — but `case_messages` is nearly empty. |
| 7 | Expected or regression? | **Known architecture gap** documented in `P16Z16_TRUE_GAPS.md` / `P16Z18_CAPACITY_MODEL.md`; **worsened by Customer First** because draft + `case_id` binding skips both append and in-progress session save. |

**Classification:** Backend persistence gap (primary) + intentional active-case API shape (secondary UX surprise).

---

## API payload audit

### `GET /api/inbox/customer/active-case?phone=`

Implemented in `active_case_lookup.active_add_car_case_summary`:

```110:132:services/fiqa_api/inbox_triage/active_case_lookup.py
def active_add_car_case_summary(case: dict[str, Any]) -> dict[str, Any]:
    ...
    return {
        "case_id": ...,
        "vehicle_display": ...,
        "missing_fields": missing,
        "still_needed_fields": missing,
        "contact_state": contact_state,
        "status_label": status_label,
        "lifecycle_status": case.get("lifecycle_status"),
        ...
    }
```

**Included:** `case_id`, `still_needed_fields`, `lifecycle_status`, `vehicle_display`, contact/submit state.  
**Not included:** `source_text`, `case_messages`, conversation turns, timeline, `client_reply_draft`, append history.

This explains why **new tab before Continue** shows status card but **no chat** — not a frontend bug at that step.

### `GET /api/inbox/cases/{case_id}` (hydration path)

After two triage turns (live `case_9a86a610fb66`):

```json
{
  "case_messages": [
    { "role": "customer", "text": "开始加车申请（Customer First 入口）", "sequence": 1 }
  ],
  "source_text": "[客户] 开始加车申请（Customer First 入口）",
  "collected_fields": [],
  "still_needed_fields": ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"]
}
```

Customer BMW line and `2027` are **absent**.

---

## Root cause chain

### 1. Customer First creates a persisted draft immediately

`create_customer_first_add_car_draft` → `save_case` with single message:

```
[客户] 开始加车申请（Customer First 入口）
```

Phone is bound; `lifecycle_status: collecting`.

### 2. Collecting-phase triage binds `case_id` but does not append messages

`CustomerEntryTab.submitMessage` → `triageMessage(..., persistCase=true, caseId=lastCaseId)`.

In `triage_inbox` (`routes/inbox_triage.py`):

- When `existing_case` found, `result["case_id"]` is set (line ~1384).
- `append_follow_up_message` is **only** used by `POST /cases/{case_id}/append-message` — **not** by `/api/inbox/triage`.
- In-progress session save runs only when **no** `case_id`:

```1534:1536:services/fiqa_api/routes/inbox_triage.py
    # In-progress persistence: save turns + workflow_state when session_id and no case
    if request.session_id and not result.get("case_id"):
```

With Customer First draft, every turn has `case_id` → **no in-progress session write**.

- `persist_case` / `save_case` only runs on formal submit or non-add-car handoff — not on each collecting turn.

**Conversation lives only in React `turns` state until tab is closed.**

### 3. Phone return hydration reads empty `case_messages`

`handleCustomerFirstComplete` → `hydrateFromSavedCase` → `getSavedCase` → `customerEntryTurnsFromSavedCase`:

```225:253:ui/src/features/intake/utils/intakePure.ts
export function customerEntryTurnsFromSavedCase(saved): ... {
    const thread = allCaseThreadMessages(saved);
    ...
    for (const m of thread) { turns.push({ role, content: m.text }); }
```

With one draft message, customer sees **no BMW / 2027 history**.

### 4. `clearSessionId()` after case_id attachment removes fallback path

On triage response with `case_id`, UI calls `clearSessionId()` — in-progress restore via `getInProgressSession` cannot recover thread on new tab.

---

## Frontend vs backend

| Layer | Responsibility |
|-------|----------------|
| **Backend** | Failed to persist customer/system messages and slot updates during collecting when `case_id` bound |
| **Frontend** | Correctly hydrates from `case_messages`; nothing to show; active-case screen never promised chat pre-Continue |
| **API contract** | active-case summary-only; full case endpoint capable but empty |

---

## Database evidence

Live case `case_9a86a610fb66` after 2 triage turns:

| Table / field | Content |
|---------------|---------|
| `service_records` row | Exists, phone `6265550888`, `lifecycle_status=collecting` |
| `case_messages` (hydrated) | 1 customer message (draft starter) |
| Message bodies for BMW / 2027 | **Not present** |
| `collected_fields` | `[]` (never updated) |
| `in_progress_sessions` | Not written (blocked by `case_id` on triage) |

---

## UI evidence

| Step | What user sees |
|------|----------------|
| New tab, enter phone | Active Add-Car Request card — Still Needed list, no chat (expected for active-case API) |
| Tap Continue Request | Loading → at most one starter line; BMW thread missing |
| Same tab during intake | Full chat (React state only) |

`CustomerFirstEntryScreen` does not call `getSavedCase` until Continue — gap is visible immediately if user expects chat at phone-entry step.

---

## Severity

**P1**

| Dimension | Impact |
|-----------|--------|
| Customer trust | **High** — “phone is return key” breaks for conversation memory |
| Office trust | Low on this defect alone (office/workbench may differ) |
| Broker trust | Medium — customer may repeat information |
| First pilot readiness | **Blocks** multi-session Customer First story |
| North Star | Violates Cap 1 “post-submit / return rehydrate” and P16 Rule 2 phone return key for **memory**, not just case existence |

Not P0: case binding and status surface work. Not P2: constitution explicitly targets phone rehydrate.

---

## Minimal fix options (do not implement in this sprint)

### Recommended

**Fix 1 — Append on collecting triage when `case_id` is bound**

In `/api/inbox/triage`, after triage when `effective_case_id` and `append_allowed`:

```python
append_follow_up_message(case_id, text, triage_result)
```

Reuses existing message + field merge + Postgres persistence. Customer Entry already has all data; post-handoff path uses same primitive via `appendFollowUpMessage`.

**Fix 2 — Extend active-case payload (optional UX)**

Add `last_customer_message`, `message_count`, or truncated `case_messages` (last 6) for status-only return — **only after Fix 1** populates messages.

**Fix 3 — Do not `clearSessionId()` until formal submit**

Restores session fallback for same-device return; **insufficient alone** for incognito / new device (phone path must work).

### Acceptable interim product copy (if fix delayed)

On active-case card when `message_count <= 1`:

> 继续后您可补充车辆信息；此前对话记录尚未同步到此设备。

Honest, constitution-aligned, no fake timeline.

### Not recommended

- Full CRM / multi-case history
- New chat subsystem
- localStorage-only thread cache (incognito fails; not office-visible)

---

## Recommendation

**Root cause:** Collecting-phase `/api/inbox/triage` with `case_id` neither appends to `case_messages` nor saves in-progress session — conversation is client-ephemeral. Phone lookup correctly finds the draft case; hydration has nothing to replay.

**Primary fix:** Wire `append_follow_up_message` (or equivalent) into the bound-case triage path (~1–2 engineer-days, low risk, uses existing merge logic).

Pair with Issue 1 field-persistence so Still Needed on return matches last turn.
