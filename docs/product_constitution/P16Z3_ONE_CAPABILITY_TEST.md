# P16-Z3 One Capability Test

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Question:** If all capabilities disappear except one, which survives — and why?

---

## The answer

**Level 4 Office Action Generation — powered by the Case Intelligence engine (`triage.py` + `case_draft_engine.py`)**

In capability-map terms: **Cap 2 — Case Intelligence**, spanning maturity levels **L1 through L4** as one inseparable transformation.

---

## If only one survives

> **Transform messy customer communication into understanding plus office action: category, urgency, summary, collected fields, still-needed fields, and a specific Chinese next action.**

Everything else is delivery wrapper (UI), continuity mechanism (append), or commercial process (invoice).

---

## Why L4 (Office Action) — not L3 alone or L5 alone?

| If only this survives | What you get | Why insufficient alone |
|-----------------------|--------------|------------------------|
| **L3 Case Distillation only** | Summary + draft bundle | Office still asks "so what do I do?" |
| **L5 Continuity only** | Append + message log | Storage without re-triage is a notepad |
| **L1 Classification only** | Category tag | No fields, no action — label maker |
| **L0 Raw Intake only** | Paste box | Textarea |
| **L4 Office Action** | Full transformation output | **Saves 2–5 min per message** — payable value |

L4 cannot exist without L1–L3 in the engine — they are one pipeline. The test names **L4 as the survivable output** because that is what Chen Kui pays for: knowing what to do next.

---

## Why not Cap 1 (Broker Front Door)?

Cap 1 is paste box + copy button + URL access.

| Test | Result |
|------|--------|
| Beautiful UI, no intelligence | **Worth $0** — textarea with chrome |
| CLI/API with intelligence, no UI | **Worth $49/mo** if ≥88 accuracy |

Cap 1 is the **door** (L0 access). Cap 2/L4 is the **room**.

**This week:** Cap 1 is execution priority (FP-004). **Forever:** Cap 2 is product soul.

---

## Why not Cap 5 (Case Lifecycle)?

P16-X: product **wins Turn 1, loses Turn 2+**.

| Fact | Implication |
|------|-------------|
| `triage_for_append()` re-runs full triage | Append **is** Cap 2 in context |
| Append without re-triage | Message log only |
| Continuity UX at 41/100 | Retention problem, not engine problem |

**Cap 5 is how you keep users. Cap 2/L4 is why they came.**

---

## The minimal viable product (one capability)

```
Input:  "Mercury 说我的保单7天内要取消，我没收到付款通知"

Output: {
  issue_category: cancellation_notice,
  urgency: urgent,
  conversation_summary: "Mercury 7天取消通知 — 客户未收到付款通知",
  collected_fields: [ carrier, deadline ],
  still_needed_fields: [ payment_screenshot ],
  broker_next_step: "今天联系 Mercury 确认 UW 状态并索取付款链接",
  client_reply_draft: "收到，我们正在帮您处理 Mercury 的取消通知..."
}
```

No UI. No queue. No append. No customer tab.

**This output alone saves 2–5 minutes** vs manual read + draft — which is what Chen Kui pays for.

---

## How it creates revenue

| Revenue mechanism | How L4 creates it |
|-------------------|-------------------|
| **Time saved** | 2–5 min × 20 msgs/day × 20 days = **6–10 hours/month** |
| **Price anchor** | $49–99/month vs $50–100/hr broker time |
| **Payment trigger** | Chen Kui sends one draft to real client without Andy on phone |
| **Renewal trigger** | Append path works → broker returns daily |
| **Upsell trigger** | Second office sees same accuracy on their paste |

**Formula:** Revenue = (minutes saved × cases per month × broker hourly rate) > subscription price.

At 15 min/day saved × 20 days = 5 hours/month. At $50/hr implicit rate = $250 value for $49 price. **ROI is obvious.**

---

## What L4 must preserve if everything else burns

| # | Element | Maturity | Non-negotiable because |
|---|---------|----------|------------------------|
| 1 | Classification | L1 | Wrong lane = wrong action |
| 2 | Field extraction | L2 | Office re-reads paste without it |
| 3 | conversation_summary | L3 | Glance replaces raw paste |
| 4 | broker_next_step | L4 | **The paid moment** |
| 5 | client_reply_draft | L4 | Beat「直接回微信」 |
| 6 | still_needed_fields | L2 |「还缺什么」prevents incomplete handoff |

**Rebuild UI, queue, customer tab, billing — never rebuild `triage.py` + `case_draft_engine` from scratch.**

---

## Evidence from sprints

| Sprint | Evidence |
|--------|----------|
| P16-Y | Office Actionability 25/25 on all 50 cases; intelligence gaps were L1–L2/L5 |
| P16-Z2 | Every benchmark company implements chaos→understanding→action |
| P16-Z0 | Don't rebuild — extend existing engine |
| P16-Z2.5 | Cap 2 ranked #1 in capacity ranking |
| P16-X | Single-turn trap is UX (L5); triage quality on Turn 1 was not the complaint |

---

## Applied test scenarios

| Scenario | Cap 2 alone? | Cap 1 alone? | Cap 5 alone? |
|----------|--------------|--------------|--------------|
| Cancel notice paste | ✅ Act immediately | ❌ Empty box | ❌ No first triage |
| Client replies with payment screenshot text | ⚠️ Needs re-run (append) | ❌ | ⚠️ Stores but doesn't understand |
| Broker asks "what's missing?" | ✅ still_needed | ❌ | ❌ |
| Chen Kui pays $49/month | ✅ If accuracy ≥88 | ❌ | ❌ |

---

## One-line answer

> **If one capability survives, it is Case Intelligence through Office Action (L4) — because customers pay for the office knowing what to do next, not for software.**

---

*End of P16-Z3 One Capability Test*
