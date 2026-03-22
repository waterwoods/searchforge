# Fix Queue / Redeploy Spec

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Purpose:** Define fix-now / acceptable / fix-next; when code fix justified; when redeploy required.

---

## Fix-Now Criteria

- Blocks real broker trial
- Trust-breaking (customer cut off, wrong info handed off)
- Broker receives unusable case

---

## Acceptable-for-Trial Criteria

- Minor timing friction
- Broker can infer from source_text
- T3 would append in real flow
- Document for observation log

---

## Fix-Next Criteria

- High value; 1–2 sprints
- Improves completeness or broker confidence
- Not blocking trial

---

## When a Code Fix Is Justified

- Evidence from simulation or manual test
- Small, low-risk change (single threshold, one ask, one summary tweak)
- No workflow engine redesign
- Clear broker value

---

## When Redeploy Is Required

- Any change to `services/fiqa_api/inbox_triage/triage.py`
- Backend deploy path: `bash scripts/deploy_rag_demo.sh`

---

## Small Fixes Allowed

- One more ask for premium when bill_sent but no remove_vehicle at T2
- One more ask for payment when paid but no screenshot at T2
- Marker additions
- Single threshold tweak

---

## NOT Allowed

- Redesign workflow engine
- Broad state machine refactor
- New scenario systems
- Platform refactors

---

## Deferred Fix-Next (This Sprint)

**Premium/Payment "one more ask":** Implemented and tested; would improve HT3, HT9, HT10 (handoff at T3 instead of T2). **Reverted** because it breaks 2-turn scenarios (SIM7, SIM9, R1, R6, SIM13) — those would never hand off. **Fix-next:** Scope the ask to 3+ turn conversations only (e.g. when conversation_turns has ≥1 prior customer turn at T2), so 2-turn flows still hand off.

---

*End of Spec*
