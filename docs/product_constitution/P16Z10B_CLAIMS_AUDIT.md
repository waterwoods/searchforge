# P16-Z10B Phase 4 — Claims Retention Audit

**Date:** 2026-06-02  
**Cases:** CL01–CL10 (`configs/role_d_claims_battery.json`)  
**Baseline:** Z7 Role D claims report — **36%** keyword retention

---

## What claim facts disappear? (pre-Z10B)

| Fact | CL cases | Mechanism |
|------|----------|-----------|
| Plate # | CL01, CL03, CL07 | No literal in collected/summary |
| Vehicle | CL02, CL08 | `unclear` lane / coverage mis-route |
| Carrier / adjuster wait | CL04, CL05 | Prose only; no `waiting_on` |
| Estimate / $ amount | CL02, CL10 | No `$` token; VIN confused as amount |
| Total loss / 全损 | CL02, CL10 | Not in collected; correction drops FNOL |
| Injury / MRI | CL06 | → `unclear`; no injury tokens |
| Police report # | CL01 | Late turn only |
| Rental extension | CL10 | No structured token |
| Glass → full pivot | CL08 | Coverage lane ate claim |
| Accident date | CL05 | 2/28 not in blob |

---

## TOP 20 retained (post-Z10B)

| # | Fact | Evidence |
|---|------|----------|
| 1 | `accident_reported` | CL01–CL10 lanes |
| 2 | `hit_and_run` | CL01 |
| 3 | `photos` | CL03, CL08 |
| 4 | `plate_*` literal tokens | CL01, CL03, CL07 |
| 5 | `claim_number_*` | CL04 |
| 6 | `policy_number` / `policy_*` | CL04 |
| 7 | `claim_amount_*` | CL02, CL10 |
| 8 | `total_loss` / `total_loss_disputed` | CL02, CL10 |
| 9 | `injuries` + `injury_neck` / `injury_mri` | CL06 |
| 10 | `rear_end` + `accident_location_101` | CL06 |
| 11 | `police_report_*` | CL01 |
| 12 | `adjuster_waiting` / `carrier_delay` | CL04, CL05 |
| 13 | `carrier_mentioned` / `adjuster_mentioned` | CL04, CL05 |
| 14 | `rental_extension` | CL10 |
| 15 | `glass_or_vehicle_damage` | CL08 |
| 16 | `vin_tail_*` | CL08 |
| 17 | `parking_scrape_damage` | CL09 |
| 18 | `accident_date_*` | CL05 |
| 19 | `at_fault_other_driver` | CL05 |
| 20 | Claim summary headline w/ plate/$ | CL01, CL04 |

---

## TOP 20 lost (pre-Z10B; residual post-Z10B)

| # | Loss | Post-Z10B status |
|---|------|------------------|
| 1 | Total loss on correction-only thread | **Fixed** CL02 @ 60% |
| 2 | Dollar amounts | **Fixed** CL02, CL10 |
| 3 | Plate in headline | **Fixed** summary hint |
| 4 | Wrong missing_document lane | **Fixed** claim lane guard |
| 5 | Injury thread → unclear | **Fixed** CL06 @ 100% |
| 6 | Adjuster → waiting_on | **Fixed** suggest carrier |
| 7 | Append without persisted merge | **Fixed** battery + production path |
| 8 | Glass-only context | **Partial** CL08 @ 60% |
| 9 | UM/deductible prose | CL07 @ 50% |
| 10 | Keyword “Prior” typo in battery | **Fixed** CL09 summary |
| 11 | Highway “101” | **Fixed** CL06 |
| 12 | Police # early turns | **Fixed** CL01 |
| 13 | Hail/roof weak markers | CL04 @ 80% |
| 14 | Rental extension prose | **Fixed** token |
| 15 | Carrier escalate intent | summary latest snip |
| 16 | Multi-turn typo turn | prior prepend |
| 17 | Claim + payment pivot | CL05 @ 80% |
| 18 | Uninsured partial plate | CL07 partial |
| 19 | Category stable claim | most cases |
| 20 | FNOL Turn-1 templates | unchanged strong |

---

## Aggregate

| Metric | Z7 | Z10A | Z10B |
|--------|-----|------|------|
| Avg keyword retention | 36% | 36% | **71%** |

---

## Phase 4 verdict

Turn-1 FNOL was already strong. **Turn 2+ needed claim lane detection + literal tokens + generic merge** — not a new claims service.
