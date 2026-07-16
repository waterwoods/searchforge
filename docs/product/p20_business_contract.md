# P20 Business Contract (SSOT)

**Status:** governing business-language and field-priority contract for every P20 product surface  
**Date:** 2026-07-16  
**Authority:** business priorities, intake vs Request More language, and field classification  
**Does not replace:** Workflow & Timeline Blueprint (internal workflow/state/event semantics), North Star (journey/release gates), or `CURRENT_PRODUCT_SHAPE.md` (runtime truth)

---

## 1. Business first principle

The broker’s first job is **not** collecting documents.

The broker’s first job is **understanding the accident**.

Documents are **Request More**.

The product must teach this naturally: Customer Start Claim → accident understanding → Broker Review → Request More only when needed.

---

## 2. Authoritative business flow

```text
Customer Start Claim
  → Accident description
  → Date
  → Location
  → Anyone injured?
  → Contact (if needed)
  → Optional: Photos / Vehicle drivable / Police / Other driver (if known)
  → Submit
  → Broker Review
  → Request More
      (VIN / Insurance card / Better photos / Other insurance / Witness / Other missing evidence)
  → Customer supplements
  → Broker Review
```

Product surfaces must describe this same flow. Capability names, Blueprint phases, roadmap slices, Missing Information, Timeline, and Founder QA may use engineering detail underneath, but user-facing and product-contract language must not contradict this sequence or priority.

---

## 3. Classification law

Every customer-facing field belongs to **exactly one** class:

| Class | Meaning |
|---|---|
| **Must Have** | Required to understand the accident and reach Broker Review. Blocks Submit if absent. |
| **Nice to Have** | Helpful on initial intake; never blocks Submit. |
| **Request More** | Broker-requested after review. Not part of minimum initial intake. |
| **Never Ask** | Out of scope for this claim journey; must not appear as an intake or Request More item without a new Business Contract amendment. |

Rules:

1. No duplicates across classes.
2. No contradictions with this table.
3. A new field may not ship until it is classified here first.
4. Missing Information checklist and Request More draft/send vocabulary must respect this classification.
5. “Minimum intake” / “broker-ready” means **Must Have** only — never VIN, insurance card, or document packs.

---

## 4. Canonical field table (SSOT)

| Field | Business Priority | Initial Intake | Optional | Request More | Never | Business Reason |
|---|---|---|---|---|---|---|
| Accident description | Must Have | Yes | No | No | No | Broker cannot understand the accident without a short story of what happened. |
| Accident date | Must Have | Yes | No | No | No | Establishes when the loss occurred; core to claim understanding. |
| Accident location | Must Have | Yes | No | No | No | Establishes where the loss occurred; core to claim understanding. |
| Anyone injured? | Must Have | Yes | No | No | No | Injury status changes urgency and broker first review focus. |
| Contact (if needed) | Must Have | Yes (conditional) | No | No | No | Only when the broker cannot reach the customer otherwise; otherwise skip. |
| Photos (initial) | Nice to Have | Yes | Yes | No | No | Useful scene/vehicle context; broker can still understand without them. |
| Vehicle drivable | Nice to Have | Yes | Yes | No | No | Helps triage severity; not required to understand the accident. |
| Police involved / report | Nice to Have | Yes | Yes | No | No | Helpful context; not required to open Broker Review. |
| Other driver (if known) | Nice to Have | Yes | Yes | No | No | Partial other-party info is welcome; unknown is allowed. |
| VIN | Request More | No | No | Yes | No | Vehicle identity document/fact — collected after broker understands the accident. |
| Insurance card / policy evidence | Request More | No | No | Yes | No | Document collection; not the broker’s first job. |
| Better / retake photos | Request More | No | No | Yes | No | Quality follow-up after broker reviews what was already received. |
| Other insurance | Request More | No | No | Yes | No | Coverage follow-up after accident understanding. |
| Witness | Request More | No | No | Yes | No | Evidence follow-up when broker needs corroboration. |
| Other missing evidence | Request More | No | No | Yes | No | Catch-all for broker-specified gaps after review — never pre-loaded as Must Have. |
| Vehicle year / make / model (full identity pack) | Request More | No | No | Yes | No | Identity detail for quoting/coverage work after accident understanding. |
| Plate as substitute vehicle ID | Request More | No | No | Yes | No | Same class as VIN: identity follow-up, not minimum intake. |
| Full document / policy package before accident understanding | Never Ask | No | No | No | Yes | Contradicts business-first principle; teaches document collection as the first job. |
| Carrier portal login / payment / unrelated vertical fields | Never Ask | No | No | No | Yes | Out of paid-pilot claim scope; complexity without proven need. |
| Engineering IDs, Cap labels, workflow codes as customer asks | Never Ask | No | No | No | Yes | Violates North Star “no visible engineering jargon”; not a business field. |

---

## 5. Surface language contract

| Surface | Must say | Must not say |
|---|---|---|
| Customer Start Claim | Start with accident understanding; optional photos OK | VIN / insurance card / documents as required first steps |
| Broker Review | Review the accident first; then decide what is missing | Treat missing VIN/photos as incomplete “start” |
| Missing Information | Separate Must Have gaps from Request More candidates | Rank VIN/photos as critical for opening review |
| Request More | Broker-ordered follow-up for classified Request More fields | Synonym for initial intake or “finish collecting documents” |
| Timeline | Accident facts → submit → review → request more → supplement | VIN/photo as required before first Broker Review |
| Capability Contract | Business capabilities consume this table | Invent field priorities per capability |
| Blueprint | Workflow semantics may stay; “minimum intake” = Must Have only | VIN/plate/photo as deterministic minimum-intake order |
| Roadmap / North Star / Production Loop | Reference this SSOT for field priority | Optimize document collection over accident understanding |

---

## 6. Release gate

Future capabilities must never violate this contract.

If a new field appears, it must be classified in §4 **before** design or code.

When documents differ:

1. This Business Contract governs **business field priority and product language**.
2. North Star governs journey optimization and release gates.
3. Blueprint governs internal workflow/state/event semantics — and must not redefine Must Have as document collection.
4. `CURRENT_PRODUCT_SHAPE.md` remains runtime/deploy truth.

---

## 7. Relationship

- Governing product principles: `docs/product/p20_product_north_star.md`
- Loop worksheet: `docs/product/p20_production_loop_template.md`
- Workflow semantics: `docs/product/p20_workflow_timeline_blueprint.md`
