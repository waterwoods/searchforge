# Broker Next Step Professionalization Spec

**Sprint:** Workbench Office Tool Professionalization

---

## 1. What Good Next-Step Quality Looks Like

- **Specific** — Names vehicle, document, or action
- **Immediate** — What to do now, not "eventually"
- **Operational** — Office-usable, not abstract
- **1–2 sentences** — Concise

### Examples (strong)

- "Verify materials received via WeChat; run quote for 2024 Tesla Model Y when confirmed."
- "Confirm name and phone for follow-up; office can continue quote."
- "Review renewal notice and confirm remove-vehicle intent."
- "Verify sale date and transfer status; process removal and confirm what stays covered."

---

## 2. What Patterns Are Too Vague

- "Continue processing"
- "Follow up as needed"
- "Review case"
- "Review and act on {category}."

---

## 3. Scenario-Specific Targets

| Scenario | Good broker_next_step |
|----------|------------------------|
| Add-car + materials sent | Verify materials received; run quote when confirmed |
| Add-car + quote-ready, no contact | Run quote; confirm name and phone for follow-up |
| Missing doc + already_sent | Verify carrier received; do not re-request |
| Remove vehicle | Verify sale date and transfer; process removal |
| Premium review + remove-vehicle | Review renewal notice; confirm which vehicle to remove |
| Cancellation risk | Confirm balance due; call or text client today |
| Contact missing | Confirm name and phone for follow-up |

---

## 4. How to Reject Weak Patterns

- Guardrail: reject "continue processing", "follow up as needed", "review and act on"
- Simulation: BS9 (remove-vehicle), BS10 (quote-ready + no contact)
- Config fallback: use "Review the {category} message; confirm what the client needs and take the next step." instead of "Review and act on {category}."

---

*End of spec*
