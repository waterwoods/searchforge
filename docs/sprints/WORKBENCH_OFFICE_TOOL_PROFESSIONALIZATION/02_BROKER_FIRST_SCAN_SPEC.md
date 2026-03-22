# Broker First-Scan Spec

**Sprint:** Workbench Office Tool Professionalization

---

## 1. What a Broker Should Understand in 3–5 Seconds

| Item | Must see | Where |
|------|----------|-------|
| Case focus | Add car / Missing doc / Payment risk / etc. | Above fold |
| Quote-ready status | Quote-ready / Almost ready / Need more | Above fold |
| Contact identity | Name, phone — or "needed" | Above fold |
| Attachments | Present or not | Above fold |
| Correction / already_sent | If relevant | Near next step |
| Urgency | Same-day / high / medium | Above fold |
| One clear next step | broker_next_step | Above fold |
| Follow-up state | waiting_on, next_contact_by, due/overdue | Above fold |

---

## 2. What Belongs Above the Fold

1. Case focus tag
2. Quote-ready status (when add-car)
3. Contact block (name/phone or "needed")
4. Attachment presence (when add-car or missing_doc)
5. Correction / already_sent badge (when applicable)
6. Urgency tag (when high/critical)
7. **Your next move** — broker_next_step, bold
8. Collected / Still needed chips
9. **Follow-up** — waiting_on, next_contact_by, due-state (when set)

---

## 3. What Must Be Emphasized Visually

| Element | Treatment |
|--------|-----------|
| broker_next_step | Bold, larger font, labeled "您的下一步" |
| quote_ready_status | Tag with color (green/gold/orange) |
| correction / already_sent | Badge with background, near next step |
| urgency critical/high | Red/orange tag |
| contact missing | "Name needed" / "Phone needed" in secondary |
| attachments present | PaperClip icon + count |
| due today / overdue | Prominent tag (orange/red) |
| waiting_on broker | "Your move" / action-now treatment |

---

## 4. What Must NOT Hide

- What the customer said last
- Whether they corrected something
- Whether they said "already sent"
- What is still needed
- What to do next
- Whether a follow-up is pending
- Whether the case is due today or overdue

---

## 5. Queue Cards vs Case Detail

| Signal | Queue card | Case detail |
|--------|------------|-------------|
| Case focus | Yes | Yes |
| Quote-ready | Yes | Yes |
| Contact needed | Yes | Yes (full block) |
| Correction / already_sent | Yes | Yes |
| Urgency | Yes | Yes |
| broker_next_step | Preview (1 line) | Full, bold |
| waiting_on / next_contact_by | Yes (compact) | Yes (full section) |
| Due/overdue | Yes | Yes |
| Collected / still needed | Compact preview | Full chips |

---

*End of spec*
