# Acceptance / Trial-Hardening Criteria

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. Realistic Simulation Value

- [ ] At least 8–15 broker/customer flows exercised
- [ ] Coverage includes: cancellation, missing doc, add-car, premium, talk-to-agent, mixed-intent, correction, vague, already-sent, append
- [ ] Results recorded in structured way

---

## 2. Useful Issue Discovery

- [ ] Issues classified: strong / acceptable / weak
- [ ] Each issue has: scenario, observation, likely root cause
- [ ] Commercial impact considered (broker work, trust, trial confidence)

---

## 3. Disciplined Issue Classification

- [ ] fix-now: blocks trial or breaks trust
- [ ] fix-next: high value, 1–2 sprints
- [ ] defer: lower priority; documented

---

## 4. Small Fixes Justified

- [ ] If fixes applied: evidence-based; small; low-risk
- [ ] If no fixes: clear explanation why stopping is correct

---

## 5. Acceptable to Defer

- [ ] Broad refactors
- [ ] New scenario systems
- [ ] Inbox sync; OCR; carrier API
- [ ] Simulation coverage counts in UI

---

*End of Acceptance Criteria*
