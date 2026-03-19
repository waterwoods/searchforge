# Scenario Status / Health Spec

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Define how to mark scenarios as strong / medium / weak and show simulation coverage.

---

## 1. Maturity Levels

| Level | Meaning | Example |
|-------|---------|---------|
| **Strong** | Well-tested; trial-ready; broker handoff clear | Add-car, Cancellation risk, Missing document |
| **Medium** | Works; some edge cases; may need polish | Premium review, Claim intake, Remove vehicle |
| **Weak** | Less tested; known gaps; fix-next candidate | Bundling, Billing clarification (distinct from payment) |

---

## 2. How to Show Simulation Coverage

| Coverage | Display |
|----------|---------|
| **Trial recommended** | SIM1–SIM5; badge "Trial" |
| **Inbox triage scenarios** | Count of scenarios in inbox_triage_scenarios.json that map to this |
| **Simulation Assistant** | SIM IDs (e.g. SIM1, SIM3, SIM6) |
| **Expression robustness** | ER1–ER4; shorthand variants |
| **Add-car gap-closing** | AC-ULTRA-1–5; ultra-short add-car |

---

## 3. How to Show Known Gaps

| Gap type | Display |
|----------|---------|
| Fix now | Red chip; blocks trial |
| Fix next | Orange chip; high value |
| Defer | Gray chip; document for later |
| No known gap | — |

---

## 4. Last Changed / Recently Hardened (If Practical)

- **Add-car rules** — Extracted to add_car_rules.json; editable in Add-Car Rules Center
- **Reply templates** — Extracted to reply_templates.json
- **Category templates** — Extracted to category_templates.json
- **Markers** — Extracted to markers.json

*(Future: could add "last_updated" to config files; for now, infer from sprint reports.)*

---

## 5. Trial Importance

| Trial order | Scenarios |
|-------------|-----------|
| 1 | Cancellation risk (SIM1) |
| 2 | Missing document (SIM2) |
| 3 | Add-car quote (SIM3) |
| 4 | Premium review (SIM6) |
| 5 | Claim intake (SIM5) |

Show "Trial #N" badge for these.

---

*See also: `docs/CHEN_KUI_TRIAL_PACK.md`, `docs/trial/FIX_NOW_QUEUE_SPEC.md`*
