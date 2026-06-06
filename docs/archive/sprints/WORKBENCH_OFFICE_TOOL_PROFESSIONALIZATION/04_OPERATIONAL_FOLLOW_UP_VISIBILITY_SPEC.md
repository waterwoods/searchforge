# Operational Follow-Up Visibility Spec

**Sprint:** Workbench Office Tool Professionalization

---

## 1. How waiting_on / next_contact_by / due-state Should Appear

| Signal | Queue card | Case detail |
|--------|------------|-------------|
| waiting_on | Tag or inline | Section header + value |
| next_contact_by | Inline (e.g. "by 2026-03-21") | Full date + due-state |
| Due-state | Overdue / Due today / Due tomorrow | Same + reason |
| follow_up_type | Optional | When relevant |

---

## 2. How Overdue / Due-today / Due-tomorrow Should Surface

| State | Visual | Priority |
|-------|--------|----------|
| Overdue | Red tag "Overdue" | Highest — action now |
| Due today | Orange tag "Due today" | High |
| Due tomorrow | Gold tag "Due tomorrow" | Medium |
| No due date | "No due date" or omit | Low |

---

## 3. How Follow-Up Influences Prioritization

- **Action-now cases:** Overdue, due today, waiting_on=broker
- **Tracking cases:** Due tomorrow, waiting_on=client, etc.
- Queue ordering: action-now first, then by due-date, then by updated_at

---

## 4. How This Reduces Broker Rework and Missed Follow-Up

- **Overdue visible on queue card** — Broker sees at a glance which cases slipped
- **Due today prominent** — Same-day check-ins don't get lost
- **waiting_on visible** — Broker knows who owns the next move
- **next_contact_by on card** — No need to open case to see follow-up plan

---

*End of spec*
