# P4 Capability 02 — Claim Prefill Capability

**Status:** Mock classification harness implemented — awaiting Founder QA  
**Date:** 2026-07-24  
**Naming:** Capability (not Slice)  
**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Business Contract:** `docs/product/p20_business_contract.md`  
**Depends on:** P4 Capability 01 — Customer Lookup (`LookupResult`)  
**Identity prerequisite (reuse):** P29B / D-016 — `person_link_key` (unchanged)

---

## Founder Decisions (LOCKED)

1. **Never ask customers for information we already know.**
2. **Ask only for new accident facts.**
3. **Prefill is classification + suggestion only** — not CRM Source of Truth; not a write path.
4. **One Capability, One Responsibility** — answers only: **“What do we already know vs still need?”**
5. **No CRM / no identity redesign / no DB redesign.** Mock LookupResult only.

---

## One objective / Out of scope

**ONE OBJECTIVE**

Given Cap 01 `LookupResult`, produce a complete `PrefillResult` that classifies every Start Claim / claim-journey field as `AUTO_PREFILL` | `CUSTOMER_REQUIRED` | `BROKER_REQUIRED` | `UNKNOWN`, so the customer is never re-asked known facts.

**OUT OF SCOPE**

- Production AMS / CRM integration  
- Identity redesign / Customer table  
- Live Mini Program form wiring / `start-claim` write-path stamp (future loop)  
- Expanding Start Claim Must Haves beyond Business Contract accident facts  
- Photos/docs as required Start Claim fields  

---

# 1. Field Classification Table

| Field | Cap 01 source | Matched + clear (S1/S3) | Multi-vehicle (S2) | Stale policy (S4) | No match / unavailable (S5/S6) | Founder shorthand |
|-------|----------------|-------------------------|--------------------|-------------------|--------------------------------|-------------------|
| Customer Name | `customer.display_name` / prefill | **AUTO_PREFILL** | AUTO_PREFILL | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| Policy | `policy.policy_ref` | **AUTO_PREFILL** | AUTO_PREFILL | **CUSTOMER_REQUIRED** (confirm) | BROKER_REQUIRED | AUTO / ASK |
| Vehicle | single vehicle summary | **AUTO_PREFILL** | **CUSTOMER_REQUIRED** (choose) | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| VIN | `vin_last4` → `****4352` | **AUTO_PREFILL** | CUSTOMER_REQUIRED | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| License Plate | `license_plate` | **AUTO_PREFILL** | CUSTOMER_REQUIRED | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| Insurance Company | `carrier_display` | **AUTO_PREFILL** | AUTO_PREFILL | **CUSTOMER_REQUIRED** (confirm) | BROKER_REQUIRED | AUTO / ASK |
| Policy Number | `policy_ref` / prefill | **AUTO_PREFILL** | AUTO_PREFILL | **CUSTOMER_REQUIRED** (confirm) | BROKER_REQUIRED | AUTO / ASK |
| Driver | default = named insured | **AUTO_PREFILL** | AUTO_PREFILL | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| Phone | `phone_e164_mock` | **AUTO_PREFILL** | AUTO_PREFILL | AUTO_PREFILL | BROKER_REQUIRED | AUTO / ASK |
| Email | *(none in mock)* | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Accident Time | — | **CUSTOMER_REQUIRED** | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | ASK |
| Accident Location | — | **CUSTOMER_REQUIRED** | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | ASK |
| Accident Story | — | **CUSTOMER_REQUIRED** | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | ASK |
| Damage | — | **CUSTOMER_REQUIRED** | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | ASK |
| Injury | — | **CUSTOMER_REQUIRED** | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | CUSTOMER_REQUIRED | ASK |
| Police Report | — | **BROKER_REQUIRED** | BROKER_REQUIRED | BROKER_REQUIRED | BROKER_REQUIRED | ASK |
| Photos | — | **BROKER_REQUIRED** | BROKER_REQUIRED | BROKER_REQUIRED | BROKER_REQUIRED | ASK |
| Documents | — | **BROKER_REQUIRED** | BROKER_REQUIRED | BROKER_REQUIRED | BROKER_REQUIRED | ASK |

**Classification meanings**

| Class | Meaning |
|-------|---------|
| `AUTO_PREFILL` | Value known from LookupResult; do not ask customer to re-enter |
| `CUSTOMER_REQUIRED` | Customer must provide or confirm (new accident fact, vehicle choice, stale policy confirm) |
| `BROKER_REQUIRED` | Broker / Request More owns the gap — not a Start Claim Must Have expansion |
| `UNKNOWN` | No mock source; do not invent; do not force-ask |

