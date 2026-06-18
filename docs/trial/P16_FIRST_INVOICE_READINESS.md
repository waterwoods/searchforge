# P16 First Invoice Readiness

**Sprint:** P16-CHEN-KUI-PILOT-SPRINT · Phase 6  
**Date:** 2026-06-06  
**Question:** Can Andy charge Chen Kui today?

---

## Can Andy charge today?

## **NO**

---

## Exact blockers

| # | Blocker | Type | Resolve by |
|---|---------|------|------------|
| 1 | **Zero real broker case logs** — no evidence Chen Kui saved time on his WeChat | Commercial proof | Complete 10-case pilot log |
| 2 | **No Day 0 / Day 7 conversation** — payment needs broker verbal YES | Sales | Run CHEN_KUI_DAY0_SCRIPT |
| 3 | **No draft-copied count from real paste** — simulation ≠ payment | Evidence | ≥7/10 drafts copied in pilot |
| 4 | **Andy Zelle/Venmo/WeChat Pay details** — invoice template has placeholders | Admin | Fill INVOICE_TEMPLATE_49 |
| 5 | **Stable broker URL confirmed** — Chen Kui must open workbench alone after Day 0 | Access | trial_launch_check + broker confirms |
| 6 | **Optional: signed acknowledgment of PILOT_TERMS_V1** — not legally required for $49 pilot but reduces dispute | Process | Send terms Day 0; WeChat OK |

**Not blockers (already done):**

- Append integrity PASS
- Demo readiness PASS
- Pricing defined ($49 / $99)
- Invoice template exists
- Simulation 30/30 PASS

---

## Shortest path to first invoice

```
Day 0 kickoff → 1 draft copied
     ↓
Days 1–6 → 9 more real add-car cases logged
     ↓
Day 7 → avg ≥4 min saved + broker says YES
     ↓
Send INVOICE_TEMPLATE_49 ($49 入门版)
     ↓
Zelle/Venmo/WeChat Pay → first payment
```

**Estimated calendar time:** 7 days (can compress to 3 if broker active).

---

## Pricing options

### Option A — Pilot Week Success Fee

| Item | Detail |
|------|--------|
| Price | **$49 one-time** for pilot week + first month |
| Trigger | ≥8/10 cases logged; avg ≥4 min saved; broker confirms value |
| Pros | Low commitment; matches "prove it first" |
| Cons | Harder to convert to recurring; feels like discount |

### Option B — Monthly SaaS

| Item | Detail |
|------|--------|
| Price | **$49/mo 入门版** or **$99/mo 标准版** (broker + assistant) |
| Trigger | Day 7 YES after 7-day free trial |
| Pros | Recurring revenue; aligns with PILOT_TERMS_V1 |
| Cons | Broker may hesitate without week of proof |

### Option C — Per Case

| Item | Detail |
|------|--------|
| Price | e.g. **$2–5 per add-car case** processed |
| Trigger | Invoice monthly by case count |
| Pros | Pay-for-value narrative |
| Cons | Tracking overhead; broker prefers simple monthly; unusual for SaaS |

---

## Recommendation

### **Option B — Monthly SaaS at $49/mo (入门版)**

**Why:**

1. **Already documented** in PILOT_TERMS_V1 and INVOICE_TEMPLATE_49 — no new commercial work.
2. **Chen Kui's volume** (~10–50 add-car cases/week) makes $49 trivial vs 6.2 min/case savings (~22 hr/mo at 50 cases).
3. **Success fee (A)** trains broker to stop after week 1; monthly builds habit.
4. **Per case (C)** adds friction (counting, disputes) with no upside at this price point.

**How to introduce at Day 7:**

> 陈哥，这 10 条你平均省了 X 分钟。试用结束了。$49/月继续用，和试用一样，随时取消提前 7 天说就行。

Start **入门版 $49**; upsell **标准版 $99** when Wu Miss consistently uses workbench.

---

## Invoice readiness checklist

| Item | Ready? |
|------|--------|
| Price defined | ✅ |
| Terms doc | ✅ PILOT_TERMS_V1 |
| Invoice template | ✅ INVOICE_TEMPLATE_49 |
| Payment rails | ⚠️ Fill placeholders |
| Broker value proof | ❌ Need pilot log |
| Broker verbal YES | ❌ Need Day 7 |
| **Charge today?** | **NO** |

---

*Phase 6 complete — invoice blocked on real pilot evidence; Option B recommended.*
