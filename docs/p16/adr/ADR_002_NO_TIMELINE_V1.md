# ADR-002: No Timeline UI in V1

**Date:** 2026-06-20  
**Sprint:** P16 Documentation Freeze  
**Status:** Accepted  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Supersedes:** `docs/p16/P16_TIMELINE_STATE_MACHINE_DESIGN.md` (design approved but implementation deferred)

---

## Decision

Timeline UI, Timeline V2 (new Postgres timeline table), and case history panels are **deferred until after the 10-case pilot gate.**

No timeline surface — in the customer flow or broker packet view — will be built in V1.

---

## What Is Deferred

| Item | Status |
|------|--------|
| Ant Design `<Timeline>` in PacketStep | Deferred |
| New `p16_timeline_events` Postgres table | Deferred |
| Case activity log surfaced to broker | Deferred |
| "What happened at 9:03 AM?" audit view | Deferred |
| Customer submission history | Deferred |
| Case status history visible to office | Deferred |

---

## What Is NOT Deferred

| Item | Status |
|------|--------|
| Case state stored in `lifecycle_status` | Kept — existing field, not new |
| `case_activity` JSONB in `service_records.extra` | Kept — internal logging only, not surfaced |
| Case ID + timestamp in Trusted Packet header | Kept — this is identity, not timeline |
| Readiness state (READY / NEED_INFO / BROKER_REVIEW) | Kept — see ADR-001 |

---

## Rules

1. **No Timeline panel** in the customer flow (Screens 0–6).
2. **No Timeline panel** in the broker Trusted Packet in V1.
3. **Case activity may be stored internally** if already available in existing fields — but must not be surfaced as product UI.
4. **Re-evaluate only after** either:
   - 10 real cases are logged (CK-001 through CK-010), OR
   - Chen Kui or Wu Xiaojie explicitly asks: "I want to see what happened and when."
5. **Do not add UI complexity** to justify technical capability. The timeline system design (P16_TIMELINE_STATE_MACHINE_DESIGN.md) is a good design — it is deferred, not rejected.

---

## Rationale

When Wu Xiaojie or Chen Kui opens a case, they have three questions:

> "Ready or not?"  
> "Missing what?"  
> "Can I copy the packet?"

They do not ask:
> "What happened at 9:03 AM?"  
> "When did the customer upload the second document?"  
> "How many state transitions has this case had?"

Timeline is a **power-user feature** for a tool they haven't adopted yet. Building it now would:

- Add 2–4 hours of development time with zero pilot ROI
- Add UI clutter to the broker's first impression of the product
- Pull developer focus away from Add Vehicle stability and Replace Vehicle V1 Safe
- Create a Salesforce-like case management surface before the wedge is proven

The broker's first 10 cases must feel fast, clean, and trustworthy — not feature-rich.

---

## Consequences

- **Less UI clutter.** Broker packet is scannable in 10 seconds.
- **Faster demo.** No "what is this timeline for?" questions from Chen Kui.
- **Faster development.** Day 2–4 focus stays on Add Vehicle stability and Replace Vehicle V1 Safe.
- **Design preserved.** `P16_TIMELINE_STATE_MACHINE_DESIGN.md` is a valid plan for V2. Nothing is thrown away.
- **Constraint documented.** No future sprint can add timeline without updating this ADR.

---

## Reconsideration Trigger

This decision is revisited if:

1. **10-case gate is reached** (CK-001 through CK-010 completed), OR
2. **Explicit broker request:** Chen Kui or Wu Xiaojie says "I want to see history" or "What happened to this case?", OR
3. **Compliance requirement** emerges that mandates an audit log surface (unlikely for V1 pilot scope)

---

*Related: `ADR_001_REQUEST_READINESS.md` · `ADR_003_NO_CARRIER_API_V1.md` · `ADR_005_ACTIVE_CASE_CONSOLIDATION.md` · `docs/p16/P16_TIMELINE_STATE_MACHINE_DESIGN.md` (deferred design)*
