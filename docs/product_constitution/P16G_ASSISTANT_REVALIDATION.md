# P16-G Phase 6 — Assistant Revalidation (Round 2)

**Date:** 2026-05-31  
**Persona:** Office assistant — 50 conversations/day, 100 unread, WeChat-primary  
**Tool:** Sprint A Preview (product_only), post-CORS

---

## Round 1 vs Round 2

| Metric | P16-F.5 | P16-G | Delta |
|--------|---------|-------|-------|
| **Overall assistant composite** | **33 / 100** | **50 / 100** | **+17** |
| First 30s (orientation) | 70 | **72** | +2 |
| First 5 min (first triage) | 30 | **58** | +28 |
| Day 1 (10 messages) | 30 | **52** | +22 |
| Day 7 (habit) | 40 | **48** | +8 |

---

## Would this save time?

**MAYBE — if broker mandates and I get training.**

| Expected savings | Post-CORS |
|------------------|-----------|
| Skip re-reading full thread | ✅ Triage summarizes |
| Queue sorted by urgency | ✅ Queue loads; filters available when cases exist |
| Draft ready to edit | ✅ API returns draft in ~5–10s |
| Same record for follow-up paste | ✅ Persisted cases in queue |

Estimated savings **if mandated:** 8–15 min/day (same as P16-F.5 estimate, now **API-validated** on Preview origin).

Estimated time **lost** on Day 0 without training: +10 min (Vercel login, tab confusion, finding follow-up paste).

---

## Would I keep using it?

**UNCERTAIN — Day 3–7 depends on broker mandate.**

Habit formation requires: (1) queue loads reliably ✅, (2) first paste succeeds within 30s ✅ API, (3) broker mandates use ❌ not yet. Without mandate, I might try it for urgent cancellations only, then revert for routine messages.

---

## Would I revert to WeChat?

**PARTIALLY** — WeChat remains default for quick replies. I would use workbench for cancellation notices and missing-doc threads if Chen Kui says "use the system for these."

Was: **YES immediately** (Network Error). Now: **mixed parallel workflow**.

---

## Would I use it every morning?

**NO** — not until queue is the office standard and stable URL exists (Production still pre-Sprint A). Hash URL + Vercel login = too fragile for morning ritual.

---

## Scorecard

| Dimension | Score /5 | ×20 → /100 |
|-----------|----------|------------|
| **Daily usefulness** | 2.5 | **50** |
| **Weekly usefulness** | 2.5 | **50** |
| **Habit formation** | 2.0 | **40** |

**Overall: 50 / 100**

---

## Assistant-specific confusions (remaining)

1. Vercel login — looks like IT setup, not product
2. Two tabs — might open 客户报送 and think Add-Car only
3. Filters hidden until queue has cases — first visit may show many cases (569 on Cloud Run) — actually OK post-load
4. 「更新客户新消息」hard to find for follow-up paste
5. No mobile proof — assistants often on phone

---

## Verdict

CORS fix moves assistant from **"system broken"** to **"could work with mandate."** Not habit-forming yet. Broker training + stable production URL required before Day 7 habit score rises above 55.

---

*End of P16-G Phase 6*
