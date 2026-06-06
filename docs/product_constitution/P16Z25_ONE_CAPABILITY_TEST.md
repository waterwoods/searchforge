# P16-Z2.5 One Capability Test

**Date:** 2026-06-01  
**Sprint:** P16-Z2.5 Product Soul Synthesis  
**Question:** If only one capability survives, which one — and why?

---

## The answer

**Cap 2 — Case Intelligence (Triage Engine)**

---

## If only one survives

> **Transform messy customer communication into understanding: category, urgency, summary, collected fields, still-needed fields, and a specific next action.**

Everything else is delivery, continuity, or commercial wrapper around this core transformation.

---

## Why Cap 2 — not Cap 1, 3, or 5?

| Capability | What it does | Why it doesn't survive alone |
|------------|--------------|------------------------------|
| Cap 1 — Broker Front Door | Paste box, copy button, URL | Empty shell without understanding |
| Cap 3 — Structured Case Record | Persist, queue, broker_next_step display | Displays nothing without triage output |
| Cap 5 — Case Lifecycle | Append, waiting_on, continuity | Re-triage on append IS Cap 2; UX alone doesn't create cases |
| Cap 4 — Customer Intake | Customer-facing collection | Broker paste is the wedge; intake is Cap 2 on customer channel |
| Cap 6 — Trial Conversion | Invoice, Day 0, observation log | Commercial process; no product without engine |
| Cap 7 — Founder Control | Guardrails, CI, health checks | Quality wrapper; doesn't create value |

---

## The minimal viable product (one capability)

```
Input:  "Mercury 说我的保单7天内要取消，我没收到付款通知"
Output: {
  category: cancellation_notice,
  urgency: urgent,
  summary: "Mercury 7天取消通知 — 客户未收到付款通知",
  collected: { carrier: Mercury, deadline: 7 days },
  still_needed: [ payment_screenshot ],
  broker_next_step: "今天联系 Mercury 确认 UW 状态并索取付款链接"
}
```

No UI. No queue. No append. No customer tab. **This output alone saves 2–5 minutes** vs manual read + draft — which is what Chen Kui pays for.

---

## Why not Cap 5 (the runner-up)?

P16-X proved the product **wins Turn 1, loses Turn 2+**. Continuity (Cap 5) is the retention mechanism. But append without re-triage is just a message log. `triage_for_append` **is Cap 2 applied in context**. Kill Cap 2 and append becomes storage.

**Cap 5 is how you keep users. Cap 2 is why they came.**

---

## Why not Cap 1 (the deployment blocker)?

Cap 1 is the **execution priority this week** — FP-004, Chinese copy, append CTA. But if the engine returned generic "follow up with client" for every paste, no amount of UI polish would produce payment.

Cap 1 is the **door**. Cap 2 is the **room**.

---

## Evidence from sprints

| Sprint | Evidence for Cap 2 as soul |
|--------|---------------------------|
| P16-Y | Office Actionability at ceiling on all 50 cases — intelligence gaps were classification/extraction |
| P16-Z2 | Every benchmark company implements chaos→understanding→case; understanding IS the product |
| P16-Z0 | Don't rebuild — extend triage.py + case_draft_engine, not new microservices |
| P16-X | Single-turn trap is UX; triage quality on Turn 1 was never the complaint |

---

## The one-capability test applied

**Question:** Would Chen Kui pay $49/month for a CLI that accepts WeChat paste and returns Chinese next action?

**Answer:** Yes — if accuracy ≥88 on wedge lanes and output beats manual drafting speed.

**Question:** Would he pay for a beautiful paste box with no intelligence?

**Answer:** No — that's a textarea.

---

## What Cap 2 must preserve if everything else burns

1. **Classification** — category + urgency (not `unclear`)
2. **Field extraction** — collected_fields + still_needed_fields
3. **conversation_summary** — office glance without opening raw paste
4. **broker_next_step** — specific Chinese next action, never generic
5. **Multi-turn merge** — prior turns in summary (P16-Y P0)

Rebuild UI, queue, customer tab, billing — but **never rebuild triage.py + case_draft_engine from scratch**.

---

## One-line answer

> **If one capability survives, it is Case Intelligence — because customers pay for the office knowing what to do next, not for software.**

---

*End of P16-Z2.5 One Capability Test*
