# Acceptance / Trial Execution Criteria

**Sprint:** Trial Execution Readiness + Last-Mile Hardening  
**Created:** 2026-03-18  
**Purpose:** Practical criteria for ease of running trial, broker clarity, office usability, handoff completeness, observation usefulness, what to defer.

---

## 1. Ease of Running the Trial

| Criterion | Pass when |
|-----------|-----------|
| Founder pre-trial checklist | Single checklist; all steps runnable; trial_readiness_check PASS |
| One-command prep | `bash scripts/run_demo_local.sh` → demo ready |
| Recovery path clear | 503 → `restore_8001_readiness.sh`; documented in runbook |
| Founder script | What to say in first 30 sec + demo path documented |

---

## 2. Broker Clarity

| Criterion | Pass when |
|-----------|-----------|
| Day 1 checklist | Broker knows: Load founder demo queue → SIM1–SIM3 → first real case |
| Daily workflow | One-page: paste → triage → handoff → act → update status |
| What to check in workbench | Queue triage, Ready to act, Verify receipt, Follow-up memory, Resume here |

---

## 3. Office Usability

| Criterion | Pass when |
|-----------|-----------|
| Case focus visible | Add car, Premium review, Missing doc, etc. at top |
| Your next move | Bold, operational, one sentence |
| Collected / Still needed | Chips visible when applicable |
| Human confirmation | Gold badge when AI collected from conversation |
| No auto-send | Explicit everywhere; broker confirms before sending |

---

## 4. Handoff Completeness

| Criterion | Pass when |
|-----------|-----------|
| Next action visible | Top of case card; not buried |
| Correction/already_sent | Badge or chip when customer said sent or corrected |
| Recent message | "Just updated" badge after append |
| Resume here | waiting_on + latest note when reopening |

---

## 5. Observation Usefulness

| Criterion | Pass when |
|-----------|-----------|
| Day-by-day log template | Exists; broker/founder can fill |
| Friction classification | Trust / High / Medium / Low defined |
| Fix now / next / defer | Decision rule documented |
| Map to product | Observation → scenario ID or backbone component |

---

## 6. Acceptable to Defer

- Email/WeChat/SMS integration
- OCR upload
- Full CRM
- Multi-tenant, Stripe
- Carrier API integration
- Handoff timing tuning (e.g. LC-AC3)
- Full add-driver multi-turn

---

## 7. Trust-Breaking vs Acceptable Friction

| Trust-breaking (must fix) | Acceptable trial friction |
|---------------------------|---------------------------|
| Wrong next move | Turn 1 occasionally slow |
| Talk to Agent routes wrong | Manual paste (no inbox sync) |
| Auto-send confusion | Broker copies draft to WeChat |
| Collected wrong + no Human confirmation | Some scenarios need polish |
| Correction invisible | |

---

*End of Acceptance / Trial Execution Criteria*
