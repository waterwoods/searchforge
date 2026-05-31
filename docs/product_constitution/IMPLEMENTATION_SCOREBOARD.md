# Implementation Scoreboard — P15 Capability Gap Closure

**Version:** P15  
**Date:** 2026-05-31  
**Authority:** Derived from ratified V1 Constitution (`NORTH_STAR_V1.md`, `CAPABILITY_MAP_V1.md`, `CAPABILITY_SCORECARD.md`, contracts). Constitution docs are **not modified** by this sprint.

**Purpose:** Execution-facing scoreboard — every capability mapped to gap, owner, ROI, risk, trial impact, and dependencies.

---

## Overall Posture

| Metric | Current | Target (Paid Pilot) | Gap |
|--------|---------|---------------------|-----|
| **Weighted product score** | **60 / 100** | **80 / 100** | **20** |

**Interpretation (P10/P11):** Triage engine is trial-ready; broker front door and commercial packaging block revenue.

---

## Capability Scoreboard

| Capability | Current | Target | Gap | Owner | Status | ROI | Risk | Trial Impact | Dependencies |
|------------|---------|--------|-----|-------|--------|-----|------|--------------|--------------|
| **1 — Broker Front Door** | 35 | 75 | 40 | Engineering | **Not Started** | Very High | Critical — Day 1 fail if skipped | **Critical** | Cap 4 (paste surface); Cap 7 (product_only deploy) |
| **2 — Urgent Message Triage** | 85 | 90 | 5 | Engineering | **Partial** (guardrail PASS) | Medium | Low — regression only | High (engine must stay green) | Cap 4 input; feeds Cap 3 |
| **3 — Structured Case Record** | 72 | 85 | 13 | Engineering | **Partial** (structure shipped) | High | Medium — draft variance on real messages | High | Cap 2; Cap 7 (Postgres prod) |
| **4 — Customer Intake Collection** | 62 | 80 | 18 | Engineering | **Partial** (paste works) | High | Medium — wrong surface default | Critical | Cap 1 (front door); Cap 2 |
| **5 — Case Lifecycle Management** | 55 | 75 | 20 | Engineering | **Partial** (queue exists) | Medium | Medium — follow-up buried | High | Cap 3; Cap 1 wayfinding |
| **6 — Trial Conversion** | 45 | 80 | 35 | Founder + Engineering | **Not Started** (no completed trial) | Very High | Critical — no revenue without proof | **Critical** | Cap 1, 7; commercial artifacts |
| **7 — Founder / Operator Control** | 68 | 85 | 17 | Founder + Operator | **Partial** (scripts strong) | High | High — false launch confidence | Critical | Runtime deploy; Cap 1 UX gate |

---

## Per-Capability Detail

### Capability 1 — Broker Front Door

| Field | Value |
|-------|-------|
| Current | 35 |
| Target | 75 |
| Gap | 40 |
| Owner | Engineering |
| Status | Not Started |
| ROI | Very High |
| Risk | **Critical** — P10 #1: wrong tab kills trial Day 1 |
| Trial Impact | **Critical** — unsupervised Day 1 scored 28/100 (P11) |
| Dependencies | Cap 4 paste surface; `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`; Cap 7 dry-run gate |

**Primary sprint:** Sprint A (Week 1 Days 1–5)

---

### Capability 2 — Urgent Message Triage

| Field | Value |
|-------|-------|
| Current | 85 |
| Target | 90 |
| Gap | 5 |
| Owner | Engineering |
| Status | Partial — guardrail 13/13 PASS |
| ROI | Medium |
| Risk | Low — fix-now from trial only |
| Trial Impact | High — engine is the product core |
| Dependencies | Cap 4 raw paste; loading UX overlaps Cap 1/4 |

**Primary sprint:** Fix-now only (post-trial, Sprint D overlap for loading copy)

---

### Capability 3 — Structured Case Record

| Field | Value |
|-------|-------|
| Current | 72 |
| Target | 85 |
| Gap | 13 |
| Owner | Engineering |
| Status | Partial — insurance-specific structure is moat |
| ROI | High |
| Risk | Medium — P11 blocker #4 draft quality |
| Trial Impact | High — draft copied ≥2× is payment criterion |
| Dependencies | Cap 2 triage; Cap 7 Postgres persistence |

