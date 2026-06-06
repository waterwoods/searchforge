> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/TRIAL_ONE_PATH.md`](../../../TRIAL_ONE_PATH.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Last-Mile Risk Spec — Real Trial Risks

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Define the top real trial risks that could break trust or create confusion.

---

## 1. Trust-Breaking Product Moments

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Talk to Agent awkward** | Customer says "联系人工" but system routes to wrong intent or gives generic reply | High | Clear talk_to_agent path; handoff-ready immediately; broker sees "Customer wants human" |
| **Wrong next move** | broker_next_step is vague ("Review and follow up") or wrong for the case | High | Operational one-liner; concrete action verbs |
| **Collected/Still needed wrong** | AI claims collected what customer didn't say; or misses what was said | Medium | Human confirmation badge when AI extracted; only show when safe |
| **Draft unusable** | Client reply draft needs full rewrite; tone wrong | Medium | Editable; broker always confirms before sending |
| **Auto-send confusion** | Broker thinks something was sent automatically | High | Explicit "不自动发送"; no auto-send anywhere |

---

## 2. Awkward Handoff Behavior

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Next action buried** | Your next move not prominent; broker scrolls to find it | Medium | Bold, top of case card |
| **Correction/already_sent invisible** | Customer said "already sent" or corrected — broker doesn't see | High | Badge or chip: correction, already_sent, verify_receipt |
| **Recent message not visible** | After append, broker can't quickly see what customer just said | Medium | "Just updated with customer follow-up" badge; snippet in queue |
| **Resume here unclear** | Reopening case: broker doesn't know where they left off | Medium | "Resume here" with waiting_on + latest note |

---

## 3. Unclear Broker Workflow

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Day 1 confusion** | Broker doesn't know what to do first | High | Day 1 checklist; Load founder demo queue → SIM1–SIM3 |
| **Daily flow unclear** | Broker doesn't know: paste → triage → handoff → act → update status | Medium | One-page broker workflow |
| **Feedback not recorded** | Friction happens but no place to log it | Medium | Observation log; friction classification |

---

## 4. Weak Office Next-Action Visibility

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **Next move generic** | "Review and follow up" — not actionable | High | Operational sentence: check/confirm/resend/quote |
| **Case focus missing** | Broker can't triage at a glance | Medium | Case focus tag: Add car, Premium review, Missing doc, etc. |
| **Queue triage weak** | Work now vs Waiting not obvious | Medium | Work now / Waiting or parked; urgency badges |

---

## 5. Unclear Observation Capture

| Risk | Description | Severity | Mitigation |
|------|-------------|----------|------------|
| **No structured log** | Founder/broker forgets what happened | Medium | Day-by-day log template |
| **Fix prioritization unclear** | Observations pile up; no fix now / next / defer | Medium | Friction classification table |
| **Feedback not tied to product** | "It felt slow" — no clear scenario or backbone work | Medium | Map observation → scenario ID or flow |

---

## 6. Summary: Top 5 Risks to Address First

1. **Talk to Agent trust** — Clear path; handoff-ready; broker sees "Customer wants human"
2. **Next action visibility** — Bold, operational, top of card
3. **Correction/already_sent visibility** — Badge when customer said sent or corrected
4. **Day 1 broker clarity** — Checklist; Load founder demo queue; SIM1–SIM3
5. **Observation → iteration** — Log template; fix now/next/defer; map to scenario

---

*End of Last-Mile Risk Spec*
