# P16-Z7 Phase 9 — Launch Readiness (Chen Kui)

**Date:** 2026-06-02  
**Persona:** Chen Kui — busy broker, 50 unread WeChat, no product training  
**Question:** Would Chen Kui trust this for a **real** 3-day case?  
**Evidence:** Role D battery, P16-Y 88.9 avg, P16-Z6 shipped UI (deploy pending)

---

## Short answer

**Not yet for all case types.**  
**Yes with guardrails** for: renewal premium (D08), UW deadline (D04), correction address (D09), claim Turn-1 (D05).  
**No without WeChat** for: Chinese payment/installment (D10, D01), remove vehicle (D07), complex claims (CL02, CL06).

---

## Trust matrix

| Case type | Trust 3-day memory? | Why |
|-----------|---------------------|-----|
| Premium renewal + bill | **Yes** | D08 reread 90; Z6 Y45 fix proven |
| UW questionnaire | **Mostly** | D04 stable; jargon OK for Chen |
| Cancel + address correction | **Mostly** | D09 Prior turn; must verify zip in thread |
| Claim FNOL → photos | **Mostly** | Collected fields good; plate in WeChat for confirm |
| Cancel + payment | **No** | D01 wrong category; $420 missing |
| Autopay / portal paid | **No** | D02 Day 3 lane break |
| Remove sold vehicle | **No** | D07 becomes add-car quote — trust killer |
| Installment restore | **No** | D10 stays unclear all 3 days |
| Claims correction / total loss | **No** | CL02 0% retention |

---

## What Chen Kui would feel (day by day)

| Day | Experience | Trust |
|-----|------------|-------|
| **1** | Paste → sensible summary + draft → copy to WeChat | **High** (7/10 journeys) |
| **2** | Append (if taught) → summary updates, thread grows | **Medium** — if he finds 追加 |
| **3** | Opens case for “any update?” ping | **Low on 4/10** — summary doesn’t say who owes what |

**Habit risk:** If he **re-pastes** instead of append, memory **resets** — duplicate case (P16-Z4).

---

## Preconditions for Chen Kui GO

| # | Requirement | Status |
|---|-------------|--------|
| 1 | FP-004 SSO off / stable URL | Founder — not Z7 |
| 2 | Z6 thread + append CTA **deployed** | Code shipped; **deploy pending** |
| 3 | One-time training: 追加 not new paste | Process |
| 4 | Assistant sets `waiting_on` on Day 2–3 | SOP |
| 5 | Block list: D07/D10/CL02-class until engine fix | Product policy |
| 6 | 3 logged real 3-day cases in observation log | **Not done** |

---

## Why he would trust it (strengths)

1. Turn 1 still beats reading 50 messages — North Star holds  
2. 对话记录 shows last client words without scrolling WeChat  
3. Premium and correction threads **feel like someone remembered**  
4. Chinese client drafts usable on payment/claim wedges  
5. Same tool for assistant paste — handoff readable on D05, D09

---

## Why he would not trust it (blockers)

1. **D10 / D01** — payment stories disappear into `unclear` or generic steps  
2. **D07** — tells him to quote a car he sold  
3. **Claims corrections** — 全损 / $18k not in case truth  
4. **No automatic “等保险公司”** — he still mentally tracks carrier wait  
5. **Deploy gap** — if preview lacks Z6 UI, feels like “yesterday’s spell checker”

---

## Comparison to his current workflow

| Today (WeChat + memory) | With Unified Intake |
|-------------------------|---------------------|
| Search chat by client name | Search case queue |
| Scroll 3 days of bubbles | 5-message thread + summary |
| Mental note who waits | Must set waiting_on or forget |
| Sometimes wrong — human | Sometimes wrong — **lane bugs feel worse** because AI implied |

Chen Kui tolerates his own mistakes; **machine wrong lane (D07) breaks trust faster.**

---

## Phase 9 verdict

| Question | Answer |
|----------|--------|
| Trust for real case? | **Conditional GO** — wedge types only |
| Trust for arbitrary 3-day? | **NO** |
| Needs Andy explaining? | **Less than pre-Z6** for D08/D09; **still yes** for append + waiting_on |
| Commercial promise safe? | “Helps on repeat messages” — **not** “never open WeChat 3 days” |

**Chen Kui GO criteria:** Deploy Z6 + 3 observation logs + fix D10/D07/payment classification → re-run Role D battery → avg reread **≥80**, needs_wechat **≤2/10**.
