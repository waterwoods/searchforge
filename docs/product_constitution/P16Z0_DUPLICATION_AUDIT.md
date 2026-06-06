# P16-Z0 Capability Duplication Audit

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 7  
**Method:** Cross-reference docs, scripts, UI, and `services/fiqa_api/inbox_triage/` for parallel implementations of the same user-visible outcome.

---

## Executive summary

The repo shows a **mature engine** with **repeated evaluation layers** and **multiple UI/simulation paths** that diverged without retirement. Estimated **waste** is concentrated in: (1) simulation UI/components, (2) add-car battery scripts, (3) evaluation sprints that restated the same friction, (4) append vs multi-turn vs session naming, (5) doc-complete commercial vs payment-ready confusion.

**Highest ROI fix:** Stop new parallel implementations; wire and delete orphans.

---

## Duplication catalog

### D1 — Simulation UI (2+ frontends)

| Instance | Path | Status |
|----------|------|--------|
| ScenarioReplayTab | `ui/src/components/simulation/ScenarioReplayTab.tsx` | **Active** (lab) |
| SimulationAssistant | `ui/src/components/simulation/SimulationAssistant.tsx` | **Orphan** — 0 imports |
| Simulation assistant scenarios | `configs/simulation_assistant_scenarios.json` + `run_simulation_assistant_scenarios.py` | Legacy harness |

**Overlap:** Both target multi-turn Role C / add-car replay.  
**Estimate:** 1–2 sprints of UI work duplicated (~2–4 engineer-weeks historical).  
**Action:** Delete or archive `SimulationAssistant.tsx`; single entry = ScenarioReplayTab.

---

### D2 — Role C naming (2 personas, 1 label)

| Label | Meaning A | Meaning B |
|-------|-----------|-----------|
| Role C | Cold end-user (P16-X/Q/Y) | Office assistant (P16-L) |

**Overlap:** Confusing sprint reports and priorities.  
**Estimate:** Low code cost, **high decision cost** across 8+ sprints.  
**Action:** Rename in future docs: Role C-cold vs Role C-assistant (or retire letter scheme).

---

### D3 — Chen Kui vs Role B

Same broker archetype documented in P16-L (Role B) and P16-X/Q (Chen Kui timed sim).

**Overlap:** Duplicate simulation writeups.  
**Action:** One canonical persona doc; others link.

---

### D4 — Skeptical Broker vs Role D

P16-Q Skeptical Broker ≈ P16-L Role D.

**Overlap:** Two names, one archetype.  
**Action:** Merge references.

---

### D5 — Case Intelligence vs Case Distillation vs case_draft_engine

| Layer | What it is |
|-------|------------|
| Case Intelligence | Rubric dimension |
| Case Distillation | Rubric composite |
| `case_draft_engine` | Actual code packaging |

**Overlap:** Risk of building three "services" for one engine.  
**Estimate:** P16-Y correctly extended rules — **avoid** new distillation microservice.  
**Action:** Map all doc terms → `triage.py` + `case_draft_engine.py`.

---

### D6 — Append vs multi-turn vs session

| Term | Implementation |
|------|----------------|
| `conversation_turns` | In-flight multi-turn triage |
| `triage_for_append` / `append-message` | Post-persist follow-up |
| `session_store` | Binding continuity |
| Append summary merge (missing) | Fourth concept — **not built** |

**Overlap:** Teams may rebuild "conversation service" unaware append API exists.  
**Action:** Document single diagram (see `P16Z0_MULTITURN_ARCHAEOLOGY.md`).

---

### D7 — Add-car scenario batteries (10+ runners)

Examples:

- `run_add_car_scenario_battery.py`
- `run_add_car_mutation_battery.py`
- `run_add_car_cplus_scenario_library.py`
- `run_add_car_expansion_rule_map_battery.py`
- `run_add_car_driver_zip_materials_stress_battery.py`
- `run_web_informed_add_car_realistic_battery.py`
- `run_add_car_edge_case_simulations.py`
- `run_add_car_llm_slot_ab_battery.py`
- `run_high_risk_add_car_pg_stage2_sprint_battery.py`

**Overlap:** Same lane (add-car) with overlapping scenario sets; operator cannot run all pre-trial.  
**Estimate:** Significant lab time (weeks cumulative); **pilot wedge** is broker paste triage, not add-car lab explosion.  
**Action:** One **operator** battery (`guardrail_inbox_triage.sh` + `p16y_50_cases`); archive rest to `docs/runbooks/OPERATOR_IGNORE_LIST.md`.

