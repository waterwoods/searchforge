# Acceptance / Launch Criteria

**Sprint:** Trial Launch + Fix-Now Queue Sprint  
**Created:** 2026-03-18  
**Purpose:** Practical criteria for founder launch clarity, broker day-1 usability, office-side usability, evidence capture usefulness, fix-now queue usefulness, and what remains acceptable to defer.

---

## 1. Founder Launch Clarity

| Criterion | Pass when |
|-----------|-----------|
| Single entry | `bash scripts/trial_launch_check.sh` runs and prints checklist |
| No confusion | Founder can complete checklist in &lt;15 min |
| Docs consolidated | FOUNDER_LAUNCH_NOTES.md exists; one place for "what to say, inspect, watch for" |

---

## 2. Broker Day-1 Usability

| Criterion | Pass when |
|-----------|-----------|
| Clear flow | BROKER_TRIAL_ONE_PAGER exists; broker can follow Day 1 steps |
| No confusion | Broker understands: paste → triage → handoff → edit draft → copy |

---

## 3. Office-Side Usability

| Criterion | Pass when |
|-----------|-----------|
| Next move visible | "Your next move" appears before Recent customer messages (smoke step 23) |
| Collected/Still needed | Chips visible |
| Correction/already_sent | Badges visible when applicable |

---

## 4. Evidence Capture Usefulness

| Criterion | Pass when |
|-----------|-----------|
| Template exists | TRIAL_OBSERVATION_LOG_TEMPLATE.md |
| Storage defined | results/trial_logs/ with README |
| Friction classification | Table in template; map to fix now/next/defer |

---

## 5. Fix-Now Queue Usefulness

| Criterion | Pass when |
|-----------|-----------|
| Template exists | FIX_NOW_QUEUE_TEMPLATE.md |
| Spec exists | FIX_NOW_QUEUE_SPEC.md — how to fill, when to sprint |

---

## 6. Acceptable to Defer

| Item | Why |
|------|-----|
| Inbox sync | Large integration |
| OCR | Large integration |
| Full trial summary export | Evidence pack is manual for now |
| Multi-tenant, auth | Out of scope |
| Production hardening | Trial-first |

---

*End of Acceptance / Launch Criteria*
