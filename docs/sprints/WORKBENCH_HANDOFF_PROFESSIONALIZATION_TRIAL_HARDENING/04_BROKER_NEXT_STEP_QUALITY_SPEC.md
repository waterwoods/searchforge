# Broker Next Step Quality Spec

**Sprint:** Workbench Handoff Professionalization + Trial Hardening

---

## 1. What Good broker_next_step Looks Like

- **Specific** — Names concrete actions (verify, confirm, run quote)
- **Context-aware** — Mentions vehicle, document, or deadline when relevant
- **Actionable** — Broker knows exactly what to do next
- **1–2 sentences** — Not a paragraph

**Good examples:**
- "Confirm delivery date and main driver, then run quote"
- "Verify registration/dec page received and continue pricing"
- "Confirm name and phone for follow-up; office can continue quote"
- "Review renewal notice and confirm remove-vehicle intent"
- "Verify with carrier that resubmitted documents were received; request any still-missing items."

---

## 2. What Weak broker_next_step Looks Like

- **Vague** — "Continue processing", "Follow up as needed"
- **Generic** — "Customer asked about insurance"
- **No concrete action** — Doesn't tell broker what to do
- **Too long** — Paragraph instead of instruction

**Weak examples:**
- "Continue processing"
- "Follow up as needed"
- "Customer asked about insurance"

---

## 3. How It Should Adapt by Scenario

| Scenario | broker_next_step pattern |
|----------|--------------------------|
| add-car quote_ready | "Run quote for {vehicle}. Confirm delivery/driver. Confirm name and phone for follow-up." |
| add-car almost_ready | "Collect {still_needed}. Then run quote." |
| missing_document + already_sent | "Verify with carrier that resubmitted documents were received; request any still-missing items." |
| premium review + remove-vehicle | "Review renewal notice and quote options; confirm remove-vehicle intent if client asked." |
| cancellation_warning + already_paid | "Confirm with carrier that payment was received; if not, process payment today." |
| contact_missing | Include "Confirm name and phone for follow-up." |
| attachment_present | Can mention "Registration/dec page received — can speed up quote." |

---

## 4. How It Should Reduce Broker Rework

- **Avoid re-reading** — Next step should summarize what broker needs to know
- **Avoid re-asking** — If contact missing, say so
- **Avoid wrong action** — If already_sent, say "verify receipt" not "request again"
- **Avoid missed urgency** — If critical, say "today" or "same-day"

---

*End of spec*
