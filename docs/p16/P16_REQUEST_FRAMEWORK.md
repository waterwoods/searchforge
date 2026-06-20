# P16 Request Framework

**Date:** 2026-06-20  
**Sprint:** P16 Documentation Freeze  
**Status:** Accepted — Formal Spec  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`  
**Supersedes for formal spec:** `docs/p16/P16_UNIFIED_FRAMEWORK_SIMULATION_V1.md` (simulation phase; this is the extracted spec)

---

## 1. Product Definition

**P16 = Unified Intake + Insurance Readiness Engine**

P16 turns messy customer documents into a Trusted Packet the broker can act on immediately.

```
Customer Request
→ Readiness
→ Broker Ready Request
```

P16 ends at the Broker Ready Packet. It does not quote. It does not update the policy. It does not connect to carriers.

---

## 2. Core Flow (All Request Types)

Every request type follows this same 7-step flow:

```
Step 0: Intent         →  Customer selects what they need
Step 1: Basic Info     →  Name · Phone · Garaging ZIP
Step 2: Upload         →  Documents (PDF / JPG / PNG / HEIC)
Step 3: Extract        →  Gemini Flash 2.5 extracts fields
Step 4: Readiness      →  Fields checked: ✅ / ⚠️ / ❌
Step 5: Fix Missing    →  Customer fixes ❌ fields (text or re-upload)
Step 6: Broker Ready   →  Trusted Packet delivered to broker/office
Step 7: Broker Action  →  Broker copies packet; follows up with customer
```

The customer experience ends at Step 6.  
The broker experience starts at Step 6.

---

## 3. Core Design Principle

> **New request type = new schema, not new product.**

Adding a new request type only requires:

1. A **request schema** (which fields are required / optional)
2. A list of **accepted documents** (what the customer should upload)
3. **Readiness rules** (what constitutes READY vs. NEED_INFO vs. BROKER_REVIEW)
4. A **packet format** (how the broker sees the extracted data)

The same flow, the same UI components, the same extraction engine serve all request types.  
No new backend routes per request type. No new pages per request type.  
Configuration drives the difference.

---

## 4. V1 Request Types (Build Now)

### 4.1 Add Vehicle

**Use case:** Customer bought a new car and needs to add it to their existing policy.

**Required fields:**
- VIN (from purchase agreement or registration)
- Year / Make / Model
- Garaging ZIP
- Customer Name + Phone

**Optional fields:**
- Lienholder (if financed)
- Delivery / Effective Date

**Accepted documents:**
- Purchase agreement (highest priority — contains VIN)
- Vehicle registration
- Current insurance card (for policy context)
- HEIC / JPG photos of VIN plate

**Readiness rules:**
- READY: VIN + Year/Make/Model + Garaging ZIP all present, no VIN conflict
- NEED_INFO: VIN missing or unreadable
- BROKER_REVIEW: Conflicting VINs across documents, or trade-in vehicle detected

**Packet format:**
```
ADD-CAR PACKET
Customer: [Name] · [Phone] · ZIP: [Garaging ZIP]
Vehicle:  VIN · Year · Make · Model  (source: filename)
Driver:   Primary Driver             (source or defaulted)
Finance:  Lienholder                 (if present)
Dates:    Effective Date             (if present)
Warnings: [any conflicts]
Missing:  [any ❌ optional fields]
Sources:  file → fields map
```

**Status:** ✅ Implemented and live. CK-DRY-01 PASS.

---

### 4.2 Replace Vehicle V1 Safe

**Use case:** Customer is replacing one vehicle on their policy with a new one. Old vehicle is removed; new vehicle is added.

**Required fields (new vehicle):**
- New VIN
- New Year / Make / Model
- Garaging ZIP

**Required fields (old vehicle — for context):**
- Old VIN or Old License Plate (at least one identifier)

**Accepted documents:**
- New vehicle purchase agreement
- New vehicle registration
- Old insurance card or declaration page (for old vehicle identification)

**Readiness rules:**
- READY: New VIN + Year/Make/Model confirmed; old vehicle identifier present
- NEED_INFO: New VIN missing; or neither old VIN nor old plate provided
- BROKER_REVIEW: New VIN conflicts across documents; or trade-in VIN matches existing policy VIN ambiguously

**Packet format:**
```
REPLACE-VEHICLE PACKET
Customer: [Name] · [Phone] · ZIP: [Garaging ZIP]

New Vehicle:    VIN · Year · Make · Model  (source: filename)
Old Vehicle:    VIN or Plate               (source: filename or intake)

