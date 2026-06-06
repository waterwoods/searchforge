# P16-Z16 Phase 3 — Append Continuity Audit

**Date:** 2026-06-03  
**Sprint:** P16-Z16 Customer Builder Reality Validation  
**Sources:** `appendFollowUpMessage`, `append_follow_up_message()`, `triage_for_append()`, `case_messages`, `case_activity`, `BrokerWorkbenchTab.tsx`

---

## Executive answer

**Continuity survives end-to-end at the data layer.** Customer append → broker visibility → draft copy works without new architecture. **Customer UX** for append is post-handoff-only, collapsed, and lost on refresh. **Broker UX** is strong.

---

## End-to-end trace

```
Customer                          Backend                           Broker
────────                          ───────                           ──────
Create case
  formal submit ──────────────► save_case()
                                  case_id, case_messages[],          Opens workbench
                                  case_activity[case_created]  ◄───  Same case_id
Leave / return
  (case in store)
Add information
  appendFollowUpMessage ──────► triage_for_append()
  POST .../append-message         append_follow_up_message()
                                  + customer msg (seq N)
                                  + system reply (seq N+1)
                                  case_activity[follow_up_added]
                                  collected_fields merged
                                  formal_submitted_at UNCHANGED  ──► Sees updated case
                                                                     case_messages thread
                                                                     broker_next_step
                                                                     client_reply_draft
Copy next draft                   ◄──────────────────────────────── Copy button
```

---

## Function chain

### Frontend: `appendFollowUpMessage(caseId, text, clientId)`

`ui/src/api/inboxTriage.ts` → `POST /api/inbox/cases/{case_id}/append-message`

Used in `CustomerEntryTab.handlePostHandoffAppendSameCase()` — only when `lastCaseId` is set and formal submission complete.

### Route: `append_case_message`

1. Load case via `get_case_for_read(case_id)`
2. `triage_for_append(existing_source_text, new_message, reply_truth_context=...)`
3. Boundary enforcement: `new_issue` / `append_allowed=false` → blocked response, **no mutation**
4. Success → `append_follow_up_message(case_id, new_message, triage_result)`

### `triage_for_append()`

- Parses existing `source_text` into turns
- Runs `triage_conversation(..., for_append=True)`
- Sets `triage_mode: append`, `handoff_ready: true`
- Post-submit context: `lifecycle_status: office_followup` when `formal_submitted_at` present
- Vehicle boundary checks: `new_vehicle` → `requires_new_case`
- `_apply_append_case_boundary()` for matter-separation rules

### `append_follow_up_message()`

Preserves: `case_id`, `case_status`, `waiting_on`, `case_notes`, **`formal_submitted_at`**

Updates:

- `case_messages[]` — append customer + system messages with incrementing `sequence`
- `source_text` — rebuilt from messages
- Triage fields: `collected_fields`, `still_needed_fields`, `broker_next_step`, `client_reply_draft`, etc.
- `lifecycle_status` → `office_followup`
- `case_activity[]` — prepends `follow_up_added` entry
- `updated_at` — new timestamp

---

## `case_messages` and `case_activity`

### `case_messages`

| Event | Effect |
|-------|--------|
| `save_case` | Parsed from `source_text` at creation |
| `append_follow_up_message` | +2 entries (customer, system) per append |
| Sequence | Monotonic integer per case |

Live simulation (Tesla 3-day):

- After create: 3 messages
- After VIN append: 5 messages
- After driver append: 7 messages, sequences `[1..7]`

### `case_activity`

| Type | When |
|------|------|
| `case_created` | Formal persist |
| `follow_up_added` | Each successful append |
| `note_added` | Broker note |
| `follow_up_updated` | Broker PATCH waiting_on |

`formal_submitted_at` never changes on append — timeline truth is preserved.

---

## Broker visibility

`BrokerWorkbenchTab.tsx` consumes the same `SavedCase` payload:

- **`broker_next_step`** — glance + detail
- **`client_reply_draft`** — copy-to-send button
- **`case_activity`** — `follow_up_added` triggers update banner
- **`case_messages`** — thread card (post–P16-Z6)
- **`collected_fields` / `still_needed_fields`** — chips

Broker does not need a separate feed — append mutates the case the workbench already lists via `GET /api/inbox/cases`.

---

## Boundary enforcement (continuity safety)

When customer sends a **new matter** (e.g., billing question on Add-Car case):

- `append_blocked_new_issue: true`
- `case_boundary_action: requires_new_case`
- Case **not mutated**
- UI shows「提交新问题」

This protects timeline integrity — continuity is intentional, not blind merge.

---

## Continuity gaps (UX, not data)

| Gap | Impact |
|-----|--------|
| Append UI collapsed post-handoff | Customer may not discover append |
| `lastCaseId` not persisted | Refresh breaks append path |
| My Requests has no append | Must return to Customer Entry |
| Pre-submit turns not in `case_messages` until formal submit | Gap only during first session |

---

## Verdict

**Does continuity survive end-to-end?**

| Layer | Answer |
|-------|--------|
| **Database / API** | ✅ Yes |
| **Broker workbench** | ✅ Yes |
| **Customer builder UX** | ⚠️ Partial — works in-session post-handoff only |

No new architecture required for append continuity. Repackaging and wiring existing append path to return-later flows is the gap.
