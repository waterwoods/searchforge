# Naming Freeze — Claim Vehicle vs Add Car

**Status:** Frozen — authoritative product-language SSOT  
**Date:** 2026-07-21  
**Authority:** Terminology only (no workflow or code change)  
**Decision Log:** D-011  
**Related:** `docs/product/CLAIM_VEHICLE_IDENTITY_V1.md` (claim object/contract freeze)

Architecture is correct. Naming was not. This document freezes language so Policy
Management, Claim, and backend objects are never confused again.

---

## 1. One-glance distinction

| Domain | Business question | Canonical English | Canonical Chinese |
|--------|-------------------|-------------------|-------------------|
| **Policy Management** | Customer already has a policy and wants to add or replace a vehicle on that policy | **Add Car** | **保单加车** |
| **Claim** | An accident happened; which vehicle is involved in this claim? | **Claim Vehicle** | **事故车辆** |
| **Backend** | Persist / merge / idempotent fact storage for a claim vehicle slot | **Vehicle Identity** (internal) | **车辆对象（内部）** |

If a sentence could mean either “change the policy” or “identify the accident car,”
it is wrong and must be rewritten.

---

## 2. Canonical terminology table

| Term | Meaning | Owner domain | Customer-facing? |
|------|---------|--------------|------------------|
| **Add Car** | Policy workflow: insured adds or replaces a vehicle on an existing policy | Policy Management | **Yes** — when that product surface is shown (`保单加车`) |
| **Add Vehicle** | Legacy English synonym for **Add Car** (WeCom/H5/docs history) | Policy Management (legacy label) | **Prefer no** — new copy uses **Add Car** / `保单加车` |
| **Claim Vehicle** | Claim workflow: identify the vehicle involved in the current accident claim | Claim | **Yes** — `事故车辆` (or softer `车辆信息` on forms) |
| **Vehicle Information** | Customer-facing Request More / form label for claim vehicle details (year/make/model, optional VIN/plate) | Claim | **Yes** — `车辆信息` |
| **Vehicle Identity** / **Claim Vehicle Identity** | Backend canonical vehicle object: persistence, merge, idempotency, fact keys | Engineering / claim storage | **No** — never show in customer or broker task UI |
| **Vehicle** (alone) | Ambiguous — not a product name | — | **No** — always qualify |
| **VIN** | Vehicle identification number; optional Request More fact on a claim | Claim (also may appear in Add Car later) | **Yes** — keep `VIN` or `车架号` per surface guide |
| **`SERVICE_LANE_ADD_CAR`** / `add_car` | Backend service-lane marker for the Policy **Add Car** lane | Policy / WeCom backend | **No** |
| **`vehicle_information`** | Claim checklist / Slice1 field key for structured claim vehicle pack | Claim backend | **No** (key); UI label = Vehicle Information / `车辆信息` |
| **`own_vehicle_info`** | Legacy claim summary fact alias (free-text / Workbench) | Claim backend | **No** (key); may project as `您的车辆信息` |
| **`vehicle_vin` / `vin`** | Claim fact keys for VIN | Claim backend | **No** (keys) |

---

## 3. Terms that must NEVER be mixed

| Do not say… | When you mean… | Why |
|-------------|----------------|-----|
| Add Car / Add Vehicle | Claim Vehicle / Request More vehicle pack | Policy change ≠ accident vehicle ID |
| Claim Vehicle / Vehicle Information | Add Car policy endorsement | Claim must not market itself as 加车 |
| Vehicle Identity | Anything customer- or broker-task-facing | Internal object name; violates North Star “no engineering jargon” |
| “Add Vehicle V1” (unqualified) | Claim Vehicle Identity V1 | Historical planning phrase; sounds like Policy Add Car |
| Vehicle (alone) in specs | Either domain | Forces readers to guess Policy vs Claim |
| `SERVICE_LANE_ADD_CAR` | Claim persistence path | Lane is Policy Add Car only |
| `intake_entities` “vehicle entity” | Claim Vehicle Identity SoT | Different storage story; see V1 freeze |

**Hard rules**

1. Claim must never call itself **Add Car** or **Add Vehicle**.  
2. Policy Add Car must never reuse **Claim Vehicle** / claim Request More copy as its product name.  
3. Customer UI must never display **Vehicle Identity**.  
4. Backend object names may differ from UI wording (`vehicle_information` ≠ “Vehicle Identity”).  
5. New docs prefer **Add Car** over **Add Vehicle** for the policy lane; treat **Add Vehicle** as legacy synonym only.

---

## 4. Chinese terminology recommendation

| English (canonical) | Chinese (canonical) | Notes |
|---------------------|---------------------|-------|
| Add Car | 保单加车 | Policy Management; explicit「保单」prevents claim confusion |
| Add Vehicle (legacy) | 保单加车 | Do not invent a second Chinese name |
| Claim Vehicle | 事故车辆 | Claim domain product concept |
| Vehicle Information | 车辆信息 | Form / Request More title (claim) |
| Vehicle Identity | 车辆对象（内部） | Engineers only |
| VIN | VIN / 车架号 | Keep short; pair with 事故车辆 context on claim |
| Explicit intent (legacy WeCom) | 我要加车 | Means **Add Car** (policy), not claim vehicle ID |

Claim form microcopy (already frozen in V1) stays under **车辆信息**, not **保单加车**.

---

## 5. Naming rules for future development

