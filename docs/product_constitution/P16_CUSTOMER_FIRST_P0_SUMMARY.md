# P16 Customer First P0 Summary

**Sprint:** P16-CUSTOMER-FIRST-CONSTITUTION-P0  
**Date:** 2026-06-07  
**Type:** Documentation / constitution sprint — no product code changed

---

## 1. Did we successfully update the source of truth?

**Yes.** Customer First rules, north star, capacity interpretations, phased roadmap, gap audit, and multi-role review are documented. Future Cursor work can read:

- `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` — **primary law**
- `docs/product_constitution/P16_CUSTOMER_FIRST_GAP_REVIEW.md` — conflicts with current code
- This summary — next sprint order and GO/NO-GO

**Caveat:** Runtime still follows pre-constitution behavior (session return, optional phone on submit). Constitution is **target**; implementation is Phases 1–5.

---

## 2. Which documents were changed?

### Created

| Document | Purpose |
|----------|---------|
| `P16_CUSTOMER_FIRST_CONSTITUTION.md` | Seven rules + role timing |
| `P16_CUSTOMER_FIRST_GAP_REVIEW.md` | Aligned / conflicting / unclear / future reqs |
| `P16_CUSTOMER_FIRST_CONSTITUTION_REVIEW.md` | Four-role review |
| `P16_CUSTOMER_FIRST_P0_SUMMARY.md` | This file |

### Updated

| Document | Change |
|----------|--------|
| `P16Z25_NORTH_STAR.md` | Customer First north star + timing goals |
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` | Customer First section; add-car one-active-case note |
| `P16Z18_CAPACITY_MODEL.md` | Customer First interpretation per capacity |
| `P16Z25_90_DAY_ROADMAP.md` | Customer First phase order + out-of-scope list |
| `P16Z25_30_DAY_ROADMAP.md` | Customer First phase order + out-of-scope list |
| `ROADMAP_FROM_CONSTITUTION.md` | Customer First phase order + out-of-scope list |
| `docs/runbooks/OPERATOR_SURFACE.md` | Pointer to constitution |

---

## 3. What is the next implementation sprint?

**P16-CUSTOMER-FIRST-PHASE-1 — Customer First Screen**

Deliverables:

- Customer entry opens to **name + phone** capture (no login).
- Phone stored on session/case early (claimed, not verified).
- Copy answers: “We use your phone to find your add-car request when you come back.”
- No SMS, no OAuth, no backend lookup yet (Phase 2).

**Exit criteria:**

- Cold URL → customer enters phone + name → continues add-car intake.
- Constitution Rules 1 and 2 partially satisfied (phone collected; lookup Phase 2).
- Guardrails still PASS; broker paste path unchanged.

---

## 4. Is the next sprint customer first screen?

**Yes.** Phase 1 = customer first screen (name + phone). Phase 2 = phone lookup returns active case. Phase 3 = formal submit requires valid phone.

---

## 5. Should Postgres cleanup happen before or after the customer first screen?

**After customer first screen; before Chen Kui re-pilot.**

| Order | Rationale |
|-------|-----------|
| **Phase 1 first** | UI and copy need a stable phone field before cleanup criteria make sense |
| **Phase 2–3 next** | Lookup and submit gate define what “active case” and “valid phone” mean |
| **Phase 4 cleanup** | Dedupe stale demo cases, close orphan actives, normalize phones — **after** rules frozen |
| **Phase 5 Chen Kui** | Real pilot on customer-first URL with clean phone keys |

**Do not** run destructive Postgres cleanup during Phase 1 — risks breaking existing demos and obscures whether UI or data caused failures.

---

## 6. Remaining risks

| Risk | Mitigation |
|------|------------|
| Doc/code drift | Link constitution from gap review; Phase 3 enforces phone gate in code |
| Master outline §3.2 many-records language | Add-car wedge note added; full CRM case model still deferred |
| WeChat OAuth temptation | Marked out of scope; optional binding stays hidden until explicit sprint |
| Wrong-phone return | Phase 2 spec: validation + broker fix on workbench |
| Chen Kui expects paste-only | Pilot SOP: share customer link + broker confirm path |
| Demo data phone collisions | Phase 4 cleanup checklist before CK re-pilot |

---

## Final Verdict

| Initiative | Verdict | Notes |
|------------|---------|-------|
| **Customer First Constitution** | **GO** | SSOT complete; seven rules documented |
| **Customer First UI implementation** | **CONDITIONAL GO** | Phase 1 approved; Phases 2–3 required before “constitution satisfied” |
| **Postgres cleanup** | **CONDITIONAL GO** | After Phase 1–3 rules frozen; not before customer screen |
| **Chen Kui Pilot** | **CONDITIONAL GO** | Re-run on customer-first path after Phase 4 cleanup; paste path can continue in parallel during transition |

---

## Success Criteria (for future agents)

Future Cursor work must know:

| Rule | Short form |
|------|------------|
| Phone is required | Formal submit blocked without valid phone (Phase 3) |
| Phone is the return key | Lookup by phone, not login (Phase 2) |
| Customer does not log in | Anonymous start only |
| One customer, one active case | Server enforces per normalized phone |
| Progress = missing fields | Customer UI shows `still_needed_fields` |
| Broker confirms identity | Claimed ≠ confirmed |
| Broker closes or reopens case | No customer terminal actions |

**Read first:** `P16_CUSTOMER_FIRST_CONSTITUTION.md`  
**Before coding:** `P16_CUSTOMER_FIRST_GAP_REVIEW.md`

---

*End of P16 Customer First P0 Summary*
