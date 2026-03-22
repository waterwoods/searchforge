# Acceptance / Mixed-Intent Criteria

**Sprint:** Mixed-Intent + Secondary Case Strategy  
**Purpose:** Practical criteria for clearer primary goal, less case pollution, clearer broker handoff.

---

## 1. Clearer Primary Goal

| Criterion | Pass |
|-----------|------|
| Primary intent is identifiable | conversation_summary starts with intent hint |
| Primary drives broker_next_step | Main action matches primary |
| Mixed messages route to LLM when flow_count >= 2 | Already in triage.py |

---

## 2. Less Case Pollution

| Criterion | Pass |
|-----------|------|
| Same-goal corrections stay in case | No split on correction/clarification |
| Secondary noted when present | secondary_issue_note or "Also asked" in summary |
| One case does not become 4 unrelated goals | Primary + at most one secondary note |

---

## 3. Clearer Broker Handoff

| Criterion | Pass |
|-----------|------|
| broker_next_step is one main action | Not a list of 5 things |
| Secondary visible when relevant | "Also asked" or "If customer also asked about X" |
| Broker can tell what to do first | Primary explicit |

---

## 4. Realistic Mixed-Intent Handling

| Criterion | Pass |
|-----------|------|
| Mixed-intent sim pack passes | run_complex_adversarial_simulation.py mixed_intent |
| At least primary addressed in draft | Draft contains primary-relevant content |
| Secondary addressed when easy (e.g. document confusion) | Draft mentions garaging/dec when in message |

---

## 5. Acceptable to Defer

| Deferred | Reason |
|----------|--------|
| Auto-split to second case | V1: mark only; broker decides |
| Full secondary draft coverage | Primary first; secondary note suffices |
| Multi-threaded conversation engine | Overbuild |
| All ambiguous cases resolved | Unrealistic |

---

*End of Criteria*
