# Handoff Timing Evaluation Criteria

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Purpose:** Define how each simulation is judged.

---

## Evaluation Dimensions

| Dimension | Question | Strong | Weak |
|-----------|----------|--------|------|
| **Too early?** | Did handoff happen before customer finished? | No | Yes |
| **Too late?** | Did we ask unnecessary questions? | No | Yes |
| **Ask-next useful?** | When we asked, was it the right next thing? | Yes | No |
| **Case complete enough?** | Did broker get sufficient context? | Yes | No |
| **broker_next_step useful?** | Is next move actionable? | Yes | No |
| **Room to finish?** | Did user have fair chance to add key details? | Yes | No |

---

## Per-Category Timing Rules

| Category | Good Handoff When | Too Early When | Too Late When |
|----------|-------------------|----------------|---------------|
| add_car | year+model + zip + (delivery or driver) | Hand off with only year+model | Ask for driver when delivery present and we have enough |
| missing_document | Item + sent status | Hand off before answering "是什么意思" | Ask same thing 3+ times |
| premium_review | Policy/bill mentioned | Hand off before remove-vehicle intent | Ask for bill when already sent |
| payment_failed | Notice + proof/screenshot | Hand off before screenshot | Ask for notice when already sent |
| talk_to_agent | Immediately | Any delay | N/A |
| vague | Never T1 | Hand off T1 | N/A |

---

## Classification

- **Strong:** Handoff at right time; case complete; broker_next_step actionable.
- **Acceptable:** Minor timing friction; broker can work with it.
- **Weak:** Handoff too early; missed key info; broker rework.
- **Trial-risky:** Trust-breaking; incomplete case; customer cut off.

---

*End of Criteria*
