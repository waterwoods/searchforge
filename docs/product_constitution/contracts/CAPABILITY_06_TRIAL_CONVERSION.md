# Capability Contract 06 — Trial Conversion

**Capability:** Trial Conversion  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §6

---

## SECTION 1 — Purpose

Why this capability exists.

Prove **time saved** during the 7-day trial to justify $49–99/month payment. Converts evaluation to paid pilot; produces fix-now queue if not ready; captures testimonial for second broker.

Without Trial Conversion evidence, the product has an engine but no revenue.

---

## SECTION 2 — Primary User

Who uses it.

| User | Role |
|------|------|
| **Founder** | Runs Day 0–7 path; Day 7 payment conversation; invoice |
| **Broker owner** (Chen Kui) | Provides behavioral evidence; answers 5 value questions |
| **Office assistant** | Optional — adoption counts toward $99 tier |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Source |
|-------|--------|
| Observation log | `trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` |
| Day 7 five value questions | TRIAL_ONE_PATH |
| Behavioral signals | Workbench opens, draft copies, real case count |
| Prod stability | `/readyz`, case persistence |
| Friction notes | Days 1–6 founder async support |

---

## SECTION 4 — Outputs

What must come out.

| Output | Requirement |
|--------|-------------|
| "Worked" lines | ≥1 with approximate minutes saved on real case |
| Payment decision | Invoice at $49 or $99 OR ranked kill reasons |
| Fix-now queue | Top 3 friction items from trial only |
| Testimonial quote | If positive — for second broker |
| Trial completion record | ≥3 real cases; draft copied ≥2×; opened ≥4/7 days |
| Commercial artifacts | 1-page pilot terms + invoice in broker's hands |

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Trial completion | 7 days with ≥3 real cases | TRIAL_ONE_PATH |
| Draft copied with edits | ≥2 times | P11 blockers |
| Workbench opens | ≥4 of 7 days | P11 blockers |
| Day 7 Q3 "save time?" | Yes + specific example | TRIAL_ONE_PATH |
| Payment | $49–99 manual invoice OR ranked blockers | P11 verdict |
| Testimonial | 1 quote captured if positive | Second broker gate |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Day 0: 30-min founder kickoff completed  
- [ ] Observation log maintained Days 0–7 with "worked" field  
- [ ] ≥3 real cases pasted (not demo-only)  
- [ ] Draft copied with edits ≥2 times (logged)  
- [ ] Day 7: five value questions answered in writing  
- [ ] Pricing ($49/$99) and terms presented before payment ask  
- [ ] Payment received OR written "not yet" with ranked blockers  
- [ ] No new features shipped during trial week  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **45 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Trial process definition | 75 | TRIAL_ONE_PATH mature |
| Observation log template | 60 | Exists; "minutes saved" field weak |
| Commercial packaging | 35 | No terms/invoice in repo; pricing not on one-pager |
| Day 1 unsupervised path | 28 | Playbook fails without founder |
| Day 7 payment path | 40 | Requires founder; no self-serve terms |
| Payment evidence | 25 | No completed trial; no testimonial |
| Fix-now discipline | 70 | Process defined; not yet executed |

**P11 reference:** Payment evidence 25/100; Day 7 unsupervised 35/100.

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| No proven time savings on real cases | **P0** |
| Pricing not on BROKER_ONE_PAGER | **P0** |
| No 1-page pilot terms (Chinese) | **P0** |
| No invoice template | **P0** |
| No standard "minutes saved" field in observation log | **P1** |
| Day 1 unsupervised fails (depends on Front Door) | **P0** |
| Simulation dependency in playbook | **P1** |
| No testimonial captured | **P2** |
| Data retention post-trial unclear | **P2** |
| Assistant training script missing | **P2** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Add $49/$99 pricing to BROKER_ONE_PAGER | Unblocks Day 7 conversation |
| 2 | Create 1-page pilot terms (Chinese) | Trust + legal clarity |
| 3 | Create invoice template (WeChat/PDF) | Expense + payment path |
| 4 | Extend observation log with "minutes saved" standard field | Quantitative proof |
| 5 | 30-min founder kickoff mandatory before Day 1 alone | Day 1 score 72 vs 28 |
| 6 | Run 7-day trial with observation log — no new features | Proof or kill |
| 7 | Update playbook — remove Simulation dependency | Playbook matches prod UI |
| 8 | Capture Day 7 quote if positive | Second broker ammo |
| 9 | State data retention in pilot terms | Reduces churn fear |
| 10 | 15-min assistant training script | $99 tier justification |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- Stripe self-serve checkout  
- Automated billing / dunning  
- In-app NPS survey platform  
- Cohort analytics dashboard  
- Multi-broker trial management portal  
- CRM-style trial pipeline  
- Referral program / affiliate tracking  
- $199 tier packaging  
- Legal terms generator SaaS  
- A/B pricing experiments before first payment  

---

*End of Capability Contract 06*
