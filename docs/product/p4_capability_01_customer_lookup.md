# P4 Capability 01 — Customer Lookup Capability

**Status:** Mock harness implemented — awaiting Founder QA  
**Date:** 2026-07-24  
**Naming:** Capability (not Slice)  
**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Identity prerequisite (reuse, do not redesign):** P29B / D-016 — `person_link_key`

---

## Founder Decisions (LOCKED)

1. **Lookup is READ ONLY** — read / match / prefill only. Never update, merge, create Customer; never modify Policy, Vehicle, or CRM. Lookup is **not** Source of Truth.
2. **One Capability, One Responsibility** — answers only: **“Who is this customer?”**
3. **Identity unchanged** — `person_link_key` only; never expose OpenID.
4. **No Customer table / CRM / Epic / EZLynx / external APIs.**
5. **Mock data only.** Feature-flagged.

---

## One objective / Out of scope

**ONE OBJECTIVE**

Provide a reusable, feature-flagged **Mock Lookup Harness** that maps `person_link_key` → complete `LookupResult` so Mini Program and Broker Workbench can later prefill without inventing CRM.

**OUT OF SCOPE**

- Production AMS / CRM integration  
- Customer table redesign  
- Identity redesign  
- Prefill write-path into live case create (future Capability / loop)  
- UI redesign as the product goal  

---

# 1. Architecture Diagram

```text
Mini Program
  wx.login → OpenID (ephemeral) → person_link_key     ← P29B (unchanged)
                         │
                         ▼
              ┌──────────────────────┐
              │ CustomerLookupFacade │  READ ONLY
              │  lookup(person_link) │  flag: P4_CUSTOMER_LOOKUP_MOCK
              └──────────┬───────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
   ┌───────────────┐           ┌──────────────────┐
   │ MockDirectory │           │ Future AmsAdapter│
   │ (Cap 01 now)  │           │ (swap later)     │
   └───────┬───────┘           └────────┬─────────┘
           │                            │
           └────────────┬───────────────┘
                        ▼
                 LookupResult
           (match_status, confidence,
            customer, policy, vehicles,
            active_case, prefill, next_action)
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
  Broker Header    Workbench         Start Claim
  (projection)     (display)         (future prefill consumer)
```

**Swappability:** Mini Program and Broker Workbench depend only on `LookupResult`. Replacing MockDirectory with AMS does not change identity or UI contracts.

---

# 2. Mock Data Design

| Scenario | Mock `person_link_key` | `match_status` | `lookup_confidence` | Notes |
|----------|------------------------|----------------|---------------------|-------|
| S1 Existing + 1 vehicle + active claim | `wx_mock_cap01_s1_existing_active` | `MATCH_FOUND` | `HIGH` | Camry; `continue_active_case` |
| S2 Existing + multi vehicle | `wx_mock_cap01_s2_multi_vehicle` | `MATCH_FOUND` | `MEDIUM` | Camry + CR-V; must `confirm_vehicle` |
| S3 Existing + no active claim | `wx_mock_cap01_s3_no_active` | `MATCH_FOUND` | `HIGH` | Prefill ready; no active case |
| S4 Existing + expired policy | `wx_mock_cap01_s4_stale_policy` | `STALE_POLICY` | `MEDIUM` | `confirm_stale_policy` |
| S5 Identity, no customer mapping | `wx_mock_cap01_s5_identity_no_mapping` | `NOT_FOUND` | `LOW` | Blank claim path |
| S6 Lookup unavailable | `wx_mock_cap01_s6_lookup_unavailable` | `LOOKUP_UNAVAILABLE` | `LOW` | Graceful degrade |
| Extra: Ambiguous | `wx_mock_cap01_ambiguous` | `AMBIGUOUS_MATCH` | `LOW` | No auto-merge |

Module: `services/fiqa_api/inbox_triage/customer_lookup/mock_directory.py`

---

# 3. Lookup Facade Design

| Item | Value |
|------|--------|
| Package | `services/fiqa_api/inbox_triage/customer_lookup/` |
| Entry | `lookup_customer(person_link_key)` / `lookup_customer_for_session(session_id)` |
| Flag | `P4_CUSTOMER_LOOKUP_MOCK=1` (default **off**) |
| Force degrade | `P4_CUSTOMER_LOOKUP_FORCE_UNAVAILABLE=1` |
| HTTP | `POST /api/h5/customer/lookup` `{ session_id? \| person_link_key? }` |
| Writes | **None** — no create/merge/update Customer/Policy/Vehicle/CRM |

When flag is off: complete `LookupResult` with `LOOKUP_UNAVAILABLE` (HTTP 200) — never UI-breaking errors.

---

# 4. LookupResult Contract

```text
LookupResult
  match_status: MATCH_FOUND | NOT_FOUND | UNMATCHED_IDENTITY
                | AMBIGUOUS_MATCH | STALE_POLICY | LOOKUP_UNAVAILABLE
  lookup_confidence: HIGH | MEDIUM | LOW
  customer: null | { display_name, phone_last4, phone_e164_mock?, broker_customer_ref }
  policy: null | { policy_ref, carrier_display, status, freshness, effective_end? }
  vehicles: [{ vehicle_ref, year, make, model, vin_last4?, license_plate?, is_primary? }]
  active_case: null | { case_id, resume_available }
  prefill: { customer_name?, customer_phone?, primary_vehicle_summary?, policy_number? }
  next_action: continue_active_case | confirm_vehicle | start_blank_claim
               | confirm_stale_policy | contact_broker | relogin
  reason_codes: string[]
  lookup_source: mock | unavailable
```

