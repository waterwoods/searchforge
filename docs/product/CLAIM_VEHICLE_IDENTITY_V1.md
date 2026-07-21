# Claim Vehicle Identity V1 — Decision Freeze

**Status:** Frozen — authoritative V1 product/contract SSOT  
**Product name:** Claim Vehicle Identity V1  
**Date:** 2026-07-21  
**Prerequisite:** P36 closed; Add Vehicle repository discovery complete  
**Authority:** Founder-confirmed V1 scope for claim-scoped vehicle identity  
**Decision Log:** D-010  
**Terminology SSOT:** `docs/product/CLAIM_VEHICLE_VS_ADD_CAR_TERMINOLOGY.md` (D-011) — Claim Vehicle ≠ Add Car  
**Does not authorize:** product implementation (T2+), Production mutation, WeCom Add Car reopen

This document freezes V1 so implementation cannot reopen a second vehicle lane,
require VIN at Start Claim, invent multi-vehicle behavior, or dual-write storage.

**Naming:** This freeze is **Claim Vehicle Identity** (claim backend object). It is
**not** Policy **Add Car** (`保单加车`). Customer-facing claim copy uses
**车辆信息** / **事故车辆**, never “Vehicle Identity” or “Add Car.”

---

## 1. One-sentence objective

Broker Request More can collect one claim-scoped primary vehicle identity
(VIN **or** year/make/model when VIN is unavailable), merge it into the
existing claim fact path, and show the same structured vehicle to customer
and broker — without a new workflow, garage, or microservice.

**Out of scope for this freeze document:** any T2+ code, UI, deploy, or QA
mutation.

---

## 2. Frozen product definition

| Rule | Freeze |
|------|--------|
| **Ownership** | Authoritative owner = current `case_id` |
| **Cardinality** | Exactly one primary vehicle slot per claim |
| **Bindings** | Intake session / `person_link` are resume and authorization bindings only — not the vehicle owner |
| **Reuse** | No cross-claim vehicle reuse in V1 |
| **VIN** | Optional |
| **Primary entry** | Broker Request More → Task Home → existing request-item / task shell → structured vehicle form |
| **Secondary entry** | Current active claim supplement/edit path only |
| **Forbidden entry** | Service Home must not start a separate case or vehicle lane |

### 2.1 What this prevents

| Anti-pattern | Status |
|--------------|--------|
| Reopen WeCom `SERVICE_LANE_ADD_CAR` as the customer claim vehicle path | Forbidden in V1 |
| Second standalone “Add Vehicle” workflow beside claim Request More | Forbidden |
| Mandatory VIN during initial Start Claim | Forbidden |
| Multi-vehicle claims / vehicle garage / profile | Forbidden |
| Dual-write to `intake_entities` as a second source of truth | Forbidden |

---

## 3. Frozen completeness rule

Partial drafts may contain any subset of vehicle fields.

**Draft / partial-save validation ≠ final-submit validation.**

A customer vehicle request is **complete** when either:

**A.** A valid normalized 17-character VIN is supplied  

**OR**

**B.** VIN is explicitly unavailable (`vin_unavailable = true`) **and** all of
the following are supplied:

- `year`
- `make`
- `model`

| Field | Completeness role |
|-------|-------------------|
| `vin` | Sufficient alone when valid (path A) |
| `vin_unavailable` | Required for path B |
| `year` / `make` / `model` | Required together for path B |
| `license_plate` | Optional V1 |
| `plate_state` | Optional V1 |

---

## 4. Frozen logical vehicle object

Canonical object keys (exact):

| Key | Type / nullability | Normalization |
|-----|--------------------|---------------|
| `vehicle_id` | string, required | Derived stable single-slot id: `veh:{case_id}` |
| `case_id` | string, required | Authoritative claim id; never null once slotted |
| `year` | string \| null | Trim; store 4-digit year string when known; empty → null |
| `make` | string \| null | Trim; case-fold for match only; persist display form |
| `model` | string \| null | Trim; case-fold for match only; persist display form |
| `vin` | string \| null | Uppercase A–Z/0–9; persist only when length == 17 and valid checksum/format per existing VIN normalizer; **partial VIN never persisted as canonical VIN** |
| `vin_unavailable` | boolean | Default `false`; `true` only when customer explicitly marks VIN unavailable |
| `license_plate` | string \| null | Trim; uppercase for match; empty → null |
| `plate_state` | string \| null | Trim; uppercase 2-letter US state when applicable; empty → null |
| `source` | enum string, required | See §4.1 |
| `verification_status` | enum string, required | See §4.2 |
| `summary` | string \| null | Human-readable projection (e.g. `2020 Toyota Camry` or masked VIN summary); derived, not an independent identity |
| `created_at` | ISO-8601 string, required | First slot write |
| `updated_at` | ISO-8601 string, required | Last successful merge |

