# P16-Z4 Phase 8 — Reality Simulation

**Date:** 2026-06-02  
**Sprint:** P16-Z4 Case Continuity Sprint  
**Personas:** Role C (cold broker) · Chen Kui · Assistant · Founder (Andy)  
**Sources:** P16-X simulations, P16-Y battery, P16-Q journeys, live product shape

---

## Simulation protocol

Each persona runs:

```
Turn 1: Paste customer message → copy draft → send WeChat
Turn 2: (48h later) Customer replies → ??? 
```

**Success:** Same `case_id`, updated draft, visible timeline, clear next action.  
**Failure:** New paste, lost context, or never reopens product.

---

## Role C — Cold independent broker

| Step | Behavior | Result |
|------|----------|--------|
| Day 0 Turn 1 | Finds trial URL (if SSO off) | Cancel notice → copy | ✅ Wins Turn 1 |
| Day 0 post-copy | Switches to WeChat | No continuation line | ❌ Doesn't know queue |
| Day 2 Turn 2 | Pastes reply in top box | **New case risk** | ❌ Continuity breaks |
| Day 7 | Doesn't return | — | ❌ Churn |

**Continuity breaks at:** Copy exit · Top paste fork · No waiting state

**Score:** 43/100 (P16-X) — unchanged without P16Z4 fixes

---

## Chen Kui — Supervised owner broker

| Step | Behavior | Result |
|------|----------|--------|
| Turn 1 | Andy shows paste → copy | ✅ Fast win |
| Turn 2 | Andy says "open queue, append" | ⚠️ Works if trained |
| Turn 2 unsupervised | Re-pastes in hero | ❌ Duplicate case |
| Day 2 habit | "直接回微信更快" | ❌ Unless 2-turn logged |

**Continuity breaks at:** Training dependency · Hero paste · No 在等客户 default

**Score:** 47/100 — Maybe once; not Day 2 without fixes

---

## Assistant — Office staff

| Step | Behavior | Result |
|------|----------|--------|
| Turn 1 | Broker delegates paste | ✅ Structured output |
| Turn 2 | Assistant reopens case | ⚠️ If broker shares case_id / screen |
| Follow-up fields | Sets waiting_on | ✅ API works |
| Timeline | Reads activity collapse | ⚠️ Buried |

**Continuity breaks at:** No shared "case link" ritual · Activity not scannable

**Score:** 44/100 — Only if mandated

---

## Founder — Andy

| Step | Behavior | Result |
|------|----------|--------|
| Demo | Knows reopen path | ✅ Two-turn demo possible |
| Trial broker | Must train append | ⚠️ Doesn't scale |
| Evidence | Needs observation log | ⚠️ Process gap |
| Deploy | FP-004 may block | ❌ L1=0 |

**Continuity breaks at:** Founder-as-UX · Access · No automated two-turn proof in CI

---

## Unified journey map

```
                    Turn 1 OK          Turn 2 FAIL
Role C              ████████░░         ░░░░░░░░░░
Chen Kui            ████████░░         ███░░░░░░░  (with Andy)
Chen Kui solo       ████████░░         ░░░░░░░░░░
Assistant           ████████░░         █████░░░░░  (mandated)
Founder demo        ██████████         ████████░░
```

---

## Where continuity breaks (master list)

| # | Breakpoint | Who hits it |
|---|------------|-------------|
| 1 | Copy → leave app | All |
| 2 | Append not visible on first persist | Chen Kui, Role C |
| 3 | Top paste = new case | Chen Kui solo, Role C |
| 4 | Summary loses Turn 1 on correction | All multi-turn |
| 5 | waiting_on never set | Chen Kui, Assistant |
| 6 | Timeline not visible (messages hidden) | Assistant, Chen Kui |
| 7 | Trial URL SSO blocked | Role C |
| 8 | Customer 提交补充 hidden | End customer |
| 9 | requires_new_case feels broken | Mixed-topic append |
| 10 | No external return trigger | All Day 2+ |

---

## Post-fix simulation (if 7-day plan shipped)

| Persona | Turn 2 success (est.) |
|---------|----------------------|
| Role C | 55% (with copy bridge + append visible) |
| Chen Kui solo | 65% (with paste collapse + waiting prompt) |
| Assistant | 75% (activity open + tracking summary) |
| Founder demo | 90% (unchanged, now teachable) |

---

*End of P16-Z4 Phase 8*
