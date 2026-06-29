# ADR-001: Request Readiness State Model

**Date:** 2026-06-20  
**Sprint:** P16 Documentation Freeze  
**Status:** Accepted  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Supersedes:** None (new decision)

---

## Decision

Only three broker-facing request states are allowed in V1:

| State | Symbol | Meaning |
|-------|--------|---------|
| **READY** | ✅ | All critical fields complete. No blocking conflicts. Broker can act now. |
| **NEED_INFO** | ⚠️ | Customer must provide missing critical information before broker can proceed. |
| **BROKER_REVIEW** | 🔵 | AI found a conflict or ambiguity that requires broker judgment. |

---

## Definitions

### READY
- All required fields for this request type are present and non-conflicting.
- VIN is valid (17 chars) and has a single source.
- Garaging ZIP is present.
- Customer name and phone are present.
- Broker can copy the packet and proceed immediately.

### NEED_INFO
- One or more **critical fields** are missing (e.g. VIN, Garaging ZIP, Make/Model for Replace Vehicle).
- System has identified the gap.
- Customer-facing prompt is generated: what is missing, how to provide it.
- Broker cannot safely quote without this information.

### BROKER_REVIEW
- AI extracted data but found a **conflict** that a human must resolve.
- Examples: conflicting VIN across two documents, effective date mismatch, multiple vehicles detected in one upload.
- Data is present but trustworthiness is flagged.
- Broker must decide: accept, override, or request correction.

---

## Field-Level Status

At the **field level**, use three symbols — distinct from request-level status:

| Symbol | Meaning |
|--------|---------|
| ✅ | Field present, single source, high confidence |
| ⚠️ | Field present but needs confirmation (e.g. defaulted from customer name, low confidence, or soft conflict) |
| ❌ | Field missing entirely |

**Request-level status is derived from field-level statuses:**

```
Any critical field = ❌           → NEED_INFO
Any critical field = conflict      → BROKER_REVIEW
All critical fields ✅ or ⚠️ only  → READY (broker sees ⚠️ individually)
```

---

## Rules

1. **Never show READY if a critical field is missing.** Optional fields (lienholder, delivery date) may be absent on a READY packet.
2. **VIN conflict always triggers BROKER_REVIEW**, not NEED_INFO. The data exists — the broker must judge, not the customer.
3. **No percentages.** Do not show "80% complete" or "3 of 5 fields ready." Brokers think in readiness, not completion scores.
4. **Do not add extra states in V1.** No PENDING, PROCESSING, IN_REVIEW, AWAITING_SIGNATURE, DRAFT, SUBMITTED, etc.
5. **BROKER_REVIEW is not an error state.** It is a judgment-required state. The packet may be good; broker confirms.
6. **Broker-facing status must be understood in 10 seconds.** If it requires explanation, the state design has failed.
7. **Readiness is evaluated on the materialized Trusted Packet. New evidence attached to an Active Case may change Packet readiness (including READY → BROKER_REVIEW on conflict). Per-field ✅ / ⚠️ / ❌ symbols remain stable within a single materialization until the next evidence append.**

---

## Critical vs. Optional Fields (Add Vehicle V0)

**Critical (required for READY):**
- VIN
- Year / Make / Model
- Garaging ZIP
- Customer Name
- Customer Phone

**Optional (missing = flagged but not blocking):**
- Lienholder
- Delivery Date
- Odometer / Mileage
- Lien amount

---

## Rationale

Broker needs exactly three answers when they open a case:

1. **Can I act now?** → READY
2. **Do I need the customer to send something?** → NEED_INFO
3. **Do I need to make a judgment call on conflicting data?** → BROKER_REVIEW

Any state model with more than three states at the request level adds cognitive load without adding action clarity. The broker's first second of attention is the most expensive second in the product.

---

## Consequences

- **UI stays simple.** Inbox shows three badge types, nothing else.
- **Request Framework remains scalable.** New request types inherit the same three states without modification.
- **Prevents state machine creep.** Future sprints cannot add PENDING_CARRIER, PARTIALLY_READY, etc. without updating this ADR.
- **Testing stays tractable.** Three states = three test paths per request type.

---

## Non-Decisions (explicitly out of scope for this ADR)

- How states are stored in the database (see `docs/CURRENT_PRODUCT_SHAPE.md`).
- How state is communicated to the customer (customer sees "sent to broker," not READY/NEED_INFO).
- Timeline events (deferred — see ADR-002).
- Carrier confirmation state (deferred — see ADR-003).

---

*Related: `ADR_002_NO_TIMELINE_V1.md` · `ADR_003_NO_CARRIER_API_V1.md` · `ADR_005_ACTIVE_CASE_CONSOLIDATION.md` (§10 — Rule #7 supersession rationale for multi-evidence Active Cases) · `docs/p16/P16_REQUEST_FRAMEWORK.md`*
