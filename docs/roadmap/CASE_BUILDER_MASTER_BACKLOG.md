# Case Builder Master Backlog

**Status:** Single ranked backlog index — do not duplicate item bodies here  
**Date:** 2026-08-03  
**SSOT for this week’s tasks:** `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md`  
**North Star:** `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md`  
**Gates:** `docs/release/PILOT_READY_RELEASE_GATES_V1.md`  
**UX risks (not feature ideas):** `docs/product/ux_problem_ledger.md`

### Ranking dimensions (1 = highest leverage / lowest concern as labeled)

Each item shows: **CV** customer value · **CU** commercial urgency · **FDE** portfolio leverage · **IR** implementation risk · **EV** evidence already available  
Scale 1–5 (5 = best for CV/CU/FDE/EV; for **IR**, 5 = highest risk).

---

## 1. Completed and frozen

Do not reopen without Founder decision.

| ID | Item | Evidence | Scores (CV/CU/FDE/IR/EV) |
|----|------|----------|---------------------------|
| F1 | Stage 1 deterministic Camry path (intake → Request More → supplement → ack → office accept) | `STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md` · tag `stage1-founder-validated-demo-2026-08-03` | 5/5/5/2/5 |
| F2 | Stage 2 known-customer policy confirm (no insurance-card fabrication; isolated identity) | `STAGE2_FOUNDER_VALIDATED_CLOSEOUT.md` | 5/5/4/2/5 |
| F3 | Real Usage Timing V1 (activity events + read-only exporter integrity) | `REAL_USAGE_TIMING_V1_CLOSEOUT.md` | 3/3/5/2/5 |
| F4 | One Active Case / append-first principles | `decision_log.md` D-001/D-002; `p0_one_active_case_identity_foundation.md` | 5/4/4/3/4 |
| F5 | P20 product development law (One Task, Production Loop, Form/Nav gates) | `p20_product_north_star.md` | 4/3/3/1/5 |

---

## 2. Must complete this week

Canonical detail lives only in the six-day plan (IDs below).  
Do not create parallel tickets with new names.

**Priority law:** P0 ranks 1–6 before any P1 MCP work. Accumulate evidence daily.

| Rank | Pri | Plan ID | Summary | CV | CU | FDE | IR | EV |
|------|-----|---------|---------|----|----|-----|----|----|
| 1 | P0 | D1-1…D1-4 | Close/freeze LangGraph PR A (phone before tag) | 5 | 5 | 5 | 3 | 4 |
| 2 | P0 | D2-1…D2-2 (+ D2-3 gate) | LangSmith traces + golden + deterministic eval | 3 | 4 | 5 | 3 | 2 |
| 3 | P0 | D3-1…D3-3 | AI Accept/Edit/Reject + fallback/latency + truthful report | 4 | 4 | 5 | 3 | 2 |
| 4 | P0 | D4-1…D4-3 | Pilot safety baseline | 5 | 5 | 4 | 3 | 3 |
| 5 | P0 | D5-1…D5-2, D6-1 | One-click demo + portfolio/evidence package | 5 | 5 | 5 | 2 | 3 |
| 6 | P0 | S-1…S-6 | Sunday final release gate | 5 | 5 | 5 | 2 | 3 |
| 7 | P1 | D5-3 | Thin MCP + second-office checklist (after P0s) | 2 | 2 | 5 | 3 | 1 |
| 8 | P2 | D2-3 judge only | Optional LLM judge | 2 | 1 | 3 | 3 | 1 |
| 9 | P2 | A2 / ledger L3 | Additional polish | 2 | 1 | 1 | 1 | 4 |
| 10 | P2 | D6-2 | Cost cleanup that does not affect demo | 1 | 2 | 2 | 1 | 4 |

---

## 3. Useful after the pilot

Track here only; do not pull into Sunday scope unless a P0 forces it.

| ID | Item | Why later | CV | CU | FDE | IR | EV |
|----|------|-----------|----|----|-----|----|----|
| A1 | Broker `broker_reviewed` deep workflow on AI facts | Confirm path enough for V1 | 3 | 2 | 3 | 3 | 2 |
| A2 | UX ledger L3 scenario-specific next-step copy | Stage 2 accepted non-blocking | 2 | 1 | 1 | 1 | 4 |
| A3 | Full DevTools walkthrough sign-off (ledger C1) | Partial phone proofs exist; full matrix open | 4 | 3 | 2 | 2 | 2 |
| A4 | HEIC/HEIF MIME end-to-end proof (ledger M8) | Current photo path verified without MIME proof | 3 | 2 | 1 | 3 | 2 |
| A5 | Online LangSmith eval in shared CI for all graphs | Case Builder offline gate first | 2 | 1 | 3 | 3 | 1 |
| A6 | Second real office (non-Chen) live config | Need Chen soft pilot learning first | 5 | 3 | 4 | 4 | 1 |
| A7 | Voice story polish beyond existing Chirp path | Not this week’s wedge | 3 | 2 | 2 | 3 | 3 |
| A8 | Metrics dashboard UI | Exporter CSV/JSON enough | 2 | 1 | 2 | 2 | 3 |

