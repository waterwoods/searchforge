# P16-Z7 Phase 3 — WeChat Re-read Test

**Date:** 2026-06-02  
**Question:** Can a broker understand the case from Unified Intake alone, or must they reopen WeChat?  
**Method:** Score 0–100 from final triage output (summary + broker_next_step + collected + still_needed + draft) vs journey must-know facts  
**Results:** `role_d_battery.json` → `scores.reread_0_100`, `needs_wechat`

---

## Scoring rubric

| Score | Meaning |
|-------|---------|
| **90–100** | Full story without WeChat — act immediately |
| **70–89** | Enough for next beat; reopen only for tone/attachments |
| **60–69** | Partial — must reopen for amounts, IDs, or lane |
| **&lt;60** | Do not trust — WeChat required |

**`needs_wechat = true`** when &lt;45% of must-know keywords appear in triage output blob.

---

## Journey results

| ID | Reread | Needs WeChat? | What broker gets without WeChat | What forces WeChat reopen |
|----|--------|---------------|--------------------------------|---------------------------|
| D01 | 65 | **Yes** | 7-day deadline, “already sent” | Cancel intent weak; **$420** missing; generic broker step |
| D02 | 60 | **Yes** | Lapse thread, some payment language | **#88291**, 3/12 paid lost on Day 3; wrong UW lane |
| D03 | 60 | **Yes** | Garaging / address headline | **94588** not in structured fields; proof status vague |
| D04 | 70 | No | 3/15 deadline, policy 4412098 | Teen form detail only in thread (if not pasted) |
| D05 | 70 | No | Claim intake, photos collected | **8ABC123** not in summary headline |
| D06 | 74 | No | Add-car collected by Day 3 | Days 1–2 `unclear`; 17/permit not in summary |
| D07 | 70 | No | Camry year/make | **Remove intent lost** — reads as new quote |
| D08 | **90** | No | Premium + Prior turn + bill_sent | Minor: target coverage preference |
| D09 | 70 | No | Prior cancel + address correction | **94566** in latest only; cancel in Prior line |
| D10 | 60 | **Yes** | Message count only | **$200, 3 installments, restore** all absent |

**Average reread: 68.9** — **4/10 mandatory WeChat reopen**

---

## Chen Kui desk simulation

| Scenario | Without WeChat | With WeChat |
|----------|----------------|-------------|
| Morning queue scan | Queue `最近：` + summary OK for D04, D08 | — |
| Open case Day 3 | D08: trust and copy draft | D01/D10: reopen for money facts |
| Handoff to assistant | D05, D09: thread card (Z6 UI) sufficient | D03: assistant needs zip from chat |
| Carrier call prep | D04: policy # in case | D02: need portal confirmation from chat |

---

## UI layer (not in engine run)

P16-Z6 shipped **对话记录** (last 5 `case_messages`) in `BrokerWorkbenchTab.tsx`. When deployed:

| Effect | Estimate |
|--------|----------|
| Reread +5–10 pts on Turn 2+ | Broker sees raw bubbles without WeChat scroll |
| Does not fix | Wrong lane text, missing collected fields |

Engine reread scores are **floor**; deployed UI adds ~**8 points** on average (P16-Z6 estimate).

---

## TOP 5 re-read failures

1. **D10** — Chinese installment/lapse never classifies; summary is message-count only  
2. **D02** — Day 3 `Boundary: new_issue` drops payment proof narrative  
3. **D01** — Cancel wedge classified as `customer_question`; payment amount not distilled  
4. **D03** — Zip and proof-sent not in collected  
5. **D07** — Sold-car story reads as add-car quote — **trust-breaking re-read**

---

## TOP 5 re-read successes

1. **D08** — Premium renewal + prior turn + bill_sent (Z6 Y45 fix)  
2. **D09** — Correction chain with `Prior turn: 保单要cancel了`  
3. **D05** — Claim collected fields accumulate photos + hit_and_run  
4. **D06** — End state has Honda + driver slots (if broker survived Day 1–2)  
5. **D04** — UW deadline + policy # stable across 3 days

---

## Phase 3 verdict

**Can Chen Kui understand the case without reopening WeChat?**

> **Turn 1: Mostly yes (7/10).**  
> **Day 3 after append: Partially (6/10 without forced reopen; 4/10 must reopen).**  
> **Best case (D08): Yes (90).**  
> **Worst case (D02, D10): No (60).**

**Compared to pre-Z6:** Correction (D09) and premium (D08) re-read **materially improved**. Payment Chinese and remove-car **unchanged or worse**.
