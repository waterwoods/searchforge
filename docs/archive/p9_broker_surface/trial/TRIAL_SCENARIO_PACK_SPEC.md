> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Trial Scenario Pack Spec

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. Scenario Pack for Trial

The trial uses the **Broker Standard Package** 7 scenarios, with **5 core trial scenarios** (SIM1–SIM5) as the primary validation path.

---

## 2. Core Trial Scenarios (Recommended Order)

| # | Scenario | SIM ID | Turns | Why included | Customer experience | Broker gets | Success |
|---|----------|--------|-------|--------------|---------------------|-------------|---------|
| 1 | **Cancellation risk** | SIM1 | 3 | Urgency, same-day action | Notice question → sent screenshot → payment confusion | Urgent case; verify receipt; clarify with carrier | Broker knows what to do same day |
| 2 | **Missing document** | SIM2 | 3 | "Already sent" pain | Need dec+garaging; client sent dec; asks what garaging means | Structured follow-up; verify receipt; clarification | Broker avoids re-asking for dec |
| 3 | **Add-car quote** | SIM3 | 3 | Revenue, multi-turn | Quote ask → year → zip+delivery | Collected chips (year, model, zip); Still needed if any | Broker has enough to quote |
| 4 | **Premium review** | SIM6 | 3 | Retention | Premium too high → sent bill → remove vehicle? | Retention follow-up; office reviews first | Broker can act on renewal |
| 5 | **Claim intake** | SIM5 | 3 | First-response | Accident → hit-and-run → what matters most? | First-response guidance; collected/still-needed | Broker knows next step |

---

## 3. Extended Trial Scenarios (Optional)

| # | Scenario | Why | When to include |
|---|----------|-----|-----------------|
| 6 | Billing clarification | Payment risk; same-day | If broker handles billing often |
| 7 | Talk to Agent / handoff | Customer wants human | Always available; part of flow |

---

## 4. Per-Scenario Success Criteria

| Scenario | Successful interaction means |
|----------|-----------------------------|
| Cancellation risk | Case shows urgency=critical; broker next move is actionable; draft mentions payment/verify |
| Missing document | Case shows what was sent vs still needed; broker can verify without re-asking |
| Add-car quote | Collected chips show year, model, zip (or delivery); broker has enough to quote |
| Premium review | Case shows policy/bill mentioned; broker can review and follow up |
| Claim intake | Case shows accident details; broker knows first-response steps |

---

## 5. Simulation Assistant Mapping

| Trial scenario | Simulation Assistant | Config |
|----------------|----------------------|--------|
| Cancellation risk | SIM1 | `configs/simulation_assistant_scenarios.json` |
| Missing document | SIM2 |同上 |
| Add-car quote | SIM3 |同上 |
| Premium review | SIM6 |同上 |
| Claim intake | SIM5 |同上 |

---

## 6. What to Measure Per Scenario

- Did the broker understand the case?
- Did Collected/Still needed reduce manual follow-up?
- Was the draft usable with minimal edits?
- Did the broker know the next move?

---

*End of Trial Scenario Pack Spec*
