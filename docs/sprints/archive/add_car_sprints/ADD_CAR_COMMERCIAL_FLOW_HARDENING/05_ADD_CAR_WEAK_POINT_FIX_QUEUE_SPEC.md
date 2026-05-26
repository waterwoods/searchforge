# Add-Car Weak-Point Fix Queue Spec

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Fix-now, fix-next, acceptable-for-trial, defer — prioritized weak points.

---

## 1. Fix-Now (Block Trial)

| # | Weak Point | Impact | Fix |
|---|------------|--------|-----|
| 1 | broker_next_step vague or generic | Broker doesn't know what to do | Ensure add-car gets "Run quote for {vehicle}. Confirm delivery/driver. Confirm name/phone." |
| 2 | Quote-ready not visible on queue card | Broker must open every case | Add quote_ready tag to add-car queue cards |
| 3 | Contact missing invisible on card | Broker re-asks "who are you?" | Add contact status to queue cards |
| 4 | Correction not visible | Broker uses wrong vehicle/zip | Correction badge above fold |
| 5 | Redundant ask for already-provided field | Customer frustration; feels broken | Verify extraction; no ask for collected field |

---

## 2. Fix-Next (Before Flagship Demo)

| # | Weak Point | Impact | Fix |
|---|------------|--------|-----|
| 6 | Concrete vehicle not in broker summary | Broker sees "model" not "2024 Tesla Model Y" | Enhance conversation_summary with vehicle_concrete |
| 7 | broker_next_step doesn't mention contact when missing | Broker forgets to confirm name/phone | Add "Confirm name and phone for follow-up" when contact_needed |
| 8 | broker_next_step doesn't mention attachment | Broker doesn't know materials received | Add "Materials received" or "Registration/dec page optional" |
| 9 | Side question (garaging, coverage) not answered before handoff | Customer feels ignored | HT8 fix; answer first, hand off |
| 10 | Ask order unnatural | Feels robotic | Verify vehicle → zip → delivery/driver |

---

## 3. Acceptable-for-Trial (Ship As-Is)

| # | Weak Point | Why Acceptable |
|---|------------|----------------|
| 11 | VIN optional, not collected | Quote works with year+model; VIN nice-to-have |
| 12 | insurance_status (add vs new) optional | Broker can ask on call |
| 13 | additional_drivers optional | Same |
| 14 | Email not collected | Phone sufficient for trial |
| 15 | Attachment types not parsed/classified | Broker sees filename; manual check OK |

---

## 4. Defer (Out of Scope)

| # | Weak Point | Reason |
|---|------------|--------|
| 16 | OCR / document extraction | Risky; not reliable |
| 17 | Carrier quote engine | Broker runs quote manually |
| 18 | Mandatory attachment | Chat-only must work |
| 19 | Full CRM | Not standard package |
| 20 | Coverage tiers / limits | V2 |
| 21 | Email/WeChat integration | Paste-only V1 |

---

## 5. Priority Order for Execution

1. **Fix-now** — Complete before any trial
2. **Fix-next** — Complete before "flagship" demo to Chen Kui
3. **Acceptable-for-trial** — Document; no work
4. **Defer** — Document; no work this sprint

---

## 6. Verification

| Priority | Verification |
|----------|---------------|
| Fix-now | guardrail_inbox_triage.sh; handoff_timing_simulations; manual broker_next_step check |
| Fix-next | Same + add-car excellence simulations; founder inspection |
| Acceptable | Document only |
| Defer | Document only |

---

*See also: 06_EXECUTION_OUTLINE.md, 07_ACCEPTANCE_COMMERCIAL_HARDENING_CRITERIA.md*
