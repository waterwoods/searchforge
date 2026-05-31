# Capability Scorecard V1 — Unified Intake

**Version:** V1 Ratified (P14-B Constitution Sprint)  
**Date:** 2026-05-31  
**Method:** Scores derived from P10/P11 audits, FOUNDER_REVIEW_REPORT (62/100 overall), and capability contract §7 assessments.

---

## Individual Capability Scores

| # | Capability | Current | Target (Paid Pilot) | Gap | Trial-ready? |
|---|------------|---------|---------------------|-----|--------------|
| 1 | **Broker Front Door** | **35** | 75 | **40** | No |
| 2 | **Urgent Message Triage** | **85** | 90 | 5 | Yes |
| 3 | **Structured Case Record** | **72** | 85 | 13 | Yes |
| 4 | **Customer Intake Collection** | **62** | 80 | 18 | Conditional |
| 5 | **Case Lifecycle Management** | **55** | 75 | 20 | Conditional |
| 6 | **Trial Conversion** | **45** | 80 | 35 | No |
| 7 | **Founder / Operator Control** | **68** | 85 | 17 | Partial |

---

## Score Rationale (Current)

### 1. Broker Front Door — 35

P11 product surface UX: 35/100. Day 1 unsupervised: 28/100. Wrong tab, engineer chrome, hidden Simulation, no demo progress.

### 2. Urgent Message Triage — 85

Guardrail 13/13 PASS. P11: "triage engine is trial-ready." Gaps: label mapping, real-message edge cases, loading UX.

### 3. Structured Case Record — 72

Strong insurance-specific structure (P11 moat). Draft quality varies. PG labels leak. chen_kui pack unused.

### 4. Customer Intake Collection — 62

Paste mechanism works (85). Undermined by wrong surface default and weak loading/expectation copy.

### 5. Case Lifecycle Management — 55

Queue exists but wayfinding weak. Engineer filters. Follow-up paste buried. Assistant playbook thin.

### 6. Trial Conversion — 45

Process defined (75) but no payment evidence (25). Missing terms, invoice, pricing on one-pager. No completed trial.

### 7. Founder / Operator Control — 68

Strong guardrails and founder docs. Missing broker UX gate. Prod validation incomplete.

---

## Overall Product Score

| Metric | Score |
|--------|-------|
| **Current (weighted)** | **60 / 100** |
| **Target (paid pilot viable)** | **80 / 100** |
| **Gap** | **20 points** |

**Weighting rationale:** Front Door (25%), Triage (15%), Case Record (15%), Intake (10%), Lifecycle (10%), Trial Conversion (15%), Founder Control (10%) — reflects P10/P11 diagnosis that UX and commercial packaging block revenue more than engine quality.

**Founder review cross-check:** 62/100 repository convergence score — aligned within rounding.

---

## Trial Path Scores (Cross-Reference)

From P11 TRIAL_REALITY_AUDIT:

| Scenario | Day 1 | Day 7 | Overall |
|----------|-------|-------|---------|
| URL only, no founder | 28 | 35 | **32** |
| URL + one-pager, no founder | 35 | 40 | **38** |
| Kickoff + prod + UI fixes (Week 1) | 72 | 68 | **70** |
| Full P10 30-day plan | 78 | 82 | **80** |

**Interpretation:** Closing the 20-point product gap maps directly to Week 1 UI sprint + prod deploy + supervised trial.

---

## Capability Maturity Labels

| Maturity | Capabilities |
|----------|--------------|
| **Trial-ready** | Urgent Message Triage, Structured Case Record |
| **Conditional** | Customer Intake Collection, Case Lifecycle Management |
| **Not trial-ready** | Broker Front Door, Trial Conversion |
| **Partial** | Founder / Operator Control |

---

## Path to Target (80/100)

| Action cluster | Capabilities lifted | Expected delta |
|----------------|---------------------|----------------|
| Week 1 UI trust + front door | #1, #4, #5 | +15–20 overall |
| Prod deploy + `/readyz` | #7, #6, #3 | +5–8 overall |
| Commercial pack (pricing, terms, invoice) | #6 | +5 overall |
| Supervised 7-day trial with observation log | #6, all | Proof or kill |

---

## Score Update Rules

1. Rescore only after capability contract acceptance criteria change or evidence from trial/commercial events  
2. No capability may claim Target score without trial ROI evidence or explicit founder decision  
3. Guardrail regression FAIL resets Triage current score ceiling to 50 until PASS  
4. Prod outage during trial week reduces Founder Control by 10 points until resolved  

---

*End of Capability Scorecard V1*
