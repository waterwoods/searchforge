# P16-F.5 Phase 6 — Office Assistant Simulation

**Date:** 2026-05-31  
**Persona:** Office assistant — 50 conversations/day, 100 unread messages, WeChat-primary  
**Tool under test:** Sprint A Preview (product_only)

---

## Daily workflow context

Morning: scan queue for 需今天处理 → open case → read 下一步 → copy/edit draft → WeChat send. Repeat 50×. Cannot afford extra clicks or "system broken" messages.

---

## Would this save time?

**NO — today.**

| Expected savings (if working) | Actual on Preview |
|------------------------------|-------------------|
| Skip re-reading full thread | ❌ Cannot triage |
| Queue sorted by urgency | ❌ Queue load fails |
| Draft ready to edit | ❌ Never reaches draft panel |
| Same record for follow-up paste | ❌ No persisted case in UI |

Estimated time **lost** vs WeChat-only: +2–5 min per attempt (retry, confusion, ask broker).

**If CORS fixed:** Estimated savings **8–15 min/day** based on P11 triage engine quality and guardrail PASS — **not validated on Preview origin**.

---

## Would I keep using it?

**NO** after Day 1 failure.

Habit formation requires: (1) queue loads reliably, (2) first paste succeeds within 30s, (3) broker mandates use. Preview fails (1) and (2). Without broker mandate, I revert immediately.

---

## Would I revert to WeChat?

**YES — immediately.**

WeChat is slow but **works**. Network Error on a broker-provided tool → I tell Chen Kui "系统打不开" and handle messages manually. Parallel workflow persists.

---

## Scorecard

| Dimension | Score /5 | ×20 → /100 |
|-----------|----------|------------|
| **Daily usefulness** | 1.5 | **30** |
| **Weekly usefulness** | 2.0 | **40** |
| **Habit formation** | 1.0 | **20** |

| Horizon | Avg /5 | /100 |
|---------|--------|------|
| First 30s (orientation) | 3.5 | 70 |
| First 5 min (first triage) | 1.5 | 30 |
| Day 1 (10 messages) | 1.5 | 30 |
| Day 7 (habit) | 2.0 | 40 |

**Overall assistant composite: 33 / 100** (vs P16-F **35**, P16-E assumed **70**)

---

## What would change the score (no new features — blockers only)

1. CORS fix → queue + triage work on Preview URL  
2. Broker mandates + 15-min training script (Sprint 4 item — process, not code)  
3. Demo queue loads so assistant sees cancellation example before real paste  
4. Production deploy of Sprint A so stable URL (no hash/CORS whack-a-mole)

---

## Assistant-specific confusions

1. Network Error looks like IT problem, not "allowlist config"  
2. Two tabs — I might open 客户报送 and think product is Add-Car only  
3. Filters hidden until queue has cases — empty first load hides urgency tools  
4.「更新客户新消息」hard to find for follow-up paste  
5. No mobile-optimized proof — assistants often on phone (not tested this sprint)

---

*End of P16-F.5 Phase 6*
