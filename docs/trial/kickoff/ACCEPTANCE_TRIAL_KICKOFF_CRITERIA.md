# Acceptance / Trial Kickoff Criteria

**Sprint:** Broker Trial Kickoff Readiness Sprint  
**Created:** 2026-03-18  
**Purpose:** Practical criteria for launch clarity, evidence clarity, issue classification clarity, founder confidence, and what remains acceptable to defer.

---

## 1. Launch Clarity

| Criterion | Pass when |
|-----------|-----------|
| Single entry | `bash scripts/trial_launch_check.sh` runs and prints checklist |
| No confusion | Founder can complete checklist in <15 min |
| Docs consolidated | FOUNDER_LAUNCH_NOTES exists; one place for "what to say, inspect, watch for" |

---

## 2. Evidence Clarity

| Criterion | Pass when |
|-----------|-----------|
| Template exists | TRIAL_OBSERVATION_LOG_TEMPLATE.md |
| Storage defined | results/trial_logs/ with README |
| Friction classification | Table in template; map to fix now/next/defer |

---

## 3. Issue Classification Clarity

| Criterion | Pass when |
|-----------|-----------|
| Template exists | FIX_NOW_QUEUE_TEMPLATE.md |
| Spec exists | FIX_NOW_QUEUE_SPEC.md — how to fill, when to sprint |
| Fix-now / fix-next / defer | Clear rules; broker "I can't use this" → fix now |

---

## 4. Founder Confidence

| Criterion | Pass when |
|-----------|-----------|
| Clear flow | BROKER_TRIAL_ONE_PAGER exists; broker can follow Day 1 steps |
| Demo path | First 5–10 min demo defined; Load founder demo queue → cancellation → missing doc → add-car |
| Recovery | 503 → restore_8001_readiness.sh; guardrail fail → fix per output |

---

## 5. Acceptable to Defer

| Item | Why |
|------|-----|
| Inbox sync | Large integration |
| OCR | Large integration |
| Full trial summary export | Evidence pack is manual for now |
| Multi-tenant, auth | Out of scope |
| Production hardening | Trial-first |

---

*End of Acceptance / Trial Kickoff Criteria*
