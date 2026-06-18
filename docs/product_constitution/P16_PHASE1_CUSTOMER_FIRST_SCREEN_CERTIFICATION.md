# P16 Phase 1 — Customer First Screen Certification

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-SCREEN  
**Date:** 2026-06-07  
**Artifact certified:** Customer Entry Screen + active case check + immediate post-continue experience  
**Not in scope:** Full product, formal submit gate, Postgres cleanup, Chen Kui re-pilot

---

## Health Score

**72 / 100**

| Dimension | Score | Note |
|-----------|-------|------|
| Constitution fit | 78 | Rules 1,2,4,7 partially enforced in UI+API |
| Customer clarity | 75 | 5-second test passes; Name field dilutes |
| Runtime reliability | 70 | PG phone index; pilot data not cleaned |
| Broker/office fit | 72 | Draft phone early; submitted gate Phase 3 |
| Commercial readiness | 68 | Entry credible; needs cold-URL broker trial |

---

## Top 5 Strengths

1. **Phone-first entry** — No login wall; constitution Rules 1 & 2 visible in first screen copy.  
2. **Active case card** — Vehicle, missing fields, submit state (saved vs submitted) on Scenario B.  
3. **Rule 7 enforcement** — Second start-add-car returns 409 with broker path.  
4. **Fast lookup** — Indexed Postgres phone query (not full-table scan).  
5. **Simulation harness** — Repeatable 4-scenario script + unit tests for regression.

---

## Top 5 Risks

1. **Wrong phone digit** — Silent empty lookup; customer may duplicate effort (Sim 3).  
2. **Name on step 1** — Low constitution value; recommend remove for Phase 1.  
3. **Formal submit without phone gate** — Still Phase 3; office may see drafts without full vehicle.  
4. **Pilot phone collisions** — Phase 4 cleanup not done; lookup may match wrong stale case.  
5. **API key in customer bundle** — Same as existing intake; not true public internet anonymity.

---

## Verdict

### Customer Entry Screen

## **CONDITIONAL GO**

| Criterion | Status |
|-----------|--------|
| Cold URL → phone → continue | ✅ |
| Scenario A / B | ✅ |
| Saved ≠ submitted visible | ✅ |
| 4 simulations pass | ✅ |
| Formal submit phone required | ❌ Phase 3 |
| Postgres cleanup | ❌ Phase 4 |
| Remove Name from step 1 (recommended) | ⏳ Optional fast follow |

**Ship for supervised demo and broker-supervised customer links.**  
**Do not claim “constitution satisfied” until Phase 3 (submit gate) + Phase 4 (data cleanup).**

---

## Sign-Off Matrix

| Stakeholder | Entry screen only |
|-------------|-------------------|
| Customer | CONDITIONAL GO |
| Broker | CONDITIONAL GO |
| Office | CONDITIONAL GO |
| Founder | CONDITIONAL GO |

---

*End of certification*
