# P16-Z9 Phase 5 — Duplicate Discovery Audit

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Sources:** P16Z0_DUPLICATION_AUDIT, P16-Z3 waste analysis, sprint chain Y→Z8, script inventory

---

## Executive summary

P16-Y through P16-Z8 **re-discovered the same facts** with different names. Estimated **3–6 engineer-months** of exploration/documentation did not convert to deployed trial UX. Dominant waste: **deploy/SSO gap**, **hidden UI**, and **parallel batteries** — not missing backend.

**Z9 rule:** No new archaeology sprint without a new battery result or deploy change.

---

## Repeated findings (≥3 sprints)

| Finding | Sprints that rediscovered | SSOT home |
|---------|---------------------------|-----------|
| Append API works; UX doesn't teach it | Z0, Z3, Z4, Z5, X | CAPABILITY_MAP + Z9 OS |
| FP-004 SSO blocks entire trial | Z0, Z3, Z4, Z6, Z7 | CURRENT_PRODUCT_SHAPE / founder ops |
| `triage.py` + `case_draft_engine` = Case Intelligence | Y, Z0, Z2, Z3 | MASTER_OUTLINE |
| Multi-turn summary merge (Y44) P0 | Y, Z3, Z4, Z5, Z6, Z8 | VALIDATION_OS |
| `case_messages` stored, not rendered | Z4, Z5, Z6 | Z6 ship list |
| `buildAddCarRailTurnModel` trapped on customer rail | Z5, Z6, Z8 | CAPABILITY_MAP |
| SimulationAssistant orphan | Z0, Z3 | DUPLICATION D1 |
| 10+ add-car batteries overlap | Z0, Z3 | OPERATOR_IGNORE_LIST |
| Commercial doc-complete ≠ payment-ready | Z0, K, Z3 | Trial INDEX |
| Risk scores computed, not shown | Z0, Z2, Z8 | Tier 2 Cap 3 |
| Role C naming collision | Z0, L, X | Glossary |
| Chen Kui = Role B persona duplicate | Z0, L, X | One persona doc |
| Skeptical Broker = Role D | Z0, Q, Z7 | Role D only |
| P16-M/N/X TOP50 friction overlap | Z0, M, N, X | Archive |
| Do not build Case Intelligence microservice | Z0, Z3, Z2 | 90_DAY_FILTER |
| OCR built; no inline product caller | Z0, Z3, Z8 | Tier 3 |
| Customer tab exists, hidden | Z0, Z3, O | Tier 3 Cap 4 |
| Copy = exit; no append CTA | X, Z4, Z5 | Tier 1 Cap 5 |
| waiting_on 100% manual | Z5, Z7, Z8 | Z8 heuristic |
| Premium D08 gold; D10/D07 fail | Z7, Z8 | Role D battery |

---

## Repeated batteries

| Battery family | Scripts / configs | Operator need | Verdict |
|----------------|-------------------|---------------|---------|
| **P16-Y single-turn** | `run_p16y_case_battery.py`, `p16y_50_cases.json` | ✅ SSOT | Keep — CI gate ≥88 |
| **Role D multi-day** | `run_role_d_memory_battery.py`, `role_d_*.json` | ✅ SSOT | Keep — post-deploy + post-engine |
| **Guardrail** | `guardrail_inbox_triage.sh` | ✅ SSOT | Keep |
| **Trial launch** | `trial_launch_check.sh` | ✅ SSOT | Keep — add append sim |
| **Add-car lab** | 10+ `run_add_car_*` | ❌ Pilot wedge | Archive path — OPERATOR_IGNORE |
| **Simulation assistant** | `run_simulation_assistant_scenarios.py` | ❌ | Retire — use ScenarioReplayTab |
| **Demo pack triple** | original / fixed / current | ⚠️ | One canonical in AGENTS.md |
| **Health checks** | quick / post_sprint / trial_readiness | ⚠️ | Pre-trial = `trial_launch_check.sh` only |
| **Claims ad-hoc** | Z6 validation doc + Role D CL* | ✅ | Fold into Role D config only |
| **P16-T runner** | lab health | Reference | Not pre-trial |

**Recommendation:** Declare **two batteries + one guardrail** for product path. Lab batteries require archive ticket to add new one.