### 4.1 `source` allowed values

| Value | Meaning |
|-------|---------|
| `customer` | Customer structured form / supplement |
| `broker_request` | Created or shaped by broker Request More context |
| `ai_extract` | AI extraction candidate (never silently overrides confirmed) |
| `document` | Document / OCR extraction candidate (never silently overrides confirmed) |

### 4.2 `verification_status` allowed values

Aligned with existing fact-status vocabulary:

| Value | Meaning |
|-------|---------|
| `supplied_unconfirmed` | Customer/AI/document supplied; broker not confirmed |
| `confirmed` | Broker-confirmed; protected from silent overwrite |
| `needs_correction` | Conflict or broker-marked correction required |

### 4.3 Explicitly excluded fields (not in V1 object)

Do **not** add quote-oriented or rating fields:

- annual mileage
- primary use
- garaging address
- ownership / lease
- effective date
- driver linkage packs
- ZIP / garaging ZIP as identity requirements

---

## 5. Frozen storage authority

### 5.1 Single source of truth

For V1, authoritative storage is the **existing claim path**:

- `known_facts`
- `fact_records`
- Slice1 command outcomes / events
- existing claim projections (Constitution / Workbench / customer task)

**Do not dual-write to `intake_entities` in V1.**

`intake_entities` (see legacy `docs/VEHICLE_ENTITY_MEMORY_MVP.md`) may be
evaluated later as a projection or migration target. It must **not** become a
second V1 source of truth for claim vehicle identity.

### 5.2 Canonical fact key mapping

| Logical object field | Canonical `known_facts` / `fact_records` key | Notes |
|----------------------|-----------------------------------------------|-------|
| `year` | `vehicle_year` | Existing repo key |
| `make` | `vehicle_make` | Existing repo key |
| `model` | `vehicle_model` | Existing repo key |
| `vin` | `vehicle_vin` | Canonical write key |
| `vin_unavailable` | `vehicle_vin_unavailable` | Boolean/string per existing fact serializer; read as bool |
| `license_plate` | `vehicle_license_plate` | Optional |
| `plate_state` | `vehicle_plate_state` | Optional |
| `verification_status` | `vehicle_verification_status` | Mirrors object enum |
| `summary` | `vehicle_information` | Structured summary projection key |
| `summary` (legacy display) | `own_vehicle_info` | **Alias — keep backward-compatible reads/writes for existing Workbench / Mini Program / golden fixtures** |
| `summary` (triage display) | `primary_vehicle_summary` | **Alias — read-compatible only unless an existing writer already sets it** |

### 5.3 VIN aliases (backward-compatible reads)

| Alias | Role |
|-------|------|
| `vin` | Checklist / Slice1 `field_key` and common write alias — normalize into `vehicle_vin` |
| `vehicle_vin` | Canonical persisted fact |
| `own_vehicle_vin` | Legacy read alias |

Writers in T2+ must converge new persistence onto `vehicle_vin` while continuing
to satisfy readers that still look up `vin` / `own_vehicle_vin`.

### 5.4 Summary aliases (backward-compatible)

| Key | Role |
|-----|------|
| `vehicle_information` | Canonical structured summary / request field projection |
| `own_vehicle_info` | Legacy free-text / Workbench / basics summary — **same logical vehicle**, not a second car |
| `primary_vehicle_summary` | Triage/case card summary alias |

Updating year/make/model/VIN must refresh these summary projections so broker
and customer never see divergent “two vehicles.”

---

## 6. Frozen request types

### 6.1 Relationship

