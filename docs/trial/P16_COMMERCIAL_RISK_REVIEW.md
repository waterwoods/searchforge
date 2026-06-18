# P16 Commercial Risk Review

**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 6  
**Date:** 2026-06-06  
**Scope:** All 33 stress-test scenarios — failed and weak cases  
**Method:** Role-based commercial impact assessment

---

## Summary

| Outcome | Count |
|---------|-------|
| Total scenarios | 33 |
| Hard failures | **0** |
| Weak cases (quality <95 or field quirk) | **6** |
| Open P0 commercial issues | **0** |
| Open P1 issues | **4** |
| Open P2 issues | **3** |

All scenarios passed the ≥80 quality bar. No append or continuity regressions. Weak cases below are **survivable with broker edit** — not pilot blockers.

---

## Weak case review

### ST01 — 新 Tesla 买家 (quality 95)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **YES** — route, VIN, ZIP, driver all correct |
| Would office trust this? | **YES with note** — delivery_date briefly collected then back in still_needed on turn 3 |
| Would customer be confused? | **NO** — draft asks for gaps only |
| Would this block payment? | **NO** |

**Rank: P2** — Relative delivery date handling; broker knows calendar

---

### ST04 — 中英混合 (quality 92)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **YES** — vehicle and VIN correct |
| Would office trust this? | **PARTIAL** — "我drive" not parsed as primary_driver on turn 2 |
| Would customer be confused? | **NO** — still_needed asks for 主驾驶人 |
| Would this block payment? | **NO** |

**Rank: P1** — Mixed-language driver shorthand; broker adds one word in draft

---

### ST06 — 有 ZIP 无 driver (quality 88)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **YES** — correctly flags undecided driver |
| Would office trust this? | **YES** — primary_driver in still_needed |
| Would customer be confused? | **NO** |
| Would this block payment? | **NO** |

**Rank: P2** — Lowest quality score but correct behavior for ambiguous driver

---

### ST10 — 换车了 (quality 93)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **YES** — new VIN (RAV4) replaces Camry |
| Would office trust this? | **YES with confirm** — vehicle swap mid-thread |
| Would customer be confused? | **NO** |
| Would this block payment? | **NO** |

**Rank: P1** — Vehicle change requires broker glance at summary; no auto-split

---

### ST15 — 只发了部分信息 (quality 95)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **PARTIAL** — turn 1 alone doesn't route; needs turn 2 |
| Would office trust this? | **N/A until complete paste** |
| Would customer be confused? | **NO** |
| Would this block payment? | **NO** |

**Rank: P1** — Minimal opener "新车 insurance 多少钱" — broker must paste full thread (Day 0 training)

---

### ST08 — 两台车 (quality 100, watch item)

| Question | Answer |
|----------|--------|
| Would Chen Kui trust this? | **YES** — processes Model Y first as instructed |
| Would office trust this? | **YES with note** — Camry mentioned but not in packet |
| Would customer be confused? | **NO** |
| Would this block payment? | **NO** |

**Rank: P1** — Second vehicle not auto-flagged for split; broker handles manually

---

## Failed cases

**None.** 33/33 passed.

---

## Ranked issue register

### P0 — Must not fail in pilot week

| ID | Issue | Status |
|----|-------|--------|
| — | *(none open from stress test)* | ✅ |

Prior P0 mitigations remain in force: `trial_launch_check.sh`, append integrity, Day 0 fallback.

### P1 — Affects retention and payment

| ID | Issue | Cases | Mitigation |
|----|-------|-------|------------|
| P1-1 | Mixed-language driver shorthand | ST04 | Paste full thread; broker edits draft |
| P1-2 | Minimal opener needs second paste | ST15 | Day 0 tip: paste all bubbles |
| P1-3 | Two-vehicle thread manual split | ST08 | Broker quotes one at a time |
| P1-4 | Vehicle swap mid-thread | ST10 | Broker confirms summary before handoff |

### P2 — Polish / defer

| ID | Issue | Cases |
|----|-------|-------|
| P2-1 | Relative delivery in still_needed | ST01, ST09 |
| P2-2 | Ambiguous driver lowest score | ST06 |
| P2-3 | Family shared vehicle driver list | ST11 |

---

## Trust assessment by role

| Role | Trust verdict | Blocker? |
|------|---------------|----------|
| Chen Kui (broker) | **Would trust** for add-car paste | No |
| Wu Miss (office) | **Would trust** packet completeness | No |
| Customer | **Would not be confused** by drafts | No |
| Payment | **Would not block** at $49 tier | No |

---

*Anchors: [`P16_STRESS_TEST_RESULTS.md`](./P16_STRESS_TEST_RESULTS.md) · 33/33 pass · 0 append regressions · 0 continuity regressions*
