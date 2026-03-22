# Acceptance — Commercial Hardening Criteria

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Realism, coherence, office usability, commercial feel, scope discipline.

---

## 1. Realism

| Criterion | Pass When |
|-----------|-----------|
| Customer flow feels natural | No "please provide more context" for clear add-car intent |
| Corrections stay in same case | "不是X5，是X3" → collected shows X3 |
| Late details captured | "对了 是我老婆开" → primary_driver updated before handoff |
| Side questions answered | Garaging, coverage — answer first, hand off |
| Contact when volunteered | Name/phone in chat → extracted and visible |
| Attachment when uploaded | Registration, VIN photo → visible to broker |

---

## 2. Coherence

| Criterion | Pass When |
|-----------|-----------|
| End-to-end flow documented | 02_ADD_CAR_END_TO_END_FLOW_SPEC complete |
| Readiness combinations defined | All quote/contact/attachment states in 03 spec |
| No contradictory logic | Quote-ready, contact, attachment independent; no blocking |
| broker_next_step matches state | Quote-ready → "Run quote"; contact needed → "Confirm name/phone" |

---

## 3. Office Usability

| Criterion | Pass When |
|-----------|-----------|
| 3–5 second scan | Broker understands case without deep reading |
| Above fold | Quote-ready, contact, attachment, correction, broker_next_step visible |
| Queue card scan | Can prioritize from list without opening every case |
| broker_next_step actionable | "Run quote for {vehicle}. Confirm delivery/driver." — not "Review and follow up" |
| No rework | Broker doesn't re-ask for vehicle, zip, contact, or materials already provided |

---

## 4. Commercial Feel

| Criterion | Pass When |
|-----------|-----------|
| Add-car as flagship | Founder can demo 4–6 flows confidently |
| "Good enough to show Chen Kui" | No awkward moments; broker sees real lead, real next step |
| Concrete vehicle in summary | "2024 Tesla Model Y" not just "model" |
| Contact block visible | Name, phone or "needed" |
| Attachment status visible | "Materials received" or "optional" |

---

## 5. Scope Discipline

| Criterion | Pass When |
|-----------|-----------|
| No OCR | Document extraction deferred |
| No carrier integration | Broker runs quote manually |
| No mandatory attachment | Chat-only works |
| No full CRM | Contact = name + phone only |
| Defer list respected | 01 blueprint "What to Defer" not violated |

---

## 6. Verification Commands

| Check | Command |
|-------|---------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| Handoff timing | `PYTHONPATH=. python3 scripts/run_handoff_timing_simulations.py` |
| Inbox triage scenarios | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| Demo validate | `bash scripts/demo_quick_validate.sh` |

---

## 7. Founder Sign-Off

Add-car is **commercially hardened** when founder can answer yes to:

1. Can I show add-car as the flagship scenario?
2. Does the broker see everything needed in 3–5 seconds?
3. Is broker_next_step always actionable?
4. Are there no fix-now weak points remaining?
5. Would I be comfortable showing this to Chen Kui?

---

*See also: 08_FOUNDER_INSPECTION_NOTES.md, 05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC.md*
