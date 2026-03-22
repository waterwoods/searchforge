# Case Card / Case Detail Structure Spec

**Sprint:** Workbench Office Tool Professionalization

---

## 1. Case Card (Queue List View)

Each case card should show at a glance:

| Element | Required | Notes |
|---------|----------|-------|
| Case focus | Yes | Tag (Add car quote, Missing document, etc.) |
| Attention state | Yes | Action now / Due today / Your move / Waiting on client |
| Due tag | When set | Overdue / Due today / Due tomorrow |
| Readiness | Yes | Quote-ready / Verify receipt / Needs more |
| Quote-ready status | Add-car | Quote-ready / Almost ready / Need more |
| Correction badge | When correction | Gold "Corrected" |
| Already sent badge | When already_sent | Blue "Already sent" |
| Contact needed | Quote-ready, no name/phone | Orange "Contact needed" |
| Attachment count | When present | PaperClip + count |
| Urgency | Yes | critical / high / medium |
| Source preview | Yes | 1 line, ~80 chars |
| Compact preview | Yes | Collected/missing summary |
| **Next step preview** | Yes | 1 line broker_next_step (~60 chars) |
| **Follow-up summary** | When set | waiting_on + next_contact_by |

---

## 2. Case Detail — Working Case Sheet Structure

The case detail should feel like a working office case sheet, not a debug panel.

### Section hierarchy (top to bottom)

1. **Case focus / status** — What this case is; lifecycle; attention
2. **Your next move** — broker_next_step (bold, prominent)
3. **Correction / already_sent** — Badge when applicable
4. **Customer** — Name, phone (or "needed")
5. **Collected** — Green chips
6. **Still needed** — Orange chips
7. **Materials** — Attachments or upload
8. **Broker next step** — (redundant with #2 if same; can be single block)
9. **Follow-up / waiting_on / next_contact_by** — Due-state, who we're waiting on
10. **Draft reply** — Editable, below action block

### What must NOT be buried

- broker_next_step
- quote_ready_status
- contact block
- correction / already_sent
- follow-up (waiting_on, next_contact_by, due-state)

---

## 3. Signals: Queue vs Detail

| Signal | Queue card | Case detail |
|--------|------------|-------------|
| Case focus | Tag | Tag + one-liner |
| Quote-ready | Tag | Tag + section |
| Contact | "Contact needed" tag | Full block |
| Correction | Badge | Badge + context |
| Already sent | Badge | Badge + context |
| broker_next_step | 1-line preview | Full, bold |
| waiting_on | Inline/tag | Full section |
| next_contact_by | Inline/tag | Full section |
| Due/overdue | Tag | Tag + section |
| Collected | Compact | Full chips |
| Still needed | Compact | Full chips |

---

## 4. Layout Principles

- **Above the fold:** Case focus, next step, correction/already_sent, quote-ready, contact, follow-up
- **Secondary:** Client prep, full conversation, activity log
- **No visual noise:** Avoid redundant labels; group related signals

---

*End of spec*