Every failure mode returns a **complete** LookupResult.

---

# 5. Simulation Report

**Command:** `P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap01_customer_lookup.py`  
**Tests:** `PYTHONPATH=. python3 -m pytest tests/test_p4_capability_01_customer_lookup_mock.py -q`  
**Date run:** 2026-07-24 — **PASS**

Chain verified for S1–S6:

```text
Mini Program → Lookup → Broker Header → Workbench → Request More
  → Customer Continue → Review → Close
```

| Check | Result |
|-------|--------|
| No duplicate customer | PASS (lookup never creates/merges) |
| No duplicate claim | PASS (active case → continue; no second create) |
| No broken workflow | PASS (all steps `ok`) |
| Correct prefill | PASS (S1/S3 Camry + 陈明; S2 no auto vehicle) |
| Graceful degradation | PASS (S5/S6 → blank claim; flag off → UNAVAILABLE) |
| No OpenID leak | PASS |
| No CRM mutation | PASS |

---

# 6. Implementation Plan (done vs next)

| Task | Status |
|------|--------|
| Contract + enums | **Done** |
| Mock directory (6 scenarios) | **Done** |
| Read-only facade + feature flag | **Done** |
| HTTP lookup endpoint | **Done** |
| Simulation script + pytest | **Done** |
| Wire prefill into live `start-claim` writes | **Future** (separate loop; still read-from-lookup only at edge) |
| AMS / Epic / EZLynx adapter | **Future Capability** — same `LookupResult` |

---

# 7. Rollback Plan

1. Set `P4_CUSTOMER_LOOKUP_MOCK=0` (or unset) → facade returns `LOOKUP_UNAVAILABLE`; existing session/context/start-claim unchanged.
2. No DB migration in Cap 01 → no schema rollback.
3. Remove/disable `POST /api/h5/customer/lookup` callers if any (none in Mini Program yet).
4. Do **not** roll back P29B identity as part of Cap 01 failure.

---

# 8. Founder QA Package (≤10 minutes)

## Executive Summary

Mock-only **Customer Lookup** harness is live behind `P4_CUSTOMER_LOOKUP_MOCK`. It answers “Who is this customer?” from `person_link_key`, returns a stable `LookupResult` (including `lookup_confidence` HIGH/MEDIUM/LOW for brokers), and never writes CRM. Future AMS plugs in behind the same facade.

## Architecture

See §1. Identity = P29B. Lookup = read-only facade. SoR remains claim case + Active Case index — not lookup.

## Risks

| Risk | Mitigation in harness |
|------|------------------------|
| Wrong-person merge | No merge APIs; `AMBIGUOUS_MATCH` → contact_broker |
| Duplicate claim | Lookup does not create cases; S1 → continue |
| Stale policy as truth | `STALE_POLICY` + confirm next_action |
| Privacy | No OpenID / person_link in LookupResult payload |
| Flag accidents in prod | Default **off** |

## Mock Screens (conceptual)

| Moment | Customer | Broker |
|--------|----------|--------|
| S1 | Continue current task | 陈明 / Camry / HIGH |
| S2 | Confirm which vehicle | 李娜 / — / MEDIUM |
| S4 | Confirm stale policy | 王强 / Camry / MEDIUM + stale |
| S5/S6 | Normal Start Claim | No prefill; degrade |

## Data Flow

`person_link_key` → Facade → MockDirectory → `LookupResult` → (optional) Broker Header projection / future prefill consumer. **No writes.**

## Recommendation

**GREEN for mock harness.**  
**YELLOW for production prefill wiring** (next loop).  
**RED for CRM/Epic now.**

## Go / No-Go

| | |
|--|--|
| **GO** | Approve mock harness + contract; keep flag off in prod until prefill loop |
| **NO-GO** | Only if Founder requires Customer table / live AMS before any harness |

**Founder checkbox**

- [ ] Approve READ ONLY rule  
- [ ] Approve `LookupResult` + `lookup_confidence`  
- [ ] Approve six mock scenarios + simulation PASS  
- [ ] Approve rollback = flag off  
- [ ] Defer AMS adapter / start-claim prefill write to a later Capability loop  

---

## Code map

| Path | Role |
|------|------|
| `services/fiqa_api/inbox_triage/customer_lookup/contract.py` | Contract |
| `services/fiqa_api/inbox_triage/customer_lookup/mock_directory.py` | Mock data |
| `services/fiqa_api/inbox_triage/customer_lookup/facade.py` | Facade |
| `services/fiqa_api/routes/h5_task_intake.py` | `POST /api/h5/customer/lookup` |
| `tests/test_p4_capability_01_customer_lookup_mock.py` | Tests |
| `scripts/simulate_p4_cap01_customer_lookup.py` | Simulation |

## Scorecard (harness loop)

| Dimension | Result | Evidence |
|-----------|--------|----------|
| Reliability | PASS | Complete LookupResult every mode; flag-off degrade |
| Simplicity | PASS | One key in → one result |
| Smoothness | PASS | No thrown UI-breaking errors |
| Business Value | PASS | Prefill + confidence ready for broker |
| Scope Control | PASS | Mock only; no CRM/identity/schema |

---

## Future ideas (record only)

- Prefill consumer on `start-claim` (still lookup-read → case facts stamp)  
- AMS adapter behind facade  
- Phone as secondary match signal  
- Household disambiguation UI  
