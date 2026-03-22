# Fix Queue Hardening Spec

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. Fix Decision Criteria

| Decision | When | Example |
|----------|------|---------|
| **Fix now** | Blocks trial or breaks trust | Talk to Agent routes wrong; next move always generic; broker says "can't use" |
| **Fix next** | High value; can ship in 1–2 sprints | Correction badge not visible; observation log missing fields |
| **Defer** | Lower priority; document for later | Inbox sync; OCR; carrier API; broad refactors |

**Rule:** If broker would say "I can't use this" → fix now. If "this could be better" → fix next. If feature request or infra → defer.

---

## 2. Group Issues By Layer

| Layer | Examples |
|-------|----------|
| **Scenario layer** | add_car_enough_for_handoff; collected_fields extraction; marker coverage |
| **Workbench / handoff** | broker_next_step; reply template; next move visibility |
| **Configuration / client-aware** | handoff_phrases; client_id persistence; append context |
| **Trial workflow / docs** | Observation log; founder checklist; broker one-pager |
| **UI/UX** | Case card readability; Human confirmation badge; Resume here |

---

## 3. Root-Cause Classes

| Class | Description |
|-------|-------------|
| Marker coverage too narrow | Intent phrase not in markers; routes to customer_question |
| Triage order issue | Higher-priority intent loses to lower |
| Handoff threshold issue | Hands off too early or too late |
| Append flow too generic | triage_for_append doesn't use correction well |
| Client-aware continuity gap | client_id lost; handoff_phrases not client-specific |
| UI/readability ambiguity | broker_next_step buried; correction invisible |
| Trial docs/process gap | No Day 1 checklist; no observation template |

---

## 4. Small Fixes Allowed (This Sprint)

- Small marker additions
- Single broker_next_step improvement
- One UI visibility tweak
- One config phrase addition

**NOT allowed:**
- Redesign platform layers
- Add big new scenario systems
- Broad infra refactors

---

*End of Fix Queue Hardening Spec*
