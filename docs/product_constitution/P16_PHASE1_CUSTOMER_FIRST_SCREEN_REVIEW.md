# P16 Phase 1 — Customer First Screen Review

**Sprint:** P16-PHASE1-CUSTOMER-FIRST-SCREEN  
**Date:** 2026-06-07  
**Scope:** Customer Entry Screen + immediate experience only

---

## 1. Customer

### Is it obvious?

**Mostly yes.** Within ~5 seconds the banner answers: no account, no password, phone matters, can come back.

**Friction:** Name field below phone adds a pause — see Name recommendation below.

### Is it simple?

**Yes.** One screen, one primary button, two outcomes (new vs continue).

### Is it trustworthy?

**Improving.** Saved vs submitted distinction on Scenario B is honest. Wrong-phone risk (Sim 3) is the main trust gap until copy warns “double-check phone.”

### What still causes confusion?

- Typo in phone → empty return (no gentle recovery hint yet).  
- Optional Name on first screen — customers may think it’s required or skip phone focus.  
- “Missing VIN” vs long missing list on fresh draft before vehicle entry.

### Name field — Phase 1 recommendation

**Recommend removing Name from the entry screen; keep Phone only.**

| For | Against |
|-----|---------|
| Phone = Constitution return key | Name is broker-assist, not continuity |
| Faster 5-second comprehension | Name can be collected in intake or at formal submit |
| Matches “Phone Is The Return Key” emphasis | Optional fields on step 1 still split attention |

If kept: move Name to after intake starts or formal submit boundary (Phase 3).

---

## 2. Broker (Chen Kui)

### Is it obvious?

**Yes.** Customer arrives with claimed phone on draft/case; workbench unchanged for paste path.

### Is it simple?

**Yes.** One active case per phone reduces duplicate WeChat threads.

### Is it trustworthy?

**Conditional.** Broker must still confirm identity (Rule 6) — no “verified” badge added (correct).

### What still causes confusion?

- Two cars same week → customer must Contact Broker (by design).  
- Wrong-phone duplicate cases until broker merges/ closes.

---

## 3. Office Assistant

### Is it obvious?

**Yes for Scenario B status** — missing fields visible to customer match workbench checklist language.

### Is it simple?

**Yes.** No new office UI; fewer “who is this?” cases when phone is on draft early.

### Is it trustworthy?

**Conditional.** Collecting drafts appear in queue — assistants should treat as **not submitted** until formal submit (Phase 3 gate).

### What still causes confusion?

- Pilot Postgres may have stale phone collisions until Phase 4 cleanup.

---

## 4. Founder

### Is it obvious?

**Yes.** Phase 1 delivers constitution-facing entry, not portal scope creep.

### Is it simple?

**Yes.** Two endpoints, one screen, simulation script.

### Is it trustworthy?

**Conditional GO** — real cross-device return works when phone on case; formal submit phone gate still Phase 3.

### Commercial lens

| Question | Answer |
|----------|--------|
| Supports Customer First? | **Yes** — anonymous entry + phone continuity |
| Supports Phone Is Return Key? | **Yes** — lookup shipped (indexed PG) |
| Reduces broker workload? | **Moderate** — less “where’s my link?”; broker confirm still required |
| Reduces office workload? | **Moderate** — phone on draft; submitted vs saved clearer |
| Chen Kui would understand? | **Yes** — WeChat-forward link → phone → continue |
| Wu Xiaojie (office) would understand? | **Yes** — missing fields = her checklist |
| Increases $49/mo probability? | **Small positive** — professional entry vs paste-only; needs pilot proof |

---

## Cross-Role Summary

| Role | Obvious | Simple | Trustworthy | Top confusion |
|------|---------|--------|-------------|---------------|
| Customer | ✅ | ✅ | ⚠️ | Wrong phone; optional Name |
| Broker | ✅ | ✅ | ⚠️ | Second car SOP |
| Office | ✅ | ✅ | ⚠️ | Draft vs submitted in queue |
| Founder | ✅ | ✅ | ⚠️ | Phase 3–4 still required |

---

*End of review*
