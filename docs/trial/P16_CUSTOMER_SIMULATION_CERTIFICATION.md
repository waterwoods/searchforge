# P16 Customer First Simulation Certification

**Sprint:** P16-CUSTOMER-FIRST-SIMULATION  
**Date:** 2026-06-07  
**Product:** Customer First Phase 1 (phone lookup restored, UI live)  
**Evidence:** `docs/trial/P16_CUSTOMER_SIMULATION_REPORT.md`

---

## Certification Statement

This sprint stress-tested the **seven Customer First Constitution rules** through eight business simulations (A–H). Validation covered:

- `GET /api/inbox/customer/active-case` on **Cloud Run** (`fiqa-api-00086-f95`) and **local strict Postgres**
- `POST /api/inbox/customer/start-add-car` Rule 7 enforcement
- Postgres case records (`STRICT_PG_ONLY`)
- Preview UI end-to-end for Scenario A (new) and B (resume)

**No production code changes were required.** No blocking bugs were found.

---

## Health Score

| Dimension | Score (0–10) | Weight | Weighted |
|-----------|--------------|--------|----------|
| Constitution rule compliance (API) | 9.0 | 30% | 2.70 |
| Customer entry UX (Preview) | 8.5 | 20% | 1.70 |
| Resume / continuity (phone return) | 9.0 | 20% | 1.80 |
| Edge-case safety (wrong phone, shared phone) | 6.0 | 15% | 0.90 |
| Office/broker operability | 8.0 | 15% | 1.20 |
| **Total** | | | **8.3 / 10** |

**Health score: 83/100**

---

## Top 5 Strengths

1. **Phone return key works in production** — Cloud Run `GET /customer/active-case` returns HTTP 200; Preview UI no longer shows `无法验证手机号` (recovery sprint verified).

2. **Rule 7 enforced server-side** — Duplicate `start-add-car` returns **409 `active_case_exists`** with active case summary for Continue / Contact Broker UX.

3. **No-login entry is real** — Customer First screen shows explicit trust copy; gate before intake chat (`customerFirstUnlocked`) respects constitution.

4. **Phone normalization is robust** — Four US formats resolve to the same 10-digit key; invalid phones return **400**.

5. **Postgres is durable truth** — Cases persist with `customer_phone`, `service_lane: add_car`, `lifecycle_status: collecting`; multi-device return via phone only (Sim G).

---

## Top 5 Remaining Risks

1. **Wrong phone digit (P1)** — Empty lookup; customer may start orphan case. No self-recovery. Broker merge/close required.

2. **Shared household phone (P2)** — One active case per phone; second household member blocked until broker splits (Rule 6 playbook).

3. **Generic vehicle display on entry card (P2)** — `primary_vehicle_summary` null until intake chat captures vehicle; “Tesla” not visible on resume card at phone-entry step.

4. **“When will someone contact me?” (P2)** — North-star question #3 not answered on Customer First entry surface; broker must set expectation manually.

5. **Append-after-submit not re-verified live (P3)** — OpenAI quota blocked local triage battery; integrity relies on P16-APPEND 22/22 certification. Re-run before first paid broker if quota restored.

---

## Constitution Rule Certification

| Rule | Status | Evidence |
|------|--------|----------|
| 1 — Customer Never Logs In | ✅ **CERTIFIED** | Entry screen + Preview UI; no auth on customer lookup |
| 2 — Phone Is The Return Key | ✅ **CERTIFIED** | Sims B, G, H; Cloud Run 200 |
| 3 — Phone Required For Formal Submit | ✅ **CERTIFIED** | Sim F — incomplete formal submit stays `collecting` |
| 4 — Progress = Missing Fields | ✅ **CERTIFIED** | Active card shows `missing_fields`; Saved ≠ Submitted copy |
| 5 — Only Broker Closes Or Reopens | ✅ **CERTIFIED** | No customer close path; Sim D broker/contact path |
| 6 — Broker Confirms Identity | ⚠️ **OPERATIONAL** | Claimed name/phone only; Sims C, E require broker playbook |
| 7 — One Active Case | ✅ **CERTIFIED** | Sims D, E — 409 enforcement |

---

## GO / NO-GO Decision

### Customer First Phase 1: **CONDITIONAL GO**

| Criterion | Met? |
|-----------|------|
| Phone lookup restored on Cloud Run | ✅ |
| Customer First UI live on Preview | ✅ |
| Scenario A (new customer) E2E | ✅ |
| Scenario B (resume) E2E | ✅ |
| Rule 7 server enforcement | ✅ |
| Wrong-phone mitigation documented | ✅ (copy/ops — not shipped) |
| Blocking bugs | ✅ None |

### Conditions for full GO (first real broker trial)

1. **Broker brief** — wrong-phone and shared-household playbooks distributed (`P16_CUSTOMER_SIMULATION_REPORT.md` §C, §E).
2. **Customer copy** — add “double-check phone if no request found” (optional P1 copy sprint).
3. **Append re-check** — run `scripts/run_p16_append_simulation_battery.py` when LLM quota available.

### Would block GO

- `GET /customer/active-case` 404 on production (resolved in `fiqa-api-00086-f95`)
- Customer login wall on entry
- Silent duplicate active cases for same phone (not observed)

---

## Sign-Off Matrix

| Stakeholder | Posture | Notes |
|-------------|---------|-------|
| **Customer** | Accept with guidance | Phone return works; typo risk needs copy |
| **Broker** | Ready supervised | 409 + Contact Broker adequate; identity confirmation on shared phones |
| **Office Assistant** | Ready | Postgres truth; stub vehicle labels until intake progress |
| **Founder** | **CONDITIONAL GO** | Ship Phase 1 to Chen Kui pilot with documented P1 mitigations |

---

## Artifacts

| Artifact | Path |
|----------|------|
| Full simulation report | `docs/trial/P16_CUSTOMER_SIMULATION_REPORT.md` |
| Phone lookup recovery | `docs/trial/P16_PHONE_LOOKUP_RECOVERY.md` |
| Constitution | `docs/product_constitution/P16_CUSTOMER_FIRST_CONSTITUTION.md` |
| API unit tests | `tests/test_active_case_by_phone.py` (3/3) |
| Screen simulations | `scripts/run_p16_customer_first_screen_simulations.py` |

---

## Final Verdict

```
╔══════════════════════════════════════════════════════════╗
║  P16 CUSTOMER FIRST PHASE 1                              ║
║  Health Score: 83/100                                    ║
║  Decision: CONDITIONAL GO                                ║
║  Blocking bugs: 0                                        ║
║  Date: 2026-06-07                                        ║
╚══════════════════════════════════════════════════════════╝
```

**Founder URL (live):**  
https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

*End of P16 Customer First Simulation Certification*