---

## Repeated simulations

| Simulation type | Locations | Overlap |
|-----------------|-----------|---------|
| Role C cold customer | P16-X/Q/Y, ScenarioReplayTab | Same journeys, different rubrics |
| Chen Kui timed | P16-X, P16-Q | Duplicate persona |
| Skeptical / Role D | P16-Q, P16-Z7 | **Merged → Role D battery** |
| Claims 10-journey | Z4, Z5, Z6, Z7 CL*, Z8 | Same C1–C10 themes |
| Reality / office sim | Z4, Z6 | Continuity loop narration |
| 50-case P16-Y | Y only | Canonical — don't fork |
| 100-office chaos | auto-evolution branch | Obsolete for pilot |

---

## Repeated documents

| Doc cluster | ~Files | Themes duplicated | Action |
|-------------|--------|-------------------|--------|
| P16-M TOP50 UI | 3+ | trust, append, English | Archive; P16-M #1–10 → backlog only |
| P16-N journey | 5+ | customer empty state | Historical |
| P16-X friction | 8+ | copy exit, timeline 41 | Historical |
| P16-Z3 plans | 2 | 30/90 day | Superseded by P16Z9_90_DAY_FILTER |
| North star paragraphs | 6+ verdicts | Same sentence | P16Z25_NORTH_STAR only |
| Capacity ranking | Z2.5, Z3, Z9 | Seven caps | P16Z9_CAPACITY_REVIEW |
| Capability maps | Z0, Z2, Z8 | Layer taxonomy | Z0 map + Z8 domains |
| Maturity | Z3 + CASE_INTELLIGENCE | L1–L7 | CASE_INTELLIGENCE_MATURITY_MODEL |
| Final verdicts | 10+ sprints | Top 10/20 lists | P16Z9_FOUNDER_SUMMARY |

---

## Repeated investigations (do not run again)

| Investigation | Last authoritative answer | Re-run only if |
|---------------|---------------------------|----------------|
| "Do we have append?" | Yes — Z0, Z4 | Append API contract changes |
| "Is there a conversation service?" | No need — triage_for_append | New backend rewrite proposed |
| "Should we build OCR product?" | Wire existing; text wedge | Broker demands image-first |
| "What does Zendesk do?" | Z2 teardown | New benchmark company |
| "Where is case intelligence?" | triage.py — Z0 inventory | Major module split |
| "Can Chen Kui use cold URL?" | FP-004 — Z0 | SSO removed |
| "SimulationAssistant?" | Delete — Z0 | Someone re-adds imports |
| "How mature are we?" | L4.5 engine / L3.5 deploy — Z3 | Role D ≥80 sustained |

---

## Waste heat map (updated)

```
CRITICAL — stop immediately:
  ├── New Case Intelligence / Conversation / OCR microservices
  ├── New add-car battery without archiving old
  └── UI TOP50 sprint before FP-004 off

HIGH — consolidate:
  ├── 270 product_constitution MDs → 15 SSOT + archive
  ├── Persona naming (Chen Kui, Role D only)
  └── 3 demo pack runners → 1

LOW — intentional duplication:
  ├── P16-Y (single-turn) + Role D (multi-day) — different gates
  └── triage.py tests + guardrail scenarios
```

---

## TOP 10 duplicate investigations to never rerun

1. Full capability inventory from scratch → read `P16Z0_CAPABILITY_INVENTORY.md`
2. "Does append work?" API test → `guardrail` FA3 + append sim
3. Zendesk/Intercom teardown → `P16Z2_COMPANY_TEARDOWN.md`
4. Hidden customer tab → `CustomerEntryTab` in Z0 map
5. Maturity model redesign → `CASE_INTELLIGENCE_MATURITY_MODEL.md`
6. 50 friction prioritization → `P16Z9_FOUNDER_SUMMARY` TOP ROI
7. SimulationAssistant audit → closed D1
8. Commercial pack completeness → trial INDEX + observation log
9. Multi-turn architecture options → `P16Z0_MULTITURN_ARCHAEOLOGY.md`
10. Claims greenfield FNOL → Z6/Z7 — tune extractors only

---

*End of P16-Z9 Phase 5 — Duplicate Discovery Audit*