1. **Pick the domain first** — Policy Management, Claim, or Backend — then pick the term.  
2. **Customer UI** uses Chinese business words (`保单加车`, `事故车辆`, `车辆信息`) — never `Vehicle Identity`, `service_lane`, or raw field keys.  
3. **Broker Workbench** may show lane badges for Add Car cases as **Add Car** / `保单加车`, and claim vehicle facts as **车辆信息** / accident vehicle — never label a claim case “Add Car” because it has VIN.  
4. **API / code keys** may keep historical names (`SERVICE_LANE_ADD_CAR`, `vehicle_information`, `own_vehicle_info`, `add_vehicle_*.py`) until an explicit rename task; comments and new symbols should follow this glossary.  
5. **New product docs and commits** must say:
   - **Add Car** for policy lane work  
   - **Claim Vehicle** / **Claim Vehicle Identity** for claim vehicle V1 work  
   - Not unqualified **Add Vehicle** for claim scope  
6. **Tests and fixtures** should name scenarios `add_car_*` vs `claim_vehicle_*` in new code; do not rename mass legacy tests in this freeze.  
7. **P36 / roadmap “out of scope: Add Vehicle”** in older evidence means “do not start the next vehicle capability yet”; going forward write **Claim Vehicle** or **Add Car** explicitly.

---

## 6. Repository locations with inconsistent naming

Documentation-only inventory. **No code rename in this task.**

### 6.1 Prefer wording updates when next touched (docs)

| Location pattern | Issue | Future wording |
|------------------|-------|----------------|
| `docs/product/CLAIM_VEHICLE_IDENTITY_V1.md` | Correct claim freeze; still mentions “Add Vehicle discovery” historically | Keep; when editing, say “Claim Vehicle discovery / planning” |
| `docs/product/decision_log.md` D-010 | Context says “Add Vehicle discovery” | Interpret as Claim Vehicle planning; optional clarify on next edit |
| `docs/evidence/p36_*`, `docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md` | “Out of scope: Add Vehicle” | Prefer “Claim Vehicle / Add Car (not in this task)” |
| `docs/design/p19h3h_add_car_*`, `docs/p19e*add_vehicle*` | Mix **Add Car** and **Add Vehicle** for same policy lane | Canonical: **Add Car** (`保单加车`) |
| `docs/design/p19m0_*`, miniapp README “No Add Car” | Correct exclusion of policy lane from claim prototype | Keep meaning; do not rewrite as Claim Vehicle |
| `docs/VEHICLE_ENTITY_MEMORY_MVP.md` | “Vehicle entity” near Add Car memory | Label as Policy/WeCom entity memory — not Claim Vehicle Identity |

### 6.2 Code / UI — document only; rename not required for V1

| Location | Issue | Guidance |
|----------|-------|----------|
| `SERVICE_LANE_ADD_CAR` / `add_car` | Name is correct for Policy Add Car | Keep; never reuse for claim |
| `services/fiqa_api/wecom/add_vehicle_*.py`, `routes/add_car.py` | File names mix Add Vehicle / Add Car | Legacy Policy lane; rename only in a dedicated cleanup |
| `ui/.../DocumentIntakeInboxPage.tsx` | Maps `add_car` / `add_vehicle` → label `Add Car` | Label is correct; keep synonym map |
| Claim keys `vehicle_information`, `own_vehicle_info` | Sound generic (“Vehicle”) | Claim-owned keys; UI = `车辆信息` |
| Workbench / Mini Program “您的车辆信息” | Correct claim customer language | Do not change to 保单加车 |
| Comments saying “Add Vehicle” inside WeCom Add Car flow | Synonym drift | Prefer “Add Car” in new comments |

### 6.3 Explicitly OK as-is

| Symbol / doc | Why OK |
|--------------|--------|
| Product name **Claim Vehicle Identity V1** | Engineering freeze title for the claim backend object + contract |
| Customer copy **车辆信息** | Claim Request More / form title |
| Lane constant **`SERVICE_LANE_ADD_CAR`** | Policy Add Car only |

---

## 7. Glossary section (for product docs)

Copy or link this block into onboarding / product indexes:

```markdown
### Glossary — Vehicle language (frozen)

- **Add Car (保单加车)** — Policy Management. Customer adds/replaces a vehicle
  on an existing policy. Backend lane: `SERVICE_LANE_ADD_CAR`. Legacy English:
  “Add Vehicle.”
- **Claim Vehicle (事故车辆)** — Claim. Which vehicle was involved in this
  accident. Entered via Request More / in-claim supplement — not Add Car.
- **Vehicle Information (车辆信息)** — Customer-facing claim form / Request More
  label for claim vehicle details.
- **Vehicle Identity / Claim Vehicle Identity (车辆对象·内部)** — Backend
  canonical claim vehicle object (merge, facts, idempotency). Never show in UI.
- **Never mix:** Claim ≠ Add Car. UI ≠ Vehicle Identity.
- **SSOT:** `docs/product/CLAIM_VEHICLE_VS_ADD_CAR_TERMINOLOGY.md`
- **Claim object contract:** `docs/product/CLAIM_VEHICLE_IDENTITY_V1.md`
```

---

## 8. Relationship to Claim Vehicle Identity V1

| Document | Answers |
|----------|---------|
| **This file** | What words mean; Policy vs Claim vs Backend |
| **`CLAIM_VEHICLE_IDENTITY_V1.md`** | How the claim vehicle object is stored, completed, and merged |

This naming freeze does **not** change V1 workflow, storage, or task sequence T2–T7.

---

## 9. Freeze verdict

**NAMING FROZEN**
