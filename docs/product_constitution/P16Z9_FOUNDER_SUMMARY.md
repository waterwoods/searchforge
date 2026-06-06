# P16-Z9 Phase 10 — Founder Summary

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Mission complete:** Consolidate P16-Y through P16-Z8 + Role D into one operating system.

**Constraint honored:** No production code. No features. No new architecture.

---

## Core answer: minimum docs for a new engineer

Read **in order** (≤12):

1. `AGENTS.md`
2. `docs/CURRENT_PRODUCT_SHAPE.md`
3. `docs/goals/insurance_paid_pilot_goal.md`
4. `CASE_INTELLIGENCE_MASTER_OUTLINE.md`
5. `CASE_INTELLIGENCE_MATURITY_MODEL.md`
6. `P16Z9_SSOT_PROPOSAL.md`
7. `P16Z9_FOUNDER_SUMMARY.md` (this file)
8. `P16Z9_DEVELOPMENT_OS.md` + `P16Z9_VALIDATION_OS.md`
9. `docs/FOUNDER_ONE_PATH.md`
10. `docs/runbooks/OPERATOR_SURFACE.md`

---

# TOP 20 DISCOVERIES

1. **Engine is L4.5; deployed experience is L3.5; Chen Kui effective is L2.5** — gap is access + UX, not backend (Z3).
2. **48 `inbox_triage` modules = complete Case Intelligence engine** — no microservice needed (Z3).
3. **P16-Y 88.6 avg** — single-turn wedge lanes work (cancel, payment, missing doc, UW) (Y).
4. **Append API production-grade** — `triage_for_append`, boundary tests exist (Z0, Z4).
5. **Broker memory UX ~41/100** — data stored, not hero-rendered (Z5, X).
6. **Y44/Y45 are the multi-turn P0** — correction drops prior intent; premium misclassified on append (Y, Z5, Z6).
7. **Role D: 60.7/75 memory, 68.9/100 reread** — 4/10 journeys need WeChat Day 3 (Z7).
8. **D08 premium path is gold; D10/D07 are worst** — payment Chinese + remove-car lane flip (Z7, Z8).
9. **65–70% of remaining memory work already in triage.py** — lane guards + merge, not new services (Z8).
10. **FP-004 Preview SSO blocks entire trial** — 5-minute founder fix (Z0).
11. **Copy = exit** — post-copy append CTA missing; spell-checker trap (X, Z4, Z5).
12. **`buildAddCarRailTurnModel` best memory UI** — trapped on customer add-car rail only (Z5).
13. **`getRecentCustomerMessages` imported unused** — literal wire fix (Z5).
14. **Claims Turn 1 pilot-ready; Turn 2+ 36% retention** — tune extractors, not FNOL greenfield (Z6, Z7).
15. **`waiting_on` 100% manual** — 0/9 carrier phrases auto-set (Z7, Z8).
16. **SimulationAssistant orphan** — ScenarioReplayTab + Role D battery (Z0).
17. **10+ add-car batteries = cognitive waste** — guardrail + p16y + role_d sufficient (Z0).
18. **Commercial doc-complete ≠ payment-ready** — observation log is commercial SSOT (Z0, K).
19. **Every benchmark company uses same pipeline** — we match engine, not deployed surface (Z2).
20. **3–6 engineer-months documentation redundancy** — Z9 SSOT stops re-discovery.

---

# TOP 10 SSOT DOCUMENTS

1. `docs/CURRENT_PRODUCT_SHAPE.md` — runtime truth
2. `CASE_INTELLIGENCE_MASTER_OUTLINE.md` — product layers
3. `CASE_INTELLIGENCE_MATURITY_MODEL.md` — L1–L7
4. `P16Z25_NORTH_STAR.md` — one sentence north star
5. `P16Z25_PRODUCT_SOUL.md` — 微信 loop soul
6. `P16Z0_CAPABILITY_MAP_V2.md` — what exists / hidden / broken
7. `P16Z9_DEVELOPMENT_OS.md` — sprint loop
8. `P16Z9_VALIDATION_OS.md` — batteries + observation log
9. `P16Z9_90_DAY_FILTER.md` — build / don't build
10. `AGENTS.md` — commands + scope

---

# TOP 10 DOCUMENTS TO ARCHIVE

1. `P16M_TOP50_UI_IMPROVEMENTS.md` — themes in Z9
2. `P16N_CUSTOMER_JOURNEY_MAP.md` — superseded by maturity model
3. `P16X_TOP50_FRICTIONS.md` — duplicate friction lists
4. `P16Z3_MATURITY_MODEL.md` — duplicate of CASE_INTELLIGENCE_MATURITY_MODEL
5. `P16Z3_30_DAY_PLAN.md` / `P16Z3_90_DAY_PLAN.md` — use Z9 filter
6. `P16Z2_TOP100_IDEAS.md` — historical brainstorm
7. `P16Z0_*_ARCHAEOLOGY.md` (6) — keep verdict + inventory only
8. `docs/archive/platform/*` — platform fantasy
9. Per-sprint phase 1–8 docs (keep final verdicts only)
10. Duplicate north star blocks inside Z4/Z5/Z7 verdicts

---

# TOP 10 DUPLICATE INVESTIGATIONS