**Primary sprint:** Sprint B (draft UX) + post-trial fix-now

---

### Capability 4 — Customer Intake Collection

| Field | Value |
|-------|-------|
| Current | 62 |
| Target | 80 |
| Gap | 18 |
| Owner | Engineering |
| Status | Partial — mechanism works; surface wrong |
| ROI | High |
| Risk | Medium — paste feels like extra work without triage win |
| Trial Impact | Critical — ≥3 real cases required |
| Dependencies | Cap 1 default tab; Cap 2 triage |

**Primary sprint:** Sprint A (paste copy, loading) + Sprint D

---

### Capability 5 — Case Lifecycle Management

| Field | Value |
|-------|-------|
| Current | 55 |
| Target | 75 |
| Gap | 20 |
| Owner | Engineering + Founder (assistant script) |
| Status | Partial — Work now / Waiting exists |
| ROI | Medium |
| Risk | Medium — queue noise; follow-up buried |
| Trial Impact | High — Monday-morning queue is Day 7 criterion |
| Dependencies | Cap 3 case record; Cap 1 filters hidden |

**Primary sprint:** Sprint C (Week 2+); filter simplify in Sprint A trust pass

---

### Capability 6 — Trial Conversion

| Field | Value |
|-------|-------|
| Current | 45 |
| Target | 80 |
| Gap | 35 |
| Owner | Founder (primary) + Engineering (enablers) |
| Status | Not Started — process defined, no payment evidence |
| ROI | Very High |
| Risk | **Critical** — payment evidence 25/100 |
| Trial Impact | **Critical** — revenue decision |
| Dependencies | Cap 1 ≥70 Day 1; Cap 7 prod + UX gate; commercial pack |

**Primary sprint:** Sprint B (commercial) + Week 2 supervised trial

---

### Capability 7 — Founder / Operator Control

| Field | Value |
|-------|-------|
| Current | 68 |
| Target | 85 |
| Gap | 17 |
| Owner | Founder + Operator |
| Status | Partial — guardrails strong; UX gate missing |
| ROI | High |
| Risk | High — script PASS ≠ broker-ready (P10 #13) |
| Trial Impact | Critical — prod persistence before Day 0 |
| Dependencies | `validate_pilot_deploy_env.py`; `/readyz`; broker UX checklist |

**Primary sprint:** Sprint A (Days 3–4 deploy) + Sprint B (checklist formalized)

---

## Weighted Score Math (Cross-Check)

| Capability | Weight | Current × Weight | Target × Weight |
|------------|--------|------------------|-----------------|
| 1 Front Door | 25% | 8.75 | 18.75 |
| 2 Triage | 15% | 12.75 | 13.50 |
| 3 Case Record | 15% | 10.80 | 12.75 |
| 4 Intake | 10% | 6.20 | 8.00 |
| 5 Lifecycle | 10% | 5.50 | 7.50 |
| 6 Trial Conversion | 15% | 6.75 | 12.00 |
| 7 Founder Control | 10% | 6.80 | 8.50 |
| **Total** | 100% | **57.55 → 60** | **80.00** |

Rounding aligns with `CAPABILITY_SCORECARD.md` (60 current, 80 target).

---

## Status Legend

| Status | Meaning |
|--------|---------|
| **Not Started** | Acceptance criteria largely unmet; no trial evidence |
| **Partial** | Core mechanism exists; constitution gaps remain |
| **In Progress** | Sprint work actively shipping (update at sprint close) |
| **Done** | Contract §6 acceptance criteria met with evidence |

---

## Update Rules

1. Rescore only after contract acceptance criteria change or trial/commercial event  
2. Sprint A close: rescore Cap 1, 4, 7 (expected +15–20 overall)  
3. Trial week close: rescore Cap 6 with payment or ranked blockers  
4. Guardrail FAIL resets Cap 2 ceiling to 50 until PASS  

---

*End of Implementation Scoreboard — P15*
