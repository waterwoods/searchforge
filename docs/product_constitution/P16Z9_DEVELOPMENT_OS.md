# P16-Z9 Phase 7 — Development Operating System

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Purpose:** Define how future sprints work — no features in this doc.

---

## The loop (canonical)

```
┌──────────┐
│   SSOT   │  Read CASE_INTELLIGENCE_* + CURRENT_PRODUCT_SHAPE + P16Z9_90_DAY_FILTER
└────┬─────┘
     ▼
┌──────────────┐
│ Implementation│  Wire / tune / deploy ONLY — no greenfield unless SSOT updated
└────┬─────────┘
     ▼
┌──────────────┐
│  Validation  │  guardrail → p16y → role_d → observation log
└────┬─────────┘
     ▼
┌──────────────┐
│ Reality Test │  Founder cold URL + Chen Kui supervised → unsupervised
└────┬─────────┘
     ▼
┌──────────────┐
│ Update SSOT  │  Edit MASTER_OUTLINE / CAPACITY / FOUNDER_SUMMARY — archive sprint docs
└──────────────┘
```

**Anti-pattern:** Documentation sprint → documentation sprint without deploy (P16-M/N/X pattern).

---

## Sprint types (only three allowed)

| Type | When | Output | Max duration |
|------|------|--------|--------------|
| **Ship** | Tier 1 cap gap with known fix | Merged PR + deploy + battery green | 3–7 days |
| **Validate** | Post-ship or pre-trial | Role D run + observation log entries | 1–2 days |
| **Archive** | SSOT consolidation (like Z9) | Updated SSOT; no code | 1–3 days |

**Forbidden sprint types:** Platform (P17), archaeology without new code delta, UI TOP50 without FP-004 off, new battery without archiving old.

---

## Sprint entry checklist

Before writing code:

- [ ] Which **capacity** (1–7) and **tier** (1–3)?
- [ ] Which **SSOT layer** (product / capability / validation)?
- [ ] Does fix **reuse** existing module? (If no → stop, update SSOT proposal first)
- [ ] In **P16Z9_90_DAY_FILTER** allowed list?
- [ ] Which **battery** proves success?

---

## Sprint exit checklist

Before claiming done:

- [ ] `bash scripts/operator/guardrail_inbox_triage.sh` green
- [ ] `run_p16y_case_battery.py` avg ≥88 (if triage touched)
- [ ] `run_role_d_memory_battery.py` if append/summary/UI touched
- [ ] Deployed to preview (not local-only)
- [ ] Observation log entry if user-visible
- [ ] SSOT updated OR sprint doc marked historical in inventory
- [ ] No new parallel doc (edit FOUNDER_SUMMARY instead)

---

## Implementation rules (from Y→Z8)

| Rule | Source |
|------|--------|
| Reuse `triage.py`, not new services | Z0, Z3, Z8 |
| UI fixes <2 days borrow existing helpers | Z5 (`getRecentCustomerMessages`, `buildAddCarRailTurnModel`) |
| Engine before polish | Z3 maturity |
| Timeline before next-action hero | MASTER_OUTLINE risks |
| Deploy same day as merge when trial-critical | Z0 FP-004 lesson |
| Founder ops parallel (SSO, invoice, log) | Cap 6 |

---

## Documentation rules

| Do | Don't |
|----|-------|
| Edit SSOT in place | Create `P16-Z10_FINAL_VERDICT` with duplicate top-10 lists |
| One north star file | Reprint north star in every verdict |
| Archive phase docs to `docs/archive/product_constitution/` | Leave 300 files in flat directory |
| Link to code paths | Describe imaginary microservices |

---

## Role split (MULTI_AGENT_OPERATING_MODEL)

| Role | Loop stage |
|------|------------|
| Engineer | Implementation + Validation scripts |
| Founder | Reality Test + observation log + FP-004 |
| Agent | SSOT read first; refuse P17 scope |

---

## 90-day sprint calendar (suggested)

| Weeks | Sprint | Type |
|-------|--------|------|
| 1 | Deploy Z6 + FP-004 + Cap 1 UX | Ship |
| 2 | Z8 engine slice (payment, remove, merge) | Ship |
| 3 | Role D validate + 3 real cases | Validate |
| 4 | waiting_on heuristic + Chinese templates | Ship |
| 5–6 | Chen Kui unsupervised + payment | Reality |
| 7–8 | Cap 3 polish + risk badge | Ship |
| 9–10 | Customer tab IF broker asks | Ship |
| 11–12 | Second office OR OCR wire | Ship |
| Rolling | Z9-style SSOT refresh | Archive (quarterly) |

---

## Definition of done (product)

Not "PR merged." **Done =**

1. Chen Kui completes scenario on **deployed** URL without Andy narrating append
2. Relevant battery threshold met
3. SSOT score updated in CAPACITY_REVIEW dashboard

---

## Escalation

| Signal | Action |
|--------|--------|
| Battery regression | Revert; fix forward — no parallel rewrite |
| Repeated discovery in retro | Add to DUPLICATE_AUDIT; delete investigation |
| New capability request | Update 90_DAY_FILTER first — founder sign-off |

---

*End of P16-Z9 Phase 7 — Development Operating System*