---

### D8 — Demo pack runners (3 variants)

- `run_demo_pack.py`
- `run_demo_pack_fixed.py`
- `run_demo_pack_original.py`

**Overlap:** Three entrypoints for same concept.  
**Action:** Deprecate two; document one in AGENTS.md.

---

### D9 — Evaluation sprints restating UI friction

| Sprint | Output | Code |
|--------|--------|------|
| P16-M | TOP50 UI improvements | None |
| P16-N | Customer journey + TOP50/100 | None |
| P16-X | TOP50 frictions + conversation audit | None |

**Overlap:** ~150 ranked items; many duplicate themes (trust copy, append, English copy).  
**Estimate:** 3 sprint-weeks documentation; **implementation lag** caused re-discovery.  
**Action:** Merge into single backlog; P16-M #1–10 as next copy sprint.

---

### D10 — Health / readiness checks (multiple scripts)

- `health_check.sh`
- `quick_health_check.sh`
- `post_sprint_check.sh`
- `trial_readiness_check.sh`
- `trial_launch_check.sh`
- P16-T runner

**Overlap:** Partial; each has role but founder confusion on which to run.  
**Action:** Already partially unified in AGENTS.md — enforce **one** pre-trial command: `trial_launch_check.sh`.

---

### D11 — Commercial pack vs Capability 6 vs trial docs

P16-K artifacts + Cap 6 contract + `TRIAL_ONE_PATH` + observation log v1/v2/v3.

**Overlap:** "Commercial ready" stated in three places with different meanings (doc vs payment vs deploy).  
**Estimate:** False confidence cost — **Day 7 blocked** despite "closed" P16-K.  
**Action:** Always label **doc-complete** vs **payment-ready** vs **deploy-ready**.

---

### D12 — Risk scores vs "risk extraction" product ask

`v4_error_risk_score` / `v5_handoff_risk_score` implemented; never shipped to UI.

**Overlap:** Future sprint might rebuild risk UI from scratch.  
**Action:** Surface existing fields in glance (S effort).

---

### D13 — OCR paths (inline vs attachment vs notice_image field)

Three paths documented in `P16Z0_IMAGE_ARCHAEOLOGY.md` — not duplicate code, but **duplicate product conversations**.

**Action:** Single image intake spec referencing existing modules.

---

### D14 — Customer intake simplification (P16-O vs P16-N)

P16-O implemented empty-state changes; P16-N evaluated same surfaces.

**Overlap:** Sequential sprints on same tab without deploy parity closure.  
**Action:** Customer tab revival only after deploy score justifies.

---

## Time-waste estimate (order of magnitude)

| Category | Historical effort | Ongoing cost |
|----------|-------------------|--------------|
| Orphan SimulationAssistant + legacy sim config | 2–4 eng-weeks | Confusion |
| Add-car battery proliferation | 4–8 eng-weeks (lab) | CI time, cognitive load |
| P16-M/N/X doc overlap | 3 founder-weeks | Re-prioritization loops |
| Deploy vs local verdict gap (multiple sprints) | 6+ sprints re-validating same FP-004 | **Every trial week delayed** |
| Rebuilding conversation/append (hypothetical) | 2–4 eng-weeks if attempted | **Prevented by this archaeology** |

**Total identifiable redundancy:** roughly **3–6 engineer-months** of exploration and documentation not converted to deployed trial UX — dominated by **deploy/SSO** and **hidden UI**, not missing backend.

---

## Redundancy heat map

```
High overlap + high risk of rebuild:
  ├── Multi-turn "new service" (D6)
  ├── Case intelligence microservice (D5)
  └── OCR upload product (D13) — frozen but tempting

High overlap + low code cost to fix:
  ├── SimulationAssistant delete (D1)
  ├── Risk score in UI (D12)
  └── Persona naming (D2–D4)

High overlap + intentional (keep one):
  ├── guardrail + p16y battery (operator path)
  └── triage.py single engine
```

---

## Recommendations

1. **Deletion quota:** Remove `SimulationAssistant.tsx` or mark deprecated with link to ScenarioReplayTab.
2. **Operator script canon:** `trial_launch_check.sh` + `guardrail_inbox_triage.sh` only for pre-trial.
3. **Glossary:** Role C-cold, Chen Kui (not Role B), Skeptical (Role D retired).
4. **Anti-pattern gate:** Constitution already flags local-only — enforce on PRs.
5. **No new batteries** without archiving an old one.

---

*End of P16-Z0 Duplication Audit*
