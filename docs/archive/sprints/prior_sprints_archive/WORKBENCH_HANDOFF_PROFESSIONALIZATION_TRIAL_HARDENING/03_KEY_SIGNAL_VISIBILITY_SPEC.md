# Key Signal Visibility Spec

**Sprint:** Workbench Handoff Professionalization + Trial Hardening

---

## 1. Signal Priority and Visual Treatment

| Signal | Priority | Visual treatment | When shown |
|--------|----------|-------------------|------------|
| quote_ready_status | High | Tag (green/gold/orange) | Add-car cases |
| customer_name / customer_phone | High | Inline text or "needed" | When quote-ready or collected has name/phone |
| case_attachments | High | PaperClip + count | When present; "Upload" when empty |
| follow_up_type=correction | High | Badge, gold background | When correction |
| follow_up_type=already_sent | High | Badge, blue background | When already_sent |
| urgency | High | Tag (red/orange) | critical/high |
| secondary_issue_note | Medium | Tag or inline | When present |
| still_needed_fields | High | Orange chips | Always when present |
| follow-up memory / waiting_on / next_contact_by | Medium | Inline or tag | When set |

---

## 2. Queue Card (List View) Signals

On each case card in the queue, broker should see at a glance:
- Case focus
- Attention state (Action now / Due today / etc.)
- Readiness (Quote-ready / Verify receipt / Needs more)
- Attachment count (if any)
- Urgency
- **Correction / already_sent** — currently missing on queue cards

---

## 3. Case Detail (Opened Case) Signals

All key signals must appear above the fold:
1. Case focus + lifecycle + attention
2. **Your next move** (broker_next_step)
3. Correction / already_sent badge (when applicable)
4. Quote-ready status (when add-car)
5. Contact block
6. Supporting materials (attachments)
7. Collected / Still needed
8. Recent customer messages

---

## 4. Signals That Must NOT Be Buried

- quote_ready_status
- customer_name / customer_phone
- attachments present
- correction made
- already_sent / already_paid
- urgency / cancellation risk
- secondary issue note (if present)
- still_needed_fields
- follow-up memory / waiting_on / next_contact_by (if present)

---

*End of spec*
