# Handoff Risk / Fix Queue Spec

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Purpose:** Define fix-now / fix-next / acceptable-for-trial.

---

## Timing Issue Groups

| Group | Description | Examples |
|-------|-------------|----------|
| **Handoff too early** | Case handed off before customer finished | T2 handoff when T3 adds driver/remove-vehicle/screenshot |
| **Handoff too late** | Unnecessary extra asks | Ask for bill when already sent |
| **Summary incomplete** | conversation_summary missing key detail | Correction not reflected |
| **broker_next_step too weak** | Vague "Review and follow up" | Should say "Verify receipt with carrier" |
| **Mixed-intent before handoff** | Close on one intent only | Add-car + garaging — answer one, ignore other |
| **Correction after handoff point** | Wrong vehicle/notice in summary | "不是这个车" not used |

---

## Fix-Now Criteria

- Blocks real broker trial
- Trust-breaking (customer cut off, wrong info handed off)
- Broker receives unusable case

---

## Fix-Next Criteria

- High value; 1–2 sprints
- Improves completeness or broker confidence
- Not blocking trial

---

## Acceptable for First Trial

- Minor timing friction
- Broker can infer from source_text
- Document for observation log

---

## Small Fixes Allowed

- Marker additions (e.g. "还有一个问题", "对了", "顺便问一下")
- Single threshold tweak (e.g. defer handoff when continuation marker)
- One broker_next_step improvement
- One summary builder tweak

---

## NOT Allowed

- Redesign workflow engine
- Broad state machine refactor
- New scenario systems
- Platform refactors

---

*End of Spec*
