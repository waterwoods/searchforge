# P16-Z0 Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-Z0 Capability Archaeology  
**Constraint honored:** No build, refactor, P17, or features — documentation only.

---

## Archaeology complete

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | `P16Z0_CAPABILITY_INVENTORY.md` | ✅ |
| 2 | `P16Z0_MULTITURN_ARCHAEOLOGY.md` | ✅ |
| 3 | `P16Z0_ROLE_SIMULATION_ARCHAEOLOGY.md` | ✅ |
| 4 | `P16Z0_CASE_INTELLIGENCE_ARCHAEOLOGY.md` | ✅ |
| 5 | `P16Z0_IMAGE_ARCHAEOLOGY.md` | ✅ |
| 6 | `P16Z0_COMMERCIAL_ARCHAEOLOGY.md` | ✅ |
| 7 | `P16Z0_DUPLICATION_AUDIT.md` | ✅ |
| 8 | `P16Z0_CAPABILITY_MAP_V2.md` | ✅ |
| 9 | `P16Z0_TOP20_REDISCOVERIES.md` | ✅ |
| 10 | This verdict | ✅ |

---

## 1. What should NOT be rebuilt?

| # | Capability | Use instead |
|---|------------|-------------|
| 1 | Multi-turn / conversation service | `triage_conversation`, `session_store`, `triage_for_append` |
| 2 | Case intelligence microservice | `triage.py` rules + `case_draft_engine.py` |
| 3 | Append / follow-up backend | `append-message` route + `case_store.append_follow_up_message` |
| 4 | OCR pipeline | `image_input_pipeline.py` + `ocr_case_fusion.py` |
| 5 | Role C LLM customer | `role_c_simulation_service.py` + ScenarioReplayTab |
| 6 | Commercial / trial docs | P16-K pack + `docs/trial/` |
| 7 | Simulation UI | ScenarioReplayTab (not SimulationAssistant) |
| 8 | Health / guardrail | `guardrail_inbox_triage.sh`, `trial_launch_check.sh`, P16-T runner |
| 9 | Risk scoring | Existing v4/v5 in `case_draft_engine.py` |
| 10 | Primary OCR-first intake product | Frozen — text paste wedge |
| 11 | P17 platform | Blocked by constitution |
| 12 | Stripe / in-app billing | Out of pilot scope |
| 13 | New add-car battery runner | Existing guardrail + p16y battery |
| 14 | Customer portal from scratch | `CustomerEntryTab` exists — enable when ready |
| 15 | Payment "product feature" | Manual invoice + observation log discipline |

---

## 2. What should be revived?

Prioritized by ROI (impact / effort). **Revival = wire, expose, or run — not rewrite.**