Warnings: [VIN conflicts · old vehicle ambiguity]
Missing:  [any ❌ fields]
Sources:  file → fields map
```

**Safety rules:**
- Do NOT auto-remove the old vehicle from any system.
- Do NOT confirm to the customer that the old vehicle is removed.
- Broker must take the manual action in their AMS/carrier portal.
- Output language: "Broker will review and process the replacement."

**Status:** ⏳ Implementation target: Day 2 of 4-day build plan.

---

## 5. V2 / Later Request Types (Do Not Build Now)

These are validated future request types. Do not implement until Add Vehicle + Replace Vehicle V1 Safe are stable and 10-case pilot gate is reached.

| Request Type | Trigger |
|-------------|---------|
| Switch Insurance | Customer wants to move to a different carrier at renewal |
| Renewal / Quote Shopping | Annual renewal — broker shops rates across carriers |
| Add Driver | New licensed driver joining policy |
| Address Change | Garaging ZIP change (affects rate) |
| Coverage Change | Limits or deductibles adjustment |

Each of these follows the same 7-step flow and the same component set. No new architecture is required — only a new schema and new readiness rules.

---

## 6. Explicit Exclusions (V1 and V1 Only)

The following are **not part of this framework** in V1. Adding them requires an ADR update, not just a sprint decision.

| Item | Exclusion Rationale |
|------|---------------------|
| Payment processing | Not the product's revenue model at pilot stage |
| Claims intake | Different workflow; different regulatory surface |
| Carrier API / quote engine | See ADR-003 |
| CRM write-back | Broker's existing tools; not P16's wedge |
| Timeline UI | See ADR-002 |
| WeChat Bot | Paste/link only; no native integration |
| Customer login / accounts | Phone + link identity only |
| PDF export | Copy All is the V1 delivery mechanism |
| Multi-broker / multi-tenant | Single pilot; no tenant isolation |
| Trade-in automation | Flag only; broker resolves manually |

---

## 7. Information Buckets (Shared Across All Request Types)

All extracted data maps to exactly three buckets:

```
┌─────────────┬──────────────────┬────────────────────────┐
│   DRIVER    │    VEHICLE       │   POLICY DETAILS       │
├─────────────┼──────────────────┼────────────────────────┤
│ Name        │ VIN              │ Garaging ZIP           │
│ Phone       │ Year             │ Effective Date         │
│ DL Number   │ Make             │ Lienholder             │
│             │ Model            │ Coverage Type          │
│             │ Color (optional) │ Deductibles (optional) │
└─────────────┴──────────────────┴────────────────────────┘
```

Every request type extracts into these same three buckets. The packet always displays in this same order. Broker always knows where to look.

---

## 8. Shared Reusable Components

These components are built once and reused across all request types. A new request type does not require new components — only configuration.

| Component | Purpose |
|-----------|---------|
| **Intent Selector** | Customer picks their request type in plain language |
| **Upload Panel** | Multi-file upload (PDF / JPG / PNG / HEIC); phone-friendly |
| **Extract Progress** | Friendly loading animation; no technical model names |
| **Readiness Checklist** | ✅ / ⚠️ / ❌ per field; no percentages |
| **Missing Items Panel** | Guides customer on what to provide and how |
| **Broker Ready Banner** | "READY FOR BROKER" or "NEED_INFO" or "BROKER REVIEW" |
| **Source Attribution** | "from: purchase_agreement.pdf" inline per field |
| **Copy Packet** | One-click copy of formatted packet to clipboard |

---

## 9. Safety Rules (Non-Negotiable)

These rules apply to every request type, every sprint, every engineer working on P16.

1. **Do not auto-remove vehicles.** Removal is a broker action in their AMS. P16 flags; broker acts.
2. **Do not silently resolve VIN conflicts.** If two documents have different VINs, show BROKER_REVIEW. Never pick one silently.
3. **Do not show READY if critical fields are missing.** A packet missing the VIN is never READY.
4. **Do not tell the customer their policy has changed.** Language must be: "sent to broker" / "broker will confirm."
5. **Do not expose AI model names to the customer or broker.** No "gemini-1.5-flash" visible in any UI.
6. **Do not show mock mode banners in production.** Guard behind `import.meta.env.DEV`.

---

## 10. Extension Rule

When adding a new request type (V2+), the work is:

```
1. Define request schema (fields: required vs. optional)
2. Define accepted documents (what customer uploads)
3. Define readiness rules (READY / NEED_INFO / BROKER_REVIEW triggers)
4. Define packet format (how broker sees the data)
5. Register in RequestTypeFieldConfig
6. Add Intent Selector option (one line)
7. Write QA test case (simulate one real upload)
```

**That is all.** No new page. No new route. No new extraction engine. No new database table.

---

## Document Hierarchy

| Priority | Document | Role |
|----------|----------|------|
| 1 | `docs/p16/P16_DECISION_FREEZE_V1.md` | Scope + architecture freeze |
| 2 | **This file** | Request framework formal spec |
| 3 | `docs/p16/adr/ADR_001_REQUEST_READINESS.md` | State model rules |
| 4 | `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` | Timeline deferral |
| 5 | `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md` | Carrier API deferral |
| 6 | `docs/CURRENT_PRODUCT_SHAPE.md` | Runtime + deploy truth |

---

*Full simulation (pre-spec exploration): `docs/p16/P16_UNIFIED_FRAMEWORK_SIMULATION_V1.md`*