| Request | Role | Same vehicle object? |
|---------|------|----------------------|
| `vin` | Request / submit VIN | Yes |
| `vehicle_information` | Request / submit structured vehicle pack (year/make/model, optional plate, VIN-unavailable path) | Yes |

Both update the **same** logical Claim Vehicle Identity object (`veh:{case_id}`).

### 6.2 MVP-sendable freeze

- `vin` remains MVP-sendable (current production path).
- `vehicle_information` **becomes MVP-sendable** in V1 implementation (T3).
- Today’s code treats checklist `vehicle_information` as `item_type: free_text`
  and **rejects send** (`unsupported_draft_item_type_for_send`). That rejection
  is a pre-V1 gap, not product law.
- Implementation should align sendable `item_type` with the existing semantic
  key `vehicle_information` (preferred) rather than inventing a third product
  request type such as `add_vehicle` / `structured_vehicle`.
- **Do not introduce a third request type** unless a hard repository constraint
  proves it unavoidable; any such exception requires an amendment to this freeze.

### 6.3 Customer-facing Chinese copy (frozen)

Keep concise and non-technical:

| Surface | Copy |
|---------|------|
| `vehicle_information` title | 车辆信息 |
| Request explanation | 请补充本次事故车辆的基本信息，方便经纪人继续处理。 |
| VIN unavailable option | 暂时提供不了 VIN |
| Year | 年份 |
| Make | 品牌 |
| Model | 车型 |
| Optional plate | 车牌号（选填） |
| Optional plate state | 州/省份（选填） |
| Save draft | 保存草稿 |
| Submit success | 已提交，经纪人会继续处理。 |
| Correction required | 车辆信息需要更正，请按提示修改后重新提交。 |

VIN-only request may keep existing short copy (e.g. 请发送或确认车辆 VIN) as long
as it merges into the same object.

---

## 7. Frozen merge and idempotency rules

### 7.1 Claim-scoped matching hierarchy

Within one `case_id`, match in order:

1. Same `case_id` + normalized valid VIN  
2. Same `case_id` + normalized `plate_state` + `license_plate`  
3. Existing `vehicle_id` / single vehicle slot (`veh:{case_id}`)  
4. Otherwise create the single slot  

No second slot is created while a primary slot exists.

### 7.2 Merge / conflict law

| Rule | Freeze |
|------|--------|
| Duplicate submission | Updates the existing object |
| One `command_id` | Produces one outcome / event |
| Safe retry | No duplicate timeline event |
| Customer updates | May update `supplied_unconfirmed` values |
| Broker-confirmed values | Must not be silently overwritten |
| Conflict vs confirmed | Set `needs_correction` / `vehicle_verification_status = needs_correction` |
| AI / document extraction | Never silently overrides confirmed facts |
| Partial VIN | Never persisted as canonical `vehicle_vin` |

---

## 8. Frozen workflow

### 8.1 No new state machine

Reuse only:

- active claim
- Task Home
- Slice1 Request More
- request-item shell
- existing resume token / session binding
- existing fact statuses
- existing timeline / event model
- existing broker review

### 8.2 Happy paths

**Path A — VIN**

1. Broker requests VIN (`vin`)  
2. Customer submits valid normalized VIN  
3. Request item satisfied  
4. Vehicle facts merged into the single slot (`vehicle_vin` + summary projection)

**Path B — Structured vehicle without VIN**

1. Broker requests vehicle information (`vehicle_information`)  
2. Customer partial-saves  
3. Customer leaves  
4. Customer resumes (same active claim / token binding)  
5. Customer marks VIN unavailable  
6. Customer submits year / make / model  
7. Request item satisfied  
8. Facts merged into the same single slot

**Path C — Correction**

1. Existing vehicle is corrected (customer supplement/edit or correction request)  
2. Merge into the same `veh:{case_id}` slot  
3. Fact / verification status updated  
4. No duplicate vehicle created  

---

## 9. Explicit non-goals (out of V1)

- WeCom `SERVICE_LANE_ADD_CAR` as customer claim path  
- Standalone Add Vehicle workflow  
- New Service Home lane that starts a separate vehicle case  
- Multi-vehicle claims  
- Customer vehicle garage / profile  
- Policy asset graph  
- Add Driver  
- Vehicle quote / rating questions (mileage, use, garaging, ownership, effective date)  
- New vehicle microservice  
- `intake_entities` dual-write / second source of truth  
- Mandatory VIN at initial claim submission  
- New claim workflow state machine for vehicle collection  