1. "Do we have append backend?"
2. "Should we build Case Intelligence service?"
3. "Where is multi-turn handled?"
4. "Is OCR built?"
5. "What does Zendesk do?"
6. "Is customer tab missing?"
7. "Full capability inventory from scratch"
8. "50 UI friction prioritization"
9. "SimulationAssistant vs ScenarioReplayTab"
10. "Maturity model redesign"

→ All answered in Z0–Z9 SSOT. **Do not rerun.**

---

# TOP 10 THINGS WE SHOULD NEVER REBUILD

1. Multi-turn conversation microservice
2. Case Intelligence microservice
3. Append / follow-up backend
4. OCR pipeline from scratch
5. Risk scoring engine (v4/v5 exists)
6. Customer portal from scratch
7. SimulationAssistant UI
8. Claims FNOL greenfield engine
9. PaymentMemoryService
10. P17 platform features

---

# TOP 10 THINGS WE SHOULD BUILD NEXT

*(Wire / tune / deploy — not greenfield)*

1. FP-004 off + redeploy Z6 UI
2. Post-copy append CTA + collapse paste when case open
3. Render `case_messages` thread + 本轮更新 delta (generalize add-car rail)
4. Y44/Y45 summary merge + generic collected merge
5. Chinese payment/lapse + remove-car lane guards (Z8 Day 1–2)
6. `waiting_on` triage heuristic
7. Claim field extensions (plate, police, carrier)
8. Chinese broker_next_step product_only pass
9. P16-Y ≥88 + Role D gates in CI
10. Founder 3× real multi-turn observation log cases

---

# UPDATED NORTH STAR

> **Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.**

**Continuity soul (subordinate loop):**

> 整理 → 复制发出 → 在等客户 → 客户回复 → 同案追加 → 看得见变了什么 → 再复制

**L5 commercial gate (new):** Role D reread ≥80, needs_wechat ≤2/10, with Z6 deployed.

---

# UPDATED CAPACITY RANKING

| Tier | Cap | Name |
|------|-----|------|
| **1** | 2 | Case Intelligence |
| **1** | 1 | Broker Front Door |
| **1** | 5 | Case Lifecycle |
| **1** | 7 | Founder Control |
| **2** | 3 | Structured Case Record |
| **2** | 6 | Trial Conversion |
| **3** | 4 | Customer Intake |

---

# UPDATED DEVELOPMENT LOOP

```
SSOT → Implementation (wire only) → Validation (guardrail → p16y → role_d) → Reality Test (observation log) → Update SSOT
```

Sprint types: **Ship** · **Validate** · **Archive** — nothing else.

---

# FINAL VERDICT

## If we start tomorrow, what is the exact operating system for the next 90 days?

### Week 1 — Access + visibility (Ship)

- FP-004 off; deploy `sprint-a/broker-front-door` (Z6 thread + append CTA)
- Post-copy append line; collapse paste; guardrail green
- **Exit:** Cold URL; founder Turn 1 on preview

### Weeks 2–3 — Memory engine (Ship)

- Z8 engine slice: payment Chinese, remove-car guard, `_merge_persisted_collected`, claim fields, waiting_on heuristic
- **Exit:** p16y ≥88; Role D reread ≥80, needs_wechat ≤2/10

### Week 4 — Commercial proof (Validate)

- 3 real multi-turn cases in observation log (`reopened_wechat=N`)
- Supervised → unsupervised Chen Kui cancel + claim two-turn
- Invoice sent
- **Exit:** G4 commercial gate

### Weeks 5–12 — Retention, not expansion (Ship Tier 2 only)

- Chinese templates, risk badge, log-driven top-3 fixes
- Customer tab **only if broker asks** after G3 pass
- Second office **only after** payment + renew signal
- Quarterly SSOT refresh (Z9-style Archive sprint)

### Daily commands

```bash
bash scripts/run_demo_local.sh          # local dev
bash scripts/operator/guardrail_inbox_triage.sh
bash scripts/trial_launch_check.sh      # pre-trial
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_p16y_case_battery.py
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_role_d_memory_battery.py
```

### What we do NOT do for 90 days

See `P16Z9_90_DAY_FILTER.md` — **no P17, no microservices, no OCR product, no Stripe, no customer tab by default, no new batteries, no archaeology sprints.**

---

## One-line founder read

> **You already built the broker-grade engine. The next 90 days are deploy + wire + Role D proof + get paid — not rediscover what append means.**

---

## P16-Z9 deliverables index

| Phase | Document |
|-------|----------|
| 1 | `P16Z9_DOCUMENT_INVENTORY.md` |
| 2 | `P16Z9_SSOT_PROPOSAL.md` |
| 3 | `P16Z9_NORTH_STAR_REVIEW.md` |
| 4 | `P16Z9_CAPACITY_REVIEW.md` |
| 5 | `P16Z9_DUPLICATE_AUDIT.md` |
| 6 | `P16Z9_BRANCH_REVIEW.md` |
| 7 | `P16Z9_DEVELOPMENT_OS.md` |
| 8 | `P16Z9_VALIDATION_OS.md` |
| 9 | `P16Z9_90_DAY_FILTER.md` |
| 10 | `P16Z9_FOUNDER_SUMMARY.md` (this file) |

---

*End of P16-Z9 — SSOT Consolidation Sprint*