---

## 4. Explicitly deferred

| ID | Item | Defer reason |
|----|------|--------------|
| X1 | Quoting | North Star exclusion |
| X2 | Coverage / liability decisions | North Star exclusion; legal risk |
| X3 | Autonomous claim filing | North Star exclusion |
| X4 | General CRM | Out of wedge |
| X5 | Open-ended chatbot | Complexity not proven necessary |
| X6 | Large multi-agent system | Complexity not proven necessary |
| X7 | Full legal/compliance certification | Draft policy only this week |
| X8 | Stripe / multi-tenant IAM | Historical paid-pilot non-goal |
| X9 | Production / waterwoods retarget | Explicit safety freeze until Founder decision |
| X10 | Unsupported ROI claims (“saves X minutes/$) | Metrics V1 unsupported list |
| X11 | Platform/lab routers as product | `CURRENT_PRODUCT_SHAPE` / simplification plan |
| X12 | Mortgage/JobHunter MCP as Case Builder dependency | LAB ONLY |

---

## 5. Customer-discovery questions for 陈总

Ask; do not build from guesses.

1. Which repeated call types waste the most office minutes today (story, photos, VIN, insurance card, other)?  
2. When is a case “ready enough” for the office to proceed—what is the real completeness bar?  
3. Which Request More loops are usually unnecessary vs truly required?  
4. Would staff trust AI-organized accident summaries if the customer must confirm first?  
5. What must never be automated (tone, liability language, carrier contact)?  
6. Prefer Mini Program-only customer path vs WeCom reminders—what do customers actually open?  
7. What retention / deletion expectation do customers already assume for accident photos?  
8. If a second office copied this, what must be configurable in one afternoon?  
9. Which single metric would make him renew a pilot: speed to broker-ready, fewer calls, or fewer missing docs?  
10. What would make him say “stop” after one bad case?

---

## 6. Real-pilot measurements

Measure only with instrumentation that exists or lands this week. Mark hypotheses separately.

| Metric | Status | Hypothesis (unproven) |
|--------|--------|------------------------|
| Time invite/open → first action | Timing V1 | Shorter with known-customer confirm |
| Time first action → formal submit | Timing V1 + business stamps | AI story assist reduces dwell |
| Request More loop count | Business facts export | AI missing-fact questions reduce loops |
| Supplement turnaround | Business facts export | Clearer requests → faster return |
| Broker first open → office accept | Timing + business | Cleaner Brief → faster accept |
| AI accept / edit / reject rates | **After Day 3** | Edit rate reveals prompt quality |
| Fallback rate / latency | **After Day 3** | Fallback stays rare on QA |
| Calls avoided / revenue | **Unsupported** | Do not report |

---

## 7. Known risks and assumptions

| Risk / assumption | Mitigation |
|-------------------|------------|
| LangGraph phone QA not yet frozen | Day 1 P0; flag off if blocked |
| Doc sprawl (P16 constitution vs P20 vs Case Builder NS) | This week: Case Builder NS + plan + gates are execution SSOT; P20 remains development law; CURRENT_PRODUCT_SHAPE remains deploy truth |
| UX ledger Critical C1 still “open” historically | Do not claim full DevTools matrix; use Stage phone evidence + Sunday walkthrough |
| Metrics n is tiny | Always publish `statistically_meaningful=false` / small-n notes |
| LangSmith PII in traces | Day 2 redaction + Gate 8 |
| MCP scope creep | Day 5 thin tools only; product_only independent |
| Cost burn on QA scale | Restore min0/max2 after demos |
| Aspiration docs mistaken for shipped (macro outline, archive blueprints) | Prefer closeouts + tests over sprint recon docs |
| Founder time is the bottleneck | Plan lists minimal phone actions; agents do the rest |

---

## Anti-duplication rules

1. **This week’s work items** are named only as `D#-*` / `S-*` in the six-day plan.  
2. **UX defects** stay in `ux_problem_ledger.md` (IDs C/H/M/L).  
3. **Frozen slices** stay in evidence closeouts; do not re-list as open work.  
4. **Portfolio narratives** live under `docs/portfolio/`; link evidence, don’t fork backlogs.  
5. If a new idea appears, add one row here under §3 or §4 — do not create a fourth plan doc.
