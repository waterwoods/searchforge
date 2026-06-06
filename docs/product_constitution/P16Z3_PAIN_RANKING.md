# P16-Z3 Pain Point Ranking

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Sources:** Founder notes (`FOUNDER_REAL_USAGE_REPORT.md`, `FOUNDER_ONE_PATH.md`, P11/P16-X Chen Kui simulations), P16-Y battery, P16-Z2.5 discoveries, trial observation specs.

---

## Pain candidates (founder-defined)

| ID | Pain | Office manifestation |
|----|------|----------------------|
| **A** | WeChat message chaos | 50+ unread threads; re-read paste; context in head not system |
| **B** | Claims information gathering | FNOL letters, adjuster asks, loss details scattered across chat and mail |
| **C** | Missing information | Don't know what's on file vs what client still owes; re-ask client |
| **D** | Follow-up loss | After copy-to-WeChat, client reply not merged; revert to manual thread |
| **E** | High-value interruption | Urgent cancel/UW pulls owner off strategic work; everything feels P0 |

---

## Scoring method

Each dimension scored **1–5** (5 = worst / highest impact).  
**Composite priority** = weighted sum:

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Frequency | 25% | Daily vs weekly |
| Pain severity | 30% | Time, money, compliance risk |
| Willingness to pay | 25% | Chen Kui payment trigger alignment |
| Implementation difficulty | 20% | Inverted — **5 = easy** (high score helps priority) |

**Priority index** = (Freq×0.25 + Pain×0.30 + WTP×0.25 + (6−Difficulty)×0.20) — higher is more urgent to solve.

---

## Dimension scores

| Pain | Frequency (1–5) | Pain (1–5) | WTP (1–5) | Difficulty (1–5, 5=easy) | Evidence |
|------|-------------------|------------|-----------|---------------------------|----------|
| **A — WeChat chaos** | **5** | **5** | **5** | **4** | Every message; FOUNDER report #1 friction;「直接回微信」competitor |
| **B — Claims gathering** | **2** | **4** | **3** | **2** | Weekly not hourly; P16-Y claims lane 3 cases ~88 avg; OCR/PDF partial |
| **C — Missing information** | **4** | **4** | **5** | **4** | Missing-doc SIM2; still_needed engine built; tune not rebuild |
| **D — Follow-up loss** | **4** | **5** | **5** | **4** | P16-X Cap 5 = 41/100; append backend done; UX gap |
| **E — High-value interruption** | **3** | **5** | **4** | **5** | Cancel wedge; urgency exists; countdown = copy fix |

*Difficulty inverted in composite: (6−Difficulty) used so easy fixes rank higher.*

---

## Composite priority index

| Rank | Pain | Freq | Pain | WTP | Easy | **Priority index** |
|------|------|------|------|-----|------|-------------------|
| **1** | **A — WeChat chaos** | 5 | 5 | 5 | 4 | **4.70** |
| **2** | **D — Follow-up loss** | 4 | 5 | 5 | 4 | **4.50** |
| **3** | **C — Missing information** | 4 | 4 | 5 | 4 | **4.30** |
| **4** | **E — High-value interruption** | 3 | 5 | 4 | 5 | **4.05** |
| **5** | **B — Claims information gathering** | 2 | 4 | 3 | 2 | **2.85** |

---

## Ranked summary (founder-facing)

### 1. WeChat message chaos (A)

| Dimension | Score | Note |
|-----------|-------|------|
| Frequency | ★★★★★ | All day |
| Pain | ★★★★★ | Cognitive overload; wrong reply risk |
| WTP | ★★★★★ | Core payment story — time back |
| Difficulty | ★★★★☆ | Engine exists; access + copy + speed |

**Fix class:** L1+L4 deploy — paste → case → copy in <45s. Not new AI.

---

### 2. Follow-up loss (D)

| Dimension | Score | Note |
|-----------|-------|------|
| Frequency | ★★★★☆ | Every multi-turn case |
| Pain | ★★★★★ | Product abandoned after Turn 1 |
| WTP | ★★★★★ | Retention = renewal |
| Difficulty | ★★★★☆ | Post-copy CTA + summary merge |

**Fix class:** L3+L5 — append UX + P16-Y P0. Highest retention ROI.

---

### 3. Missing information (C)

| Dimension | Score | Note |
|-----------|-------|------|
| Frequency | ★★★★☆ | Most cancel/payment/UW |
| Pain | ★★★★☆ | Re-ask client; carrier delay |
| WTP | ★★★★★ |「还缺什么」is the product |
| Difficulty | ★★★★☆ | Rules + 3 engine tunes |

**Fix class:** L2 — still_needed tuning; not interactive gap-fill dialogue.

---

### 4. High-value interruption (E)

| Dimension | Score | Note |
|-----------|-------|------|
| Frequency | ★★★☆☆ | Spiky — cancel season |
| Pain | ★★★★★ | Revenue loss if missed |
| WTP | ★★★★☆ | Wedge scenario for trial |
| Difficulty | ★★★★★ | Urgency + deadline already in engine |

**Fix class:** L3+L4 — countdown + Chinese next action naming carrier/deadline.

---

### 5. Claims information gathering (B)

| Dimension | Score | Note |
|-----------|-------|------|
| Frequency | ★★☆☆☆ | Lower volume lane |
| Pain | ★★★★☆ | Real but not Day-0 |
| WTP | ★★★☆☆ | Secondary to cancel wedge |
| Difficulty | ★★☆☆☆ | OCR/PDF; partial lane |

**Fix class:** Defer to week 2–3 / office 2 — wire OCR, not primary GTM.

---

## Pain → maturity level mapping

| Pain | Primary levels | 30-day must-fix |
|------|----------------|-----------------|
| A | L1, L4 | Week 1 |
| D | L3, L5 | Week 1–2 |
| C | L2 | Week 1 |
| E | L3, L4 | Week 1 |
| B | L2, L6 | Week 3+ |

---

## What NOT to prioritize (despite loudness)

| Temptation | Why lower rank |
|------------|----------------|
| Claims OCR-first product | B is #5; cancel text wedge wins payment |
| Customer portal week 1 | A/D solved broker-side first |
| Smarter LLM Turn-1 | A is speed + deploy, not model |
| Full CRM status admin | E solved by glance urgency, not Salesforce |

---

## Payment trigger alignment

Chen Kui pays when **A + D + C** are felt in one real case:

> Paste cancel chaos → see gaps → copy draft → client replies → append → second copy — **without Andy on the phone**.

That is **not** claims gathering (B) on Day 0.

---

*End of P16-Z3 Pain Ranking*
