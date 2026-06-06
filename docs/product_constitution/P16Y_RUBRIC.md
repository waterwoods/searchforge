# P16-Y Phase 2 — Case Intelligence Rubric

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Scope:** Office-executable case quality — not UI, not deployment  
**Scoring:** 0–100 per case (4 × 25 points)

---

## Purpose

Measure how well the triage engine converts messy customer communication into a case an insurance office can **act on without re-reading the raw WeChat paste**.

---

## Dimensions

### 1. Understanding (0–25)

| Score | Criteria |
|-------|----------|
| **25** | Correct `issue_category` + correct `urgency` + summary reflects primary intent |
| **20** | Category correct; urgency off by one level |
| **12** | Category correct only |
| **0–8** | Wrong category or empty summary |

**Signals reviewed:** `issue_category`, `urgency`, `conversation_summary`, intent hints (add car, claim, address, etc.)

---

### 2. Missing Info Detection (0–25)

| Score | Criteria |
|-------|----------|
| **25** | `still_needed_fields` and `collected_fields` match what office must verify; deadline/policy surfaced when present |
| **20** | Most gaps caught; one minor miss |
| **12** | Partial gap detection |
| **0–8** | No structured gaps; office must re-derive from raw paste |

**Signals reviewed:** `still_needed_fields`, `collected_fields`, deadline in summary, policy number extraction, `notice_image` when screenshot-only

---

### 3. Office Actionability (0–25)

| Score | Criteria |
|-------|----------|
| **25** | `broker_next_step` is one operational sentence; `client_prep` specific; draft language matches customer |
| **20** | Actionable but slightly generic |
| **12** | Generic fallback wording |
| **0–8** | Empty or “request clarification” only |

**Blocklist (generic):** “review the…”, “follow up shortly”, “provide more details”, “earliest convenience”

---

### 4. Multi-message Handling (0–25)

| Score | Criteria |
|-------|----------|
| **25** | Prior turns reflected in summary/collected; message count correct; correction honored |
| **20** | Single-turn adequate OR multi-turn mostly merged |
| **12** | Multi-turn count wrong or prior context dropped |
| **0–8** | Append/correction treated as new unrelated case |

**Applies to:** Cases Y41–Y45 and any future append path.

---

## Aggregate score interpretation

| Range | Label | Office meaning |
|-------|-------|----------------|
| **90–100** | Excellent | Paste → act immediately |
| **80–89** | Good | Minor broker edit; saves time |
| **70–79** | Fair | Useful draft; broker re-reads paste for gaps |
| **60–69** | Weak | Classification or gaps wrong — manual triage |
| **<60** | Fail | Do not trust for unsupervised use |

---

## Composite indices (derived)

| Index | Formula | Sprint target |
|-------|---------|---------------|
| **Case Intelligence** | Understanding + Missing Info | ↑ |
| **Case Distillation** | Understanding + Multi-message | ↑ |
| **Office Actionability** | Office Actionability dimension | Maintain ≥24 avg |

---

## Scoring method (this sprint)

Automated runner: `scripts/run_p16y_case_battery.py`  
Case pack: `configs/p16y_50_cases.json`  
Results: `docs/product_constitution/.p16y_results/p16y_battery_{before|after}.json`

Human review spot-checks applied to borderline cases (Y44, Y45) in role simulations.

---

*End of P16-Y Phase 2 — Rubric*