---

## 10. Implementation plan (one task → one commit)

Stop after each task. Do not auto-start the next.

| Task | Scope | Entry criteria | Exit criteria |
|------|-------|----------------|---------------|
| **T1** (this doc) | Documentation + contract freeze | P36 closed; Founder confirmed V1 decisions | This SSOT merged; verdict `VEHICLE V1 FROZEN` |
| **T2** | Backend vehicle object normalization, completeness, merge, idempotency, claim fact persistence, tests | T1 frozen | Unit/integration tests prove single-slot merge, completeness A/B, no partial VIN persist, no `intake_entities` write |
| **T3** | Slice1 `vehicle_information` send/submit integration; request satisfaction; event tests | T2 green | Broker can send `vehicle_information`; customer submit satisfies item; one `command_id` → one event; merges with VIN path |
| **T4** | Mini Program structured request-item UX; partial save/resume; Build Gates | T3 green | `cd miniapp && npm run build:gate` PASS; Path B UX works; Founder Form / Nav gates respected |
| **T5** | Workbench structured vehicle projection / readback | T4 green | Broker detail shows same structured vehicle as customer submit (read-after-write) |
| **T6** | Founder QA fixture and inspection support | T5 green | Deterministic QA fixture can seed/inspect one vehicle slot without Production touch |
| **T7** | Cloud QA Founder PAT + Production non-mutation proof | T6 green | Full §11 acceptance on Cloud QA; Production untouched |

---

## 11. Acceptance contract (final V1)

```text
Active QA claim
  → Broker requests vehicle information
  → Customer partially saves
  → Customer exits
  → Customer resumes
  → Customer completes without VIN using year/make/model
  → Founder / Workbench sees the same structured vehicle
  → Retrying submission creates no duplicate
  → Database / claim projection contains one vehicle slot
  → Production remains untouched
```

Capability is not done until Founder/manual QA evidence records the above.

---

## 12. Contradictions vs existing SSOT (discovered)

These are **pre-V1 gaps or legacy lanes**, not permission to violate this freeze.
Implementation (T2+) must close gaps toward this document.

| Area | Current repo truth | V1 freeze |
|------|--------------------|-----------|
| `vehicle_information` send | Checklist field exists; send rejected (`free_text` not in `MVP_SENDABLE_ITEM_TYPES`); tests assert rejection | Becomes MVP-sendable; same logical vehicle as `vin` |
| WeCom Add Car | `SERVICE_LANE_ADD_CAR` + H5 Add Vehicle docs/flows still exist | Not the customer claim vehicle path; do not reopen as V1 entry |
| `intake_entities` | `docs/VEHICLE_ENTITY_MEMORY_MVP.md` describes session-scoped entity memory as authoritative snapshot for add-car style identity | Claim V1 authority = claim facts/events only; no dual-write |
| Free-text `own_vehicle_info` | Still used in claim basics / Workbench / golden fixtures as summary text | Remains **summary alias** for the single slot — not a second workflow or second vehicle |
| Default intake plan | `TASK_ID_VEHICLE_INFORMATION` / `TASK_ID_VEHICLE_VIN` constants exist but are **not** in `DEFAULT_AUTO_CLAIM_INTAKE_PLAN` | Correct: vehicle identity stays Request More / supplement, not Start Claim Must Have |
| Business Contract | VIN and year/make/model already classified Request More (`p20_business_contract.md`) | **Aligned** — this freeze is the structured-object and merge SSOT under that classification |

---

## 13. Related documents

| Doc | Relationship |
|-----|--------------|
| `docs/product/p20_business_contract.md` | Field priority: VIN / vehicle pack = Request More |
| `docs/product/p20_product_north_star.md` | Journey / release gates |
| `docs/product/decision_log.md` | D-010 pointer |
| `docs/VEHICLE_ENTITY_MEMORY_MVP.md` | Legacy entity memory — not V1 claim SoT |
| Add Car / WeCom lane docs | Historical lane — non-goal for claim V1 path |

---

## 14. Freeze verdict

**VEHICLE V1 FROZEN**
