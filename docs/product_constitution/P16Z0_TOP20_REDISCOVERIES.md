# P16-Z0 Top 20 Rediscoveries

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 9  
**Audience:** Andy — valuable capabilities that already exist and are easy to forget amid sprint churn.

Ranked by **revival ROI** (impact ÷ rebuild risk).

---

## 1. Append follow-up API (`triage_for_append`)

**What:** Full re-triage of new customer message in case context with boundary detection.  
**Where:** `triage.py`, `POST .../append-message`  
**Forgotten because:** Deploy UX hides path until queue reopen.  
**ROI:** ★★★★★ — wire UX only.

---

## 2. P16-Y 50-case battery + missing info library

**What:** Objective regression for case intelligence; 88.6 avg post-fix.  
**Where:** `scripts/run_p16y_case_battery.py`, `configs/p16y_50_cases.json`  
**Forgotten because:** Sprint closed as engine-only.  
**ROI:** ★★★★★ — add to CI / pre-deploy gate.

---

## 3. `guardrail_inbox_triage.sh` orchestration

**What:** Single command runs multi-turn, append, boundary, core triage scenarios.  
**Where:** `scripts/guardrail_inbox_triage.sh`  
**Forgotten because:** Many other scripts exist.  
**ROI:** ★★★★★ — canonical operator validation.

---

## 4. Commercial Pack (P16-K) — complete docs

**What:** Pricing, terms, invoices, Day 0/7, observation log v2.  
**Where:** `docs/trial/`, `P16K_FINAL_VERDICT.md`  
**Forgotten because:** Mistaken for "payment ready."  
**ROI:** ★★★★☆ — fill IDs + run process.

---

## 5. Constitution + 7 capability contracts

**What:** Mandatory map from feature → cap contract → evidence.  
**Where:** `CONSTITUTION_ENFORCEMENT.md`, `contracts/CAPABILITY_*.md`  
**Forgotten because:** Velocity sprints skip gate.  
**ROI:** ★★★★☆ — stops scope creep.

---

## 6. Failure Pattern Library (FP-004, FP-009, …)

**What:** Named root causes across sprints (SSO, invoice, observation log).  
**Where:** `FAILURE_PATTERN_LIBRARY.md`  
**Forgotten because:** Each sprint rediscovers Preview 401.  
**ROI:** ★★★★☆ — check before any "deploy fixed" claim.

---

## 7. Customer multi-turn (`CustomerEntryTab` + session API)

**What:** Full chat loop, 提交补充, session restore — works in dev.  
**Where:** `CustomerEntryTab.tsx`, `session_store.py`  
**Forgotten because:** Hidden on trial URL.  
**ROI:** ★★★★☆ — enable when Cap 4 deploy justified.

---

## 8. `case_draft_engine` + `conversation_summary`

**What:** Office-ready packaging and intent lines without new LLM product.  
**Where:** `case_draft_engine.py`, `triage.py`  
**Forgotten because:** UI shows glance not "draft engine."  
**ROI:** ★★★★☆ — extend summary merge, don't rebuild.

---

## 9. Attachment upload + OCR sidecar (broker)

**What:** Image upload on workbench with OCR when keys set.  
**Where:** `BrokerWorkbenchTab.tsx`, attachment routes  
**Forgotten because:** Paste-first trial narrative.  
**ROI:** ★★★☆☆ — ops: add Vision keys.

---

## 10. P16-T health check runner

**What:** Automated Preview/production survival checks.  
**Where:** P16-T docs + runner scripts  
**Forgotten because:** Overlaps with other health scripts.  
**ROI:** ★★★☆☆ — post-SSO verification.

---

## 11. `trial_launch_check.sh`

**What:** Single pre-first-trial gate (AGENTS.md entry).  
**Where:** `scripts/trial_launch_check.sh`  
**Forgotten because:** `trial_readiness` vs `founder_pre_trial` confusion.  
**ROI:** ★★★☆☆ — one command for founder.

---

## 12. ScenarioReplayTab + Role C API

**What:** LLM-driven customer replay for add-car depth testing.  
**Where:** `ScenarioReplayTab.tsx`, `role_c_simulation_service.py`  
**Forgotten because:** SimulationAssistant orphan distracts.  
**ROI:** ★★★☆☆ — lab only; delete duplicate component.

---

## 13. v4/v5 risk scores (already computed)

**What:** Error and handoff risk on every triage — not shown in UI.  
**Where:** `case_draft_engine.py`  
**Forgotten because:** Never productized.  
**ROI:** ★★★☆☆ — small UI surfacing.

---

## 14. Case boundary A/B scenarios

**What:** Guarded tests for same-issue vs new-issue append.  
**Where:** `configs/case_boundary_append_scenarios.json`, `run_append_boundary_ab_scenarios.py`  
**Forgotten because:** Invisible when UX creates duplicate cases anyway.  
**ROI:** ★★★☆☆ — pair with append UX fix.

---

## 15. Chen Kui client pack + ui_copy

**What:** Per-broker copy and calibration cases.  
**Where:** `configs/clients/chen_kui/`  
**Forgotten because:** Hardcoded trial strings on deploy.  
**ROI:** ★★★☆☆ — deploy parity for Chinese copy.

---

## 16. REALITY_VALIDATION_CHECKLIST Q13–27

**What:** Cross-sprint comparable Day 0 / Preview survival questions.  
**Where:** `REALITY_VALIDATION_CHECKLIST.md`  
**Forgotten because:** Each sprint writes new matrix.  
**ROI:** ★★★☆☆ — reuse every deploy sprint.

---

## 17. `product_only` as intentional wedge isolator

**What:** Flag correctly hides lab surface for trial — not accidental deletion.  
**Where:** `productSurface.ts`, `deployment_profile.py`  
**Forgotten because:** Feels like "missing features."  
**ROI:** ★★★☆☆ — understand before re-adding tabs to trial URL.

---

## 18. WeChat binding stub + simulate-complete

**What:** Identity path for customer without building WeChat OAuth product.  
**Where:** `wechat_binding.py`, routes  
**Forgotten because:** Customer tab off.  
**ROI:** ★★☆☆☆ — future Cap 4.

---

## 19. Support deployment manifest + case-head endpoints

**What:** Ops/debug endpoints for founder without DB access.  
**Where:** `routes/inbox_triage.py` support routes  
**Forgotten because:** Not in demo UI.  
**ROI:** ★★☆☆☆ — trial support.

---

## 20. P16-M TOP10 under-1-hour UI fixes

**What:** Ranked copy/layout fixes already specified — no new features.  
**Where:** `P16M_TOP50_UI_IMPROVEMENTS.md` § Top 10  
**Forgotten because:** P16-M marked evaluation-only.  
**ROI:** ★★★★☆ — **cheapest deploy score lift** for Cap 1/5.

---

## Honorable mentions (21–25)

- `run_follow_up_append_simulations.py` — proves append without UI  
- `FOUNDER_DEMO_QUEUE` — instant trial demo  
- `restore_8001_readiness.sh` — embedding recovery (AGENTS.md)  
- `workbench_enrichment.py` — lane kind for queue  
- `POST_SPRINT_HEALTH_CHECK.md` — sprint close template  

---

## Anti-rediscoveries (do NOT celebrate)

| Item | Why |
|------|-----|
| Build new conversation microservice | Duplicates append + session |
| SimulationAssistant.tsx | Dead code |
| Primary OCR upload product | Frozen P16-L |
| P17 platform | Explicitly blocked |
| Third demo pack runner | Use one |

---

*End of P16-Z0 Top 20 Rediscoveries*
