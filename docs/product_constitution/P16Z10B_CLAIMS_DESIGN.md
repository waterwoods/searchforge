# P16-Z10B Phase 5 — Claims Memory Design

**Date:** 2026-06-02  
**Pattern:** Z10A `_merge_persisted_collected` + add-car literal tokens (`zip_94588`)

---

## Core question

Can claim facts survive append the way payment/add-car facts do?

**Yes** — same contract:

1. Expand `_is_claim_intake_request()` for **claim-status** language (total loss, adjuster, filed claim, rear-ended, glass, etc.)  
2. `_thread_is_claim_lane()` — persisted claim tokens OR FNOL markers  
3. `_claim_structured_fields()` — boolean spine  
4. `_augment_claim_collected_from_merged()` — literal tokens from **full thread**  
5. `_merge_persisted_collected()` — union with `reply_truth_context.persisted_collected_fields`  
6. Summary — claim `collected_hint` with plate / $ / claim #  

---

## Generic claim merge (no CollectedFieldsService)

```
triage_for_append / triage_conversation
  └─ _thread_is_claim_lane(merged, persisted)?
  └─ _claim_structured_fields(merged)
  └─ _augment_claim_collected_from_merged(...)
  └─ _merge_persisted_collected(fresh, still, persisted, persisted_still=...)
  └─ _build_conversation_summary → claim Collected: plate X, $Y
```

**Lane guard:** missing_document branch checks claim lane first — prevents CL03 DL chase mis-route.

---

## New collected token families

| Token pattern | Source |
|---------------|--------|
| `plate_{PLATE}` | `_extract_plate_hint` |
| `claim_number_{ID}` | `_extract_claim_number_hint` |
| `claim_amount_{N}` | `_extract_claim_amount_hint` (VIN-window guard) |
| `policy_{N}` | `_extract_policy_number_hint` |
| `police_report_{ID}` | regex LA-2026-4412 |
| `total_loss` / `total_loss_disputed` | 全损 correction |
| `adjuster_waiting` / `carrier_delay` | carrier wait language |
| `injury_neck` / `injury_mri` / `rear_end` | CL06 |
| `accident_date_{M_D}` | CL05 |
| `glass_or_vehicle_damage` | CL08 |
| `vin_tail_{N}` | VIN ends N |
| `parking_scrape_damage` | CL09 |

---

## Preserved fields (mission list)

| Field | Token |
|-------|-------|
| plate | `plate_*` |
| amount | `claim_amount_*` |
| total_loss | `total_loss` / `total_loss_disputed` |
| injury | `injuries`, `injury_*` |
| police_report | `police_report`, `police_report_*` |
| carrier | `carrier_mentioned`, `carrier_delay` |
| adjuster | `adjuster_mentioned`, `adjuster_waiting` |

Vehicle: `vehicle_{year_make}` token in augment.

---

## Reuse map

| Reuse | From |
|-------|------|
| Persisted merge | Z10A `_merge_persisted_collected` |
| Policy hint | existing `_extract_policy_number_hint` |
| Correction prepend | Z6 `_prepend_prior_customer_turn_on_correction` |
| Claim templates | Turn-1 unchanged |
| Waiting suggest | Z10B `_suggest_waiting_on` |

---

## Out of scope

- New claim DB table  
- Claims microservice  
- OCR plate reader  
- Auto `waiting_on` PATCH  

---

## Target

Claims battery **36% → 70%+** → design acceptance **71%**.
