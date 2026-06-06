# Acceptance / Trial Execution Criteria

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20

---

## 1. Believable customer entry

- [ ] Default experience presents a **client-safe** hub (language, quick starts, examples).  
- [ ] Primary intents are reachable without insider knowledge.  
- [ ] No prominent internal-only labels on the default path.

## 2. Believable Add-Car flow

- [ ] Multi-turn collection matches broker expectations (vehicle, zip, timing).  
- [ ] Quote-ready / almost-ready / need-more **maps to what the broker would say** out loud.

## 3. Usable quote-ready state

- [ ] Broker can tell “can quote” vs “need one more chip” from workbench fields + summary.  
- [ ] Contact gaps are visible when present.

## 4. Usable workbench handoff

- [ ] Queue scan: identify urgency and intent in **&lt; 30 seconds** for seeded cases.  
- [ ] Open case: **one clear next action** in `broker_next_step` for standard scenarios.

## 5. Usable follow-up visibility

- [ ] Status / waiting_on / next_contact_by usable for office rhythm.  
- [ ] Append / activity trail does not confuse “new message” vs “new case.”

## 6. Acceptable trial readiness (bar)

- [ ] `bash scripts/guardrail_inbox_triage.sh` **PASS**.  
- [ ] No known **trust-breaking** fix-now item left unaddressed or explicitly accepted by founder.  
- [ ] Founder can demo **Add-Car + one risk scenario + one human** without apology.

---

*End of Acceptance Criteria*