| Rank | Item | Type | Effort | Cap |
|------|------|------|--------|-----|
| 1 | **Disable Preview SSO** (FP-004) | Founder ops | ~5 min | 1, 6, 7 |
| 2 | **Post-copy continuation + append discoverability** | UI copy/layout | S–M | 5 |
| 3 | **P16-M TOP10 under-1h** (trust line, demo demotion, Chinese glance) | UI copy | <1 day | 1 |
| 4 | **Append summary merge** (P16-Y #1) | Engine | M | 3, 5 |
| 5 | **P16-Y battery in CI** (≥88 gate) | Automation | S | 2, 3 |
| 6 | **Fill invoice payment IDs** | Founder | ~30 min | 6 |
| 7 | **Observation log row 1 on Day 0** | Process | S | 6 |
| 8 | **Redeploy P16-W fix + Andy E2E log** | Deploy | M | 7 |
| 9 | **Surface v4 risk in broker glance** | UI | S | 3 |
| 10 | **Vision API keys on pilot** | Ops | S | 2 |
| 11 | **Delete/archive SimulationAssistant.tsx** | Cleanup | S | 7 |
| 12 | **Chen Kui ui_copy deploy parity** | Config/deploy | M | 1 |
| 13 | **ScenarioReplayTab** for lab rehearsal | Already exists | S | 7 |
| 14 | **Follow-up editor on trial** (optional) | UI | M | 5 |
| 15 | **Customer tab on separate route** (P16-M #23) | UI | L | 4 |

---

## 3. What should be deleted?

| Item | Rationale |
|------|-----------|
| `SimulationAssistant.tsx` (if no import planned) | Zero usage; duplicate of ScenarioReplayTab |
| Unused import `getRecentCustomerMessages` in workbench | Lint / confusion |
| `run_demo_pack_original.py` / `run_demo_pack_fixed.py` (after confirming) | Triple demo pack entry |
| Retire **Role C** dual meaning in new docs | Use Role C-cold vs assistant |
| Archive redundant add-car batteries from operator path | Document in OPERATOR_IGNORE_LIST |

**Do not delete:** `triage.py`, append routes, P16-Y configs, commercial templates, constitution contracts.

---

## 4. What should become next sprint priority?

**Recommended next sprint (not P17):** **"P16-Z1 — Trial Path Revival"**

Scope: deploy + UX + evidence only — no new capabilities.

### Sprint goal

Raise **deployed** Cap 1 + Cap 5 above trial threshold by reviving existing assets.

### Ordered backlog

1. FP-004 Preview SSO off + `trial_launch_check.sh` PASS  
2. P16-M TOP10 batch (broker copy/append CTA)  
3. P16-Y P0 append summary merge  
4. Andy: invoice IDs + observation log protocol start  
5. Supervised Chen Kui Day 0 (process, not code)  
6. CI: `run_p16y_case_battery.py` gate  

### Explicit non-goals (again)

- P17  
- New pages / customer tab on trial URL (defer to Z2)  
- Primary OCR upload product  
- Rebuild conversation service  

---

## ROI-ranked discoveries (all phases)

| Rank | Discovery | ROI | Action class |
|------|-----------|-----|--------------|
| 1 | Backend append works; UI doesn't teach it | ★★★★★ | Revive UX |
| 2 | FP-004 SSO blocks entire trial | ★★★★★ | Founder toggle |
| 3 | P16-Y engine gains not felt on deploy | ★★★★★ | Deploy + copy sprint |
| 4 | Commercial docs complete; payment not | ★★★★☆ | Process |
| 5 | guardrail + p16y battery = quality gate | ★★★★☆ | Automate |
| 6 | product_only hides ~20 capabilities intentionally | ★★★★☆ | Understand |
| 7 | SimulationAssistant dead | ★★★☆☆ | Delete |
| 8 | Risk scores computed, not shown | ★★★☆☆ | Revive UI |
| 9 | Inline OCR API with no product caller | ★★★☆☆ | Wire or defer |
| 10 | 10+ add-car batteries overlap | ★★☆☆☆ | Archive |
| 11 | Role C naming collision | ★★☆☆☆ | Glossary |
| 12 | PDF OCR stub | ★★☆☆☆ | Document/defer |
| 13 | Customer tab ready in dev | ★★☆☆☆ | Z2 sprint |
| 14 | Audit export scaffold | ★☆☆☆☆ | Ignore |
| 15 | ML distillation experiment | ★☆☆☆☆ | Out of scope |

---

## One-line founder read

> **You already built a broker-grade triage engine with append, case intelligence, OCR side paths, commercial docs, and guardrails — the trial fails on URL access and discoverability, not missing backend. Next sprint should revive and deploy, not reinvent.**

---

## Success criteria for P16-Z0 (met)

- [x] Full capability inventory with status columns  
- [x] Multi-turn archaeology with 4 questions answered  
- [x] Role simulation archaeology  
- [x] Case intelligence map (implemented / partial / planned)  
- [x] Image archaeology with system-can/cannot answer  
- [x] Commercial archaeology  
- [x] Duplication audit with waste estimate  
- [x] Capability map v2 (current/hidden/broken/unused/high-value)  
- [x] Top 20 rediscoveries  
- [x] Final verdict with ROI ranking  

---

## Document index

All artifacts live in `docs/product_constitution/`:

- `P16Z0_CAPABILITY_INVENTORY.md`
- `P16Z0_MULTITURN_ARCHAEOLOGY.md`
- `P16Z0_ROLE_SIMULATION_ARCHAEOLOGY.md`
- `P16Z0_CASE_INTELLIGENCE_ARCHAEOLOGY.md`
- `P16Z0_IMAGE_ARCHAEOLOGY.md`
- `P16Z0_COMMERCIAL_ARCHAEOLOGY.md`
- `P16Z0_DUPLICATION_AUDIT.md`
- `P16Z0_CAPABILITY_MAP_V2.md`
- `P16Z0_TOP20_REDISCOVERIES.md`
- `P16Z0_FINAL_VERDICT.md`

---

*End of P16-Z0 — Capability Archaeology Sprint*
