# Early-Handoff Simulation Pack Spec

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Purpose:** Define realistic pack focused on "one more useful question" patterns.

---

## Simulation Categories

| ID | Category | Business Goal | Timing Risk | Strong Behavior | Acceptable-for-Trial |
|----|----------|---------------|-------------|-----------------|----------------------|
| HT1 | add_car | Add-car + driver in T3 | Ask driver T2; handoff T3 | Ask driver T2; handoff T3 | Same |
| HT2 | missing_document | Missing doc + garaging T3 | T2 handoff; T3 question | Handoff T2; T3 append | Same |
| HT3 | premium_review | Premium + remove-vehicle T3 | T2 handoff; T3 adds idea | Defer T2; ask remove-vehicle; handoff T3 | T2 handoff; T3 append |
| HT4 | talk_to_agent | Fast handoff | Must hand off T1 | Hand off T1 | Same |
| HT5 | add_car | Correction | Wrong vehicle | Use correction; handoff T3 | Same |
| HT6 | mixed_intent | Mixed T1 | Close on one | No handoff T1; collect both | Same |
| HT7 | vague | Vague T1 | Hand off T1 | No handoff T1 | Same |
| HT8 | add_car | Add-car + side question same turn | Ignore question | Answer + handoff T2 | Same |
| HT9 | payment_failed | Payment + screenshot T3 | T2 handoff; T3 adds proof | Ask screenshot T2; handoff T3 | T2 handoff; T3 append |
| HT10 | premium_review | Premium + which vehicle T3 | T2 handoff; T3 adds detail | Defer T2; ask which vehicle; handoff T3 | T2 handoff; T3 append |

---

## One More Useful Question Patterns

1. **Premium review after bill_sent but before remove-vehicle idea** — Ask "是否有一辆想拿掉或调整？"
2. **Payment marked paid but screenshot not yet asked for** — Ask "截图发了吗"
3. **Missing document but one clarifying material question remains** — Answer doc question; hand off
4. **Add-car where one practical detail still matters** — Ask driver when delivery present
5. **Correction arriving one turn after likely handoff point** — Use correction; hand off with correct info

---

## Over-Questioning (What to Avoid)

- Asking for bill when already sent
- Asking for driver when add-car + doc question in same turn (HT8 fix)
- Endless questioning when user already provided enough
- Slowing talk-to-agent handoff

---

*End of Spec*
