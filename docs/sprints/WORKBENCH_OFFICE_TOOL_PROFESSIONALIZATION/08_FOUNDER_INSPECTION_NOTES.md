# Founder Inspection Notes

**Sprint:** Workbench Office Tool Professionalization

---

## 1. What Founder Should Inspect After This Sprint

1. **Queue scan** — Load demo queue → Can you tell in 3–5 seconds which cases need same-day action, which are quote-ready, which have correction/already_sent, which are due today?
2. **Next-step preview** — Do queue cards show a 1-line broker_next_step preview?
3. **Follow-up on cards** — Do cards show waiting_on / next_contact_by / due-state when set?
4. **Case detail hierarchy** — Does the opened case feel like a working case sheet? Is follow-up above the fold?
5. **broker_next_step quality** — Open add-car, missing doc, remove-vehicle cases → Is the next step concrete?

---

## 2. Which Case Types to Test First

| # | Case type | What to expect |
|---|-----------|----------------|
| 1 | Cancellation risk | Same-day action; concrete next step |
| 2 | Missing document + already_sent | "Already sent" badge; "Verify receipt" |
| 3 | Add-car quote-ready | Quote-ready tag; contact block; vehicle in next step |
| 4 | Add-car + no contact | "Contact needed" tag; next step mentions contact |
| 5 | Remove vehicle | broker_next_step says verify sale/transfer, process removal |
| 6 | Due today / overdue | Due tag on queue card; prominent in case detail |

---

## 3. What "Good Enough for Real Broker Office Demo" Looks Like

- Broker can scan queue in 3–5 seconds
- Key signals (quote-ready, correction, already_sent, contact, due-state) visible without opening
- broker_next_step feels like real office instruction
- Case detail has clear section hierarchy
- Follow-up (waiting_on, next_contact_by) visible and actionable

---

*End of notes*
