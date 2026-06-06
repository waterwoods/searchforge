# P16-Z17 Phase 5 — Timeline Test

**Date:** 2026-06-03  
**Sprint:** P16-Z17 Customer Case Builder Reality Sprint  
**Case:** `case_98f4ac099d15`  
**Inspect:** `case_messages`, `case_activity`

---

## Question

Do we already have a usable timeline across Day 1, Day 2, Day 3?

---

## case_messages (full thread — 11 entries)

| Seq | Role | Created (UTC) | Text (summary) |
|-----|------|---------------|----------------|
| 1 | customer | 2026-06-03T08:58:13Z | I bought a Tesla. |
| 2 | system | 2026-06-03T08:58:13Z | Confirmation prompt — still need slots |
| 3 | customer | 2026-06-03T08:58:13Z | VIN + zip + delivery + driver + 2024 Model 3 |
| 4 | system | 2026-06-03T08:58:13Z | Update saved on service record |
| 5 | customer | 2026-06-03T08:58:13Z | OK |
| 6 | system | 2026-06-03T08:58:13Z | Update saved |
| 7 | customer | 2026-06-03T08:58:13Z | 【正式提交办公室】… |
| 8 | customer | 2026-06-03T08:58:21Z | VIN is 5YJ3E1EA1KF123456 *(Day 2 append)* |
| 9 | system | 2026-06-03T08:58:21Z | 补充已写入同一条服务记录 |
| 10 | customer | 2026-06-03T08:58:23Z | My daughter will drive it too. *(Day 3 append)* |
| 11 | system | 2026-06-03T08:58:23Z | 已把这次补充记到当前服务记录里 |

**Properties verified:**

- Monotonic `sequence` 1→11
- Distinct `created_at` on append messages (Day 2/3 later than Day 1 batch)
- Customer + system roles both stored
- `source_text` rebuilt from messages (broker collapse view)

---

## case_activity (audit trail — 3 entries)

| Type | Created (UTC) | Message |
|------|---------------|---------|
| `conversation_appended` | 2026-06-03T08:58:23Z | Conversation updated (lifecycle: office_followup). |
| `conversation_appended` | 2026-06-03T08:58:21Z | Conversation updated (lifecycle: office_followup). |
| `case_created` | 2026-06-03T08:58:13Z | Case record created. |

Newest-first ordering in store. Broker dev panel maps all entries; trial uses latest activity for update badges.

---

## Day boundary mapping

```
Day 1 (collection + formal submit)
  seq 1-7 @ 08:58:13Z
  activity: case_created

Day 2 (append)
  seq 8-9 @ 08:58:21Z
  activity: conversation_appended

Day 3 (append)
  seq 10-11 @ 08:58:23Z
  activity: conversation_appended
```

All three days preserved in one record. `formal_submitted_at` stays at Day 1 submit moment.

---

## Who sees the timeline?

| Actor | Timeline surface | Usable? |
|-------|------------------|---------|
| **Broker** | 对话记录 (last 5) + full source_text + activity (dev) | ✅ Yes |
| **Customer My Requests** | Progress fields + timestamps; **not** full message thread | ⚠️ Partial |
| **Customer Entry** | In-memory `turns[]` only; **lost on refresh** post-submit | ❌ No |

---

## Answer

## **Yes — we already have a usable timeline at the persistence layer.**

`case_messages` + `case_activity` on the saved case are sufficient for broker multi-day review. No new timeline service required.

**Customer-facing timeline UI is not built** — that is a wiring gap, not a data gap.

---

## Verdict

| Criterion | Score |
|-----------|-------|
| Messages preserved across days | ✅ |
| Sequences monotonic | ✅ |
| Activity audit trail | ✅ |
| Broker can read chronology | ✅ |
| Customer sees chronology after return | ❌ |

**Timeline infrastructure: 90/100. Customer visibility: 35/100.**