**Founder shorthand:** AUTO = `AUTO_PREFILL`; ASK = `CUSTOMER_REQUIRED` or `BROKER_REQUIRED`; UNKNOWN = `UNKNOWN`.

---

# 2. Customer Input Reduction (before / after)

Baseline “before” = treat all 18 founder fields as potentially asked without lookup.

| Scenario | Before (askable) | After `CUSTOMER_REQUIRED` | AUTO_PREFILL | Removed from customer ask* |
|----------|------------------|---------------------------|--------------|----------------------------|
| S1 Existing + active | 18 | **5** (accident facts only) | 9 | 13 |
| S2 Multi-vehicle | 18 | **8** (5 accident + vehicle/vin/plate confirm) | 6 | 10 |
| S3 No active claim | 18 | **5** | 9 | 13 |
| S4 Stale policy | 18 | **8** (5 accident + policy/carrier/policy# confirm) | 6 | 10 |
| S5 No mapping | 18 | **5** (accident only; identity → broker) | 0 | 13 |
| S6 Unavailable | 18 | **5** | 0 | 13 |

\* “Removed from customer ask” = fields no longer `CUSTOMER_REQUIRED` (AUTO, BROKER, or UNKNOWN).  
Aligned with live Start Claim Must Haves: story / time / location / injury (+ damage as accident fact in Cap 02 table). VIN/docs stay out of Start Claim enablement (Business Contract).

---

# 3. UI Changes

**This capability does not ship a Mini Program redesign.** Conceptual consumer rules for the next wiring loop:

| Surface | Change when PrefillResult available |
|---------|-------------------------------------|
| Start Claim | Show read-only chips for AUTO fields (name / vehicle / policy); keep editable Must Haves = accident story, time, location, injury |
| S2 | Add one confirm control: “哪辆车出险？” with Cap 01 vehicle candidates — no blank VIN form |
| S4 | Prefill policy/carrier with confirm CTA (“保单可能已过期，请确认”) — not silent trust |
| S5/S6 | No identity chips; blank accident form (today’s path); no error wall |
| Broker Header / Workbench | Display AUTO values + confidence from Cap 01; Request More only for BROKER_REQUIRED gaps |
| Customer UI | Never expose `AUTO_PREFILL` / `LookupResult` / `person_link_key` jargon |

**Not in this capability:** changing `startClaimValidation.ts` Must Have list; writing prefill into case create.

---

# 4. Capability Boundary

```text
Cap 01 Customer Lookup          Cap 02 Claim Prefill
─────────────────────          ─────────────────────
Who is this customer?    →     What do we already know?
person_link → LookupResult →   LookupResult → PrefillResult
READ ONLY match                READ ONLY classify
```

| In Cap 02 | Out of Cap 02 |
|-----------|---------------|
| Field classification | CRM / AMS adapters (Cap 01 future) |
| Suggested values from LookupResult | Case create / merge / update |
| Confirm flags (vehicle / stale) | Identity redesign |
| Simulation S1–S6 reuse | Live form enablement rewrite |
| Founder QA package | Photos as Start Claim required |

**Swappability:** When Cap 01 swaps MockDirectory → AMS, Cap 02 needs no contract change if `LookupResult` shape holds.

---

# 5. Risks

| Risk | Mitigation |
|------|------------|
| Wrong-person prefill | Cap 01 `AMBIGUOUS_MATCH` → zero AUTO; broker path |
| Silent stale policy | S4 policy fields `CUSTOMER_REQUIRED` + `needs_confirm` |
| Multi-vehicle wrong car | S2 vehicle/VIN/plate not AUTO; candidates only |
| Expanding Start Claim illegally | Identity gaps → `BROKER_REQUIRED`, not new Must Haves |
| Treating prefill as SoR | PrefillResult is suggestion; claim case remains SoR |
| Email invent | `UNKNOWN` — no fake email |
| Full VIN exposure | Mock exposes last4 only (`****4352`) |

---

# 6. Future CRM integration impact

| When AMS replaces mock | Cap 02 impact |
|------------------------|---------------|
| Same `LookupResult` keys | **No Cap 02 contract change** |
| Richer fields (email, full VIN) | Engine can promote `UNKNOWN` / `BROKER_REQUIRED` → `AUTO_PREFILL` behind same classes |
| Lower AMS confidence | Prefer withhold AUTO (mirror Cap 01 confidence); never auto-merge |
| Write-back to AMS | **Forbidden in Cap 02** — still read/classify only |
| Live Start Claim stamp | Separate loop: PrefillResult → case facts copy on create (still not CRM write) |

---

# 7. Founder QA Package (≤10 minutes)

## Executive Summary

Mock-only **Claim Prefill** classifies every Start Claim field from Cap 01 `LookupResult`. Matched customers get identity/policy/vehicle AUTO; customers only provide **new accident facts** (and confirms for multi-vehicle / stale policy). No CRM. No identity redesign.

## Architecture

```text
Mini Program / sim
  → Cap 01 lookup_customer(person_link)
  → LookupResult
  → Cap 02 build_prefill_result(LookupResult)
  → PrefillResult (18 fields classified)
  → (future) Start Claim UI chips / Broker Header
```

## Simulation

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap02_claim_prefill.py
PYTHONPATH=. python3 -m pytest tests/test_p4_capability_02_claim_prefill.py -q
```

**Expected:** `RESULT: PASS` and pytest green.

## Mock Screens (conceptual)

| Scenario | Customer sees | Broker sees |
|----------|---------------|-------------|
| S1 | Accident form only; 陈明 / Camry chips | AUTO identity + HIGH |
| S2 | Accident form + “哪辆车？” | 李娜 AUTO; vehicle pending confirm |
| S3 | Same as S1 chips; new claim | Prefill ready |
| S4 | Accident + confirm expired policy | 王强 + stale confirm |
| S5/S6 | Accident form only (no chips) | No prefill; degrade |

## Go / No-Go

| | |
|--|--|
| **GO** | Approve classification table + PrefillResult; keep live form wiring as next loop |
| **NO-GO** | Only if Founder requires CRM email/VIN or Start Claim document collection now |

**Founder checkbox**

- [ ] Approve “never ask what we know / ask only accident facts”  
- [ ] Approve Field Classification Table (§1)  
- [ ] Approve Customer Input Reduction (§2) — S1: 18 → 5 customer asks  
- [ ] Approve UI Changes as conceptual only (§3) — no live wire this capability  
- [ ] Approve Capability Boundary (§4) — Cap 02 classifies only  
- [ ] Approve Risks + CRM impact (§5–6)  
- [ ] Confirm simulation S1–S6 PASS  

## Recommendation

**GREEN for mock PrefillResult harness.**  
**YELLOW for live Start Claim chip wiring** (next loop).  
**RED for CRM write-back / identity redesign now.**

## Scorecard (harness loop)

| Dimension | Result | Evidence |
|-----------|--------|----------|
| Reliability | PASS | Complete PrefillResult for every Cap 01 mode |
| Simplicity | PASS | One function: LookupResult → PrefillResult |
| Smoothness | PASS | Matched path drops identity re-entry |
| Business Value | PASS | S1 customer asks 18 → 5 |
| Scope Control | PASS | Mock only; no CRM/UI/DB redesign |

---

## Code map

| Path | Role |
|------|------|
| `services/fiqa_api/inbox_triage/claim_prefill/contract.py` | PrefillResult + field list |
| `services/fiqa_api/inbox_triage/claim_prefill/engine.py` | Classifier |
| `tests/test_p4_capability_02_claim_prefill.py` | Tests |
| `scripts/simulate_p4_cap02_claim_prefill.py` | S1–S6 simulation |
| `docs/product/p4_capability_02_claim_prefill.md` | This Founder package |

## Future ideas (record only)

- Wire PrefillResult chips into Mini Program Start Claim (read-only display)  
- Stamp AUTO values into case facts on create (still no CRM write)  
- Promote email → AUTO when AMS provides it  
- Damage as Nice-to-Have vs Must Have (Business Contract amendment if needed)  

---

## Production Loop worksheet

- **Loop:** 1  
- **One objective:** LookupResult → complete PrefillResult field classification (mock)  
- **Explicitly out of scope:** CRM, identity, DB, live form wiring  
- **Minimum change:** `claim_prefill` package + sim + tests + Founder doc  
- **Focused tests:** `tests/test_p4_capability_02_claim_prefill.py`  
- **Commit authorized:** NO (unless Founder asks)  
- **QA deploy authorized:** NO  
- **Founder/manual QA evidence:** simulation + this package (pending Founder checkboxes)  
