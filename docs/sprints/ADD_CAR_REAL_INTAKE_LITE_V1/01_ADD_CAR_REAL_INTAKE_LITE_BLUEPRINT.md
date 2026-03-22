# Add-Car Real Intake Lite Blueprint

**Sprint:** Add-Car Real Intake Lite V1  
**Created:** 2026-03-19  
**Purpose:** Transform add-car from "good chat demo" into a more realistic insurance intake experience.

---

## 1. Why Add-Car Still Feels Fake Today

| Weakness | What it means |
|----------|---------------|
| **Chat-only feel** | User chats; broker sees collected/still_needed only after handoff. No visible "we're collecting real info" during flow. |
| **No quote-ready visibility** | Broker sees "Ready to act" vs "Needs more info" but not explicit "Quote-ready" / "Almost ready" / "Need more" for add-car. |
| **No customer identity** | Name and phone are not collected in add-car flow; broker gets vehicle+zip but not who to call. |
| **Under-filled handoff** | Sometimes handoff occurs with only partial vehicle info; broker must re-ask. |
| **No intake card** | No lightweight structured block during chat that shows collected vs still-needed in real time. |

---

## 2. Why This Sprint Matters Now

- **Broker trust:** Chen Kui needs to see that add-car collects real, quote-relevant information — not just chat.
- **Trial credibility:** "Real intake" feel is a prerequisite for paid pilot.
- **Commercial value:** Add-car is the highest-frequency, highest-value scenario; making it feel real multiplies product value.

---

## 3. What This Sprint Will Strengthen

| Area | Target |
|------|--------|
| Quote-ready visibility | Explicit "Quote-ready" / "Almost ready" / "Need more" status for add-car |
| Collected vs still-needed | Clearer during chat and at handoff; lightweight intake card or equivalent |
| Broker handoff | More structured; broker_next_step actionable; quote_ready_status visible |
| Real-intake feel | User sees that real information is being collected |
| Simulation coverage | Add-car real-intake scenarios (partial → complete, skip VIN, corrections) |

---

## 4. What This Sprint Intentionally Will NOT Do

- **No full quote engine** — no premium calculation, no carrier integration
- **No OCR** — no document extraction
- **No giant form** — keep chat + lightweight structure
- **No VIN requirement** — VIN remains optional, not blocking
- **No split** — chat and structured intake stay integrated

---

## 5. Success Criteria

Add-car feels "real enough for trial" when:

1. Quote-ready / almost-ready / need-more is visible to broker and (where appropriate) customer
2. Collected vs still-needed is clear during and after chat
3. Broker sees structured add-car intake block with minimum fields
4. broker_next_step is actionable and quote-specific
5. Founder can demo 4–6 add-car flows on Vercel with confidence

---

*See also: 02_MINIMAL_INTAKE_FIELD_SPEC.md, 03_QUOTE_READY_STATE_SPEC.md, 04_BROKER_INTAKE_VISIBILITY_SPEC.md*
