# Evaluation Criteria Spec

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Purpose:** Define how each simulation is judged.

---

## Judgment Dimensions

| Dimension | Definition | Strong | Acceptable | Weak |
|-----------|------------|--------|------------|------|
| **Too early?** | Handoff before customer finished | No | No | Yes |
| **Too late?** | Unnecessary extra asks | No | No | Yes |
| **Case completeness** | Broker can act without reconstructing | High | Sufficient | Low |
| **broker_next_step** | Concrete, actionable | Yes | Yes | Vague |
| **One more question** | Would materially help broker | Asked when needed | T3 append OK | Missed |

---

## Per-Simulation Criteria

- **HT1–HT2, HT4–HT8:** Strong = pass; acceptable = pass with note
- **HT3, HT9, HT10:** Strong = defer T2, ask one more, handoff T3; acceptable = T2 handoff, T3 append
- **Fix-now:** Blocks trial; trust-breaking
- **Fix-next:** High value; not blocking
- **Acceptable:** Document for observation; no fix this sprint

---

*End of Spec*
