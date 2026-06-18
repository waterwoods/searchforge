# P16 Pre-Pilot Stress Test Plan

**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 0  
**Date:** 2026-06-06  
**Purpose:** Simulation-only validation before Chen Kui pilot CK-001  
**Authority:** Pre-pilot gate — no deployment, no architecture work

---

## Objectives

1. **Find remaining weaknesses** in add-car intake before real broker paste begins.
2. **Validate Southern California Chinese customer realism** — messy WeChat threads, not idealized forms.
3. **Confirm append integrity** — name/phone/VIN/ZIP/driver/delivery preserved across follow-ups.
4. **Confirm continuity integrity** — return-later threads do not duplicate cases or lose fields.
5. **Detect commercial P0 risks** — trust, payment, abandonment triggers for Chen Kui, Wu Miss, and customers.
6. **Upgrade pilot posture** from CONDITIONAL GO toward STRONG GO if ≥95% pass with zero append/continuity regressions.

---

## Case categories

| Category | Count | IDs | Focus |
|----------|-------|-----|-------|
| Realistic add-car customers | 20 | ST01–ST20 | SoCal Chinese WeChat realism |
| Edge / conflict cases | 3 | EC01–EC03 | Conflicting info, ZIP change, driver change |
| Return-later battery | 5 | RL01–RL05 | Multi-day continuity, no field loss |
| Append battery | 5 | AP01–AP05 | Formal-submit append, slot preservation |
| **Total** | **33** | | |

### Realistic case sub-types (ST01–ST20)

| Sub-type | Cases |
|----------|-------|
| New Tesla buyer | ST01 |
| Honda Accord, missing VIN | ST02 |
| Teen driver | ST03 |
| Chinese + English mixed | ST04 |
| Insurance card already sent | ST05 |
| ZIP provided, no driver | ST06 |
| Driver provided, no ZIP | ST07 |
| Two vehicles | ST08 |
| Delivery date change | ST09 |
| Vehicle change | ST10 |
| Family shared vehicle | ST11 |
| Retired parent driver | ST12 |
| Student driver | ST13 |
| Customer unsure of VIN | ST14 |
| Partial info upload | ST15 |
| Return after 2 days | ST16 |
| Return after 1 week | ST17 |
| Append phone only | ST18 |
| Append name only | ST19 |
| Append multiple times | ST20 |

---

## Pass criteria

| Dimension | Pass threshold |
|-----------|----------------|
| **Overall quality score** | ≥80/100 per scenario |
| **Route accuracy** | `service_type == add_car` for add-car threads |
| **Field extraction** | Expected collected/still fields match scenario intent |
| **Broker next step** | Actionable, non-generic Chinese/English step present |
| **Append integrity** | VIN, ZIP, driver, delivery_date, name, phone not lost on append |
| **Continuity integrity** | Prior collected fields preserved across return-later turns |
| **Formal submit readiness** | `handoff_ready` / `action_ready` correct for completeness level |
| **Aggregate pass rate** | ≥95% (≥32/33 scenarios) |
| **Commercial P0** | Zero open P0 issues blocking trust or payment |

---

## Failure criteria

| Failure type | Definition | Commercial rank |
|--------------|------------|-----------------|
| Wrong route | Non–add-car route on clear add-car thread | **P0** |
| Field loss on append | Prior slot drops from collected | **P0** |
| Field loss on continuity | Return-later turn erases prior slot | **P0** |
| Generic broker step | "Review the message" / no actionable gap list | **P1** |
| Wrong still_needed | Asks for field already collected | **P1** |
| Customer confusion draft | Draft re-asks for materials customer says sent | **P1** |
| Quality <80 | Composite score below pass bar | **P1** (P0 if route wrong) |
| Relative date unresolved | "下周五" in still_needed | **P2** |
| Draft tone mismatch | Too formal for WeChat customer | **P2** |
| Two-vehicle ambiguity | Second vehicle not flagged for split | **P1** |

---

## Commercial impact ranking

| Rank | Meaning | Pilot action |
|------|---------|--------------|
| **P0** | Blocks trust, payment, or pilot continuation | Must fix or document hard mitigation before CK-001 |
| **P1** | Annoying but survivable with broker edit | Log in case evidence; monitor in first 3 real cases |
| **P2** | Polish / edge case | Defer post-pilot |

---

## Execution method

```bash
PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16_pre_pilot_stress_test.py
```

**Engine:** `triage_conversation` + `triage_for_append` (actual P16 flow, no LLM generation)  
**Output:** `docs/trial/P16_STRESS_TEST_RESULTS.md`

---

## Deliverables

| Phase | Document |
|-------|----------|
| 0 | This plan |
| 1 | `P16_STRESS_TEST_CASE_PACK.md` |
| 2 | `P16_EDGE_CASE_PACK.md` |
| 3–4 | Return-later + append batteries (in case packs + JSON config) |
| 5 | `P16_STRESS_TEST_RESULTS.md` |
| 6 | `P16_COMMERCIAL_RISK_REVIEW.md` |
| 7 | `P16_PRE_PILOT_SCORECARD.md` |
| 8 | `P16_PRE_PILOT_FOUNDER_REVIEW.md` |
| 9 | `P16_PRE_PILOT_CERTIFICATION.md` |

---

## Success target

| Metric | Target |
|--------|--------|
| Scenarios run | 33 |
| Pass rate | ≥95% |
| Append regressions | 0 |
| Continuity regressions | 0 |
| Commercial P0 open | 0 |
| Verdict upgrade | CONDITIONAL GO → **STRONG GO** if all targets met |

---

*Simulation only. No deployment. No architecture work.*
